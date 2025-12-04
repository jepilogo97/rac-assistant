"""
Componentes UI comunes y utilidades de visualización
"""

import pandas as pd
import streamlit as st
from config import UI_CONFIG, FILE_CONFIG
from services.data_processing import find_matching_columns

def display_data_overview(df: pd.DataFrame) -> None:
    """Mostrar resumen del dataset con métricas principales"""
    st.markdown("### 📊 Métricas del Dataset")
    cols = st.columns(UI_CONFIG['metrics_columns'])
    
    metrics_data = [
        ("📊", "Filas", df.shape[0], "#3498DB"),
        ("📋", "Columnas", df.shape[1], "#1ABC9C"),
        ("⚠️", "Valores faltantes", df.isnull().sum().sum(), "#F39C12"),
        ("💾", "Memoria", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB", "#9B59B6")
    ]
    
    for i, (icon, label, value, color) in enumerate(metrics_data):
        with cols[i]:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {color}, {color}dd);
                color: white;
                padding: 1.2rem 0.8rem;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 4px 12px {color}33;
                margin-bottom: 0.5rem;
            ">
                <div style="font-size: 1.8rem; margin-bottom: 0.3rem;">{icon}</div>
                <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.2rem;">{value}</div>
                <div style="font-size: 0.85rem; opacity: 0.9;">{label}</div>
            </div>
            """, unsafe_allow_html=True)


def display_column_info(df: pd.DataFrame) -> None:
    """Mostrar información detallada de columnas"""
    
    column_matches = find_matching_columns(df.columns.tolist(), FILE_CONFIG['expected_columns'])
    
    col_info = []
    for col in df.columns:
        col_data = df[col]
        dtype_str = str(col_data.dtype)
        
        # Verificar si está mapeada
        mapped_to_required = None
        for expected_col, actual_col in column_matches.items():
            if actual_col == col:
                mapped_to_required = expected_col
                break
        
        # Calcular estadísticas según tipo
        if pd.api.types.is_numeric_dtype(col_data):
            non_null = col_data.dropna()
            if len(non_null) > 0:
                stats_info = f"Min: {non_null.min():.2f}, Max: {non_null.max():.2f}, Prom: {non_null.mean():.2f}"
            else:
                stats_info = "Sin datos numéricos"
        else:
            unique_vals = len(col_data.dropna().unique())
            most_common = col_data.mode().iloc[0] if len(col_data.mode()) > 0 else "N/A"
            stats_info = f"Valores únicos: {unique_vals}, Más común: {str(most_common)[:30]}"
        
        col_info.append({
            'Columna': col,
            'Mapeada a': mapped_to_required if mapped_to_required else "No mapeada",
            'Tipo': dtype_str,
            'Valores únicos': col_data.nunique(),
            'Valores faltantes': col_data.isnull().sum(),
            'Porcentaje faltantes': f"{(col_data.isnull().sum() / len(df) * 100):.1f}%",
            'Estadísticas': stats_info,
            'Es requerida': mapped_to_required is not None
        })
    
    col_df = pd.DataFrame(col_info)
    
    st.subheader("📊 Análisis Detallado de Columnas")
    
    st.dataframe(
        col_df, 
        use_container_width=True,
        hide_index=True
    )
    
    # Validación de columnas requeridas
    st.markdown("### 🎯 Validación de Columnas Requeridas")
    
    required_cols = set(FILE_CONFIG['expected_columns'])
    matched_cols = set(column_matches.keys())
    missing_cols = required_cols - matched_cols
    extra_cols = set(df.columns) - set(column_matches.values())
    
    col1, col2 = st.columns(2)
    
    with col1:
        if missing_cols:
            st.error(f"❌ **Columnas faltantes ({len(missing_cols)}):**")
            for col in sorted(missing_cols):
                st.write(f"• {col}")
        else:
            st.success("✅ **Todas las columnas requeridas están mapeadas**")
    
    with col2:
        if extra_cols:
            st.warning(f"⚠️ **Columnas adicionales ({len(extra_cols)}):**")
            for col in sorted(extra_cols):
                st.write(f"• {col}")
        else:
            st.info("ℹ️ **No hay columnas adicionales**")
    
    st.markdown('</div>', unsafe_allow_html=True)


def initialize_session_state() -> None:
    """Inicializar el estado de la sesión de Streamlit"""
    default_state = {
        "messages": [],
        "uploaded_data": None,
        "analysis_results": None,
        "expert_diagram": None,
        "selected_model": "local",
        "api_key": None
    }
    
    for key, value in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = value


def display_footer() -> None:
    """Mostrar el footer de la aplicación"""
    st.markdown("""
    <div style="
        margin-top: 3rem;
        padding: 2rem;
        background: linear-gradient(135deg, #2C3E50 0%, #34495E 100%);
        color: white;
        border-radius: 12px;
        text-align: center;
    ">
        <h4 style="margin: 0 0 0.5rem 0; color: #1ABC9C;">🚀 Asistente de IA</h4>
        <p style="margin: 0; opacity: 0.8;">
            Optimización Inteligente de Procesos con IA
        </p>
        <div style="margin-top: 1rem; opacity: 0.6;">
            Icesi, Tecnología en IA
        </div>
    </div>
    """, unsafe_allow_html=True)