"""
RAC Assistant - Aplicación principal para optimización de procesos con IA
Versión: 2.0.0
- Validador de Dependencias ejecutándose automáticamente en segundo plano
- BPMN 2.0 Advanced integrado con tiempos estándar
"""

import streamlit as st
import sys
from streamlit.runtime.scriptrunner import RerunException
from config import PAGE_CONFIG
from services.gemini_utils import procesar_y_guardar_archivos
from services.file_utils import load_excel_file
from services.data_processing import validate_dataframe
from ui.common import display_footer
from ui.layout import render_sidebar, render_main_layout
from ui.styles import apply_custom_css
from ui.tabs.upload import render_file_upload_tab, render_data_preview
from ui.tabs.process import render_process_understanding_tab
from ui.tabs.classifier import render_classifier_tab
from ui.tabs.segmenter import render_activity_segmenter_tab
from ui.tabs.tobe import render_tobe_tab
from ui.tabs.kpis import render_kpis_tab
from services.dependency_validator import validate_and_estimate_process_integrated
from ui.validator_controller import ejecutar_validador_silencioso, render_validator_status_global


def main():
    """Función principal de la aplicación"""
    try:
        # Configurar página
        st.set_page_config(**PAGE_CONFIG)
        
        # ✨ APLICAR ESTILOS PERSONALIZADOS (BOTONES AZULES)
        apply_custom_css()
        
        # Renderizar sidebar y obtener configuración
        selected_model, api_key = render_sidebar(
            st.session_state.get("selected_model", "gemini"),
            st.session_state.get("api_key")
        )
        
        # Tabs (sin Validador visible)
        tab1, tab2, tab3, tab4, tab5, tab6 = render_main_layout()

        # ============== TAB 1: CARGA DE DATOS ==============
        with tab1:
            uploaded_file = render_file_upload_tab()
            if uploaded_file is not None:
                # 🔥 DETECTAR CAMBIO DE ARCHIVO Y LIMPIAR CACHÉ
                file_id = f"{uploaded_file.name}_{uploaded_file.size}"
                last_file_id = st.session_state.get("last_uploaded_file_id")
                
                if file_id != last_file_id:
                    # Nuevo archivo detectado - limpiar todo el caché
                    st.session_state.last_uploaded_file_id = file_id
                    
                    # Limpiar datos del validador
                    st.session_state.validated_data = None
                    st.session_state.validation_result = None
                    st.session_state.validator_running = False
                    st.session_state.validator_status = None
                    st.session_state.validator_error = None
                    
                    # Limpiar datos del clasificador Lean
                    st.session_state.classified_data = None
                    st.session_state.classification_summary = None
                    
                    # Limpiar datos del segmentador de actividades
                    st.session_state.classified_data_ca = None
                    st.session_state.classification_summary_ca = None
                    st.session_state.last_processed_file_id_actividades = None
                    
                    # Limpiar datos del proceso TO-BE
                    st.session_state.tobe_result = None
                    
                    # Limpiar datos de KPIs
                    st.session_state.kpis_analysis = None
                    st.session_state.kpis_generated = False
                    
                    # Limpiar datos del BPMN
                    st.session_state.current_bpmn_xml = None
                    st.session_state.current_activities = None
                    st.session_state.bpmn_guardado = False
                    st.session_state.force_regen_bpmn = False
                    
                    st.info("🔄 Nuevo archivo detectado - Limpiando datos previos...")
                
                df = load_excel_file(uploaded_file)
                if df is not None:
                    validation = validate_dataframe(df)
                    if validation["is_valid"]:
                        st.session_state.uploaded_data = df
                        for warning in validation.get("warnings", []):
                            st.warning(f"⚠️ {warning}")
                        for suggestion in validation.get("suggestions", []):
                            st.info(f"💡 {suggestion}")
                        render_data_preview(df)
                        
                        # EJECUTAR VALIDADOR AUTOMÁTICAMENTE EN SEGUNDO PLANO
                        if selected_model == "gemini" and api_key:
                            st.info("🔄 Procesando datos con validador de dependencias...")
                            df_validated, validation_result = ejecutar_validador_silencioso(df)
                            
                            if validation_result and validation_result.get("success"):
                                st.success("✅ Datos procesados y validados correctamente")
                                # Mostrar métricas resumidas del validador
                                summary = validation_result.get("summary", {})
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Actividades", summary.get("total_activities", 0))
                                with col2:
                                    st.metric("Con tiempo", summary.get("activities_with_time", 0))
                                with col3:
                                    st.metric("Tiempo estimado", summary.get("activities_without_time", 0))
                    else:
                        for error in validation.get("errors", []):
                            st.error(f"❌ {error}")
                        for warning in validation.get("warnings", []):
                            st.warning(f"⚠️ {warning}")
                        for suggestion in validation.get("suggestions", []):
                            st.info(f"💡 {suggestion}")

        # ============== TAB 2: DIAGRAMA DE FLUJO ==============
        with tab2:
            render_process_understanding_tab(
                st.session_state.get("uploaded_data"),
                st.session_state.get("validated_data"),
                st.session_state.get("validation_result")
            )

        # ============== TAB 3: CLASIFICADOR LEAN ==============
        with tab3:
            render_classifier_tab(
                st.session_state.get("uploaded_data")
            )

        # ============== TAB 4: SEGMENTADOR DE ACTIVIDADES ==============
        with tab4:
            render_activity_segmenter_tab(
                st.session_state.get("uploaded_data")
            )

        # ============== TAB 5: PROCESO TO-BE ==============
        with tab5:
            render_tobe_tab(selected_model, api_key)

        # ============== TAB 6: KPIs Y MÉTRICAS ==============
        with tab6:
            render_kpis_tab(selected_model, api_key)

        # Footer
        display_footer()

    except RerunException:
        raise
    
    except Exception as e:
        st.error("❌ **Error crítico en la aplicación**")
        st.error(f"Detalles: {str(e)}")
        with st.expander("🔍 Información de depuración"):
            st.code(f"Tipo de error: {type(e).__name__}")
            st.code(f"Mensaje: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
        st.info("💡 **Sugerencias:**")
        st.info("1. Recarga la página (F5)")
        st.info("2. Limpia el cache: Menu → Clear cache")
        st.info("3. Verifica que todos los archivos estén presentes")
        st.info("4. Reinstala dependencias: `pip install -r requirements.txt`")


if __name__ == "__main__":
    if sys.version_info < (3, 8):
        print("❌ Error: Python >= 3.8 es requerido")
        print(f"Versión actual: {sys.version}")
        sys.exit(1)
    main()