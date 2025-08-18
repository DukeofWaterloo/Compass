"""
Compass - Course Recommendation API
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.api import recommendations, courses, health

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Compass API",
    description="AI-powered course recommendations for UWaterloo students",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(courses.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Compass API is running! 🧭"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True").lower() == "true"
    )