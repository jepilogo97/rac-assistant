"""
RAC Assistant - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from api.routes import upload, validation, bpmn, classification, segmentation, tobe, kpis
from api.middleware.error_handler import add_error_handlers

# Create FastAPI app
app = FastAPI(
    title="RAC Assistant API",
    description="API para optimización de procesos empresariales con IA",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative port
        "http://localhost:80",    # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add error handlers
add_error_handlers(app)

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(validation.router, prefix="/api", tags=["Validation"])
app.include_router(bpmn.router, prefix="/api/bpmn", tags=["BPMN"])
app.include_router(classification.router, prefix="/api/classify", tags=["Classification"])
app.include_router(segmentation.router, prefix="/api/segment", tags=["Segmentation"])
app.include_router(tobe.router, prefix="/api/tobe", tags=["TO-BE"])
app.include_router(kpis.router, prefix="/api/kpis", tags=["KPIs"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RAC Assistant API",
        "version": "2.0.0",
        "docs": "/api/docs"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "RAC Assistant API"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
