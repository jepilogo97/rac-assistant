"""
Utilidades para carga y manejo de archivos
"""

import pandas as pd
import streamlit as st
from typing import Optional
from config import FILE_CONFIG
from services.data_processing import convert_numeric_columns

def load_excel_file(uploaded_file) -> Optional[pd.DataFrame]:
    """
    Cargar archivo Excel y retornar DataFrame
    
    Args:
        uploaded_file: Archivo subido por el usuario
        
    Returns:
        DataFrame con los datos o None si hay error
    """
    try:
        if uploaded_file.name.endswith(tuple(f'.{ext}' for ext in FILE_CONFIG['allowed_extensions'])):
            df = pd.read_excel(
                uploaded_file,
                engine='openpyxl',
                na_values=['', ' ', 'N/A', 'n/a', 'NULL', 'null'],
                keep_default_na=True,
                header=0,
                dtype=str  # Leer como texto inicialmente
            )
            
            # Limpiar filas completamente vacías
            df = df.dropna(how='all')
            
            # Convertir columnas numéricas
            df = convert_numeric_columns(df)
            
            #st.success(f"✅ Archivo cargado: {len(df)} filas, {len(df.columns)} columnas")
            
            return df
        else:
            st.error(f"Por favor, sube un archivo Excel ({', '.join(FILE_CONFIG['allowed_extensions'])})")
            return None
    except Exception as e:
        st.error(f"Error al cargar el archivo: {str(e)}")
        st.error("💡 Verifica que el archivo no esté corrupto y tenga el formato correcto")
        return None
