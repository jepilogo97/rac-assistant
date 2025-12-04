"""
Classification endpoint - Lean classification of activities
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, List
import pandas as pd
import io
from datetime import datetime

from services.classification import (
    classify_activities_batch,
    generate_classification_summary,
    export_classification_report
)

router = APIRouter()

class ClassificationRequest(BaseModel):
    """Request model for classification"""
    data: List[Dict[str, Any]]
    api_key: str

@router.post("")
async def classify_activities(request: ClassificationRequest) -> Dict[str, Any]:
    """
    Classify activities using Lean methodology
    
    Args:
        request: {
            "data": list of activity records,
            "api_key": Google Gemini API key
        }
    
    Returns:
        {
            "success": bool,
            "classified_data": list of classified records,
            "summary": classification summary
        }
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame(request.data)
        
        # Configure Gemini
        import google.generativeai as genai
        genai.configure(api_key=request.api_key)
        
        # Classify activities with required parameters
        df_classified = classify_activities_batch(
            df=df,
            api_key=request.api_key,
            contexto_proceso="Proceso de negocio",
            progress_callback=None
        )
        
        # Generate summary
        summary = generate_classification_summary(df_classified)
        
        return {
            "success": True,
            "classified_data": df_classified.to_dict('records'),
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during classification: {str(e)}"
        )

@router.post("/export")
async def export_classification(classified_data: List[Dict[str, Any]]) -> StreamingResponse:
    """
    Export classification results to Excel
    
    Args:
        classified_data: List of classified activity records
    
    Returns:
        Excel file download
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame(classified_data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Clasificación', index=False)
            
            # Add summary sheet
            summary = generate_classification_summary(df)
            summary_df = pd.DataFrame([summary])
            summary_df.to_excel(writer, sheet_name='Resumen', index=False)
        
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"clasificacion_lean_{timestamp}.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting classification: {str(e)}"
        )

@router.get("/categories")
async def get_classification_categories():
    """
    Get available Lean waste categories
    
    Returns:
        List of waste categories with descriptions
    """
    categories = [
        {
            "id": "transporte",
            "name": "Transporte",
            "description": "Movimiento innecesario de materiales o información"
        },
        {
            "id": "inventario",
            "name": "Inventario",
            "description": "Exceso de materiales, información o trabajo en proceso"
        },
        {
            "id": "movimiento",
            "name": "Movimiento",
            "description": "Movimiento innecesario de personas"
        },
        {
            "id": "espera",
            "name": "Espera",
            "description": "Tiempo de inactividad esperando recursos o información"
        },
        {
            "id": "sobreprocesamiento",
            "name": "Sobreprocesamiento",
            "description": "Trabajo que no agrega valor al cliente"
        },
        {
            "id": "sobreproduccion",
            "name": "Sobreproducción",
            "description": "Producir más de lo necesario o antes de tiempo"
        },
        {
            "id": "defectos",
            "name": "Defectos",
            "description": "Errores que requieren retrabajo"
        },
        {
            "id": "talento",
            "name": "Talento no utilizado",
            "description": "No aprovechar habilidades y conocimientos del personal"
        },
        {
            "id": "ninguno",
            "name": "Sin desperdicio",
            "description": "Actividad que agrega valor"
        }
    ]
    
    return {"categories": categories}
