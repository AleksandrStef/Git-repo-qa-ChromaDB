import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import HOST, PORT, validate_config, CHROMA_PERSIST_DIRECTORY
from app.api.routes import router
from app.utils.logger import logger

# Create FastAPI app
app = FastAPI(
    title="Vanna AI Repository Q&A API",
    description="API for answering questions about the Vanna AI GitHub repository",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(router)


@app.get("/")
async def root():
    """
    Root endpoint
    
    Returns:
        dict: Basic information about the API
    """
    return {
        "message": "Vanna AI Repository Q&A API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    
    Args:
        request (Request): Request
        exc (Exception): Exception
        
    Returns:
        JSONResponse: Error response
    """
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected error occurred: {str(exc)}"},
    )


def startup():
    """
    Application startup function
    
    Validates configuration and creates required directories
    """
    # Validate configuration
    valid, error = validate_config()
    if not valid:
        logger.error(f"Invalid configuration: {error}")
        raise ValueError(f"Invalid configuration: {error}")
    
    # Create data directory
    os.makedirs(CHROMA_PERSIST_DIRECTORY, exist_ok=True)
    
    logger.info("Application started successfully")


def main():
    """
    Main entry point
    """
    import uvicorn
    
    # Run startup function
    startup()
    
    # Run application
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()
