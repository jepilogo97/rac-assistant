"""
Componentes para la pestaña de segmentación de actividades
"""
import streamlit as st
import pandas as pd
import traceback
from datetime import datetime
import json
import re
from typing import Dict, Any, Optional
from services.segmentation import segment_process, export_segmentation_report, generate_segmentation_summary
from services.classification import export_classification_report # Reusing export function if compatible or use segmentation one

def ensure_arrow_safe_dataframe(df):
    if not isinstance(df, pd.DataFrame):
        return df
    try:
        df_safe = df.copy()
    except Exception:
        return df

    def _to_serializable(value):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""
        if isinstance(value, (dict, list)):
            try:
                return json.dumps(value, ensure_ascii=False)
            except Exception:
                return str(value)
        return str(value)

    def _series_is_numeric_like(series):
        try:
            cleaned = series.dropna().map(lambda x: str(x).strip())
            if cleaned.empty:
                return False
            return cleaned.map(lambda x: x.lstrip("-+").isdigit()).all()
        except Exception:
            return False

    preferred_numeric_cols = {
        "id",
        "dependencias",
        "tiempo_promedio_min",
        "tiempo_estimado_total_min",
        "tiempo_min",
        "duracion_min",
        "numero_subactividades"
    }

    for column in df_safe.columns:
        series = df_safe[column]
        col_name_lower = str(column).lower()

        wants_numeric = col_name_lower in preferred_numeric_cols or _series_is_numeric_like(series)
        if wants_numeric:
            try:
                numeric_series = pd.to_numeric(series, errors="coerce")
                if pd.api.types.is_integer_dtype(numeric_series.dtype) or pd.api.types.is_float_dtype(numeric_series.dtype):
                    df_safe[column] = numeric_series.astype("Int64") if pd.api.types.is_integer_dtype(numeric_series.dtype) else numeric_series.astype("Float64")
                    continue
            except Exception:
                pass

        needs_string = bool(getattr(series, "dtype", None) is not None and pd.api.types.is_object_dtype(series))
        if not needs_string:
            try:
                needs_string = series.map(lambda x: isinstance(x, (dict, list, tuple, set))).any()
            except Exception:
                needs_string = False
        if needs_string:
            try:
                sanitized_series = series.apply(_to_serializable)
                try:
                    df_safe[column] = sanitized_series.astype("string")
                except Exception:
                    df_safe[column] = sanitized_series.astype(str)
            except Exception:
                df_safe[column] = series.astype("string")

    return df_safe

def parse_model_response(resultado_modelo, proceso):
    """Parse robusto de respuesta del modelo con múltiples estrategias de recuperación"""
    
    # Estrategia 1: Ya es DataFrame
    if isinstance(resultado_modelo, pd.DataFrame):
        try:
            # Extraer valor escalar de proceso si existe como columna
            proceso_valor = proceso
            if "proceso" in resultado_modelo.columns:
                # Obtener el primer valor de la columna proceso (escalar, no Series)
                proceso_valor = resultado_modelo["proceso"].iloc[0] if len(resultado_modelo) > 0 else proceso
            
            return {
                "subactividades": resultado_modelo.to_dict(orient="records"),
                "proceso": str(proceso_valor) if proceso_valor is not None else proceso
            }
        except Exception:
            pass
    
    # Estrategia 2: Ya es dict - validar y sanitizar cualquier Series dentro
    if isinstance(resultado_modelo, dict):
        # Sanitizar el dict para asegurar que no contenga Series
        sanitized = {}
        for key, value in resultado_modelo.items():
            if isinstance(value, pd.Series):
                # Convertir Series a lista
                sanitized[key] = value.tolist()
            elif isinstance(value, pd.DataFrame):
                # Convertir DataFrame a lista de dicts
                sanitized[key] = value.to_dict(orient="records")
            else:
                sanitized[key] = value
        return sanitized
    
    # Estrategia 3: Es lista
    if isinstance(resultado_modelo, list):
        return {
            "subactividades": resultado_modelo,
            "proceso": proceso,
            "numero_subactividades": len(resultado_modelo)
        }
    
    # Estrategia 4: Es string - intentar parsear con múltiples técnicas
    raw = str(resultado_modelo).strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    
    # 4a. Intentar parsear directo
    try:
        return json.loads(raw)
    except:
        pass
    
    # 4b. Limpiar comillas tipográficas y comas finales
    cleaned = (
        raw.replace('"', '"').replace('"', '"')
           .replace("'", "'")
    )
    cleaned = re.sub(r",\s*\]", "]", cleaned)
    cleaned = re.sub(r",\s*\}", "}", cleaned)
    
    try:
        return json.loads(cleaned)
    except:
        pass
    
    # 4c. Buscar objeto JSON balanceado {...}
    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except:
            pass
    
    # 4d. Buscar array JSON balanceado [...]
    arr_match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if arr_match:
        try:
            arr = json.loads(arr_match.group(0))
            return {
                "subactividades": arr, 
                "proceso": proceso,
                "numero_subactividades": len(arr)
            }
        except:
            pass
    
    # Fallo total
    return None

def render_activity_segmenter_tab(uploaded_data) -> None:

    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: var(--primary); margin-bottom: 1rem; font-weight: 700;">🧠 Segmentador de Actividades (As-IS → Subactividades)</h1>
        <p style="color: var(--muted-foreground); font-size: 1.1rem; margin: 0;">
            Powered by Google Gemini 2.0 - Identifica y clasifica actividades de valor
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Validaciones
    if st.session_state.get("selected_model") != "gemini":
        st.warning("⚠️ Para usar el clasificador, selecciona 'Google Gemini 2.0' en la barra lateral.")
        return
    
    if not st.session_state.get("api_key"):
        st.error("❌ Necesitas configurar tu API Key de Google Gemini en la barra lateral.")
        return
    
    # Validar archivo AS-IS
    if "uploaded_data" not in st.session_state:
        st.warning("⚠ Debes cargar un archivo AS-IS en la pestaña 'Carga de Datos'.")
        return
    
    api_key = st.session_state.api_key
    proceso = st.session_state.get("project_id", "").strip()
    df_as_is = st.session_state["uploaded_data"]

    if not proceso:
        st.warning("⚠️ Debes ingresar una **Descripción del proyecto** antes de clasificar las actividades.")
        return

    # 🔄 VALIDACIÓN: Detectar si el archivo cambió desde el último procesamiento
    current_file_id = st.session_state.get("last_uploaded_file_id", "")
    last_processed_file_id = st.session_state.get("last_processed_file_id_actividades", "")
    
    if current_file_id and current_file_id != last_processed_file_id:
        # Archivo cambió - limpiar resultados antiguos y notificar al usuario
        st.session_state.classified_data_ca = None
        st.session_state.classification_summary_ca = None
        
        st.info("ℹ️ **Nuevo archivo detectado:** Los resultados anteriores de 'A. Actividades' han sido limpiados. "
               "Ejecuta el análisis nuevamente para procesar el nuevo archivo.")
    
    # Verificar si hay resultados previos válidos para el archivo actual
    has_previous_results = (
        st.session_state.get("classified_data_ca") is not None and
        last_processed_file_id == current_file_id
    )

    # Controles avanzados (optimización de llamadas al LLM)
    with st.expander("⚙️ Opciones avanzadas de segmentación", expanded=False):
        st.info("💡 **Recomendación**: Si experimentas errores de JSON, reduce las 'Subactividades por página' a 3-4")
        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1:
            page_size_user = st.number_input(
                "Subactividades por página", 
                min_value=3, 
                max_value=15, 
                value=4,  # Reducido de 5 a 4 para mayor estabilidad
                step=1,
                help="Menor valor = más estable pero más llamadas al modelo"
            )
        with col_a2:
            max_pages_user = st.number_input(
                "Máx. páginas", 
                min_value=1, 
                max_value=50, 
                value=15, 
                step=1,
                help="Número máximo de páginas a solicitar al modelo"
            )
        with col_a3:
            temperature_user = st.slider(
                "Temperatura (referencia)", 
                0.0, 
                1.0, 
                0.10, 
                0.05,
                help="0.0 = más determinista, 1.0 = más creativo"
            )
        use_cache_user = st.checkbox("Usar caché de páginas", value=True, 
                                     help="Reutiliza respuestas previas para acelerar el proceso")
        force_reclassify_user = st.checkbox("Forzar reclasificación", value=False,
                                           help="Ignora caché y regenera toda la clasificación")

    # Convertir AS-IS → texto para el modelo
    def df_to_as_is_text(df):
        columnas = df.columns.tolist()
        texto = ""
        for idx, row in df.iterrows():
            linea = " - ".join(str(row[col]) for col in columnas if str(row[col]).strip() != "")
            texto += f"{idx+1}. {linea}\n"
        return texto

    # Validar que el DataFrame no sea None y tenga columnas
    if df_as_is is None:
        st.warning("⚠ El dataset cargado está vacío. Carga un archivo válido en la pestaña 'Carga de Datos'.")
        return

    st.markdown("### Vista previa del proceso AS-IS cargado")
    df_as_is_preview = ensure_arrow_safe_dataframe(df_as_is)
    st.dataframe(df_as_is_preview, use_container_width=True)

    try:
        proceso_as_is_text = df_to_as_is_text(df_as_is)
    except Exception as e:
        st.error("Error preparando texto AS-IS: asegúrate que el archivo cargado contiene datos tabulares válidos.")
        st.error(str(e))
        return

    boton_clasificar = st.button(
        "🔎 Dividir y Clasificar Actividades",
        type="primary",
        use_container_width=True,
        disabled=not bool(proceso)
    )

    # Botón para segmentar
    if boton_clasificar:
        try:
            st.info("🧠 Analizando actividades... por favor espera ⏳")
            progress_bar = st.progress(0)
            status_text = st.empty()

            if "uploaded_data" not in st.session_state:
                st.warning("⚠ Primero carga un archivo válido en la pestaña 'Carga de Datos'.")
                pass # st.stop()

            df_as_is = st.session_state["uploaded_data"]

            # función de progreso usada por el agente (si lo soporta)
            def update_progress(current: int, total: int, activity_name: str):
                try:
                    progress = float(current) / float(total) if total else 0.0
                except Exception:
                    progress = 0.0
                progress = max(0.0, min(1.0, progress))
                try:
                    progress_bar.progress(progress)
                    status_text.text(f"Analizando: {activity_name} ({current}/{total})")
                except Exception:
                    pass

            with st.spinner("Analizando actividades..."):
                # Llamada principal al agente con todos los parámetros
                try:
                    resultado_modelo = segment_process(
                        proceso_general=proceso,
                        proceso_as_is=proceso_as_is_text,
                        api_key=api_key,
                        batch_mode=True,
                        progress_callback=update_progress,
                        max_pages=int(max_pages_user),
                        page_size=int(page_size_user),
                        use_cache=bool(use_cache_user),
                        force_reclassify=bool(force_reclassify_user),
                    )
                except TypeError as te:
                    # En caso de que la función no acepte algunos parámetros, reintentamos sin ellos
                    st.warning(f"⚠️ Algunos parámetros no son soportados por esta versión: {str(te)}")
                    resultado_modelo = segment_process(
                        proceso_general=proceso,
                        proceso_as_is=proceso_as_is_text,
                        api_key=api_key,
                        batch_mode=True,
                        progress_callback=update_progress
                    )

            if isinstance(resultado_modelo, pd.DataFrame):
                resultado_modelo = ensure_arrow_safe_dataframe(resultado_modelo)

            # limpiar barra y estado
            try:
                progress_bar.empty()
            except Exception:
                pass
            try:
                status_text.empty()
            except Exception:
                pass

            # Resumen y almacenamiento en sesión
            try:
                summary = generate_segmentation_summary(resultado_modelo)
            except Exception:
                summary = {}

            st.session_state.classified_data_ca = resultado_modelo
            st.session_state.classification_summary_ca = summary
            
            # 🔄 Guardar el ID del archivo procesado para detectar cambios futuros
            current_file_id = st.session_state.get("last_uploaded_file_id", "")
            st.session_state.last_processed_file_id_actividades = current_file_id

            st.success("✅ Clasificación completada exitosamente!")
            # Título y descripción breve de la tabla de resultados
            try:
                st.markdown("""
                <div style="margin-top:1rem;">
                    <h3 style="margin:0;">📋 Resultados de la Clasificación</h3>
                    <p style="margin:0; color:var(--muted-foreground);">Tabla con las subactividades extraídas y su clasificación sugerida. Incluye tipo de actividad, justificación y metadatos (proceso, fecha).</p>
                </div>
                """, unsafe_allow_html=True)
            except Exception:
                pass

            try:
                st.dataframe(resultado_modelo)
            except Exception:
                st.write(resultado_modelo)
        except Exception as e:
            st.error(f"❌ Error al clasificar: {str(e)}")
            st.error(f"🔍 Detalles:\n{traceback.format_exc()}")
    if st.session_state.get("classified_data_ca") is not None:
        st.markdown("### 📊 Resultados de Clasificación Anterior")
        
        # Verificar si los resultados corresponden al archivo actual
        current_file_id = st.session_state.get("last_uploaded_file_id", "")
        last_processed_file_id = st.session_state.get("last_processed_file_id_actividades", "")
        
        if current_file_id != last_processed_file_id:
            st.warning("⚠️ **Atención:** Los resultados mostrados corresponden a un archivo anterior. "
                      "Ejecuta el análisis nuevamente para procesar el archivo actual.")
        else:
            st.success("✅ Los resultados corresponden al archivo actual cargado.")
        
        # Recuperar el resultado previo de la sesión en una variable local para las operaciones siguientes
        try:
            resultado_modelo = st.session_state.get("classified_data_ca")
            if isinstance(resultado_modelo, pd.DataFrame):
                resultado_modelo = ensure_arrow_safe_dataframe(resultado_modelo)
        except Exception:
            resultado_modelo = None
        if st.button("🔄 Ver Resultados clasificación", key="ver resultados1"):
            display_classification_Act_results(
                st.session_state.classified_data_ca,
                st.session_state.classification_summary_ca
            )
      
        # Validar distintos tipos de retorno de `segment_process` de forma segura
        is_empty_df = isinstance(resultado_modelo, pd.DataFrame) and resultado_modelo.empty
        is_empty_str = isinstance(resultado_modelo, str) and resultado_modelo.strip() == ""
        is_false_bool = resultado_modelo is False

        if resultado_modelo is None or is_empty_df or is_empty_str or is_false_bool:
            st.error("❌ No se pudo procesar la respuesta del agente.")
            pass # st.stop()

        parsed = parse_model_response(resultado_modelo, proceso)
        json_text = None
        
        if parsed is None:
            raw = str(resultado_modelo).strip()
            st.error("❌ No se encontró JSON válido dentro de la respuesta del agente.")
            st.text_area("Respuesta completa:", raw, height=350)
            st.info("💡 **Sugerencias para resolver este error:**\n"
                   "1. Reduce 'Subactividades por página' a 3-5 en opciones avanzadas\n"
                   "2. Verifica que tu API Key de Gemini sea válida\n"
                   "3. Asegúrate de que el proceso AS-IS tenga información clara y completa")
            return
        
        # Sanitizar parsed para asegurar que es JSON-serializable
        def sanitize_for_json(obj):
            """Convierte objetos pandas (Series, DataFrame) a tipos JSON-serializables"""
            if isinstance(obj, pd.Series):
                return obj.tolist()
            elif isinstance(obj, pd.DataFrame):
                return obj.to_dict(orient="records")
            elif isinstance(obj, dict):
                return {k: sanitize_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [sanitize_for_json(item) for item in obj]
            else:
                return obj
        
        parsed = sanitize_for_json(parsed)
        
        try:
            json_text = json.dumps(parsed, ensure_ascii=False)
        except Exception as e:
            st.warning(f"⚠️ No se pudo serializar a JSON: {e}")
            json_text = None

        # ============================================================
        # 📊 Mostrar resultados
        # ============================================================

        if "subactividades" in parsed:
            df_result = pd.DataFrame(parsed["subactividades"])
            df_result = ensure_arrow_safe_dataframe(df_result)
            st.success("✔ Análisis completado")
            # Título y descripción de la tabla de subactividades parseadas
            try:
                st.markdown("""
                <div style="margin-top:0.5rem;">
                    <h3 style="margin:0;">🗂️ Subactividades extraídas</h3>
                    <p style="margin:0; color:var(--muted-foreground);">Listado estructurado de subactividades detectadas por el modelo. Cada fila representa una subactividad con su descripción, objetivo, tiempos estimados y sugerencia de automatización.</p>
                </div>
                """, unsafe_allow_html=True)
            except Exception:
                pass
            st.dataframe(df_result, use_container_width=True)

            # Botón descargar (con manejo de error para JSON serialization)
            try:
                json_download_data = json.dumps(parsed, ensure_ascii=False, indent=2)
                st.download_button(
                    label="📥 Descargar resultado JSON",
                    data=json_download_data,
                    file_name="resultado_actividades.json",
                    mime="application/json"
                )
            except TypeError as e:
                st.error(f"❌ Error al preparar descarga JSON: {e}")
                st.info("💡 Los datos se muestran en la tabla pero no se pueden exportar a JSON. "
                       "Esto puede ocurrir si hay objetos pandas en la respuesta.")

        else:
            st.warning("⚠ No se encontraron subactividades en el JSON.")
            st.text_area("JSON recibido:", json_text)


def display_classification_Act_results(df_classified: pd.DataFrame, summary: Dict) -> None:
    """Mostrar resultados de la clasificación en un cuadro visual (card),
    garantizando columnas: 'desperdicio', 'justificación', 'fecha de analisis'."""
    df_view = df_classified.copy()

    if "desperdicio" not in df_view.columns:
        if "Tipo Desperdicio" in df_view.columns:
            df_view["desperdicio"] = df_view["Tipo Desperdicio"].fillna("").astype(str)
        else:
            df_view["desperdicio"] = ""

    if "justificación" not in df_view.columns:
        if "Justificación" in df_view.columns:
            df_view["justificación"] = df_view["Justificación"].fillna("").astype(str)
        else:
            df_view["justificación"] = ""

    if "fecha de analisis" not in df_view.columns:
        if "Fecha Análisis" in df_view.columns:
            df_view["fecha de analisis"] = pd.to_datetime(
                df_view["Fecha Análisis"], errors="coerce"
            ).dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            df_view["fecha de analisis"] = ""

    st.markdown('<div class="cuadro-card">', unsafe_allow_html=True)
    st.markdown("""
      <div class="cuadro-header">
        <div>
          <p class="cuadro-title">🎯 Clasificación Lean – Resultado</p>
          <div class="cuadro-sub">Incluye totales de la clasificacion, automatizaciones y tipos de actividad </div>
        </div>
      </div>
    """, unsafe_allow_html=True)
    # Mostrar métricas clave provenientes directamente de generate_segmentation_summary
    # Campos esperados en `summary`: total_subactividades, tipos_actividad, porcentaje_operativas,
    # porcentaje_cognitivas, porcentaje_analiticas, porcentaje_colaborativa, porcentaje_decisoria,
    # porcentaje_administrativa, porcentaje_espera_transición, total_automatizables, total_posibles,
    # total_no_automatizables
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total subactividades", summary.get("total_subactividades", 0))
    with c2:
        st.metric("Automatizables (Sí)", summary.get("total_automatizables", 0))
    with c3:
        st.metric("Posibles automatizar", summary.get("total_posibles", 0))
    with c4:
        st.metric("No automatizables", summary.get("total_no_automatizables", 0))

    # Segunda fila: porcentajes por tipo
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.metric("Operativas (%)", f"{summary.get('porcentaje_operativas', 0):.1f}%")
    with p2:
        st.metric("Cognitivas (%)", f"{summary.get('porcentaje_cognitivas', 0):.1f}%")
    with p3:
        st.metric("Analíticas (%)", f"{summary.get('porcentaje_analiticas', 0):.1f}%")
    with p4:
        st.metric("Colaborativa (%)", f"{summary.get('porcentaje_colaborativa', 0):.1f}%")

    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.metric("Decisoria (%)", f"{summary.get('porcentaje_decisoria', 0):.1f}%")
    with q2:
        st.metric("Administrativa (%)", f"{summary.get('porcentaje_administrativa', 0):.1f}%")
    with q3:
        # clave con acento/guion usada en generate_segmentation_summary
        st.metric("Espera / Transición (%)", f"{summary.get('porcentaje_espera_transición', 0):.1f}%")
    with q4:
        # mostrar breakdown por tipo si está disponible
        tipos = summary.get("tipos_actividad", {})
        if isinstance(tipos, dict) and tipos:
            tipos_df = pd.DataFrame(list(tipos.items()), columns=["Tipo", "Cantidad"]).sort_values("Cantidad", ascending=False)
            st.caption("Distribución por tipo (top 5):")
            st.table(tipos_df.head(5))
        else:
            st.write("")

    st.markdown("### 📋 Detalle: subactividades")
    try:
        st.markdown("<div style='margin-bottom:0.5rem; color:var(--muted-foreground)'>Mostrando el resultante del segmentador (filas = subactividades).</div>", unsafe_allow_html=True)
    except Exception:
        pass

    # Mostrar solo las columnas solicitadas: id, nombre, tipo_actividad, tiempos, automatizable, justificacion, fecha_generacion
    try:
        cols_lower_map = {c.lower(): c for c in df_view.columns}

        def find_col(*names):
            for n in names:
                key = n.lower()
                if key in cols_lower_map:
                    return cols_lower_map[key]
            return None

        col_id = find_col('id')
        col_nombre = find_col('nombre', 'name', 'actividad')
        col_tipo = find_col('tipo_actividad', 'tipo', 'classification', 'clasificacion')
        col_t1 = find_col('tiempo_promedio_min', 'tiempo_promedio', 'tiempo_promedio_minutos')
        col_t2 = find_col('tiempo_estimado_total_min', 'tiempo_estimado_total', 'tiempo_total_min')
        col_automatizable = find_col('automatizable')
        col_just = find_col('justificacion', 'justificación', 'justificaciÃ³n')
        col_fecha = find_col('fecha_generacion', 'fecha_de_generacion', 'fecha')

        display_df = df_view.copy()

        # Crear columna 'tiempos' combinando las columnas de tiempo si existen
        tiempos_vals = []
        if col_t1 or col_t2:
            def make_tiempos(row):
                parts = []
                if col_t1:
                    v = row.get(col_t1, "")
                    if pd.notna(v) and str(v).strip() != "":
                        parts.append(f"avg: {v}")
                if col_t2:
                    v2 = row.get(col_t2, "")
                    if pd.notna(v2) and str(v2).strip() != "":
                        parts.append(f"total: {v2}")
                return ' / '.join(parts) if parts else ''

            display_df['tiempos'] = display_df.apply(make_tiempos, axis=1)
        else:
            display_df['tiempos'] = ""

        # Asegurar columnas solicitadas existen en el DataFrame final
        final_cols = []
        for c in [col_id, col_nombre, col_tipo, 'tiempos', col_automatizable, col_just, col_fecha]:
            if c and c in display_df.columns:
                final_cols.append(c)
            elif c == 'tiempos':
                final_cols.append('tiempos')
            else:
                # crear columna vacía con ese nombre si no existe (usar nombre amigable en minúsculas)
                # prefer usar el alias si no encontrada
                alias = c if isinstance(c, str) else None
                if alias and alias not in display_df.columns:
                    display_df[alias] = ""
                    final_cols.append(alias)

        # Normalizar nombres de columnas a la forma esperada en la vista (id, nombre, tipo_actividad, tiempos, automatizable, justificacion, fecha_generacion)
        # Para facilitar lectura, renombramos las columnas seleccionadas a los nombres esperados si es posible
        rename_map = {}
        if final_cols:
            # map first found id-like to 'id'
            if col_id and col_id in final_cols:
                rename_map[col_id] = 'id'
            if col_nombre and col_nombre in final_cols:
                rename_map[col_nombre] = 'nombre'
            if col_tipo and col_tipo in final_cols:
                rename_map[col_tipo] = 'tipo_actividad'
            if 'tiempos' in final_cols:
                rename_map['tiempos'] = 'tiempos'
            if col_automatizable and col_automatizable in final_cols:
                rename_map[col_automatizable] = 'automatizable'
            if col_just and col_just in final_cols:
                rename_map[col_just] = 'justificacion'
            if col_fecha and col_fecha in final_cols:
                rename_map[col_fecha] = 'fecha_generacion'

        display_df = display_df.rename(columns=rename_map)

        # Definir orden final garantizando presencia
        ordered = [c for c in ['id', 'nombre', 'tipo_actividad', 'tiempos', 'automatizable', 'justificacion', 'fecha_generacion'] if c in display_df.columns]

        if not ordered:
            st.warning("No se detectaron las columnas esperadas para mostrar el detalle. Mostrando DataFrame completo en su lugar.")
            st.dataframe(display_df, use_container_width=True)
        else:
            st.dataframe(display_df[ordered], use_container_width=True, hide_index=True)

    except Exception:
        # Fallback robusto: mostrar todo si algo falla
        try:
            st.dataframe(df_view, use_container_width=True)
        except Exception:
            st.write(df_view)

    st.markdown("### 📥 Exportar Resultados")
    c1, c2, c3 = st.columns(3)
    
    excel_data = export_segmentation_report(df_view, summary, "excel")
    csv_data   = export_segmentation_report(df_view, summary, "csv")
    json_data  = export_segmentation_report(df_view, summary, "json")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with c1:
        st.download_button(
            "📊 Descargar Excel",
            data=excel_data,
            file_name=f"clasificacion_lean_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with c2:
        st.download_button(
            "📄 Descargar CSV",
            data=csv_data,
            file_name=f"clasificacion_lean_{ts}.csv",
            mime="text/csv"
        )
    with c3:
        st.download_button(
            "🔧 Descargar JSON",
            data=json_data,
            file_name=f"clasificacion_lean_{ts}.json",
            mime="application/json"
        )

    st.markdown('</div>', unsafe_allow_html=True)
