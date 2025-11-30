"""
Controlador para la ejecución y visualización del validador de dependencias
"""
import streamlit as st
from services.dependency_validator import validate_and_estimate_process_integrated

def ejecutar_validador_silencioso(df):
    """
    Ejecutar el validador de dependencias en segundo plano sin mostrar UI adicional.
    Retorna el DataFrame actualizado y el resultado de validación.
    """
    
    # Inicializar flags de estado
    st.session_state.setdefault("validator_running", False)
    st.session_state.setdefault("validator_status", None)
    st.session_state.setdefault("validator_error", None)

    # Verificar requisitos
    if st.session_state.get("selected_model") != "gemini":
        st.session_state.validator_status = "Modelo no compatible para validar dependencias"
        return df, None
    
    if not st.session_state.get("api_key"):
        st.session_state.validator_status = "API Key de Gemini no configurada"
        return df, None
    
    try:
        # 🔄 Marcar que está corriendo
        st.session_state.validator_running = True
        st.session_state.validator_status = "Procesando datos con el Validador de Dependencias..."
        st.session_state.validator_error = None

        # Ejecutar validador silenciosamente
        with st.spinner("🔍 Analizando dependencias en segundo plano..."):
            df_updated, validation_result = validate_and_estimate_process_integrated(
                df,
                st.session_state.api_key,
                apply_estimates=True
            )
        
        # Guardar en session state
        st.session_state.validated_data = df_updated
        st.session_state.validation_result = validation_result

        # Actualizar estado
        if validation_result and validation_result.get("success"):
            st.session_state.validator_status = "Datos validados correctamente con el Validador de Dependencias"
        else:
            st.session_state.validator_status = "Validación completada, pero sin resultados exitosos"
        
        return df_updated, validation_result
        
    except Exception as e:
        st.session_state.validator_error = str(e)
        st.session_state.validator_status = f"No se pudo completar la validación automática: {e}"
        return df, None
    
    finally:
        # Siempre marcar que dejó de correr
        st.session_state.validator_running = False


def render_validator_status_global():
    """
    Muestra un banner global de estado del Validador de Dependencias
    (se puede llamar en todas las pestañas/tablas).
    """
    running = st.session_state.get("validator_running", False)
    status = st.session_state.get("validator_status")
    error  = st.session_state.get("validator_error")

    if running:
        st.info("🔄 **Validador de dependencias en ejecución:** tus datos se están procesando en segundo plano.")
    elif error:
        st.warning(f"⚠️ Validador de dependencias: {error}")
    elif status:
        # Ya corrió al menos una vez
        st.success(f"✅ {status}")
    # Si no hay nada, no mostramos banner
