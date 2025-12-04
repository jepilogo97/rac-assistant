"""
Validation endpoint - Data validation with dependency validator
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import pandas as pd

from services.dependency_validator import validate_and_estimate_process_integrated

router = APIRouter()

class ValidationRequest(BaseModel):
    """Request model for validation"""
    data: List[Dict[str, Any]]
    api_key: Optional[str] = None

@router.post("/validate")
async def validate_data(request: ValidationRequest) -> Dict[str, Any]:
    """
    Validate data and estimate missing times using dependency validator
    
    Args:
        request: {
            "data": list of records,
            "api_key": Google Gemini API key (optional)
        }
    
    Returns:
        {
            "success": bool,
            "validated_data": list of records with estimated times,
            "validation_result": validation summary,
            "summary": {
                "total_activities": int,
                "activities_with_time": int,
                "activities_without_time": int
            }
        }
    """
    try:
        # Convert data to DataFrame
        df = pd.DataFrame(request.data)
        
        # Run dependency validator if API key provided
        if request.api_key:
            # Configure Gemini
            import google.generativeai as genai
            genai.configure(api_key=request.api_key)
            
            # Run validation
            df_validated, validation_result = validate_and_estimate_process_integrated(df, request.api_key)
            
            if validation_result and validation_result.get("success"):
                return {
                    "success": True,
                    "validated_data": df_validated.to_dict('records'),
                    "validation_result": validation_result,
                    "summary": validation_result.get("summary", {})
                }
            else:
                return {
                    "success": False,
                    "error": "Validation failed",
                    "validated_data": None,
                    "validation_result": validation_result
                }
        else:
            # No API key - return original data
            return {
                "success": True,
                "validated_data": df.to_dict('records'),
                "validation_result": {
                    "success": True,
                    "message": "No validation performed (no API key provided)"
                },
                "summary": {
                    "total_activities": len(df),
                    "activities_with_time": 0,
                    "activities_without_time": 0
                }
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during validation: {str(e)}"
        )
