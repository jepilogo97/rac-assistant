"""
Componentes para la pestaña de Proceso TO-BE
"""
import streamlit as st
import pandas as pd
import traceback
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional
from services.prompt_to_be import get_prompt_TOBE

def parse_tobe_response(response_text: str) -> Dict[str, Any]:
    """Parsear la respuesta del TO-BE y extraer el JSON estructurado"""
    if not response_text or not response_text.strip():
        return {
            "success": False,
            "error": "Respuesta vacía",
            "raw_text": response_text,
            "actividades_optimizadas": [],
            "sipoc": {},
            "mejoras_cuantitativas": {}
        }
    
    try:
        # Limpiar el texto de respuesta
        clean_text = response_text.strip()
        json_str = None
        
        # Estrategia 1: Buscar JSON en bloque de código markdown (más común)
        patterns = [
            r'```json\s*(\{.*?\})\s*```',  # ```json { ... } ```
            r'```json\s*(\{.*)',  # ```json { ... (sin cierre)
            r'```\s*(\{.*?\})\s*```',  # ``` { ... } ```
            r'```\s*(\{.*)',  # ``` { ... (sin cierre)
        ]
        
        for pattern in patterns:
            json_match = re.search(pattern, clean_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                break
        
        # Estrategia 2: Buscar JSON que contenga palabras clave del formato esperado
        if not json_str:
            # Buscar JSON que contenga "actividades_optimizadas" o "mejoras_cuantitativas"
            keyword_patterns = [
                r'(\{.*?"actividades_optimizadas".*?\})',
                r'(\{.*?"mejoras_cuantitativas".*?\})',
                r'(\{.*?"sipoc".*?\})',
            ]
            for pattern in keyword_patterns:
                json_match = re.search(pattern, clean_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1).strip()
                    break
        
        # Estrategia 3: Buscar el primer { hasta el último } balanceado (más robusta)
        if not json_str:
            start_idx = clean_text.find('{')
            if start_idx != -1:
                # Encontrar el último } balanceado contando llaves
                brace_count = 0
                end_idx = start_idx
                in_string = False
                escape_next = False
                
                for i in range(start_idx, len(clean_text)):
                    char = clean_text[i]
                    
                    if escape_next:
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        continue
                    
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    
                    if not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = i + 1
                                break
                
                if end_idx > start_idx:
                    json_str = clean_text[start_idx:end_idx].strip()
        
        # Si encontramos un candidato, intentar parsearlo
        if json_str:
            # Limpiar el JSON de posibles caracteres residuales
            json_str = json_str.strip()
            
            # Remover bloques de código markdown si aún existen
            json_str = re.sub(r'^```json\s*', '', json_str, flags=re.IGNORECASE)
            json_str = re.sub(r'^```\s*', '', json_str)
            json_str = re.sub(r'\s*```$', '', json_str)
            json_str = json_str.strip()
            
            # Intentar parsear el JSON
            try:
                parsed_data = json.loads(json_str)
                # Validar que sea un diccionario
                if isinstance(parsed_data, dict):
                    parsed_data["success"] = True
                    parsed_data["raw_text"] = response_text
                    return parsed_data
            except json.JSONDecodeError:
                # Si falla, intentar limpiar más agresivamente
                try:
                    # Buscar el primer { y último } válidos
                    first_brace = json_str.find('{')
                    last_brace = json_str.rfind('}')
                    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                        cleaned_json = json_str[first_brace:last_brace + 1]
                        parsed_data = json.loads(cleaned_json)
                        if isinstance(parsed_data, dict):
                            parsed_data["success"] = True
                            parsed_data["raw_text"] = response_text
                            return parsed_data
                except:
                    pass
        
        # Si no se pudo extraer JSON, devolver estructura vacía
        return {
            "success": False,
            "error": "No se pudo encontrar JSON válido en la respuesta",
            "raw_text": response_text,
            "actividades_optimizadas": [],
            "sipoc": {},
            "mejoras_cuantitativas": {}
        }
        
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Error al parsear JSON: {str(e)}",
            "raw_text": response_text,
            "resumen_as_is": {},
            "actividades_optimizadas": [],
            "sipoc": {},
            "mejoras_cuantitativas": {},
            "justificacion_texto": response_text
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error inesperado: {str(e)}",
            "raw_text": response_text,
            "resumen_as_is": {},
            "actividades_optimizadas": [],
            "sipoc": {},
            "mejoras_cuantitativas": {},
            "justificacion_texto": response_text
        }


def display_tobe_results(parsed_data: Dict[str, Any]) -> None:
    """Mostrar resultados del TO-BE en formato de tabla similar al Clasificador Lean"""
    
    st.markdown('<div class="cuadro-card">', unsafe_allow_html=True)
    st.markdown("""
      <div class="cuadro-header">
        <div>
          <p class="cuadro-title">🚀 Proceso TO-BE – Resultado</p>
          <div class="cuadro-sub">Análisis optimizado basado en clasificación Lean</div>
        </div>
      </div>
    """, unsafe_allow_html=True)
    
    # ========== SECCIÓN PRINCIPAL: Tabla Editable de Actividades Optimizadas ==========
    # Mostrar primero la tabla editable de actividades optimizadas (la más importante)
    actividades = parsed_data.get("actividades_optimizadas", [])
    
    # Mostrar mensaje si no hay actividades
    if not actividades:
        st.warning("⚠️ **No se encontraron actividades optimizadas en el resultado JSON.**")
        st.info("💡 El análisis TO-BE no generó actividades optimizadas. Verifica que el prompt se haya ejecutado correctamente.")
        # Mostrar el JSON completo para depuración
        with st.expander("🔍 Ver JSON completo recibido", expanded=False):
            st.json(parsed_data)
    
    if actividades:
        st.markdown("### 📊 Tabla Editable de Actividades Optimizadas")
        st.info("💡 **Tabla editable principal**: Aquí puedes ver y editar todas las actividades optimizadas del resultado JSON. Los cambios se guardan cuando presionas 'Guardar Cambios'.")
        
        df_actividades = pd.DataFrame(actividades)
        
        # Filtros
        fc1, fc2 = st.columns(2)
        with fc1:
            acciones = df_actividades["accion"].unique().tolist() if "accion" in df_actividades.columns else []
            filtro_accion = st.multiselect(
                "Filtrar por acción:",
                options=acciones,
                default=acciones,
                key="filtro_accion_tab5"
            )
        with fc2:
            columnas_disponibles = df_actividades.columns.tolist()
            columnas_default = [col for col in [
                "actividad",
                "descripcion",
                "clasificacion_original",
                "accion",
                "tiempo_original_minutos",
                "tiempo_mejorado_minutos",
                "reduccion_tiempo_porcentaje",
                "personas_originales",
                "personas_mejoradas",
                "justificacion_tiempo",
                "justificacion",
                "recomendacion_aplicada"
            ] if col in columnas_disponibles]
            mostrar_columnas = st.multiselect(
                "Columnas a mostrar:",
                options=columnas_disponibles,
                default=columnas_default,
                key="columnas_actividades_tab5"
            )
        
        # Aplicar filtros
        df_filtrado = df_actividades.copy()
        if "accion" in df_filtrado.columns and filtro_accion:
            df_filtrado = df_filtrado[df_filtrado["accion"].isin(filtro_accion)]
        
        # Usar data_editor para hacer la tabla editable
        edited_key = "tobe_edited_actividades_tab5"
        
        # Inicializar o actualizar el DataFrame editable
        if edited_key not in st.session_state:
            st.session_state[edited_key] = df_actividades.copy()
        
        # Aplicar filtros al DataFrame editable
        df_to_edit = st.session_state[edited_key].copy()
        if "accion" in df_to_edit.columns and filtro_accion:
            df_to_edit = df_to_edit[df_to_edit["accion"].isin(filtro_accion)]
        
        # Seleccionar columnas a mostrar
        if mostrar_columnas:
            df_to_edit = df_to_edit[mostrar_columnas]
        
        # Configurar columnas para mejor edición
        column_config_actividades = {}
        for col in df_to_edit.columns:
            col_lower = col.lower()
            if any(k in col_lower for k in ["tiempo", "minutos", "personas", "porcentaje", "reduccion"]):
                # Columnas numéricas
                column_config_actividades[col] = st.column_config.NumberColumn(
                    col,
                    help=f"Valor numérico para {col}",
                    min_value=0,
                    step=0.1 if "porcentaje" in col_lower or "reduccion" in col_lower else 1,
                    format="%.2f" if "porcentaje" in col_lower or "reduccion" in col_lower else "%.0f"
                )
            elif any(k in col_lower for k in ["justificacion", "descripcion", "recomendacion"]):
                # Columnas de texto largo
                column_config_actividades[col] = st.column_config.TextColumn(
                    col,
                    help=f"Texto descriptivo para {col}",
                    width="large"
                )
            else:
                # Columnas de texto normal
                column_config_actividades[col] = st.column_config.TextColumn(
                    col,
                    help=f"Campo de texto para {col}"
                )
        
        # Mostrar tabla editable de actividades optimizadas
        st.markdown("**📝 Edita los valores directamente en la tabla:**")
        edited_df = st.data_editor(
            df_to_edit,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config=column_config_actividades,
            key="editor_actividades_tab5"
        )
        
        # Actualizar el DataFrame completo con los cambios
        if mostrar_columnas:
            # Actualizar solo las columnas visibles
            for col in mostrar_columnas:
                if col in edited_df.columns and col in st.session_state[edited_key].columns:
                    # Mantener el índice original para actualizar correctamente
                    indices = df_to_edit.index
                    st.session_state[edited_key].loc[indices, col] = edited_df[col].values
        else:
            # Actualizar todo el DataFrame
            st.session_state[edited_key] = edited_df.copy()
        
        # Botón para guardar cambios y actualizar parsed_data
        col_save1, col_save2 = st.columns([1, 3])
        with col_save1:
            if st.button("💾 Guardar Cambios", key="save_actividades_tab5", type="primary"):
                # Actualizar parsed_data con los cambios
                parsed_data["actividades_optimizadas"] = st.session_state[edited_key].to_dict('records')
                # Actualizar también el resultado en session_state
                if st.session_state.get("tobe_result"):
                    response_text = st.session_state.tobe_result.get("response", "")
                    # Reconstruir el JSON con los cambios
                    try:
                        import json as json_module
                        # Intentar actualizar el JSON en la respuesta
                        updated_json = json_module.dumps(parsed_data, indent=2, ensure_ascii=False)
                        st.session_state.tobe_result["response"] = updated_json
                    except:
                        pass
                st.success("✅ Cambios guardados exitosamente!")
                st.rerun()
        
        st.markdown("---")
    
    # Métricas principales
    mejoras = parsed_data.get("mejoras_cuantitativas", {})
    actividades = parsed_data.get("actividades_optimizadas", [])
    total_actividades = len(actividades) if actividades else 0
    
    # Primera fila de métricas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Actividades", total_actividades)
    with col2:
        st.metric("Actividades Eliminadas", mejoras.get("actividades_eliminadas", 0))
    with col3:
        st.metric("Actividades Optimizadas", mejoras.get("actividades_optimizadas", 0))
    with col4:
        # Contar actividades de valor (VA) si existe la clasificación
        if actividades:
            va_count = sum(1 for act in actividades if act.get("clasificacion_original", "").upper() == "VA")
            va_pct = (va_count / total_actividades * 100) if total_actividades > 0 else 0
            st.metric("Actividades de Valor", va_count, delta=f"{va_pct:.1f}%")
        else:
            st.metric("Actividades de Valor", 0)
    
    # Segunda fila: métricas de tiempo y personal
    tiempo_original = mejoras.get("tiempo_total_original_minutos", 0)
    tiempo_mejorado = mejoras.get("tiempo_total_mejorado_minutos", 0)
    reduccion_tiempo = mejoras.get("reduccion_tiempo_total_porcentaje", 0)
    personas_originales = mejoras.get("personas_totales_originales", 0)
    personas_mejoradas = mejoras.get("personas_totales_mejoradas", 0)
    reduccion_personas = mejoras.get("reduccion_personas_porcentaje", 0)
    
    if tiempo_original > 0 or tiempo_mejorado > 0:
        st.markdown("### ⏱️ Métricas de Mejora de Tiempo y Personal")
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        with col_t1:
            tiempo_original_hrs = tiempo_original / 60 if tiempo_original > 0 else 0
            st.metric("Tiempo Total AS-IS", f"{tiempo_original:.1f} min", f"{tiempo_original_hrs:.2f} hrs")
        with col_t2:
            tiempo_mejorado_hrs = tiempo_mejorado / 60 if tiempo_mejorado > 0 else 0
            st.metric("Tiempo Total TO-BE", f"{tiempo_mejorado:.1f} min", f"{tiempo_mejorado_hrs:.2f} hrs")
        with col_t3:
            tiempo_ahorrado = tiempo_original - tiempo_mejorado
            tiempo_ahorrado_hrs = tiempo_ahorrado / 60 if tiempo_ahorrado > 0 else 0
            st.metric("Tiempo Ahorrado", f"{tiempo_ahorrado:.1f} min", f"{reduccion_tiempo:.1f}%", delta_color="inverse")
        with col_t4:
            reduccion_personas_val = personas_originales - personas_mejoradas
            st.metric("Reducción de Personal", f"{reduccion_personas_val:.0f} personas", f"{reduccion_personas:.1f}%", delta_color="inverse")
    
    # Tabla SIPOC
    sipoc = parsed_data.get("sipoc", {})
    sipoc_data = []  # Inicializar fuera del if para uso en exportación
    
    if sipoc:
        st.markdown("### 🗺️ Modelo SIPOC (TO-BE)")
        
        # Crear DataFrame para SIPOC
        # Suppliers
        for supplier in sipoc.get("suppliers", []):
            sipoc_data.append({"Elemento": "Supplier", "Descripción": supplier})
        
        # Inputs
        for input_item in sipoc.get("inputs", []):
            sipoc_data.append({"Elemento": "Input", "Descripción": input_item})
        
        # Process
        for process_step in sipoc.get("process", []):
            if isinstance(process_step, dict):
                nombre = process_step.get("nombre", "")
                descripcion = process_step.get("descripcion", "")
                paso = process_step.get("paso", "")
                desc_completa = f"Paso {paso}: {nombre}" if paso else nombre
                if descripcion:
                    desc_completa += f" - {descripcion}"
                sipoc_data.append({"Elemento": "Process", "Descripción": desc_completa})
            else:
                sipoc_data.append({"Elemento": "Process", "Descripción": str(process_step)})
        
        # Outputs
        for output in sipoc.get("outputs", []):
            sipoc_data.append({"Elemento": "Output", "Descripción": output})
        
        # Customers
        for customer in sipoc.get("customers", []):
            sipoc_data.append({"Elemento": "Customer", "Descripción": customer})
        
        if sipoc_data:
            df_sipoc = pd.DataFrame(sipoc_data)
            
            # Filtro por elemento SIPOC
            elementos = df_sipoc["Elemento"].unique().tolist()
            filtro_elemento = st.multiselect(
                "Filtrar por elemento SIPOC:",
                options=elementos,
                default=elementos,
                key="filtro_sipoc"
            )
            
            df_sipoc_filtrado = df_sipoc[df_sipoc["Elemento"].isin(filtro_elemento)]
            
            # Usar data_editor para hacer la tabla SIPOC editable
            edited_sipoc_key = "tobe_edited_sipoc"
            
            # Inicializar o actualizar el DataFrame editable SIPOC
            if edited_sipoc_key not in st.session_state:
                st.session_state[edited_sipoc_key] = df_sipoc.copy()
            
            # Aplicar filtros al DataFrame editable
            df_sipoc_to_edit = st.session_state[edited_sipoc_key].copy()
            df_sipoc_to_edit = df_sipoc_to_edit[df_sipoc_to_edit["Elemento"].isin(filtro_elemento)]
            
            # Mostrar tabla editable
            st.info("💡 **Tabla editable**: Puedes modificar los valores directamente en la tabla. Los cambios se guardan automáticamente.")
            edited_sipoc_df = st.data_editor(
                df_sipoc_to_edit,
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                key="editor_sipoc"
            )
            
            # Actualizar el DataFrame completo con los cambios
            indices = df_sipoc_to_edit.index
            for col in edited_sipoc_df.columns:
                if col in st.session_state[edited_sipoc_key].columns:
                    st.session_state[edited_sipoc_key].loc[indices, col] = edited_sipoc_df[col].values
            
            # Botón para guardar cambios SIPOC
            col_save1, col_save2 = st.columns([1, 3])
            with col_save1:
                if st.button("💾 Guardar Cambios SIPOC", key="save_sipoc", type="primary"):
                    # Reconstruir estructura SIPOC desde el DataFrame editado completo
                    sipoc_updated = {
                        "suppliers": [],
                        "inputs": [],
                        "process": [],
                        "outputs": [],
                        "customers": []
                    }
                    
                    for _, row in st.session_state[edited_sipoc_key].iterrows():
                        elemento = row.get("Elemento", "")
                        descripcion = row.get("Descripción", "")
                        
                        if elemento == "Supplier":
                            sipoc_updated["suppliers"].append(descripcion)
                        elif elemento == "Input":
                            sipoc_updated["inputs"].append(descripcion)
                        elif elemento == "Process":
                            sipoc_updated["process"].append(descripcion)
                        elif elemento == "Output":
                            sipoc_updated["outputs"].append(descripcion)
                        elif elemento == "Customer":
                            sipoc_updated["customers"].append(descripcion)
                    
                    parsed_data["sipoc"] = sipoc_updated
                    st.success("✅ Cambios en SIPOC guardados exitosamente!")
                    st.rerun()
    
    # Exportar resultados
    st.markdown("### 📥 Exportar Resultados")
    c1, c2, c3 = st.columns(3)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Preparar datos para exportación (usar datos editados si están disponibles)
    actividades_para_export = actividades
    sipoc_para_export = sipoc
    
    # Crear resumen desde actividades (ya que resumen_as_is no existe en el nuevo formato)
    resumen_para_export = {
        "total_actividades": len(actividades) if actividades else 0,
        "actividades_va": sum(1 for act in actividades if act.get("clasificacion_original", "").upper() == "VA") if actividades else 0,
        "actividades_nva_n": sum(1 for act in actividades if act.get("clasificacion_original", "").upper() == "NVA-N") if actividades else 0,
        "actividades_nva_p": sum(1 for act in actividades if act.get("clasificacion_original", "").upper() == "NVA-P") if actividades else 0,
        "tipos_desperdicio": {}  # Ya no disponible en el nuevo formato
    }
    
    # Usar datos editados si están en session_state
    if "tobe_edited_actividades_tab5" in st.session_state:
        actividades_para_export = st.session_state["tobe_edited_actividades_tab5"].to_dict('records')
        # Recalcular resumen con datos editados
        resumen_para_export = {
            "total_actividades": len(actividades_para_export) if actividades_para_export else 0,
            "actividades_va": sum(1 for act in actividades_para_export if act.get("clasificacion_original", "").upper() == "VA") if actividades_para_export else 0,
            "actividades_nva_n": sum(1 for act in actividades_para_export if act.get("clasificacion_original", "").upper() == "NVA-N") if actividades_para_export else 0,
            "actividades_nva_p": sum(1 for act in actividades_para_export if act.get("clasificacion_original", "").upper() == "NVA-P") if actividades_para_export else 0,
            "tipos_desperdicio": {}
        }
    elif "tobe_edited_actividades" in st.session_state:
        actividades_para_export = st.session_state["tobe_edited_actividades"].to_dict('records')
        # Recalcular resumen con datos editados
        resumen_para_export = {
            "total_actividades": len(actividades_para_export) if actividades_para_export else 0,
            "actividades_va": sum(1 for act in actividades_para_export if act.get("clasificacion_original", "").upper() == "VA") if actividades_para_export else 0,
            "actividades_nva_n": sum(1 for act in actividades_para_export if act.get("clasificacion_original", "").upper() == "NVA-N") if actividades_para_export else 0,
            "actividades_nva_p": sum(1 for act in actividades_para_export if act.get("clasificacion_original", "").upper() == "NVA-P") if actividades_para_export else 0,
            "tipos_desperdicio": {}
        }
    
    if "tobe_edited_sipoc" in st.session_state:
        # Reconstruir SIPOC desde el DataFrame editado
        sipoc_para_export = {
            "suppliers": [],
            "inputs": [],
            "process": [],
            "outputs": [],
            "customers": []
        }
        for _, row in st.session_state["tobe_edited_sipoc"].iterrows():
            elemento = row.get("Elemento", "")
            descripcion = row.get("Descripción", "")
            if elemento == "Supplier":
                sipoc_para_export["suppliers"].append(descripcion)
            elif elemento == "Input":
                sipoc_para_export["inputs"].append(descripcion)
            elif elemento == "Process":
                sipoc_para_export["process"].append(descripcion)
            elif elemento == "Output":
                sipoc_para_export["outputs"].append(descripcion)
            elif elemento == "Customer":
                sipoc_para_export["customers"].append(descripcion)
    
    export_data = {
        "resumen": resumen_para_export,
        "actividades_optimizadas": actividades_para_export,
        "sipoc": sipoc_para_export,
        "mejoras": mejoras,
        "fecha_analisis": ts
    }
    
    with c1:
        # Excel
        try:
            from io import BytesIO
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                if actividades_para_export:
                    pd.DataFrame(actividades_para_export).to_excel(writer, sheet_name="Actividades Optimizadas", index=False)
                if sipoc_data:
                    # Reconstruir sipoc_data desde el DataFrame editado si está disponible
                    if "tobe_edited_sipoc" in st.session_state:
                        sipoc_data_export = []
                        for _, row in st.session_state["tobe_edited_sipoc"].iterrows():
                            sipoc_data_export.append({
                                "Elemento": row.get("Elemento", ""),
                                "Descripción": row.get("Descripción", "")
                            })
                        pd.DataFrame(sipoc_data_export).to_excel(writer, sheet_name="SIPOC", index=False)
                    else:
                        pd.DataFrame(sipoc_data).to_excel(writer, sheet_name="SIPOC", index=False)
            excel_data = excel_buffer.getvalue()
            st.download_button(
                "📊 Descargar Excel",
                data=excel_data,
                file_name=f"proceso_tobe_{ts}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Error generando Excel: {str(e)}")
    
    with c2:
        # CSV
        try:
            if actividades_para_export:
                csv_data = pd.DataFrame(actividades_para_export).to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📄 Descargar CSV",
                    data=csv_data,
                    file_name=f"proceso_tobe_{ts}.csv",
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"Error generando CSV: {str(e)}")
    
    with c3:
        # JSON
        try:
            # Convierte objetos de tipo Series a diccionarios antes de serializar
            for key, value in export_data.items():
                if isinstance(value, pd.Series):
                    export_data[key] = value.to_dict()

            json_data = json.dumps(export_data, indent=2, ensure_ascii=False).encode('utf-8')
            st.download_button(
                "🔧 Descargar JSON",
                data=json_data,
                file_name=f"proceso_tobe_{ts}.json",
                mime="application/json"
            )
        except Exception as e:
            st.error(f"Error generando JSON: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)


def _prepare_tobe_data_context(classified_data) -> str:
    """
    Preparar el contexto de datos para el prompt TO-BE basado en datos clasificados.
    """
    if classified_data is None or classified_data.empty:
        return ""
    
    # Buscar columnas de tiempo y personas
    tiempo_cols = [col for col in classified_data.columns if any(x in col.lower() for x in ['tiempo', 'time', 'prom', 'promedio'])]
    personas_cols = [col for col in classified_data.columns if any(x in col.lower() for x in ['persona', 'colaborador', 'collaborator', 'no.'])]
    
    tiempo_info = ""
    if tiempo_cols:
        tiempo_info = f"\n- Columnas de tiempo disponibles: {', '.join(tiempo_cols[:3])}"
    
    personas_info = ""
    if personas_cols:
        personas_info = f"\n- Columnas de personal disponibles: {', '.join(personas_cols[:2])}"
    
    return f"""
                
IMPORTANTE: Se proporcionan datos ya clasificados por el Clasificador Lean de Actividades. Estos datos incluyen:
- Clasificación Lean (VA/NVA-N/NVA-P) para cada actividad
- Justificaciones de las clasificaciones
- Tipos de desperdicio identificados
- Recomendaciones específicas para cada actividad{tiempo_info}{personas_info}

CRÍTICO PARA ESTIMACIÓN DE TIEMPO:
- Para cada actividad en los datos, busca las columnas de tiempo (ej: "Tiempo Prom (Min/Tarea)") y personas (ej: "No. Colaboradores que ejecutan la tarea")
- Usa estos valores como base para calcular el tiempo y personal mejorado en el proceso TO-BE
- Si una actividad se combina con otras, suma los tiempos y personas originales antes de aplicar la reducción
- Si una actividad se elimina, establece tiempo = 0 y personas = 0

Utiliza estos datos clasificados como base para tu análisis y optimización del proceso TO-BE.
"""


def _build_tobe_prompt(predefined_prompt: str, data_context: str) -> str:
    """
    Construir el prompt completo para el análisis TO-BE.
    """
    return f"""
            Analiza el proceso o servicio inicialmente suministrado en su estado actual (AS-IS), identificar desperdicios según la metodología Lean Six Sigma, y diseñar el proceso mejorado (TO-BE) sintetizado en un diagrama SIPOC.
            {data_context}
            PROMPT ORIGINAL: {predefined_prompt}
            
            Formato la respuesta de manera clara y estructurada.
            """


def _execute_tobe_analysis(analyzer, classified_data, tobe_prompt: str, predefined_prompt: str, model_name: str) -> None:
    """
    Ejecutar el análisis TO-BE usando el analyzer proporcionado.
    """
    has_classified_data = classified_data is not None and not classified_data.empty
    data_to_analyze = classified_data if has_classified_data else None
    
    with st.spinner("🎯 Analizando proceso y generando optimización TO-BE..."):
        response = analyzer.analyze(data_to_analyze, tobe_prompt)
    
    # Guardar resultado en session_state
    st.session_state.tobe_result = {
        "prompt": predefined_prompt,
        "response": response,
        "model": model_name
    }
    
    st.success("✅ Análisis TO-BE completado exitosamente!")


def render_tobe_tab(selected_model: str, api_key: Optional[str] = None) -> None:
    """Render the Proceso TO-BE tab interface"""
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: var(--primary); margin-bottom: 1rem; font-weight: 700;">🚀 Proceso TO-BE</h1>
        <p style="color: var(--muted-foreground); font-size: 1.1rem; margin: 0;">
            Análisis de proceso mejorado con metodología Lean Six Sigma
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if "tobe_result" not in st.session_state:
        st.session_state.tobe_result = None
    
    try:
        import torch
        _ = torch.tensor([1, 2, 3])
    except RuntimeError as e:
        if "torch" in str(e).lower() or "path" in str(e).lower():
            st.warning("⚠️ **Advertencia de compatibilidad:** Se detectó un problema con PyTorch. El análisis usará el motor local como respaldo.")
    
    # Obtener contexto del proceso
    contexto_proceso = st.session_state.get("project_id", "").strip()
    
    # Verificar si hay datos clasificados disponibles
    classified_data = st.session_state.get("classified_data")
    has_classified_data = classified_data is not None and not classified_data.empty
    
    # Obtener datos del Clasificador Lean de Actividades (classified_data_ca)
    classified_data_ca = st.session_state.get("classified_data_ca")
    has_classified_data_ca = classified_data_ca is not None
    if has_classified_data_ca:
        try:
            import pandas as pd
            has_classified_data_ca = isinstance(classified_data_ca, pd.DataFrame) and not classified_data_ca.empty
            # Validación adicional: verificar que tenga columnas mínimas esperadas
            if has_classified_data_ca:
                required_cols = ['nombre', 'tipo_actividad']  # Columnas mínimas necesarias
                has_classified_data_ca = all(col in classified_data_ca.columns for col in required_cols)
        except Exception as e:
            st.warning(f"⚠️ Error validando datos del Segmentador: {str(e)}")
            has_classified_data_ca = False
    
    # Mostrar información sobre el contexto y datos disponibles
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        if contexto_proceso:
            st.success(f"✅ **Contexto del proceso disponible**\n\n📋 {contexto_proceso[:100]}{'...' if len(contexto_proceso) > 100 else ''}")
        else:
            st.warning("⚠️ **No hay contexto del proceso definido.** Para mejores resultados, define el contexto en la pestaña 'Carga de Datos'.")
    
    with col_info2:
        if has_classified_data_ca:
            st.success(f"✅ **Datos del Segmentador de Actividades disponibles**\n\n📊 {len(classified_data_ca)} subactividades clasificadas")
        elif has_classified_data:
            st.success(f"✅ **Datos del Clasificador Lean disponibles**\n\n📊 {len(classified_data)} actividades clasificadas")
        else:
            st.warning("⚠️ **No se encontraron datos clasificados.** Ejecuta primero:\n\n1. **A. Actividades** (Segmentador) para generar subactividades\n2. O **A. desperdicios** (Clasificador Lean) como alternativa")
    
    # Prompt Predefinido (oculto al usuario)
    # Pasar el contexto del proceso y los datos clasificados al prompt
    # Priorizar classified_data_ca si está disponible, sino usar classified_data
    datos_para_prompt = classified_data_ca if has_classified_data_ca else (classified_data if has_classified_data else None)
    predefined_prompt = get_prompt_TOBE(contexto_proceso, datos_para_prompt)
    
    boton_ejecutar = st.button(
        "🚀 Ejecutar Prompt",
        type="primary",
        use_container_width=True,
        help="Procesará el prompt predefinido usando los datos clasificados si están disponibles"
    )
    
    if boton_ejecutar:
        try:
            st.info("🎯 Analizando proceso y generando optimización TO-BE... por favor espera ⏳")
            
            from services.analysis import get_analyzer
            analyzer = get_analyzer(selected_model, api_key)
            
            # Priorizar classified_data_ca sobre classified_data
            data_to_use = classified_data_ca if has_classified_data_ca else (classified_data if has_classified_data else None)
            
            # Preparar el contexto de datos y el prompt usando funciones auxiliares
            data_context = _prepare_tobe_data_context(data_to_use)
            tobe_prompt = _build_tobe_prompt(predefined_prompt, data_context)
            
            # Ejecutar el análisis con los datos correctos
            _execute_tobe_analysis(analyzer, data_to_use, tobe_prompt, predefined_prompt, selected_model)
            
        except RuntimeError as e:
            if "torch" in str(e).lower() or "path" in str(e).lower():
                st.warning("⚠️ Error de compatibilidad con PyTorch detectado. Usando analizador local como respaldo...")
                from services.analysis import LocalAnalyzer
                local_analyzer = LocalAnalyzer()
                
                # Priorizar classified_data_ca sobre classified_data (mismo que arriba)
                data_to_use = classified_data_ca if has_classified_data_ca else (classified_data if has_classified_data else None)
                
                # Usar las mismas funciones auxiliares para preparar el contexto y prompt
                data_context = _prepare_tobe_data_context(data_to_use)
                tobe_prompt = _build_tobe_prompt(predefined_prompt, data_context)
                
                # Ejecutar el análisis con el analizador local usando los datos correctos
                _execute_tobe_analysis(local_analyzer, data_to_use, tobe_prompt, predefined_prompt, "local (fallback)")
            else:
                st.error(f"❌ Error de runtime: {str(e)}")
                st.error(f"🔍 Detalles:\n{traceback.format_exc()}")
        except Exception as e:
            st.error(f"❌ Error al procesar el análisis TO-BE: {str(e)}")
            st.error(f"🔍 Detalles:\n{traceback.format_exc()}")
    
    # Mostrar resultado siempre que exista (similar al Clasificador Lean que muestra el dataframe)
    if st.session_state.get("tobe_result") is not None:
        result = st.session_state.tobe_result
        response_text = result.get("response", "")
        
        # Parsear la respuesta
        parsed_data = parse_tobe_response(response_text)
        
        # Mostrar resultados en tabla
        if parsed_data.get("success", False):
            display_tobe_results(parsed_data)
        else:
            # Si no se pudo parsear, mostrar el texto completo y un aviso
            error_msg = parsed_data.get("error", "No se pudo extraer JSON válido")
            st.warning(f"⚠️ **No se pudo extraer información estructurada de la respuesta.**\n\n**Error:** {error_msg}")
            
            # Mostrar información de depuración
            with st.expander("🔍 Información de Depuración y Respuesta Completa", expanded=True):
                st.markdown(f"**Longitud de la respuesta:** {len(response_text)} caracteres")
                
                # Buscar posibles JSONs en el texto
                st.markdown("**🔎 Buscando JSON en la respuesta...**")
                
                # Intentar encontrar cualquier JSON
                json_candidates = []
                start_positions = []
                for i, char in enumerate(response_text):
                    if char == '{':
                        start_positions.append(i)
                
                for start in start_positions[:5]:  # Probar los primeros 5 {
                    try:
                        brace_count = 0
                        end_idx = start
                        in_string = False
                        escape_next = False
                        
                        for i in range(start, min(start + 50000, len(response_text))):  # Limitar búsqueda
                            char = response_text[i]
                            
                            if escape_next:
                                escape_next = False
                                continue
                            
                            if char == '\\':
                                escape_next = True
                                continue
                            
                            if char == '"' and not escape_next:
                                in_string = not in_string
                                continue
                            
                            if not in_string:
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        end_idx = i + 1
                                        candidate = response_text[start:end_idx]
                                        try:
                                            test_json = json.loads(candidate)
                                            if isinstance(test_json, dict):
                                                json_candidates.append({
                                                    "start": start,
                                                    "end": end_idx,
                                                    "length": len(candidate),
                                                    "preview": candidate[:200] + "..." if len(candidate) > 200 else candidate
                                                })
                                        except:
                                            pass
                                        break
                    except:
                        continue
                
                if json_candidates:
                    st.success(f"✅ Se encontraron {len(json_candidates)} posibles JSONs en la respuesta")
                    for idx, candidate in enumerate(json_candidates, 1):
                        with st.expander(f"JSON Candidato {idx} (posición {candidate['start']}-{candidate['end']}, {candidate['length']} caracteres)", expanded=False):
                            st.code(candidate['preview'], language='json')
                            if st.button(f"🔄 Intentar usar este JSON", key=f"use_json_{idx}"):
                                try:
                                    full_json = response_text[candidate['start']:candidate['end']]
                                    parsed_candidate = json.loads(full_json)
                                    if isinstance(parsed_candidate, dict):
                                        parsed_candidate["success"] = True
                                        parsed_candidate["raw_text"] = response_text
                                        st.session_state.tobe_result["response"] = full_json
                                        st.success("✅ JSON aplicado! Recargando...")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error al parsear: {str(e)}")
                else:
                    st.warning("⚠️ No se encontraron JSONs válidos en la respuesta")
                
                st.markdown("---")
                st.markdown("**📋 Respuesta completa del modelo:**")
                st.text_area(
                    "Respuesta completa:",
                    value=response_text,
                    height=400,
                    key="tobe_raw_response_debug",
                    label_visibility="collapsed"
                )
            
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 🎯 Resultado del Análisis TO-BE (Texto Completo)")
            st.info(f"📊 Longitud de la respuesta: {len(response_text)} caracteres")
            
            # Intentar extraer JSON manualmente para mostrar
            with st.expander("📋 Ver Respuesta Completa", expanded=True):
                st.markdown("**Respuesta del modelo:**")
                st.markdown("---")
                # Mostrar en un text area para que sea más fácil copiar
                st.text_area(
                    "Respuesta completa:",
                    value=response_text,
                    height=400,
                    key="tobe_raw_response_viewer",
                    label_visibility="collapsed"
                )
                st.markdown("---")
            
            # Botón para intentar parsear manualmente
            if st.button("🔄 Intentar Parsear JSON Manualmente", key="manual_parse_json"):
                # Intentar encontrar y parsear JSON de nuevo con más agresividad
                try:
                    # Buscar cualquier JSON en el texto
                    import json as json_module
                    # Buscar el primer { y último } balanceado
                    start_idx = response_text.find('{')
                    if start_idx != -1:
                        brace_count = 0
                        end_idx = start_idx
                        for i in range(start_idx, len(response_text)):
                            if response_text[i] == '{':
                                brace_count += 1
                            elif response_text[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        if end_idx > start_idx:
                            json_candidate = response_text[start_idx:end_idx]
                            try:
                                parsed_manual = json_module.loads(json_candidate)
                                if isinstance(parsed_manual, dict):
                                    parsed_manual["success"] = True
                                    parsed_manual["raw_text"] = response_text
                                    st.session_state.tobe_result["parsed_data"] = parsed_manual
                                    st.success("✅ JSON parseado exitosamente! Recargando...")
                                    st.rerun()
                            except json_module.JSONDecodeError:
                                st.error("❌ El JSON encontrado no es válido")
                except Exception as e:
                    st.error(f"❌ Error al intentar parsear: {str(e)}")
            
            st.markdown("</div>", unsafe_allow_html=True)
