from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from lamatic_client import lamatic_client
import time

router = APIRouter()

class LamaticRequest(BaseModel):
    query: str
    context: Optional[str] = None

class LamaticResponse(BaseModel):
    answer: str
    raw_response: Dict[str, Any]
    processing_time: float

@router.post("/lamatic/chat", response_model=LamaticResponse)
async def chat_with_lamatic(request: LamaticRequest):
    """
    Direct chat with Lamatic workflow.
    """
    start_time = time.time()
    try:
        # If context is not provided, we might want to fetch it or send empty
        context = request.context or ""
        
        result = await lamatic_client.execute_workflow(request.query, context)
        
        # Parse response - assuming Lamatic returns 'output' or 'result'
        answer = result.get("output") or result.get("result") or str(result)
        
        return LamaticResponse(
            answer=answer,
            raw_response=result,
            processing_time=time.time() - start_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
