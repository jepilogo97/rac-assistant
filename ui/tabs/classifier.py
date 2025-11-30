"""
Componentes para la pestaña de clasificación Lean
"""
import streamlit as st
import pandas as pd
import traceback
from datetime import datetime
from typing import Dict
from services.classification import classify_activities_batch, generate_classification_summary, export_classification_report

def render_classifier_tab(uploaded_data) -> None:
    """Renderizar la pestaña de clasificación Lean"""

    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: var(--primary); margin-bottom: 1rem; font-weight: 700;">🎯 Detección de desperdicios</h1>
        <p style="color: var(--muted-foreground); font-size: 1.1rem; margin: 0;">
            Powered by Google Gemini 2.0 - Identifica actividades de valor vs desperdicio
        </p>
    </div>
    """, unsafe_allow_html=True)

    if uploaded_data is None:
        st.info("📂 Primero carga tus datos desde la pestaña 'Carga de Datos'.")
        return

    if st.session_state.get("selected_model") != "gemini":
        st.warning("⚠️ Para usar el clasificador, selecciona 'Google Gemini 2.0' en la barra lateral.")
        return

    if not st.session_state.get("api_key"):
        st.error("❌ Necesitas configurar tu API Key de Google Gemini en la barra lateral.")
        return

    contexto_proceso = st.session_state.get("project_id", "").strip()

    if not contexto_proceso:
        st.warning("⚠️ Debes ingresar una **Descripción del proyecto** antes de clasificar las actividades.")

    boton_clasificar = st.button(
        "🚀 Clasificar Actividades con IA",
        type="primary",
        use_container_width=True,
        disabled=not bool(contexto_proceso)
    )

    if boton_clasificar:
        try:
            st.info("🧠 Analizando actividades... por favor espera ⏳")

            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(current, total, activity_name):
                progress = current / total
                progress_bar.progress(progress)
                status_text.text(f"Analizando: {activity_name} ({current}/{total})")

            df_resultado = classify_activities_batch(
                uploaded_data,
                st.session_state.api_key,
                contexto_proceso,
                progress_callback=update_progress
            )

            progress_bar.empty()
            status_text.empty()

            summary = generate_classification_summary(df_resultado)

            st.session_state.classified_data = df_resultado
            st.session_state.classification_summary = summary

            st.success("✅ Clasificación completada exitosamente!")
            st.dataframe(df_resultado)

        except Exception as e:
            st.error(f"❌ Error al clasificar: {str(e)}")
            st.error(f"🔍 Detalles:\n{traceback.format_exc()}")

    if st.session_state.get("classified_data") is not None:
        st.markdown("### 📊 Resultados de Clasificación Anterior")
        if st.button("🔄 Ver Resultados"):
            display_classification_results(
                st.session_state.classified_data,
                st.session_state.classification_summary
            )


def display_classification_results(df_classified: pd.DataFrame, summary: Dict) -> None:
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
          <div class="cuadro-sub">Incluye Valor, Desperdicio y Falta detalle, con justificación y recomendación</div>
        </div>
      </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Actividades", summary.get("total_actividades", 0))
    with col2:
        valor_pct = summary.get("porcentaje_valor", 0)
        st.metric("Actividades de Valor", summary.get("valor", 0), delta=f"{valor_pct:.1f}%")
    with col3:
        desperdicio_pct = summary.get("porcentaje_desperdicio", 0)
        st.metric("Desperdicios", summary.get("desperdicio", 0),
                  delta=f"{desperdicio_pct:.1f}%", delta_color="inverse")
    with col4:
        st.metric("Recomendaciones", summary.get("recomendaciones_count", 0))

    if summary.get("tipos_desperdicio"):
        st.markdown("### 📈 Tipos de Desperdicio Identificados")
        tipos_df = pd.DataFrame(
            list(summary["tipos_desperdicio"].items()),
            columns=["Tipo", "Cantidad"]
        ).sort_values("Cantidad", ascending=False)
        st.bar_chart(tipos_df.set_index("Tipo"))

    st.markdown("### 📋 Detalles de Clasificación")
    fc1, fc2 = st.columns(2)
    with fc1:
        opciones = ["Valor", "Desperdicio", "Falta detalle", "Indeterminado", "Error"]
        existentes = [o for o in opciones if o in df_view.get("Clasificación Lean", pd.Series([], dtype=str)).astype(str).unique()]
        if not existentes:
            existentes = ["Valor", "Desperdicio", "Falta detalle"]
        filtro_clasificacion = st.multiselect(
            "Filtrar por clasificación:",
            options=opciones,
            default=existentes
        )
    with fc2:
        columnas_disponibles = df_view.columns.tolist()
        columnas_default = [col for col in [
            "Actividad",
            "Descripción",
            "justificación",
            "fecha de analisis",
            "Clasificación Lean",
            "desperdicio",
        ] if col in columnas_disponibles]
        if not columnas_default:
            columnas_default = [col for col in columnas_disponibles
                                if col in ["Actividad",
                                           "Descripción",
                                           "Clasificación Lean",
                                           "Justificación"]][:5]
        mostrar_columnas = st.multiselect(
            "Columnas a mostrar:",
            options=columnas_disponibles,
            default=columnas_default
        )

    df_filtrado = df_view.copy()
    if "Clasificación Lean" in df_filtrado.columns and filtro_clasificacion:
        df_filtrado = df_filtrado[df_filtrado["Clasificación Lean"].astype(str).isin(filtro_clasificacion)]

    if mostrar_columnas:
        st.dataframe(df_filtrado[mostrar_columnas], use_container_width=True, hide_index=True)
    else:
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    st.markdown("### 📥 Exportar Resultados")
    c1, c2, c3 = st.columns(3)
    
    excel_data = export_classification_report(df_view, summary, "excel")
    csv_data   = export_classification_report(df_view, summary, "csv")
    json_data  = export_classification_report(df_view, summary, "json")
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
