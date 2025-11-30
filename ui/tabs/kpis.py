"""
Componentes para la pestaña de KPIs
"""
import streamlit as st
import pandas as pd
import traceback
import json
from typing import Dict, Any, Optional
from streamlit.runtime.scriptrunner import RerunException
from ui.tabs.tobe import parse_tobe_response

def _build_kpis_prompt(parsed_data: Dict[str, Any], mejoras: Dict, actividades: list, resumen: Dict) -> str:
    """Construir el prompt para generar análisis de KPIs"""
    
    prompt = f"""
Eres un analista experto en Lean Six Sigma y gestión de procesos. Tu tarea es analizar los resultados del proceso TO-BE y generar un análisis detallado de 5 KPIs clave.

DATOS DEL PROCESO TO-BE:

RESUMEN AS-IS (calculado desde actividades):
{json.dumps(resumen, indent=2, ensure_ascii=False) if resumen else "{}"}

MEJORAS CUANTITATIVAS:
{json.dumps(mejoras, indent=2, ensure_ascii=False)}

ACTIVIDADES OPTIMIZADAS (primeras 10):
{json.dumps(actividades[:10], indent=2, ensure_ascii=False) if len(actividades) > 0 else "[]"}

INSTRUCCIONES:
1. Analiza los datos numéricos proporcionados, especialmente las comparaciones entre valores originales (AS-IS) y mejorados (TO-BE).
2. Identifica los 5 KPIs más relevantes para mostrar el impacto de las mejoras.
3. Para cada KPI, proporciona:
   - Nombre del KPI
   - Valor original (AS-IS)
   - Valor mejorado (TO-BE)
   - Porcentaje de mejora
   - Descripción breve del impacto
   - Tipo de visualización recomendada (bar_chart, line_chart, area_chart, etc.)

RESPONDE EN FORMATO JSON con esta estructura:
{{
  "kpis": [
    {{
      "nombre": "Nombre del KPI",
      "valor_original": <número>,
      "valor_mejorado": <número>,
      "porcentaje_mejora": <número>,
      "descripcion": "Descripción del impacto",
      "tipo_visualizacion": "bar_chart|line_chart|area_chart|metric",
      "unidad": "minutos|horas|personas|porcentaje|actividades|etc"
    }}
  ],
  "resumen_impacto": "Resumen general del impacto de las mejoras"
}}

IMPORTANTE: 
- Usa los números reales de los datos proporcionados
- Enfócate en comparaciones original vs mejorado
- Los KPIs deben ser visualmente impactantes y fáciles de entender
- Incluye métricas de tiempo, personal, costos, y eficiencia
"""
    return prompt


def _display_kpis_visualizations(parsed_data: Dict[str, Any], mejoras: Dict, actividades: list, resumen: Dict) -> None:
    """Mostrar las visualizaciones de KPIs"""
    
    # Extraer valores numéricos clave
    tiempo_original = mejoras.get("tiempo_total_original_minutos", 0)
    tiempo_mejorado = mejoras.get("tiempo_total_mejorado_minutos", 0)
    reduccion_tiempo_pct = mejoras.get("reduccion_tiempo_total_porcentaje", 0)
    
    personas_originales = mejoras.get("personas_totales_originales", 0)
    personas_mejoradas = mejoras.get("personas_totales_mejoradas", 0)
    reduccion_personas_pct = mejoras.get("reduccion_personas_porcentaje", 0)
    
    actividades_eliminadas = mejoras.get("actividades_eliminadas", 0)
    actividades_optimizadas = mejoras.get("actividades_optimizadas", 0)
    # Calcular total_actividades desde la lista de actividades si resumen no lo tiene
    total_actividades = resumen.get("total_actividades", len(actividades) if actividades else 0)
    
    # KPI 1: Reducción de Tiempo Total del Proceso
    st.markdown("### 📊 KPI 1: Reducción de Tiempo Total del Proceso")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Tiempo Original (AS-IS)",
            f"{tiempo_original:.1f} min" if tiempo_original > 0 else "N/A",
            help="Tiempo total del proceso original en minutos"
        )
    with col2:
        st.metric(
            "Tiempo Mejorado (TO-BE)",
            f"{tiempo_mejorado:.1f} min" if tiempo_mejorado > 0 else "N/A",
            delta=f"-{reduccion_tiempo_pct:.1f}%" if reduccion_tiempo_pct > 0 else None,
            delta_color="inverse",
            help="Tiempo total del proceso optimizado en minutos"
        )
    with col3:
        st.metric(
            "Reducción Total",
            f"{reduccion_tiempo_pct:.1f}%",
            help="Porcentaje de reducción del tiempo total"
        )
    
    if tiempo_original > 0 and tiempo_mejorado > 0:
        tiempo_df = pd.DataFrame({
            "Estado": ["AS-IS (Original)", "TO-BE (Mejorado)"],
            "Tiempo (minutos)": [tiempo_original, tiempo_mejorado]
        })
        st.bar_chart(tiempo_df.set_index("Estado"), height=300)
    
    # KPI 2: Reducción de Personal
    st.markdown("### 👥 KPI 2: Reducción de Personal Requerido")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Personas Originales (AS-IS)",
            f"{personas_originales:.1f}" if personas_originales > 0 else "N/A",
            help="Número total de personas requeridas en el proceso original"
        )
    with col2:
        st.metric(
            "Personas Mejoradas (TO-BE)",
            f"{personas_mejoradas:.1f}" if personas_mejoradas > 0 else "N/A",
            delta=f"-{reduccion_personas_pct:.1f}%" if reduccion_personas_pct > 0 else None,
            delta_color="inverse",
            help="Número total de personas requeridas en el proceso optimizado"
        )
    with col3:
        st.metric(
            "Reducción de Personal",
            f"{reduccion_personas_pct:.1f}%",
            help="Porcentaje de reducción de personal"
        )
    
    if personas_originales > 0 and personas_mejoradas > 0:
        personas_df = pd.DataFrame({
            "Estado": ["AS-IS (Original)", "TO-BE (Mejorado)"],
            "Personas": [personas_originales, personas_mejoradas]
        })
        st.bar_chart(personas_df.set_index("Estado"), height=300)
    
    # KPI 3: Actividades Optimizadas y Eliminadas
    st.markdown("### 🎯 KPI 3: Actividades Optimizadas y Eliminadas")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Actividades", total_actividades)
    with col2:
        st.metric("Eliminadas", actividades_eliminadas, delta=f"-{actividades_eliminadas}", delta_color="inverse")
    with col3:
        st.metric("Optimizadas", actividades_optimizadas)
    with col4:
        actividades_conservadas = total_actividades - actividades_eliminadas
        st.metric("Conservadas", actividades_conservadas)
    
    if total_actividades > 0:
        actividades_kpi_df = pd.DataFrame({
            "Categoría": ["Eliminadas", "Optimizadas", "Conservadas"],
            "Cantidad": [
                actividades_eliminadas,
                actividades_optimizadas,
                max(0, total_actividades - actividades_eliminadas)
            ]
        })
        st.bar_chart(actividades_kpi_df.set_index("Categoría"), height=300)
    
    # KPI 4: Reducción de Tiempo por Actividad (Top 10)
    st.markdown("### ⏱️ KPI 4: Reducción de Tiempo por Actividad (Top 10)")
    if actividades and len(actividades) > 0:
        # Preparar datos para el gráfico
        actividades_tiempo = []
        for act in actividades[:10]:
            tiempo_orig = act.get("tiempo_original_minutos", 0)
            tiempo_mej = act.get("tiempo_mejorado_minutos", 0)
            reduccion = act.get("reduccion_tiempo_porcentaje", 0)
            if tiempo_orig > 0:
                actividades_tiempo.append({
                    "Actividad": act.get("actividad", "N/A")[:30],  # Limitar longitud
                    "Tiempo Original": tiempo_orig,
                    "Tiempo Mejorado": tiempo_mej,
                    "Reducción %": reduccion
                })
        
        if actividades_tiempo:
            actividades_tiempo_df = pd.DataFrame(actividades_tiempo)
            actividades_tiempo_df = actividades_tiempo_df.sort_values("Reducción %", ascending=False)
            
            # Gráfico de barras comparativo
            chart_data = actividades_tiempo_df[["Actividad", "Tiempo Original", "Tiempo Mejorado"]].set_index("Actividad")
            st.bar_chart(chart_data, height=400)
            
            # Tabla con detalles
            with st.expander("📋 Ver detalles de reducción por actividad"):
                st.dataframe(
                    actividades_tiempo_df[["Actividad", "Tiempo Original", "Tiempo Mejorado", "Reducción %"]],
                    use_container_width=True
                )
    else:
        st.info("No hay datos de actividades disponibles para este KPI.")
    
    # KPI 5: Impacto General - Resumen de Mejoras
    st.markdown("### 📈 KPI 5: Impacto General - Resumen de Mejoras")
    
    # Calcular métricas adicionales
    mejoras_list = []
    if reduccion_tiempo_pct > 0:
        mejoras_list.append({"Métrica": "Reducción de Tiempo", "Valor": reduccion_tiempo_pct, "Unidad": "%"})
    if reduccion_personas_pct > 0:
        mejoras_list.append({"Métrica": "Reducción de Personal", "Valor": reduccion_personas_pct, "Unidad": "%"})
    if actividades_eliminadas > 0:
        mejoras_list.append({"Métrica": "Actividades Eliminadas", "Valor": actividades_eliminadas, "Unidad": "unidades"})
    if actividades_optimizadas > 0:
        mejoras_list.append({"Métrica": "Actividades Optimizadas", "Valor": actividades_optimizadas, "Unidad": "unidades"})
    
    if mejoras_list:
        mejoras_df = pd.DataFrame(mejoras_list)
        mejoras_df["Valor_Display"] = mejoras_df.apply(
            lambda x: f"{x['Valor']:.1f} {x['Unidad']}", axis=1
        )
        
        # Mostrar métricas en columnas
        cols = st.columns(len(mejoras_list))
        for idx, mejora in enumerate(mejoras_list):
            with cols[idx]:
                st.metric(
                    mejora["Métrica"],
                    f"{mejora['Valor']:.1f} {mejora['Unidad']}"
                )
        
        # Gráfico de impacto general
        if len(mejoras_list) > 0:
            impacto_df = pd.DataFrame({
                "Métrica": [m["Métrica"] for m in mejoras_list],
                "Impacto": [m["Valor"] for m in mejoras_list]
            })
            st.bar_chart(impacto_df.set_index("Métrica"), height=300)
    
    # Mostrar análisis de IA si está disponible
    if st.session_state.get("kpis_analysis"):
        st.markdown("---")
        st.markdown("### 🤖 Análisis de KPIs Generado por IA")
        with st.expander("📊 Ver análisis completo", expanded=False):
            st.markdown(st.session_state.kpis_analysis)
    
    # Resumen de impacto
    if mejoras.get("reduccion_costo_estimada"):
        st.markdown("---")
        st.markdown("### 💰 Estimación de Reducción de Costos")
        st.info(f"**{mejoras.get('reduccion_costo_estimada', 'N/A')}**")
    
    if mejoras.get("mejora_calidad"):
        st.markdown("### ✨ Mejora en Calidad")
        st.success(mejoras.get("mejora_calidad", "N/A"))


def render_kpis_tab(selected_model: str, api_key: Optional[str] = None) -> None:
    """Render the KPIs tab that generates 5 graphical KPIs from TO-BE results"""
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: var(--primary); margin-bottom: 1rem; font-weight: 700;">📊 KPIs y Métricas</h1>
        <p style="color: var(--muted-foreground); font-size: 1.1rem; margin: 0;">
            Visualización de indicadores clave de rendimiento basados en el análisis TO-BE
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar si existe tobe_result y si está parseado correctamente
    tobe_result = st.session_state.get("tobe_result")
    
    if tobe_result is None:
        st.warning("""
        ⚠️ **Esta pestaña está bloqueada**
        
        Para generar los KPIs, primero debes completar el análisis en la pestaña **🚀 Proceso Sugerido (Tab 5)**.
        
        Una vez que hayas ejecutado el análisis TO-BE, esta pestaña se desbloqueará automáticamente.
        """)
        return
    
    # Parsear la respuesta del TO-BE
    response_text = tobe_result.get("response", "")
    if not response_text:
        st.warning("""
        ⚠️ **No hay resultados disponibles**
        
        El análisis TO-BE no generó resultados válidos. Por favor, ejecuta nuevamente el análisis en la pestaña **🚀 Proceso Sugerido**.
        """)
        return
    
    # Parsear los datos
    parsed_data = parse_tobe_response(response_text)
    
    if not parsed_data.get("success", False):
        st.warning("""
        ⚠️ **No se pudieron parsear los resultados del TO-BE**
        
        Los datos generados no tienen el formato esperado. Por favor, ejecuta nuevamente el análisis en la pestaña **🚀 Proceso Sugerido**.
        """)
        return
    
    # Si llegamos aquí, tenemos datos válidos - mostrar los KPIs
    st.success("✅ **Datos del análisis TO-BE disponibles** - Generando visualizaciones de KPIs...")
    
    # Extraer datos para los KPIs
    mejoras = parsed_data.get("mejoras_cuantitativas", {})
    actividades = parsed_data.get("actividades_optimizadas", [])
    # Nota: resumen_as_is ya no existe en el nuevo formato, crear resumen desde actividades
    resumen = {
        "total_actividades": len(actividades) if actividades else 0,
        "actividades_va": sum(1 for act in actividades if act.get("clasificacion_original", "").upper() == "VA") if actividades else 0,
        "actividades_nva_n": sum(1 for act in actividades if act.get("clasificacion_original", "").upper() == "NVA-N") if actividades else 0,
        "actividades_nva_p": sum(1 for act in actividades if act.get("clasificacion_original", "").upper() == "NVA-P") if actividades else 0,
        "tipos_desperdicio": {}  # Ya no disponible en el nuevo formato
    }
    
    # Generar el prompt para crear los KPIs usando IA
    if st.button("🎯 Generar KPIs con IA", type="primary", use_container_width=True):
        try:
            st.info("🤖 Generando análisis de KPIs con IA... por favor espera ⏳")
            
            from services.analysis import get_analyzer
            analyzer = get_analyzer(selected_model, api_key)
            
            # Construir prompt para generar KPIs
            kpis_prompt = _build_kpis_prompt(parsed_data, mejoras, actividades, resumen)
            
            # Generar análisis de KPIs
            kpis_analysis = analyzer.analyze(None, kpis_prompt)
            
            # Guardar en session state
            st.session_state.kpis_analysis = kpis_analysis
            st.session_state.kpis_generated = True
            
            st.success("✅ Análisis de KPIs generado exitosamente!")
            st.rerun()
            
        except RerunException:
            # RerunException es normal en Streamlit, no debe ser capturada
            raise
        except Exception as e:
            st.error(f"❌ Error al generar KPIs: {str(e)}")
            st.error(f"🔍 Detalles:\n{traceback.format_exc()}")
    
    # Mostrar los KPIs gráficos
    if st.session_state.get("kpis_generated", False) or mejoras:
        _display_kpis_visualizations(parsed_data, mejoras, actividades, resumen)
    else:
        st.info("💡 Haz clic en 'Generar KPIs con IA' para crear visualizaciones personalizadas, o revisa las visualizaciones básicas a continuación.")
        _display_kpis_visualizations(parsed_data, mejoras, actividades, resumen)
