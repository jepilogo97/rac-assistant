"""
Componentes para la pestaña de carga de datos
"""
import streamlit as st
from typing import Optional
from config import FILE_CONFIG
from ui.common import display_data_overview, display_column_info

def render_file_upload_tab() -> Optional[object]:
    """Renderizar la pestaña de carga de archivos"""
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: var(--primary); margin-bottom: 1rem; font-weight: 700;">📂 Cargue sus datos</h1>
        <p style="color: var(--muted-foreground); font-size: 1.1rem; margin: 0;">
            Sube tu archivo Excel y comienza el análisis de procesos
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="margin: 1rem 0;">
        <h3 style="color: #2C3E50; text-align: center; margin-bottom: 0.5rem;">⬆️ Selecciona tu archivo</h3>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Arrastra y suelta tu archivo Excel aquí, o haz clic para seleccionar",
        type=['xlsx', 'xls'],
        help="El archivo debe contener las 11 columnas requeridas para análisis de procesos",
        label_visibility="collapsed"
    )

    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""        
        **Estructura requerida del archivo Excel:**
        
        **📋 Columnas Obligatorias (11 columnas):**
        1. **Estado Actividad** - Estado actual de la actividad
        2. **Actividad** - Nombre de la actividad o proceso
        3. **Descripción** - Descripción detallada de las tareas
        4. **Cargo que ejecuta la tarea** - Rol o posición responsable
        5. **Tarea Automatizada** - Si la tarea está automatizada (SI/NO)
        6. **No. Colaboradores que ejecutan la tarea** - Número de personas asignadas
        7. **Volumen Promedio Mensual** - Cantidad promedio mensual
        8. **Tiempo Menor** - Tiempo mínimo registrado
        9. **Tiempo Mayor** - Tiempo máximo registrado  
        10. **Tiempo Prom** - Tiempo promedio en minutos (Min/Tarea)
        11. **Tiempo Estándar** - Tiempo estándar esperado (Min/Tarea)
        """)
    
    with col2:
        st.markdown("""
        <div style="
            background: var(--primary);
            color: var(--primary-foreground);
            padding: 1rem;
            border-radius: var(--radius);
            text-align: center;
            font-size: 0.9rem;
            box-shadow: var(--shadow-md);
        ">
            📊 Máximo 10MB<br>
            📁 Formatos: .xlsx, .xls
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return uploaded_file


def render_data_preview(df) -> None:
    """Renderizar vista previa de los datos cargados - TODAS LAS FILAS Y COLUMNAS"""
    if df is not None:
        st.markdown("""
        <div class="gradient-primary" style="
            color: white;
            padding: 1rem 2rem;
            border-radius: var(--radius);
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-glow);
        ">
            <h3 style="margin: 0; color: white;">✅ Archivo cargado exitosamente</h3>
        </div>
        """, unsafe_allow_html=True)
        
        display_data_overview(df)
        
        st.markdown("### 👀 Vista Previa Completa de los Datos")
        
        # CAMBIO PRINCIPAL: Siempre mostrar todas las filas
        data_to_show = df
        st.info(f"📊 **{len(df)} filas**")
        
        # Configurar pandas para mostrar todas las filas y columnas
        import pandas as pd
        with pd.option_context(
            'display.max_rows', None,      # Mostrar todas las filas
            'display.max_columns', None,   # Mostrar todas las columnas
            'display.width', None,         # Ajustar ancho automáticamente
            'display.max_colwidth', None   # No truncar contenido de celdas
        ):
            st.dataframe(
                data_to_show, 
                use_container_width=True,
                hide_index=False,  # Mostrar índice para referencia
                height=400         # Altura del contenedor (ajustable)
            )
        
        display_column_info(df)
