"""
BPMN endpoint - BPMN diagram generation and manipulation
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import pandas as pd

from services.bpmn import (
    build_bpmn_xml_advanced,
    to_builder_inputs_from_process_data
)
from config import BPMN_CONFIG

router = APIRouter()

class BPMNGenerateRequest(BaseModel):
    """Request model for BPMN generation"""
    activities: List[Dict[str, Any]]
    pool_name: Optional[str] = "Proceso"
    use_lanes: Optional[bool] = True
    show_times: Optional[bool] = True

class BPMNUpdateRequest(BaseModel):
    """Request model for BPMN update"""
    activities: List[Dict[str, Any]]
    pool_name: Optional[str] = "Proceso"

@router.post("/generate")
async def generate_bpmn(request: BPMNGenerateRequest) -> Dict[str, Any]:
    """
    Generate BPMN 2.0 XML from activities
    
    Args:
        request: {
            "activities": list of activity objects,
            "pool_name": name of the process pool,
            "use_lanes": whether to use lanes for roles,
            "show_times": whether to show times in activities
        }
    
    Returns:
        {
            "success": bool,
            "xml": BPMN XML string,
            "activities": processed activities metadata
        }
    """
    try:
        # Build BPMN XML
        xml_output = build_bpmn_xml_advanced(
            activities=request.activities,
            pool_name=request.pool_name,
            use_lanes=request.use_lanes,
            show_times=request.show_times,
            add_di=True
        )
        
        return {
            "success": True,
            "xml": xml_output,
            "activities": request.activities
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating BPMN: {str(e)}"
        )

@router.post("/update")
async def update_bpmn(request: BPMNUpdateRequest) -> Dict[str, Any]:
    """
    Update BPMN diagram with modified activities
    
    Args:
        request: {
            "activities": updated list of activity objects,
            "pool_name": name of the process pool
        }
    
    Returns:
        {
            "success": bool,
            "xml": updated BPMN XML string
        }
    """
    try:
        # Regenerate BPMN with updated activities
        xml_output = build_bpmn_xml_advanced(
            activities=request.activities,
            pool_name=request.pool_name,
            use_lanes=BPMN_CONFIG.get("use_lanes", True),
            show_times=BPMN_CONFIG.get("show_times", True),
            add_di=True
        )
        
        return {
            "success": True,
            "xml": xml_output
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating BPMN: {str(e)}"
        )

@router.post("/download")
async def download_bpmn(xml: str) -> Response:
    """
    Download BPMN XML file
    
    Args:
        xml: BPMN XML string
    
    Returns:
        XML file download
    """
    return Response(
        content=xml,
        media_type="application/xml",
        headers={
            "Content-Disposition": "attachment; filename=proceso.bpmn"
        }
    )

@router.post("/from-process-data")
async def generate_from_process_data(process_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate BPMN from process data structure
    
    Args:
        process_data: Process data dictionary
    
    Returns:
        {
            "success": bool,
            "xml": BPMN XML string,
            "activities": processed activities
        }
    """
    try:
        # Convert process data to builder inputs
        activities, flows = to_builder_inputs_from_process_data(process_data)
        
        # Build BPMN
        xml_output = build_bpmn_xml_advanced(
            activities=activities,
            flows=flows,
            pool_name=BPMN_CONFIG.get("pool_name", "Proceso"),
            use_lanes=BPMN_CONFIG.get("use_lanes", True),
            show_times=BPMN_CONFIG.get("show_times", True),
            add_di=True
        )
        
        return {
            "success": True,
            "xml": xml_output,
            "activities": activities
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating BPMN from process data: {str(e)}"
        )
