"""
Segmentation endpoint - Activity segmentation
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List
import pandas as pd

from services.segmentation import segment_process as segment_process_service, generate_segmentation_summary

router = APIRouter()

class SegmentationRequest(BaseModel):
    """Request model for segmentation"""
    data: List[Dict[str, Any]]
    api_key: str
    proceso_general: str = "Proceso de negocio"

@router.post("")
async def segment_activities(request: SegmentationRequest) -> Dict[str, Any]:
    """
    Segment activities into logical groups using AI
    
    Args:
        request: {
            "data": list of activity records,
            "api_key": Google Gemini API key,
            "proceso_general": general process name
        }
    
    Returns:
        {
            "success": bool,
            "segmented_data": list of segmented records,
            "segments": segment metadata,
            "summary": segmentation summary
        }
    """
    try:
        print("=" * 80)
        print("SEGMENTATION REQUEST STARTED")
        print(f"Data length: {len(request.data) if request.data else 0}")
        print(f"API key present: {bool(request.api_key)}")
        print(f"Proceso general: {request.proceso_general}")
        
        # Validate API key
        if not request.api_key or not request.api_key.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key es requerida"
            )
        
        # Convert to DataFrame
        df = pd.DataFrame(request.data)
        
        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionaron datos para segmentar"
            )
        
        print(f"DataFrame created with {len(df)} rows and {len(df.columns)} columns")
        print(f"Columns: {list(df.columns)}")
        
        # Build proceso_as_is description from data
        proceso_as_is_lines = []
        for i, row in enumerate(request.data[:50]):  # Limit to first 50 for prompt
            actividad = row.get('Actividad') or row.get('actividad') or row.get('name') or f'Actividad {i+1}'
            descripcion = row.get('Descripción') or row.get('descripcion') or row.get('description') or ''
            proceso_as_is_lines.append(f"{i+1}. {actividad}: {descripcion}")
        
        proceso_as_is = "\n".join(proceso_as_is_lines)
        
        # Validate proceso_as_is is not empty
        if not proceso_as_is or proceso_as_is.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo generar descripción del proceso. Verifica que los datos tengan columnas 'Actividad' o 'Descripción'"
            )
        
        print(f"Proceso AS-IS created with {len(proceso_as_is_lines)} activities")
        print(f"First line: {proceso_as_is_lines[0] if proceso_as_is_lines else 'N/A'}")
        
        # Segment process using AI
        print("Calling segment_process_service...")
        df_segmented = segment_process_service(
            proceso_general=request.proceso_general,
            proceso_as_is=proceso_as_is,
            api_key=request.api_key,
            batch_mode=True,
            max_pages=10,
            page_size=5
        )
        
        print(f"Segmentation completed. Result: {len(df_segmented) if df_segmented is not None else 'None'} rows")

        
        if df_segmented is None or df_segmented.empty:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudieron generar segmentos. Verifica tu API key y los datos de entrada."
            )
        
        # VALIDATION: Check activity count (warning only for now)
        input_count = len(request.data) if request.data else 0
        output_count = len(df_segmented)
        min_allowed = input_count
        max_allowed = input_count + 3
        
        if output_count < min_allowed or output_count > max_allowed:
            print(f"⚠️ WARNING: Segmentation count mismatch - Input: {input_count}, Output: {output_count}, Expected: {min_allowed}-{max_allowed}")
            # For now, log warning but continue (instead of hard rejection)
            # This allows users to see results while we diagnose the AI model issue

            
        # Enrich segmented data with original columns if available
        # We try to match by Activity name to preserve Classification and Time
        if request.data:
            # Create lookup dictionary from original data (by index and by name)
            lookup_by_index = {}
            lookup_by_name = {}
            for idx, row in enumerate(request.data):
                # Index-based lookup (1-based, as AI uses 1, 2, 3...)
                lookup_by_index[idx + 1] = row
                
                # Name-based lookup
                name = row.get('Actividad') or row.get('actividad') or row.get('name')
                if name:
                    lookup_by_name[str(name).strip().lower()] = row
            
            # First pass: Group sub-activities by their original activity
            original_activity_groups = {}
            for record in df_segmented.to_dict('records'):
                original_id = record.get('actividad_original_id')
                if original_id and isinstance(original_id, (int, float)) and not pd.isna(original_id):
                    original_id = int(original_id)
                    if original_id not in original_activity_groups:
                        original_activity_groups[original_id] = []
                    original_activity_groups[original_id].append(record)
            
            # Calculate time distribution for split activities
            time_distribution = {}
            for original_id, sub_activities in original_activity_groups.items():
                if original_id in lookup_by_index:
                    original_time = lookup_by_index[original_id].get('Tiempo Estándar') or \
                                   lookup_by_index[original_id].get('time') or \
                                   lookup_by_index[original_id].get('tiempo')
                    
                    if original_time and len(sub_activities) > 1:
                        # Get AI's time estimates for each sub-activity
                        ai_times = []
                        for sub_act in sub_activities:
                            ai_time = sub_act.get('tiempo_promedio_min') or \
                                     sub_act.get('tiempo_estimado_total_min') or 0
                            ai_times.append(float(ai_time) if ai_time else 0)
                        
                        total_ai_time = sum(ai_times)
                        
                        # Distribute original time proportionally
                        if total_ai_time > 0:
                            for i, sub_act in enumerate(sub_activities):
                                proportion = ai_times[i] / total_ai_time
                                distributed_time = float(original_time) * proportion
                                sub_act_id = sub_act.get('id')
                                if sub_act_id:
                                    time_distribution[sub_act_id] = distributed_time
            
            # Second pass: Enrich the segmented dataframe
            enriched_records = []
            for record in df_segmented.to_dict('records'):
                act_name = record.get('Actividad') or record.get('actividad') or \
                          record.get('name') or record.get('nombre')
                original_id = record.get('actividad_original_id')
                
                # Try to find the original activity
                matched_original = None
                
                # First, try by actividad_original_id (most reliable)
                if original_id and isinstance(original_id, (int, float)) and not pd.isna(original_id):
                    original_id = int(original_id)
                    if original_id in lookup_by_index:
                        matched_original = lookup_by_index[original_id]
                
                # If no match by ID, try fuzzy matching by name
                if not matched_original and act_name:
                    act_name_lower = str(act_name).strip().lower()
                    
                    # Exact match
                    if act_name_lower in lookup_by_name:
                        matched_original = lookup_by_name[act_name_lower]
                    else:
                        # Fuzzy match
                        for orig_name, orig_data in lookup_by_name.items():
                            if orig_name in act_name_lower or act_name_lower in orig_name:
                                matched_original = orig_data
                                break
                        
                        # Keyword matching
                        if not matched_original:
                            act_words = set(act_name_lower.split())
                            best_match = None
                            best_score = 0
                            
                            for orig_name, orig_data in lookup_by_name.items():
                                orig_words = set(orig_name.split())
                                common_words = act_words.intersection(orig_words)
                                if len(common_words) > 0:
                                    score = len(common_words) / max(len(act_words), len(orig_words))
                                    if score > best_score and score > 0.3:
                                        best_score = score
                                        best_match = orig_data
                            
                            if best_match:
                                matched_original = best_match
                
                # If we found a match, copy all classification data
                if matched_original:
                    # Copy Classification Lean
                    if not record.get('Clasificación Lean') and not record.get('clasificacion'):
                        clasificacion = matched_original.get('Clasificación Lean') or \
                                       matched_original.get('clasificacion') or \
                                       matched_original.get('classification')
                        if clasificacion:
                            record['Clasificación Lean'] = clasificacion
                        
                    # Copy Waste Type
                    if not record.get('Tipo Desperdicio') and not record.get('tipo_desperdicio'):
                        tipo_desp = matched_original.get('Tipo Desperdicio') or \
                                   matched_original.get('tipo_desperdicio') or \
                                   matched_original.get('desperdicio')
                        if tipo_desp:
                            record['Tipo Desperdicio'] = tipo_desp
                    
                    # Copy Justification
                    if not record.get('Justificación') and not record.get('justificacion'):
                        justif = matched_original.get('Justificación') or \
                                matched_original.get('justificacion')
                        if justif:
                            record['Justificación'] = justif
                    
                    # Copy Responsible
                    if not record.get('Cargo que ejecuta la tarea') and \
                       not record.get('responsible') and not record.get('responsable'):
                        resp = matched_original.get('Cargo que ejecuta la tarea') or \
                              matched_original.get('responsible') or \
                              matched_original.get('responsable')
                        if resp:
                            record['Cargo que ejecuta la tarea'] = resp
                    
                    # Copy Description if missing
                    if not record.get('Descripción') and not record.get('descripcion') and \
                       not record.get('description'):
                        desc = matched_original.get('Descripción') or \
                              matched_original.get('descripcion') or \
                              matched_original.get('description')
                        if desc:
                            record['Descripción'] = desc
                    
                    # Handle time distribution (ALWAYS enforce correct times)
                    record_id = record.get('id')
                    
                    # Check if this is a subdivided activity
                    if record_id and record_id in time_distribution:
                        # FORCE the proportionally distributed time (override AI's estimate)
                        record['Tiempo Estándar'] = round(time_distribution[record_id], 2)
                    elif matched_original:
                        # For 1:1 activities, use the exact original time
                        tiempo = matched_original.get('Tiempo Estándar') or \
                                matched_original.get('time') or \
                                matched_original.get('tiempo')
                        if tiempo:
                            record['Tiempo Estándar'] = float(tiempo)
                        else:
                            # Fall back to AI's estimate only if no original time exists
                            ai_time = record.get('tiempo_promedio_min') or \
                                     record.get('tiempo_estimado_total_min')
                            if ai_time:
                                record['Tiempo Estándar'] = float(ai_time)
                
                enriched_records.append(record)
            
            if enriched_records:
                df_segmented = pd.DataFrame(enriched_records)
        
        # Normalize capitalization of tipo_actividad (OPERATIVA -> Operativa)
        if "tipo_actividad" in df_segmented.columns:
            df_segmented["tipo_actividad"] = df_segmented["tipo_actividad"].apply(
                lambda x: x.capitalize() if isinstance(x, str) and x.isupper() else x
            )
        
        # Generate summary
        try:
            summary = generate_segmentation_summary(df_segmented)
        except Exception as e:
            # Fallback summary if generation fails
            summary = {
                "total_activities": len(df_segmented),
                "total_segments": len(df_segmented.get("tipo_actividad", pd.Series([])).unique()) if "tipo_actividad" in df_segmented.columns else 0
            }
        
        # Extract segments metadata
        segments_metadata = []
        if "tipo_actividad" in df_segmented.columns:
            tipos = df_segmented["tipo_actividad"].dropna().unique()
            for i, tipo in enumerate(tipos):
                if pd.isna(tipo) or tipo == "":
                    continue
                    
                segment_df = df_segmented[df_segmented["tipo_actividad"] == tipo]
                
                # Try to get time total from different possible column names
                time_total = 0
                for time_col in ["tiempo_estimado_total_min", "time", "tiempo", "Tiempo Estándar"]:
                    if time_col in segment_df.columns:
                        time_total = segment_df[time_col].fillna(0).sum()
                        break
                
                segments_metadata.append({
                    "id": i,
                    "name": str(tipo),
                    "description": f"Actividades de tipo {tipo}",
                    "activity_count": len(segment_df),
                    "time_total": float(time_total) if time_total else 0
                })
        
        return {
            "success": True,
            "segmented_data": df_segmented.to_dict('records'),
            "segments": segments_metadata,
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error during segmentation: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )

@router.post("/export")
async def export_segmentation(request: List[Dict[str, Any]]):
    """
    Export segmented activities to Excel
    """
    try:
        from fastapi.responses import StreamingResponse
        from io import BytesIO
        from services.segmentation import export_segmentation_report
        
        df = pd.DataFrame(request)
        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data to export"
            )
            
        excel_bytes = export_segmentation_report(df)
        
        return StreamingResponse(
            BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=segmentacion_actividades.xlsx"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting data: {str(e)}"
        )
