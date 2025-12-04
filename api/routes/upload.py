"""
Upload endpoint - File upload and initial processing
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any
import pandas as pd
import io
import os
from datetime import datetime

from services.file_utils import load_excel_file
from services.data_processing import validate_dataframe

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload and validate Excel file
    
    Args:
        file: Excel file (.xlsx or .xls)
    
    Returns:
        {
            "success": bool,
            "data": list of records,
            "validation": validation results,
            "metadata": file metadata
        }
    """
    # Validate file extension
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only .xlsx and .xls files are allowed."
        )
    
    # Validate file size (max 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10MB limit."
        )
    
    try:
        # Load Excel file
        df = pd.read_excel(io.BytesIO(contents))
        
        # Validate dataframe structure
        validation = validate_dataframe(df)
        
        if not validation["is_valid"]:
            return {
                "success": False,
                "error": f"Error de validación: {'; '.join(validation['errors'])}",
                "validation": validation,
                "data": None
            }
        
        # Convert dataframe to records
        data_records = df.to_dict('records')
        
        # Prepare metadata
        metadata = {
            "filename": file.filename,
            "size": len(contents),
            "rows": len(df),
            "columns": len(df.columns),
            "uploaded_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": data_records,
            "validation": validation,
            "metadata": metadata
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )

@router.get("/upload/example")
async def get_example_files():
    """
    Get list of example files available
    
    Returns:
        List of example files with metadata
    """
    example_dir = "files-example"
    
    if not os.path.exists(example_dir):
        return {"files": []}
    
    example_files = []
    for filename in os.listdir(example_dir):
        if filename.endswith(('.xlsx', '.xls')):
            filepath = os.path.join(example_dir, filename)
            file_size = os.path.getsize(filepath)
            example_files.append({
                "filename": filename,
                "size": file_size,
                "path": filepath
            })
    
    return {"files": example_files}
