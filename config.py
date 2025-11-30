"""
Configuración centralizada de RAC Assistant
"""

# Configuración de página Streamlit
PAGE_CONFIG = {
    "page_title": "RAC Assistant - Optimización con IA",
    "page_icon": "🚀",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Modelos de IA disponibles
MODEL_OPTIONS = {
    "gemini": "Google Gemini 2.0 (Requiere API Key)"
}

# Configuración de análisis de IA
ANALYSIS_CONFIG = {
    # Gemini
    "max_tokens_gemini": 4000,
    "temperature_gemini": 0.3,
    "timeout_gemini": 120,
    # Reintentos
    "retry_attempts": 3,
    "retry_delay": 2
}

# Configuración de archivos Excel
FILE_CONFIG = {
    "allowed_extensions": ['xlsx', 'xls'],
    "expected_columns": [
        "Estado",
        "Actividad", 
        "Descripción",
        "Cargo que ejecuta la tarea",
        "Tarea Automatizada",
        "No. Colaboradores que ejecutan la tarea",
        "Volumen Promedio Mensual",
        "Tiempo Menor",
        "Tiempo Mayor", 
        "Tiempo Promedio",
        "Tiempo Estándar"
    ]
}

# Configuración de UI
UI_CONFIG = {
    "main_title": "🚀 Optimización Inteligente de Procesos",
    "metrics_columns": 4
}

# Configuración de BPMN
BPMN_CONFIG = {
    "use_lanes": True,        # Usar lanes (carriles) para responsables
    "add_di": True,           # Agregar información de diagrama (posiciones)
    "show_times": True,       # Mostrar tiempos en las actividades
    "pool_name": "Proceso con tiempos estimados"
}