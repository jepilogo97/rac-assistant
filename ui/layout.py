"""
Componentes de layout y estructura general de la UI
"""
import streamlit as st
from typing import Optional, Tuple
from config import MODEL_OPTIONS

def render_sidebar(selected_model: str, api_key: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """Renderizar la barra lateral con configuración"""
    with st.sidebar:
        st.markdown("""        
        <div style="text-align: center; padding: 1rem 0; border-bottom: 2px solid var(--primary); margin-bottom: 1.5rem;">
            <h2 style="color: var(--primary); margin: 0; font-size: 1.5rem; font-weight: 600;">⚙️ Configuración</h2>
        </div>
        """, unsafe_allow_html=True)

        # 🔹 Contexto
        st.markdown("---")
        st.subheader("🧩 Contexto")

        project_id = st.text_area(
            "Descripción del proyecto",
            placeholder="Ejemplo: proceso para la gestión de servicios de ambulancias en la ciudad, agendamiento de servicios y gestion de ambulancias para atender las demandas diarias",
            help="Nombre o código interno para identificar el proyecto actual",
            height=120
        )
        st.session_state.project_id = project_id

        # Motor de IA
        st.subheader("🤖 Motor de IA")
        
        available_models = [k for k in MODEL_OPTIONS.keys() if k != "local"]
        default_index = available_models.index("gemini") if "gemini" in available_models else 0

        selected_model = st.selectbox(
            "Selecciona el tipo de IA",
            options=list(MODEL_OPTIONS.keys()),
            index=default_index,
            format_func=lambda x: MODEL_OPTIONS[x],
            help="Elige el motor de IA que mejor se adapte a tus necesidades",
            label_visibility="collapsed"
        )
        
        api_key_input = None
        
        if selected_model == "openai":
            st.markdown("**🔑 API Key requerida**")
            api_key_input = st.text_input(
                "OpenAI API Key",
                type="password",
                value=api_key if api_key else "",
                placeholder="Ingresa tu API Key de OpenAI",
                help="Ingresa tu API Key de OpenAI para acceder a GPT models",
                label_visibility="collapsed"
            )
            if not api_key_input:
                st.info("💡 Necesitas una API Key de OpenAI para usar este modelo")
                
        elif selected_model == "deepseek":
            st.markdown("**🔑 API Key requerida**")
            api_key_input = st.text_input(
                "DeepSeek API Key",
                type="password",
                value=api_key if api_key else "",
                placeholder="Ingresa tu API Key de DeepSeek",
                help="Ingresa tu API Key de DeepSeek para acceso premium",
                label_visibility="collapsed"
            )
            if not api_key_input:
                st.info("💡 Necesitas una API Key de DeepSeek para usar este modelo")
                
        elif selected_model == "gemini":
            st.markdown("**🔑 API Key requerida**")
            api_key_input = st.text_input(
                "Google Gemini API Key",
                type="password",
                value=api_key if api_key else "",
                placeholder="Ingresa tu API Key de Google Gemini",
                help="Ingresa tu API Key de Google Gemini para análisis avanzado de procesos",
                label_visibility="collapsed"
            )
            if not api_key_input:
                st.info("💡 Necesitas una API Key de Google Gemini para usar este modelo")
        else:
            api_key_input = None
            st.info("✅ Modelo listo para usar sin configuración adicional")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Documentación complementaria (subida de archivos)
        st.markdown("""        
        <div style="margin-top: 1.5rem;">
            <h3 style="color: #2C3E50; margin-bottom: 0.8rem; text-align: left;">✨ Documentacion complementaria</h3>
        </div>
        """, unsafe_allow_html=True)

        uploaded_files = st.file_uploader(
            "Archivos con información que complementaran las decisiones del agente de IA",
            type=["pdf", "docx", "txt", "csv", "xlsx"],
            accept_multiple_files=True,
            help="Puedes cargar varios archivos a la vez para análisis o procesamiento.",
            label_visibility="visible"
        )
    
    # Guardar en session state
    st.session_state.selected_model = selected_model
    st.session_state.api_key = api_key_input
    
    return selected_model, api_key_input


def render_main_layout():
    """Renderizar el layout principal con pestañas"""
    st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem;">
        <h1 style="
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 1rem;
            letter-spacing: -0.05em;
        ">
            <span style="font-size: 3.5rem;">🚀</span>
            <span style="
                background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            ">RAC ASSISTANT - Optimización Inteligente de Procesos </span>
        </h1>
        <p style="
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 1.5rem;
            font-weight: 600;
            max-width: 700px;
            margin: 0 auto;
            line-height: 1.6;
        ">
            Transforma tus procesos con inteligencia artificial
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Crear pestañas
    tabs = st.tabs([
        "📂 Carga de Datos",
        "📊 Diagrama de Flujo",
        "🎯 A. Desperdicios",
        "🧠 A. Actividades",
        "🚀 Proceso Sugerido",
        "📈 KPIs y Métricas"
    ])
    
    # Forzar estilos de pestañas con CSS inline (para evitar problemas de caché)
    st.markdown("""
    <style>
    /* Forzar tamaño grande en pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px !important;
    }
    
    .stTabs [data-baseweb="tab"],
    .stTabs button[role="tab"],
    div[data-baseweb="tab-list"] button {
        font-size: 2.0rem !important;
        font-weight: 600 !important;
        padding: 18px 36px !important;
        min-height: 60px !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #4169E1 !important;
        font-weight: 700 !important;
        border-bottom: 3px solid #4169E1 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    return tabs


def display_footer():
    """Mostrar pie de página"""
    st.markdown("""
    <div style="
        text-align: center;
        margin-top: 4rem;
        padding-top: 2rem;
        border-top: 1px solid var(--border);
        color: var(--muted-foreground);
        font-size: 0.875rem;
    ">
        <p>© 2024 RAC Assistant. Todos los derechos reservados.</p>
        <p style="font-size: 0.75rem;">Versión 2.0.0 | Powered by Google Gemini 2.0</p>
    </div>
    """, unsafe_allow_html=True)
