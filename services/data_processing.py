"""
Utilidades para procesamiento y validación de datos (DataFrames)
"""

import pandas as pd
import re
import streamlit as st
from typing import Dict, Any, Optional
from config import FILE_CONFIG

def normalize_column_name(col_name: str) -> str:
    """
    Normalizar nombre de columna para comparación flexible
    
    Args:
        col_name: Nombre original de la columna
        
    Returns:
        Nombre normalizado (sin acentos, números, caracteres especiales)
    """
    col_name = str(col_name).strip().lower()
    
    # Reemplazar acentos y ñ
    replacements = str.maketrans("áéíóúñ", "aeioun")
    normalized = col_name.translate(replacements)
    
    # Eliminar números y puntos
    normalized = re.sub(r'[\d\.]', '', normalized)
    
    # Eliminar caracteres especiales (dejar solo letras y espacios)
    normalized = re.sub(r'[^a-z\s]', '', normalized)
    
    # Colapsar múltiples espacios
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def find_matching_columns(df_columns: list, expected_columns: list) -> Dict[str, str]:
    """
    Encontrar mapeo entre columnas del DataFrame y columnas esperadas
    
    Args:
        df_columns: Lista de columnas del DataFrame
        expected_columns: Lista de columnas esperadas
        
    Returns:
        Diccionario {columna_esperada: columna_encontrada}
    """
    matches = {}
    df_cols_normalized = {normalize_column_name(col): col for col in df_columns}
    
    for expected_col in expected_columns:
        expected_normalized = normalize_column_name(expected_col)
        
        # 1. Coincidencia exacta
        if expected_normalized in df_cols_normalized:
            matches[expected_col] = df_cols_normalized[expected_normalized]
            continue
            
        # 2. Coincidencia parcial
        for df_col_norm, df_col_orig in df_cols_normalized.items():
            if expected_normalized in df_col_norm or df_col_norm in expected_normalized:
                matches[expected_col] = df_col_orig
                break
                
        # 3. Búsqueda por palabras clave (>3 caracteres)
        if expected_col not in matches:
            expected_keywords = expected_normalized.split()
            for df_col_norm, df_col_orig in df_cols_normalized.items():
                if any(keyword in df_col_norm for keyword in expected_keywords if len(keyword) > 3):
                    matches[expected_col] = df_col_orig
                    break
    
    return matches


def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convertir automáticamente columnas que deberían ser numéricas
    
    Args:
        df: DataFrame a procesar
        
    Returns:
        DataFrame con columnas numéricas convertidas
    """
    numeric_columns_mapping = {
        "Tiempo Menor": ["tiempo", "menor"],
        "Tiempo Mayor": ["tiempo", "mayor"], 
        "Tiempo Prom (Min/Tarea)": ["tiempo", "prom", "min", "promedio"],
        "Tiempo Estándar (Min/Tarea)": ["tiempo", "estándar", "estandar", "min"],
        "No. Colaboradores que ejecutan la tarea": ["colaboradores", "no", "número", "numero"],
        "Volumen Promedio Mensual": ["volumen", "promedio", "mensual"]
    }
    
    for col in df.columns:
        col_lower = col.lower()
        
        # Verificar si debería ser numérica
        should_be_numeric = False
        for pattern_key, keywords in numeric_columns_mapping.items():
            if all(keyword in col_lower for keyword in keywords):
                should_be_numeric = True
                break
        
        if should_be_numeric:
            try:
                # Limpiar y convertir
                cleaned_col = df[col].astype(str).str.strip()
                cleaned_col = cleaned_col.replace(['', 'nan', 'NaN', 'NULL', 'null', 'N/A', 'n/a'], pd.NA)
                cleaned_col = cleaned_col.str.replace(r'[^\d.,\-]', '', regex=True)
                cleaned_col = cleaned_col.str.replace(',', '.')
                df[col] = pd.to_numeric(cleaned_col, errors='coerce')
            except Exception as e:
                st.warning(f"⚠️ No se pudo convertir '{col}' a numérico: {str(e)}")
    
    return df


def validate_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validar estructura del DataFrame para análisis de procesos
    
    Args:
        df: DataFrame a validar
        
    Returns:
        Diccionario con información de validación
    """
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "suggestions": [],
        "column_mapping": {}
    }
    
    # Mapear columnas
    column_matches = find_matching_columns(df.columns.tolist(), FILE_CONFIG['expected_columns'])
    validation_result["column_mapping"] = column_matches
    
    # Verificar columnas requeridas
    required_columns = set(FILE_CONFIG['expected_columns'])
    matched_columns = set(column_matches.keys())
    missing_columns = required_columns - matched_columns
    
    if missing_columns:
        validation_result["is_valid"] = False
        validation_result["errors"].append(
            f"Columnas requeridas faltantes ({len(missing_columns)}): {', '.join(sorted(missing_columns))}"
        )
    
    # Verificar si hay datos
    if df.empty:
        validation_result["is_valid"] = False
        validation_result["errors"].append("El archivo está vacío")
    
    # Validaciones específicas (solo si no está vacío)
    if not df.empty and len(missing_columns) == 0:
        
        # Validar columnas de tiempo
        time_columns = ["Tiempo Menor", "Tiempo Mayor", "Tiempo Prom (Min/Tarea)", "Tiempo Estándar (Min/Tarea)"]
        for expected_col in time_columns:
            if expected_col in column_matches:
                actual_col = column_matches[expected_col]
                if not pd.api.types.is_numeric_dtype(df[actual_col]):
                    try:
                        df[actual_col] = pd.to_numeric(df[actual_col], errors='coerce')
                        if pd.api.types.is_numeric_dtype(df[actual_col]):
                            validation_result["suggestions"].append(
                            #    f"✅ Columna '{actual_col}' convertida a numérica"
                            )
                    except:
                        validation_result["warnings"].append(
                            f"La columna '{actual_col}' debería ser numérica."
                        )
                
                # Verificar valores negativos
                if pd.api.types.is_numeric_dtype(df[actual_col]) and (df[actual_col] < 0).any():
                    validation_result["warnings"].append(
                        f"La columna '{actual_col}' contiene valores negativos."
                    )
        
        # Validar columnas numéricas generales
        numeric_columns = ["No. Colaboradores que ejecutan la tarea", "Volumen Promedio Mensual"]
        for expected_col in numeric_columns:
            if expected_col in column_matches:
                actual_col = column_matches[expected_col]
                if not pd.api.types.is_numeric_dtype(df[actual_col]):
                    try:
                        df[actual_col] = pd.to_numeric(df[actual_col], errors='coerce')
                        if pd.api.types.is_numeric_dtype(df[actual_col]):
                            validation_result["suggestions"].append(
                            #    f"✅ Columna '{actual_col}' convertida a numérica"
                            )
                    except:
                        validation_result["warnings"].append(
                            f"La columna '{actual_col}' debería ser numérica, se realizará conversión"
                        )
        
        # Validar columna de automatización
        if "Tarea Automatizada" in column_matches:
            actual_col = column_matches["Tarea Automatizada"]
            unique_values = df[actual_col].dropna().str.upper().unique()
            expected_values = {"SI", "NO", "SÍ"}
            if not all(val in expected_values for val in unique_values):
                validation_result["warnings"].append(
                    f"La columna '{actual_col}' debería contener: SI/NO/SÍ"
                )
        
        # Validar consistencia de tiempos
        if "Tiempo Menor" in column_matches and "Tiempo Mayor" in column_matches:
            menor_col = column_matches["Tiempo Menor"]
            mayor_col = column_matches["Tiempo Mayor"]
            invalid_times = df[menor_col] > df[mayor_col]
            if invalid_times.any():
                validation_result["warnings"].append(
                    f"Hay {invalid_times.sum()} filas donde '{menor_col}' > '{mayor_col}'"
                )
    
    # Advertir sobre datos faltantes
    missing_data_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
    if missing_data_ratio > 0.1:
        validation_result["warnings"].append(
            f"Alto porcentaje de datos faltantes: {missing_data_ratio:.1%}"
        )
    
    return validation_result
