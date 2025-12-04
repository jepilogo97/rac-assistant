"""
Agente Validador de Dependencias y Estimador de Tiempos con Gemini
Integrado con la estructura de RAC Assistant
"""

import json
import pandas as pd

from typing import List, Dict, Any, Optional
import google.generativeai as genai
from datetime import datetime


# =============================================================================
# INICIALIZACIÓN DE GEMINI
# =============================================================================

def initialize_gemini_validator(api_key: str) -> bool:
    """Inicializar Gemini para validación de dependencias"""
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"Error configurando Gemini: {str(e)}")
        return False


# =============================================================================
# CONSTRUCCIÓN DEL PROMPT
# =============================================================================

def build_dependency_validation_prompt(activities: List[Dict[str, Any]]) -> str:
    """Construir prompt estructurado para validación de dependencias y tiempos (sin mejoras TO-BE)"""
    
    activities_json = json.dumps(activities, indent=2, ensure_ascii=False)
    
    prompt = f"""Eres un experto en análisis de procesos de negocio y BPMN.

Tu ÚNICO objetivo es:
- Analizar la lógica de dependencias entre actividades
- Completar y validar tiempos de ejecución (en minutos)
- Describir el estado ACTUAL del proceso (AS-IS)

⚠️ IMPORTANTE: 
- NO propongas rediseños, mejoras TO-BE ni optimizaciones Lean.
- NO sugieras cambios al proceso, solo describe inconsistencias y completa tiempos.
- El campo summary.recommendations debe ser SIEMPRE una lista vacía [].

TAREAS:

1. VALIDAR DEPENDENCIAS Y LÓGICA DEL PROCESO:
- Verifica si el orden de las actividades tiene sentido lógico
- Identifica dependencias faltantes o incorrectas
- Detecta actividades que podrían ejecutarse en paralelo (solo márcalas, no rediseñes el proceso)
- Encuentra ciclos o dependencias circulares
- Valida que el flujo sea coherente de inicio a fin

2. ESTIMAR TIEMPOS FALTANTES:
- Para actividades SIN tiempo definido (time_standard = null/0), estima un tiempo razonable en MINUTOS
- Basa tus estimaciones en:
  * Nombre y descripción de la actividad
  * Tipo de tarea (manual vs automatizada)
  * Actividades similares en el proceso
- Sé conservador pero realista

3. VALIDAR TIEMPOS EXISTENTES:
- Para actividades CON tiempo definido, valida si el tiempo parece razonable
- Marca tiempos que parezcan demasiado cortos o largos
- Compara con actividades similares del mismo proceso
- NO propongas cambios al proceso, solo señala posibles outliers.

ACTIVIDADES DEL PROCESO (AS-IS):
```json
{activities_json}


**RESPONDE ÚNICAMENTE EN FORMATO JSON** con esta estructura exacta:

{{
  "validation": {{
    "is_valid": true/false,
    "issues": [
      {{
        "type": "dependency|time|logic|sequence",
        "severity": "error|warning|info",
        "activity_id": "ID de la actividad afectada",
        "message": "Descripción clara del problema",
        "suggestion": "Sugerencia específica de solución"
      }}
    ],
    "parallel_opportunities": [
      {{
        "activities": ["act_id_1", "act_id_2"],
        "reason": "Estas actividades pueden ejecutarse en paralelo porque...",
        "estimated_time_saved": 15
      }}
    ],
    "dependency_graph": {{
      "nodes": ["A1", "A2", "A3"],
      "edges": [
        {{"from": "A1", "to": "A2", "type": "sequential"}},
        {{"from": "A1", "to": "A3", "type": "parallel"}}
      ]
    }}
  }},
  "time_estimates": [
    {{
      "activity_id": "ID",
      "activity_name": "Nombre de la actividad",
      "current_time": 0,
      "estimated_time": 15,
      "confidence": "high|medium|low",
      "reasoning": "Razón detallada de la estimación",
      "similar_activities": ["IDs de actividades similares en el proceso"]
    }}
  ],
  "summary": {{
    "total_activities": 10,
    "activities_with_time": 7,
    "activities_without_time": 3,
    "total_estimated_time": 120,
    "critical_path_time": 100,
    "potential_parallelization_savings": 30,
    "recommendations": [
      "Recomendación específica 1",
      "Recomendación específica 2"
    ]
  }}
}}

**REGLAS IMPORTANTES:**
- NO incluyas ningún texto adicional, solo el JSON válido
- NO uses bloques de código markdown (```json)
- Asegúrate de que el JSON sea válido y parseable
- Incluye TODAS las secciones requeridas
- Sé específico en las justificaciones y recomendaciones

Responde AHORA con el JSON:"""
    
    return prompt


# =============================================================================
# PROCESAMIENTO Y PARSEO
# =============================================================================

def validate_dependencies_with_gemini(
    activities: List[Dict[str, Any]],
    api_key: str,
    model: str = "gemini-2.0-flash"
) -> Dict[str, Any]:
    """
    Validar dependencias y estimar tiempos usando Gemini
    
    Args:
        activities: Lista de actividades del proceso
        api_key: API key de Google Gemini
        model: Modelo de Gemini a usar
        
    Returns:
        Diccionario con validación y estimaciones
    """
    
    if not initialize_gemini_validator(api_key):
        return {
            "success": False,
            "error": "No se pudo inicializar Gemini"
        }
    
    prompt = build_dependency_validation_prompt(activities)
    
    try:
        gemini_model = genai.GenerativeModel(
            model_name=model,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 4000,
            }
        )
        
        response = gemini_model.generate_content(prompt)
        result = parse_gemini_response(response.text)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error al conectar con Gemini"
        }


def parse_gemini_response(response_text: str) -> Dict[str, Any]:
    """Parsear y validar la respuesta de Gemini"""
    
    try:
        # Limpiar la respuesta
        clean_text = response_text.strip()
        
        # Intentar encontrar JSON con regex
        import re
        json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        if json_match:
            clean_text = json_match.group(0)
        
        # Remover bloques de código markdown si persisten
        clean_text = clean_text.replace("```json", "").replace("```", "").strip()
        
        # Parsear JSON
        result = json.loads(clean_text)
        
        # Validar estructura mínima
        required_keys = ["validation", "time_estimates", "summary"]
        missing_keys = [key for key in required_keys if key not in result]
        
        if missing_keys:
            return {
                "success": False,
                "error": f"Respuesta incompleta. Faltan: {', '.join(missing_keys)}",
                "raw_response": response_text
            }
        
        result["success"] = True
        return result
        
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Error al parsear JSON: {str(e)}",
            "raw_response": response_text
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error inesperado: {str(e)}",
            "raw_response": response_text
        }


# =============================================================================
# APLICACIÓN DE ESTIMACIONES
# =============================================================================

def apply_time_estimates(
    df: pd.DataFrame,
    estimates: List[Dict[str, Any]],
    overwrite: bool = False
) -> pd.DataFrame:
    """
    Aplicar estimaciones de tiempo al DataFrame
    
    Args:
        df: DataFrame original con actividades
        estimates: Lista de estimaciones de Gemini
        overwrite: Si True, sobrescribe tiempos existentes
        
    Returns:
        DataFrame actualizado con estimaciones
    """
    # Importar desde el nuevo módulo de procesamiento de datos
    # Se asume que find_matching_columns estará en services.data_processing
    # Si no existe aún, se importará de utils temporalmente
    from services.data_processing import find_matching_columns
        
    from config import FILE_CONFIG
    
    # Encontrar columnas relevantes
    column_matches = find_matching_columns(
        df.columns.tolist(),
        ["Actividades del Proceso", "Tiempo Estándar (Min/Tarea)"]
    )
    
    activity_col = column_matches.get("Actividades del Proceso")
    time_col = column_matches.get("Tiempo Estándar (Min/Tarea)")
    
    if not activity_col or not time_col:
        print("No se encontraron columnas necesarias para aplicar estimaciones")
        return df
    
    # Crear mapa de estimaciones
    estimate_map = {est["activity_id"]: est for est in estimates}
    
    # Aplicar estimaciones
    df_updated = df.copy()
    
    # Crear nuevas columnas para tracking
    df_updated["tiempo_estimado_gemini"] = None
    df_updated["confianza_estimacion"] = None
    df_updated["razonamiento_estimacion"] = None
    
    for idx, row in df_updated.iterrows():
        activity_id = f"A{idx+1}"
        
        if activity_id in estimate_map:
            estimate = estimate_map[activity_id]
            current_time = row[time_col] if pd.notna(row[time_col]) else 0
            
            # Solo aplicar si no tiene tiempo o si overwrite=True
            if current_time == 0 or overwrite:
                df_updated.at[idx, time_col] = estimate["estimated_time"]
                df_updated.at[idx, "tiempo_estimado_gemini"] = estimate["estimated_time"]
                df_updated.at[idx, "confianza_estimacion"] = estimate.get("confidence", "medium")
                df_updated.at[idx, "razonamiento_estimacion"] = estimate.get("reasoning", "")
    
    return df_updated


# =============================================================================
# INTERFAZ DE STREAMLIT (INTEGRADA)
# =============================================================================




# =============================================================================
# FUNCIÓN PRINCIPAL INTEGRADA
# =============================================================================

def validate_and_estimate_process_integrated(
    df: pd.DataFrame,
    api_key: str,
    apply_estimates: bool = True
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Función principal integrada para RAC Assistant
    
    Args:
        df: DataFrame con datos del proceso
        api_key: API key de Gemini
        apply_estimates: Si True, aplica estimaciones al DataFrame
        
    Returns:
        Tuple (df_actualizado, resultado_validacion)
    """
    from services.data_processing import find_matching_columns
        
    from config import FILE_CONFIG
    
    # Preparar actividades desde el DataFrame
    column_matches = find_matching_columns(
        df.columns.tolist(),
        FILE_CONFIG['expected_columns']
    )
    
    activities = []
    for idx, row in df.iterrows():
        activity = {
            "id": f"A{idx+1}",
            "name": "",
            "description": "",
            "responsible": "",
            "automated": False,
            "time_standard": None,
            "time_avg": None,
            "time_min": None,
            "time_max": None
        }
        
        # Mapear datos
        for expected_col, actual_col in column_matches.items():
            if actual_col in df.columns and pd.notna(row[actual_col]):
                value = row[actual_col]
                
                if expected_col == "Actividades del Proceso":
                    activity["name"] = str(value)
                elif expected_col == "Descripción de las Tareas":
                    activity["description"] = str(value)
                elif expected_col == "Cargo que ejecuta la tarea":
                    activity["responsible"] = str(value)
                elif expected_col == "Tarea Automatizada":
                    activity["automated"] = str(value).upper() in ["SI", "SÍ", "YES"]
                elif expected_col == "Tiempo Estándar (Min/Tarea)":
                    try:
                        activity["time_standard"] = float(value)
                    except:
                        pass
                elif expected_col == "Tiempo Prom (Min/Tarea)":
                    try:
                        activity["time_avg"] = float(value)
                    except:
                        pass
                elif expected_col == "Tiempo Menor":
                    try:
                        activity["time_min"] = float(value)
                    except:
                        pass
                elif expected_col == "Tiempo Mayor":
                    try:
                        activity["time_max"] = float(value)
                    except:
                        pass
        
        activities.append(activity)
    
    # Validar con Gemini
    print("🤖 Analizando dependencias y estimando tiempos con Gemini...")
    result = validate_dependencies_with_gemini(activities, api_key)
    
    # Aplicar estimaciones si se solicita
    df_updated = df
    if result.get("success") and apply_estimates:
        estimates = result.get("time_estimates", [])
        if estimates:
            df_updated = apply_time_estimates(df, estimates)
            print(f"✅ Se aplicaron {len(estimates)} estimaciones de tiempo")
    
    return df_updated, result


# =============================================================================
# EXPORTACIÓN DE REPORTE
# =============================================================================

def export_validation_report(
    validation_result: Dict[str, Any],
    format: str = "json"
) -> bytes:
    """
    Exportar reporte de validación
    
    Args:
        validation_result: Resultado de la validación
        format: Formato de exportación (json, csv, excel)
        
    Returns:
        Bytes del archivo generado
    """
    if format == "json":
        return json.dumps(validation_result, ensure_ascii=False, indent=2).encode('utf-8')
    
    elif format == "csv":
        # Convertir issues a CSV
        issues = validation_result.get("validation", {}).get("issues", [])
        if issues:
            df_issues = pd.DataFrame(issues)
            return df_issues.to_csv(index=False).encode('utf-8')
        return b""
    
    elif format == "excel":
        from io import BytesIO
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1: Resumen
            summary = validation_result.get("summary", {})
            df_summary = pd.DataFrame([summary])
            df_summary.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Sheet 2: Problemas
            issues = validation_result.get("validation", {}).get("issues", [])
            if issues:
                df_issues = pd.DataFrame(issues)
                df_issues.to_excel(writer, sheet_name='Problemas', index=False)
            
            # Sheet 3: Estimaciones
            estimates = validation_result.get("time_estimates", [])
            if estimates:
                df_estimates = pd.DataFrame(estimates)
                df_estimates.to_excel(writer, sheet_name='Estimaciones', index=False)
        
        return output.getvalue()
    
    return b""
