from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
 
from app.api.router import api_router
 
 
app = FastAPI(
    title="AI Landslide Risk Monitoring System",
    description=(
        "AI-based early warning and landslide risk monitoring "
        "system for North-East India"
    ),
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
 
app.include_router(
    api_router,
    prefix="/api/v1",
)
 
app.mount("/dashboard", StaticFiles(directory="frontend", html=True), name="frontend")
 
 
@app.get("/")
def root():
    return {
        "message": "AI Landslide Risk Monitoring System API",
        "version": "1.0.0",
        "status": "running",
    }
 