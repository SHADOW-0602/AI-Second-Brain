from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

# Import the global tracker instance defined in backend/analytics.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from analytics import analytics_tracker

router = APIRouter()

@router.get("/search", response_model=Dict[str, Any])
async def get_search_analytics(days: int = 30):
    """Return aggregated search analytics for the last ``days`` days."""
    try:
        return analytics_tracker.get_search_analytics(days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/file", response_model=Dict[str, Any])
async def get_file_analytics(days: int = 30):
    """Return file‑access analytics for the last ``days`` days."""
    try:
        return analytics_tracker.get_file_analytics(days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search_history", response_model=List[Dict[str, Any]])
async def get_search_history(limit: int = 50):
    """Return the most recent ``limit`` search entries."""
    try:
        return analytics_tracker.get_search_history(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
