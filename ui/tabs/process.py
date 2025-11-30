"""
Componentes para la pestaña de entendimiento del proceso (BPMN)
"""
import streamlit as st
import pandas as pd
import re
from config import FILE_CONFIG, BPMN_CONFIG
from services.data_processing import find_matching_columns
from services.bpmn import (
    build_bpmn_xml_advanced,
    render_bpmn_xml,
    render_bpmn_editable,
)

def render_process_understanding_tab(
    uploaded_data,
    validated_data=None,
    validation_result=None
) -> None:
    """
    Renderizar la pestaña de entendimiento del proceso con BPMN HÍBRIDO.
    Modo Lectura (Viewer) y Modo Edición (Modeler)
    """
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: var(--primary); margin-bottom: 1rem; font-weight: 700;">📊 Generador de Flujo</h1>
        <p style="color: var(--muted-foreground); font-size: 1.1rem; margin: 0;">
            Visualiza y edita tu diagrama de proceso
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. Validar que haya datos cargados
    if uploaded_data is None:
        st.markdown("""
        <div style="
            background: #F8F9FA;
            border: 2px dashed #1ABC9C;
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            margin: 2rem 0;
        ">
            <div style="color: #7F8C8D; font-size: 1.2rem;">
                📂 <strong>Primero carga tus datos</strong><br>
                Ve a la pestaña "Carga de Datos" para subir tu archivo Excel
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Usar el DataFrame validado (si existe), sino el original
    # 👉 Asegurar que validated_data esté en session_state
    data = validated_data if validated_data is not None else uploaded_data

    if validated_data is not None:
        st.session_state.validated_data = validated_data

    df_valid = st.session_state.get("validated_data", data)

    # 👉 Crear columna Dependencias SOLO una vez
    if df_valid is not None and "Dependencias" not in df_valid.columns:
        df_valid["Dependencias"] = ""
        st.session_state.validated_data = df_valid

    # A partir de aquí usa df_valid en lugar de validated_data
    validated_data = df_valid


    # Verificar columnas mínimas
    required_columns = ["Actividad", "Cargo que ejecuta la tarea"]
    column_matches = find_matching_columns(data.columns.tolist(), required_columns)
    missing_columns = [col for col in required_columns if col not in column_matches]
    
    if missing_columns:
        st.error(f"❌ No se pudieron encontrar las columnas necesarias: {', '.join(missing_columns)}")
        st.info("💡 Asegúrate de que tu archivo contenga columnas similares a 'Actividad' y 'Cargo que ejecuta la tarea'")
        
        st.markdown("**📋 Columnas disponibles en tu archivo:**")
        for col in uploaded_data.columns:
            st.write(f"• {col}")
        return

    # 2. Información sobre el generador
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    ">
        <strong>💡 Cómo funciona:</strong> Se genera el diagrama del flujo actual, incluyendo responsables y tiempos por actividad.
    </div>
    """, unsafe_allow_html=True)

    # 3. Botón para generar BPMN
    btn_validator = st.button(
        "🧪 Generar Diagrama de Flujo",
        type="primary",
        use_container_width=True,
        help="Genera el diagrama usando los tiempos y dependencias"
    )

    # 4. Validar configuración de Gemini
    if st.session_state.get("selected_model") != "gemini":
        st.warning("⚠️ Para usar el generador BPMN, selecciona 'Google Gemini 2.0' en la barra lateral")
        return
    
    if not st.session_state.get("api_key"):
        st.error("❌ Necesitas configurar tu API Key de Google Gemini en la barra lateral")
        return

    # 5. Generar BPMN
    if btn_validator or st.session_state.get("force_regen_bpmn"):
        # limpiar la bandera para próximos ciclos
        st.session_state.force_regen_bpmn = False

        if validation_result is None or not validation_result.get("success") or validated_data is None:
            st.error("❌ No hay un resultado válido del Validador de Dependencias.")
            st.info("💡 Asegúrate de haber cargado un archivo Excel válido en la pestaña 'Carga de Datos'")
        else:
            with st.spinner("🎨 Generando diagrama de flujo..."):
                # 🔄 Asegurar que usamos la versión más reciente de los datos (del session_state si existe)
                # Esto corrige el bug donde "Regenerar Diagrama" usaba datos antiguos
                data_val = st.session_state.get("validated_data", validated_data)

                column_matches_val = find_matching_columns(
                    data_val.columns.tolist(),
                    FILE_CONFIG['expected_columns']
                )

                activity_col = column_matches_val.get("Actividad")
                desc_col     = column_matches_val.get("Descripción")  
                resp_col     = column_matches_val.get("Cargo que ejecuta la tarea")
                auto_col     = column_matches_val.get("Tarea Automatizada")
                time_std_col = column_matches_val.get("Tiempo Estándar")
                time_avg_col = column_matches_val.get("Tiempo Promedio")
                tmin_col     = column_matches_val.get("Tiempo Menor")
                tmax_col     = column_matches_val.get("Tiempo Mayor")

                if not activity_col:
                    st.error("❌ No se encontró la columna 'Actividad' para construir las tareas BPMN.")
                    return

                # Construir actividades
                activities = []
                for idx, row in data_val.iterrows():
                    act_id = f"A{idx+1}"
                    t_std = float(row[time_std_col]) if time_std_col and pd.notna(row[time_std_col]) else None
                    
                    activities.append({
                        "id": act_id,
                        "name": str(row[activity_col]),
                        "description": str(row[desc_col]) if desc_col and pd.notna(row[desc_col]) else "",
                        "responsible": str(row[resp_col]) if resp_col and pd.notna(row[resp_col]) else "Sin asignar",
                        "automated": str(row[auto_col]).upper() in ["SI", "SÍ", "YES"] if auto_col in data_val.columns else False,
                        "time_standard": t_std,
                        "time_avg": float(row[time_avg_col]) if time_avg_col and pd.notna(row[time_avg_col]) else None,
                        "time_min": float(row[tmin_col]) if tmin_col and pd.notna(row[tmin_col]) else None,
                        "time_max": float(row[tmax_col]) if tmax_col and pd.notna(row[tmax_col]) else None,
                    })
                
                # ================================
                # 4) Construir flujos (edges BPMN)
                # ================================
                id_set = {a["id"].upper() for a in activities}
                flows = []

                # 4.1 Intentar usar la columna "Dependencias" (edición manual)
                use_dep_col = (
                    "Dependencias" in validated_data.columns
                    and any(str(x).strip() for x in validated_data["Dependencias"])
                )

                if use_dep_col:
                    invalid_refs = set()

                    for idx, row in validated_data.iterrows():
                        target_id = f"A{idx+1}".upper()
                        raw_deps = str(row.get("Dependencias") or "").strip()
                        if not raw_deps:
                            continue

                        # Separar por coma o punto y coma
                        for dep in re.split(r"[;,]", raw_deps):
                            dep = dep.strip()
                            if not dep:
                                continue

                            # Permitir "1" o "A1" o "a1"
                            if re.fullmatch(r"\d+", dep):
                                dep_id = f"A{dep}".upper()
                            else:
                                dep_id = dep.replace(" ", "").upper()

                            if dep_id not in id_set:
                                invalid_refs.add(dep)
                                continue

                            flows.append({
                                "source": dep_id,
                                "target": target_id,
                                "name": None
                            })

                    if invalid_refs:
                        st.warning(
                            "⚠️ Algunas dependencias no coinciden con IDs válidos de actividades: "
                            + ", ".join(sorted(invalid_refs))
                            + ". Usa IDs tipo A1, A2, A3… o números (1,2,3) que se convierten a A1, A2, A3."
                        )

                    if not flows:
                        st.warning(
                            "⚠️ No se pudo construir ningún flujo a partir de la columna 'Dependencias'. "
                            "Se usará el grafo de dependencias original (si existe) o un flujo secuencial."
                        )

                # 4.2 Fallback: usar dependency_graph del validador si no hay dependencias válidas
                if not flows:
                    dep_graph = validation_result.get("validation", {}).get("dependency_graph", {})
                    edges = dep_graph.get("edges", []) if isinstance(dep_graph, dict) else []

                    for e in edges:
                        raw_src = (e.get("from") or "").strip()
                        raw_dst = (e.get("to") or "").strip()
                        etype   = (e.get("type") or "sequential").lower()

                        src = raw_src.replace(" ", "").upper()
                        dst = raw_dst.replace(" ", "").upper()

                        if src not in id_set or dst not in id_set:
                            continue

                        label = None
                        if etype == "parallel":
                            label = "Paralelo"
                        elif etype != "sequential":
                            label = etype

                        flows.append({
                            "source": src,
                            "target": dst,
                            "name": label
                        })


                # Generar XML BPMN
                bpmn_xml = build_bpmn_xml_advanced(
                    activities=activities,
                    flows=flows if flows else None,
                    pool_name=BPMN_CONFIG.get("pool_name", "Proceso con tiempos estimados"),
                    use_lanes=BPMN_CONFIG.get("use_lanes", True),
                    decisions=[],
                    timers=[],
                    messages=[],
                    subprocesses=[],
                    add_di=BPMN_CONFIG.get("add_di", True),
                    show_times=BPMN_CONFIG.get("show_times", True)
                )

                # Guardar XML en session state
                st.session_state.current_bpmn_xml = bpmn_xml
                st.session_state.current_activities = activities

                st.success("✅ Diagrama generado exitosamente")

    # 6. Mostrar diagrama si existe
    if st.session_state.get("current_bpmn_xml"):
        st.markdown("---")
        st.markdown("### 🎨 Visualización del Diagrama")
        
        # MODO HÍBRIDO: Toggle entre Viewer y Modeler
        col_mode, col_edit = st.columns([3, 1])
        
        with col_edit:
            edit_mode = st.toggle(
                "✏️ Modo Edición", 
                value=False,
                help="Activa para editar el diagrama visualmente (arrastrar actividades y cambiar conexiones)"
            )
        
        with col_mode:
            if edit_mode:
                st.info("📝 **Modo Edición Activo:** Puedes reorganizar el diagrama. Los cambios se pueden descargar en XML.")
            else:
                st.info("👁️ **Modo Lectura:** Visualización optimizada del diagrama.")
        
        # Renderizar según el modo
        if edit_mode:
            # Reiniciar bandera de guardado al entrar en modo edición
            st.session_state.bpmn_guardado = False

            # Render editable BPMN y obtener el XML editado si lo hay
            bpmn_editado = render_bpmn_editable(
                st.session_state.current_bpmn_xml, 
                height=800, 
                key="bpmn_editor"
            )

            # Si el usuario pulsa el botón "Guardar en Backend" del componente, bpmn_editado tendrá el XML editado
            if bpmn_editado:
                st.session_state.current_bpmn_xml = bpmn_editado
                st.session_state.bpmn_guardado = True
                
                # 🔄 SINCRONIZACIÓN BIDIRECCIONAL: Actualizar tabla desde el diagrama
                try:
                    import xml.etree.ElementTree as ET
                    
                    # Parsear XML
                    # Eliminar namespaces para facilitar búsqueda (hack simple)
                    xml_clean = re.sub(r'\sxmlns="[^"]+"', '', bpmn_editado, count=1)
                    root = ET.fromstring(xml_clean)
                    
                    # Namespaces comunes en BPMN
                    ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
                    
                    # Buscar tareas. Intentar con y sin namespace
                    tasks = root.findall(".//bpmn:task", ns)
                    if not tasks:
                        tasks = root.findall(".//task")
                        
                    if tasks and validated_data is not None:
                        df_update = validated_data.copy()
                        changes_count = 0
                        
                        # Buscar columna de actividad
                        col_matches = find_matching_columns(df_update.columns.tolist(), ["Actividad"])
                        act_col = col_matches.get("Actividad")
                        
                        if act_col:
                            for task in tasks:
                                t_id = task.get("id") # Ej: A1
                                t_name = task.get("name")
                                
                                # Extraer índice de "A1" -> 1 -> index 0
                                if t_id and t_id.startswith("A") and t_id[1:].isdigit():
                                    idx = int(t_id[1:]) - 1
                                    
                                    if 0 <= idx < len(df_update):
                                        current_name = str(df_update.at[idx, act_col])
                                        if t_name and t_name != current_name:
                                            df_update.at[idx, act_col] = t_name
                                            changes_count += 1
                            
                            if changes_count > 0:
                                st.session_state.validated_data = df_update
                                st.success(f"✅ Tabla actualizada con {changes_count} cambios del diagrama.")
                                st.rerun()
                                
                except Exception as e:
                    st.error(f"Error al sincronizar diagrama con tabla: {e}")

                st.success("Diagrama guardado en la sesión.")

            # Advertencia solo si no se ha guardado en esta ejecución
            if not st.session_state.get("bpmn_guardado", False) and not bpmn_editado:
                st.warning("""
                ⚠️ **Importante:** Los cambios visuales en el diagrama (posiciones, conexiones) 
                se pueden descargar pero NO se sincronizan automáticamente con la tabla de datos. 
                Para cambiar tiempos o propiedades, edita la tabla abajo y regenera el diagrama.
                """)
        else:
            render_bpmn_xml(
                st.session_state.current_bpmn_xml, 
                height=800, 
                key="bpmn_viewer"
            )
        
        # 7. Panel de edición de propiedades
        st.markdown("---")
        st.markdown("### ✏️ Editar Propiedades de Actividades")
        
        with st.expander("📝 Editor de Tabla", expanded=True):
            st.info("""
            💡 **Cómo usar:** 
            1. Edita los valores en la tabla (nombres, tiempos, responsables, dependencias)
            2. Presiona el botón "Regenerar Diagrama"
            3. El diagrama se actualizará con los nuevos valores
            """)

            if validated_data is not None:
                # Seleccionar columnas editables (incluimos dependencias y tiempo estandar)
                editable_columns = []
                for col in validated_data.columns:
                    if any(keyword in col.lower() for keyword in [
                        "actividad", "descripción", "cargo", "responsable",
                        "tiempo", "automatizada", "colaboradores", "dependencia", "estandar"
                    ]):
                        editable_columns.append(col)

            if editable_columns:
                df_to_edit = validated_data[editable_columns].copy()

                # Configuración de columnas para el editor
                column_config = {}
                
                # Identificar columnas de tiempo para configurarlas como numéricas
                for col in editable_columns:
                    col_lower = col.lower()
                    is_numeric_col = any(k in col_lower for k in ["tiempo", "estandar", "min", "colaboradores", "no."])
                    
                    if is_numeric_col:
                        # 🔢 Forzar conversión a numérico para evitar errores de tipo con NumberColumn
                        # Esto convierte "10 min" -> NaN (o lo que se pueda) y asegura que sea editable
                        try:
                            df_to_edit[col] = pd.to_numeric(df_to_edit[col], errors='coerce')
                        except Exception:
                            pass

                        column_config[col] = st.column_config.NumberColumn(
                            col,
                            help="Tiempo en minutos",
                            min_value=0,
                            step=1,
                            required=False
                        )
                    else:
                        # Configurar el resto como texto editable explícito
                        column_config[col] = st.column_config.TextColumn(
                            col,
                            required=False
                        )

                df_edited = st.data_editor(
                    df_to_edit,
                    use_container_width=True,
                    hide_index=False,
                    num_rows="fixed",
                    key="activity_editor",
                    column_config=column_config
                )

                # 💾 PERSISTENCIA INMEDIATA: Guardar cambios al dar Enter
                # Esto asegura que si se recarga la página (rerun), los datos no se pierdan
                if df_edited is not None:
                    has_changes = False
                    for col in editable_columns:
                        # Comparar series para ver si hay cambios (simple check)
                        if not df_edited[col].equals(df_to_edit[col]):
                            validated_data[col] = df_edited[col]
                            has_changes = True
                    
                    if has_changes:
                        st.session_state.validated_data = validated_data

                col_regen, col_cancel = st.columns([1, 3])

                with col_regen:
                    if st.button("🔄 Regenerar Diagrama", type="primary", use_container_width=True):
                        # ✅ Guardar cambios en session_state.validated_data
                        for col in editable_columns:
                            validated_data[col] = df_edited[col]

                        st.session_state.validated_data = validated_data

                        # Marca para que se regenere el BPMN en este mismo rerun
                        st.session_state.force_regen_bpmn = True
                        st.success("✅ Datos actualizados, regenerando diagrama...")
                        st.rerun()
            else:
                st.info("No se encontraron columnas editables relevantes.")
