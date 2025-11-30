"""
Servicio de Clasificación de Actividades con Gemini 2.0
Clasifica actividades como: Valor, Desperdicio o Falta detalle
Basado en metodologías Lean, Six Sigma, Kaizen y SCAMPER
"""

import pandas as pd
import json
import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from services.gemini_utils import initialize_gemini

def create_classification_prompt(actividad: str, descripcion: str, contexto_proceso: str) -> str:
    """
    Crear prompt para clasificación de actividad
    """
    return f"""
Eres un **asesor experto en optimización de procesos** bajo metodologías **Lean, Six Sigma, Kaizen y SCAMPER**.  
Tu tarea es **identificar si cada actividad del proceso agrega valor o representa desperdicio**.

---

### Contexto del proceso:
Proceso de **{contexto_proceso}**.

---

### 🎯 Tu objetivo:
Debes analizar cada actividad y decidir una de las siguientes categorías:

- **"Valor"** → Transforma el producto o servicio para cumplir los requisitos del cliente. 
    Es esencial para entregar lo que el cliente espera.
    No genera desperdicio ni retrabajo.
- **"Desperdicio"** → es toda acción que:
    No transforma el producto o servicio desde la perspectiva del cliente.
    No es necesaria para cumplir una regulación o requisito.
    Consume tiempo, recursos o esfuerzo sin aportar valor.
- **"Falta detalle"** → No se puede determinar el valor por falta de información o ambigüedad.

---

### 🧩 Formato de salida:
Responde **solo en formato JSON válido**, sin texto antes ni después.

Estructura esperada:
{{
    "clasificacion": "Valor" | "Desperdicio" | "Falta detalle",
    "justificacion": "Breve explicación del motivo de la clasificación",
    "tipo_desperdicio": "Si es Desperdicio: Espera|Transporte|Sobreproceso|Defectos|Movimiento|Inventario|Sobreproducción|Talento no utilizado, sino null",
    "recomendacion": "Sugerencia breve de mejora u optimización"
}}

### 🧠 Actividad a analizar:

Actividad: {actividad}
Descripción: {descripcion}

Responde **solo JSON**, sin texto adicional, explicaciones ni formato Markdown.
"""


def classify_single_activity(
    model: Any,
    actividad: str,
    descripcion: str,
    contexto_proceso: str
) -> Dict[str, Any]:
    """
    Clasificar una actividad individual
    """
    prompt = create_classification_prompt(actividad, descripcion, contexto_proceso)
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Limpiar formato markdown
        text = text.replace("```json", "").replace("```", "").strip()
        
        # Parsear JSON
        analisis = json.loads(text)
        
        # Validar estructura
        if "clasificacion" not in analisis:
            analisis["clasificacion"] = "Indeterminado"
        if "justificacion" not in analisis:
            analisis["justificacion"] = "Sin justificación"
        if "tipo_desperdicio" not in analisis:
            analisis["tipo_desperdicio"] = None
        if "recomendacion" not in analisis:
            analisis["recomendacion"] = "Sin recomendación"
        
        return analisis
        
    except json.JSONDecodeError as e:
        st.warning(f"⚠️ Error parseando JSON para '{actividad}': {str(e)}")
        return {
            "clasificacion": "Error",
            "justificacion": f"Error al parsear respuesta: {text[:100]}",
            "tipo_desperdicio": None,
            "recomendacion": "Revisar manualmente"
        }
    except Exception as e:
        st.error(f"❌ Error al analizar '{actividad}': {str(e)}")
        return {
            "clasificacion": "Error",
            "justificacion": f"Error del modelo: {str(e)}",
            "tipo_desperdicio": None,
            "recomendacion": "Reintentar análisis"
        }


def classify_activities_batch(
    df: pd.DataFrame,
    api_key: str,
    contexto_proceso: str,
    progress_callback=None
) -> pd.DataFrame:
    """
    Clasificar todas las actividades del DataFrame
    """
    # Inicializar Gemini
    if not initialize_gemini(api_key):
        st.error("No se pudo inicializar Gemini")
        return df
    
    # Configurar modelo
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config={
            "temperature": 0.2,  # Más determinístico
            "max_output_tokens": 1000,
        }
    )
    
    # Buscar columnas relevantes
    from services.data_processing import find_matching_columns
    
    column_matches = find_matching_columns(
        df.columns.tolist(),
        ["Actividades del Proceso", "Descripción de las Tareas"]
    )
    
    actividad_col = column_matches.get("Actividades del Proceso")
    descripcion_col = column_matches.get("Descripción de las Tareas")
    
    if not actividad_col or not descripcion_col:
        st.error("No se encontraron columnas de actividad y descripción")
        return df
    
    # Clasificar cada actividad
    resultados = []
    total = len(df)
    
    for idx, row in df.iterrows():
        actividad = str(row[actividad_col]) if pd.notna(row[actividad_col]) else "Sin nombre"
        descripcion = str(row[descripcion_col]) if pd.notna(row[descripcion_col]) else "Sin descripción"
        
        # Callback de progreso
        if progress_callback:
            progress_callback(idx + 1, total, actividad)
        
        # Clasificar
        analisis = classify_single_activity(model, actividad, descripcion, contexto_proceso)
        
        resultados.append({
            "clasificacion": analisis["clasificacion"],
            "justificacion": analisis["justificacion"],
            "tipo_desperdicio": analisis["tipo_desperdicio"],
            "recomendacion": analisis["recomendacion"],
            "fecha_analisis": datetime.now().isoformat()
        })
    
    # Agregar columnas al DataFrame
    df_resultado = df.copy()
    df_resultado["Clasificación Lean"] = [r["clasificacion"] for r in resultados]
    df_resultado["Justificación"] = [r["justificacion"] for r in resultados]
    df_resultado["Tipo Desperdicio"] = [r["tipo_desperdicio"] for r in resultados]
    df_resultado["Recomendación"] = [r["recomendacion"] for r in resultados]
    df_resultado["Fecha Análisis"] = [r["fecha_analisis"] for r in resultados]
    
    return df_resultado


def generate_classification_summary(df_classified: pd.DataFrame) -> Dict[str, Any]:
    """
    Generar resumen estadístico de la clasificación
    """
    if "Clasificación Lean" not in df_classified.columns:
        return {}
    
    total = len(df_classified)
    clasificaciones = df_classified["Clasificación Lean"].value_counts().to_dict()
    
    valor_count = clasificaciones.get("Valor", 0)
    desperdicio_count = clasificaciones.get("Desperdicio", 0)
    falta_detalle_count = clasificaciones.get("Falta detalle", 0)
    
    # Tipos de desperdicio
    tipos_desperdicio = {}
    if "Tipo Desperdicio" in df_classified.columns:
        tipos_desperdicio = df_classified[
            df_classified["Tipo Desperdicio"].notna()
        ]["Tipo Desperdicio"].value_counts().to_dict()
    
    return {
        "total_actividades": total,
        "valor": valor_count,
        "desperdicio": desperdicio_count,
        "falta_detalle": falta_detalle_count,
        "porcentaje_valor": (valor_count / total * 100) if total > 0 else 0,
        "porcentaje_desperdicio": (desperdicio_count / total * 100) if total > 0 else 0,
        "tipos_desperdicio": tipos_desperdicio,
        "recomendaciones_count": len([
            r for r in df_classified["Recomendación"].tolist()
            if r and r != "Sin recomendación"
        ])
    }


def export_classification_report(
    df_classified: pd.DataFrame,
    summary: Dict[str, Any],
    format: str = "excel"
) -> bytes:
    """
    Exportar reporte de clasificación
    """
    if format == "excel":
        from io import BytesIO
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja 1: Actividades clasificadas
            df_classified.to_excel(writer, sheet_name='Clasificación', index=False)
            
            # Hoja 2: Resumen
            df_summary = pd.DataFrame([summary])
            df_summary.to_excel(writer, sheet_name='Resumen', index=False)
        
        return output.getvalue()
        
    elif format == "csv":
        return df_classified.to_csv(index=False).encode('utf-8')
        
    elif format == "json":
        result = {
            "actividades": df_classified.to_dict(orient='records'),
            "resumen": summary
        }
        return json.dumps(result, ensure_ascii=False, indent=2).encode('utf-8')
    
    return b""
