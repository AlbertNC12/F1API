"""
Formula 1 API Entry Point
Starts the Uvicorn server with the FastAPI application.
"""
import uvicorn
from app import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
