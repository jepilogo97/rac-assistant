"""
TO-BE endpoint - Process improvement proposals
"""
from fastapi import APIRouter, HTTPException, status, Response
import io
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import pandas as pd
import json
import google.generativeai as genai

from services.prompt_to_be import get_prompt_TOBE

router = APIRouter()

class TOBERequest(BaseModel):
    """Request model for TO-BE generation"""
    classified_data: Optional[List[Dict[str, Any]]] = None
    segmented_data: Optional[List[Dict[str, Any]]] = None
    api_key: str
    focus_areas: Optional[List[str]] = None
    contexto_proceso: str = "Proceso de negocio"

@router.post("/generate")
async def generate_tobe(request: TOBERequest) -> Dict[str, Any]:
    """
    Generate TO-BE process improvement proposals
    
    Args:
        request: {
            "classified_data": list of classified activity records,
            "segmented_data": optional list of segmented records,
            "api_key": Google Gemini API key,
            "focus_areas": optional list of focus areas,
            "contexto_proceso": process context description
        }
    
    Returns:
        {
            "success": bool,
            "tobe_data": list of improved activities,
            "proposals": improvement proposals,
            "sipoc": SIPOC diagram,
            "quantitative_improvements": metrics
        }
    """
    try:
        print("=" * 80)
        print("TO-BE: START - Processing request")
        print(f"TO-BE: Received data - classified: {len(request.classified_data) if request.classified_data else 0}, segmented: {len(request.segmented_data) if request.segmented_data else 0}")
        
        # Validate input data
        if not request.classified_data and not request.segmented_data:
            print("TO-BE: ERROR - No data provided")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionaron datos clasificados ni segmentados para generar el TO-BE"
            )
        
        print("TO-BE: Step 1 - Configuring Gemini")
        # Configure Gemini
        try:
            genai.configure(api_key=request.api_key)
            print("TO-BE: Step 1 DONE - Gemini configured")
        except Exception as e:
            print(f"TO-BE: ERROR in Step 1 - {str(e)}")
            raise
        
        print("TO-BE: Step 2 - Converting data to DataFrame")
        # Convert data to DataFrame
        # Prioritize segmented_data as it contains the most detailed structure (A. Actividades)
        data_for_prompt = request.segmented_data if request.segmented_data else request.classified_data
        
        if not data_for_prompt or len(data_for_prompt) == 0:
            print("TO-BE: ERROR - Data is empty")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Los datos enviados están vacíos. Asegúrate de haber ejecutado el Segmentador de Actividades."
            )
        
        try:
            df_for_prompt = pd.DataFrame(data_for_prompt)
            print(f"TO-BE: Step 2 DONE - Using {'segmented' if request.segmented_data else 'classified'} data with {len(df_for_prompt)} activities")
            print(f"TO-BE: DataFrame columns: {list(df_for_prompt.columns)}")
        except Exception as e:
            print(f"TO-BE: ERROR in Step 2 - {str(e)}")
            raise
        
        print("TO-BE: Step 3 - Generating prompt")
        # Generate prompt
        try:
            prompt = get_prompt_TOBE(
                contexto_proceso=request.contexto_proceso,
                classified_data=df_for_prompt
            )
            print(f"TO-BE: Step 3 DONE - Prompt generated ({len(prompt)} characters)")
        except Exception as e:
            print(f"TO-BE: ERROR in Step 3 - {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al generar el prompt: {str(e)}"
            )
        
        print("TO-BE: Step 4 - Creating Gemini model")
        # Call Gemini API
        try:
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 4096,
                }
            )
            print("TO-BE: Step 4 DONE - Model created")
        except Exception as e:
            print(f"TO-BE: ERROR in Step 4 - {str(e)}")
            raise
        
        print("TO-BE: Step 5 - Calling Gemini API")
        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            print(f"TO-BE: Step 5 DONE - Received response ({len(response_text)} characters)")
        except Exception as e:
            print(f"TO-BE: ERROR in Step 5 - {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al llamar a Gemini: {str(e)}"
            )
        
        print("TO-BE: Step 6 - Cleaning and parsing response")
        # Clean response
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        # Log the JSON for debugging
        print(f"TO-BE: JSON Preview (first 1000 chars): {response_text[:1000]}")
        
        # Parse JSON response
        try:
            result = json.loads(response_text)
            print("TO-BE: Step 6 DONE - JSON parsed successfully")
        except json.JSONDecodeError as e:
            print(f"TO-BE: WARNING - Initial JSON parse failed: {str(e)}")
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))
                    print("TO-BE: Step 6 DONE - JSON extracted and parsed")
                except:
                    print(f"TO-BE: ERROR - Failed to parse extracted JSON")
                    print(f"TO-BE: Response preview: {response_text[:500]}...")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"No se pudo parsear la respuesta de Gemini."
                    )
            else:
                print(f"TO-BE: ERROR - No JSON found in response")
                print(f"TO-BE: Response preview: {response_text[:500]}...")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"No se pudo encontrar JSON en la respuesta de Gemini."
                )
        
        print("TO-BE: Step 7 - Extracting data from result")
        # Extract data
        try:
            actividades_optimizadas = result.get("actividades_optimizadas", [])
            sipoc = result.get("sipoc", {})
            mejoras = result.get("mejoras_cuantitativas", {})
            print(f"TO-BE: Step 7 DONE - Extracted {len(actividades_optimizadas)} optimized activities")
        except Exception as e:
            print(f"TO-BE: ERROR in Step 7 - {str(e)}")
            raise
        
        print("TO-BE: Step 8 - Preparing response")
        response_data = {
            "success": True,
            "tobe_data": actividades_optimizadas,
            "proposals": actividades_optimizadas,
            "sipoc": sipoc,
            "quantitative_improvements": mejoras
        }
        print("TO-BE: SUCCESS - Request completed")
        print("=" * 80)
        return response_data
        
    except HTTPException as he:
        print(f"TO-BE: HTTPException - {he.detail}")
        raise
    except Exception as e:
        print(f"TO-BE: UNEXPECTED ERROR - {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating TO-BE: {str(e)}"
        )

@router.post("/compare")
async def compare_processes(
    asis_data: List[Dict[str, Any]],
    tobe_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compare AS-IS and TO-BE processes
    
    Args:
        asis_data: AS-IS process data
        tobe_data: TO-BE process data
    
    Returns:
        Comparison metrics and analysis
    """
    try:
        # Calculate AS-IS metrics
        asis_df = pd.DataFrame(asis_data)
        asis_total_activities = len(asis_df)
        asis_total_time = asis_df.get("Tiempo Estándar", asis_df.get("Tiempo Promedio", pd.Series([0]))).sum()
        asis_automated = asis_df.get("Tarea Automatizada", pd.Series(["NO"])).str.upper().eq("SI").sum()
        
        # Calculate TO-BE metrics
        tobe_df = pd.DataFrame(tobe_data)
        tobe_total_activities = len(tobe_df)
        tobe_total_time = tobe_df.get("tiempo_mejorado_minutos", pd.Series([0])).sum()
        tobe_automated = tobe_df.get("accion", pd.Series([""])).str.contains("Automatizada", case=False).sum()
        
        # Calculate improvements
        activities_reduction = asis_total_activities - tobe_total_activities
        time_reduction = asis_total_time - tobe_total_time
        time_reduction_pct = (time_reduction / asis_total_time * 100) if asis_total_time > 0 else 0
        automation_increase = tobe_automated - asis_automated
        
        return {
            "comparison": {
                "asis": {
                    "total_activities": int(asis_total_activities),
                    "total_time": float(asis_total_time),
                    "automated_activities": int(asis_automated)
                },
                "tobe": {
                    "total_activities": int(tobe_total_activities),
                    "total_time": float(tobe_total_time),
                    "automated_activities": int(tobe_automated)
                }
            },
            "improvements": {
                "activities_reduction": int(activities_reduction),
                "time_reduction": float(time_reduction),
                "time_reduction_pct": float(time_reduction_pct),
                "automation_increase": int(automation_increase)
            },
            "savings": {
                "efficiency_gain_percentage": float(time_reduction_pct)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error comparing processes: {str(e)}"
        )

@router.post("/export")
async def export_tobe(data: List[Dict[str, Any]]):
    """
    Export TO-BE data to Excel
    """
    try:
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='TO-BE Process')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['TO-BE Process']
            for idx, col in enumerate(df.columns):
                max_len = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_len, 50)
                
        output.seek(0)
        
        headers = {
            'Content-Disposition': 'attachment; filename="tobe_process.xlsx"'
        }
        
        return Response(
            content=output.getvalue(),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers=headers
        )
        
    except Exception as e:
        print(f"Export error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting data: {str(e)}"
        )
