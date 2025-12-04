"""
KPIs endpoint - KPI analysis and metrics
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import pandas as pd
import google.generativeai as genai

router = APIRouter()

class KPIRequest(BaseModel):
    """Request model for KPI analysis"""
    asis_data: List[Dict[str, Any]]
    tobe_data: Optional[List[Dict[str, Any]]] = None
    classified_data: Optional[List[Dict[str, Any]]] = None
    api_key: str

@router.post("/analyze")
async def analyze_kpis(request: KPIRequest) -> Dict[str, Any]:
    """
    Analyze KPIs and generate metrics
    
    Args:
        request: {
            "asis_data": AS-IS process data,
            "tobe_data": optional TO-BE process data,
            "classified_data": optional classified data,
            "api_key": Google Gemini API key
        }
    
    Returns:
        {
            "success": bool,
            "metrics": calculated metrics,
            "charts_data": data for charts,
            "insights": AI-generated insights
        }
    """
    try:
        # Convert to DataFrames
        df_asis = pd.DataFrame(request.asis_data)
        df_tobe = pd.DataFrame(request.tobe_data) if request.tobe_data else None
        df_classified = pd.DataFrame(request.classified_data) if request.classified_data else None
        
        # Configure Gemini
        genai.configure(api_key=request.api_key)
        
        # Calculate basic metrics
        metrics = calculate_process_metrics(df_asis, df_tobe, df_classified)
        
        # Prepare chart data
        charts_data = prepare_charts_data(df_asis, df_tobe, df_classified)
        
        # Generate AI insights
        insights = await generate_ai_insights(metrics, request.api_key)
        
        return {
            "success": True,
            "metrics": metrics,
            "charts_data": charts_data,
            "insights": insights
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing KPIs: {str(e)}"
        )

def calculate_process_metrics(
    df_asis: pd.DataFrame,
    df_tobe: Optional[pd.DataFrame] = None,
    df_classified: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """Calculate process metrics"""
    
    # Helper to safely get counts
    def get_automation_counts(df):
        if df is None or df.empty or "Tarea Automatizada" not in df.columns:
            return 0, 0
        automated = len(df[df["Tarea Automatizada"] == "SI"])
        manual = len(df[df["Tarea Automatizada"] == "NO"])
        return automated, manual

    # Helper to safely sum/mean time
    def get_time_metrics(df):
        if df is None or df.empty:
            return 0, 0
        
        # Try different column names for time
        time_col = None
        for col in ["Tiempo Estándar", "Tiempo Promedio", "tiempo", "time"]:
            if col in df.columns:
                time_col = col
                break
        
        if not time_col:
            return 0, 0
            
        # Ensure numeric
        series = pd.to_numeric(df[time_col], errors='coerce').fillna(0)
        return series.sum(), series.mean()

    # Calculate AS-IS metrics
    asis_automated, asis_manual = get_automation_counts(df_asis)
    asis_total_time, asis_avg_time = get_time_metrics(df_asis)

    metrics = {
        "asis": {
            "total_activities": len(df_asis),
            "total_time": asis_total_time,
            "avg_time_per_activity": asis_avg_time,
            "automated_count": asis_automated,
            "manual_count": asis_manual,
        }
    }
    
    # Add TO-BE metrics if available
    if df_tobe is not None:
        tobe_automated, tobe_manual = get_automation_counts(df_tobe)
        tobe_total_time, tobe_avg_time = get_time_metrics(df_tobe)

        metrics["tobe"] = {
            "total_activities": len(df_tobe),
            "total_time": tobe_total_time,
            "avg_time_per_activity": tobe_avg_time,
            "automated_count": tobe_automated,
            "manual_count": tobe_manual,
        }
        
        # Calculate improvements
        metrics["improvements"] = {
            "time_reduction": metrics["asis"]["total_time"] - metrics["tobe"]["total_time"],
            "time_reduction_pct": ((metrics["asis"]["total_time"] - metrics["tobe"]["total_time"]) / metrics["asis"]["total_time"] * 100) if metrics["asis"]["total_time"] > 0 else 0,
            "activities_reduction": metrics["asis"]["total_activities"] - metrics["tobe"]["total_activities"],
            "automation_increase": metrics["tobe"]["automated_count"] - metrics["asis"]["automated_count"]
        }
    
    # Add classification metrics if available
    if df_classified is not None and "desperdicio" in df_classified.columns:
        waste_counts = df_classified["desperdicio"].value_counts().to_dict()
        metrics["waste_analysis"] = {
            "total_waste_activities": len(df_classified[df_classified["desperdicio"] != "ninguno"]),
            "waste_by_type": waste_counts,
            "waste_percentage": (len(df_classified[df_classified["desperdicio"] != "ninguno"]) / len(df_classified) * 100) if len(df_classified) > 0 else 0
        }
    else:
        metrics["waste_analysis"] = {
            "total_waste_activities": 0,
            "waste_by_type": {},
            "waste_percentage": 0
        }
    
    return metrics

def prepare_charts_data(
    df_asis: pd.DataFrame,
    df_tobe: Optional[pd.DataFrame] = None,
    df_classified: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """Prepare data for charts"""
    
    charts = {}
    
    # Helper to safely sum time
    def get_total_time(df):
        if df is None or df.empty:
            return 0
        
        time_col = None
        for col in ["Tiempo Estándar", "Tiempo Promedio", "tiempo", "time"]:
            if col in df.columns:
                time_col = col
                break
        
        if not time_col:
            return 0
            
        return pd.to_numeric(df[time_col], errors='coerce').fillna(0).sum()

    # Helper to safely get automation counts
    def get_automation_counts(df):
        if df is None or df.empty or "Tarea Automatizada" not in df.columns:
            return 0, 0
        automated = len(df[df["Tarea Automatizada"] == "SI"])
        manual = len(df[df["Tarea Automatizada"] == "NO"])
        return manual, automated # Return manual first for chart order
    
    # Time comparison chart
    if df_tobe is not None:
        charts["time_comparison"] = {
            "labels": ["AS-IS", "TO-BE"],
            "data": [
                get_total_time(df_asis),
                get_total_time(df_tobe)
            ]
        }
    
    # Automation chart
    asis_manual, asis_automated = get_automation_counts(df_asis)
    charts["automation"] = {
        "labels": ["Manual", "Automatizada"],
        "asis": [asis_manual, asis_automated]
    }
    
    if df_tobe is not None:
        tobe_manual, tobe_automated = get_automation_counts(df_tobe)
        charts["automation"]["tobe"] = [tobe_manual, tobe_automated]
    
    # Waste distribution chart
    if df_classified is not None and "desperdicio" in df_classified.columns:
        waste_counts = df_classified["desperdicio"].value_counts()
        charts["waste_distribution"] = {
            "labels": waste_counts.index.tolist(),
            "data": waste_counts.values.tolist()
        }
    
    return charts

async def generate_ai_insights(metrics: Dict[str, Any], api_key: str) -> List[str]:
    """Generate AI insights from metrics"""
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Build context based on available data
        has_tobe = "tobe" in metrics and metrics["tobe"]["total_time"] > 0
        has_improvements = "improvements" in metrics
        has_waste = "waste_analysis" in metrics and metrics["waste_analysis"]["total_waste_activities"] > 0
        
        context_parts = []
        context_parts.append(f"Proceso AS-IS: {metrics['asis']['total_activities']} actividades, {metrics['asis']['total_time']:.2f} minutos totales")
        
        if has_tobe:
            context_parts.append(f"Proceso TO-BE: {metrics['tobe']['total_activities']} actividades, {metrics['tobe']['total_time']:.2f} minutos totales")
            if has_improvements:
                context_parts.append(f"Mejoras: {metrics['improvements']['time_reduction']:.2f} minutos ahorrados ({metrics['improvements']['time_reduction_pct']:.1f}% reducción)")
                context_parts.append(f"Actividades eliminadas: {metrics['improvements']['activities_reduction']}")
                context_parts.append(f"Aumento en automatización: {metrics['improvements']['automation_increase']} actividades")
        
        if has_waste:
            context_parts.append(f"Desperdicios: {metrics['waste_analysis']['total_waste_activities']} actividades ({metrics['waste_analysis']['waste_percentage']:.1f}%)")
        
        context = "\n".join(context_parts)
        
        # Build explicit status message
        status_message = ""
        if has_tobe and has_improvements:
            status_message = "IMPORTANTE: Ya existe un proceso TO-BE con mejoras implementadas. Enfócate en analizar las mejoras REALES logradas."
        else:
            status_message = "IMPORTANTE: No existe proceso TO-BE aún. Enfócate en oportunidades de mejora del proceso AS-IS actual."
        
        prompt = f"""
        Eres un experto en análisis de procesos y mejora continua. Analiza las siguientes métricas de proceso y genera exactamente 5 insights clave en español.
        
        {status_message}
        
        CONTEXTO DEL PROCESO:
        {context}
        
        INSTRUCCIONES CRÍTICAS:
        - Genera insights ESPECÍFICOS basados ÚNICAMENTE en los números reales proporcionados arriba
        - NO menciones la ausencia de datos TO-BE si el contexto muestra que YA EXISTEN
        - NO inventes datos ni hagas suposiciones sobre información no proporcionada
        - Si ves "Proceso TO-BE" en el contexto, significa que YA EXISTE y debes analizarlo
        - Sé conciso, accionable y basado en hechos
        - Cada insight debe ser una oración completa y clara
        
        TEMAS A CUBRIR (según datos disponibles):
        1. Análisis de eficiencia del proceso AS-IS
        2. Impacto y resultados de las mejoras TO-BE (SOLO si existen en el contexto)
        3. Oportunidades adicionales de automatización
        4. Análisis de desperdicios identificados (si aplica)
        5. Recomendación estratégica basada en los datos reales
        
        Formato: Lista numerada de exactamente 5 puntos, cada uno en una línea.
        """
        
        response = model.generate_content(prompt)
        insights_text = response.text
        
        # Parse insights into list
        insights = []
        for line in insights_text.split('\n'):
            line = line.strip()
            
            # Skip empty lines and headers
            if not line or line.startswith('#'):
                continue
            
            # Skip common introductory phrases
            lower_line = line.lower()
            if any(phrase in lower_line for phrase in [
                'aquí tienes', 'aquí están', 'a continuación', 
                'estos son', 'insights clave', 'basados en',
                'análisis:', 'resumen:'
            ]):
                continue
            
            # Remove numbering and bullet points
            cleaned = line.lstrip('0123456789.-*• ')
            
            # Only add if it's a meaningful insight (not too short, not a title)
            if cleaned and len(cleaned) > 15 and ':' not in cleaned[:30]:
                insights.append(cleaned)
        
        return insights[:5]  # Return top 5 insights
        
    except Exception as e:
        return [
            "Error generando insights con IA",
            f"Detalles: {str(e)}"
        ]

@router.get("/metrics-definitions")
async def get_metrics_definitions():
    """
    Get definitions of available metrics
    
    Returns:
        Dictionary of metric definitions
    """
    return {
        "metrics": [
            {
                "id": "total_time",
                "name": "Tiempo Total",
                "description": "Suma de todos los tiempos estándar de las actividades",
                "unit": "minutos"
            },
            {
                "id": "total_activities",
                "name": "Total de Actividades",
                "description": "Número total de actividades en el proceso",
                "unit": "actividades"
            },
            {
                "id": "automation_rate",
                "name": "Tasa de Automatización",
                "description": "Porcentaje de actividades automatizadas",
                "unit": "porcentaje"
            },
            {
                "id": "waste_percentage",
                "name": "Porcentaje de Desperdicio",
                "description": "Porcentaje de actividades con desperdicio identificado",
                "unit": "porcentaje"
            },
            {
                "id": "time_reduction",
                "name": "Reducción de Tiempo",
                "description": "Diferencia de tiempo entre AS-IS y TO-BE",
                "unit": "minutos"
            },
            {
                "id": "efficiency_gain",
                "name": "Ganancia de Eficiencia",
                "description": "Porcentaje de mejora en eficiencia",
                "unit": "porcentaje"
            }
        ]
    }
