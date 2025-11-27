from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from database import qdrant_manager
from ingestion import get_embedding
from workflow_client import workflow_client
import time

router = APIRouter()
COLLECTION_NAME = "second_brain"

class ChatRequest(BaseModel):
    query: str
    limit: int = 5
    min_score: float = 0.6
    file_types: Optional[List[str]] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    processing_time: float
    workflow_response: Optional[Dict[str, Any]] = None

@router.post("/chat", response_model=ChatResponse)
async def chat_with_brain(request: ChatRequest):
    """
    Chat with your Second Brain.
    1. Embeds query.
    2. Retrieves relevant chunks from Qdrant.
    3. Sends Query + Context to External Workflow (n8n/Flowise).
    4. Returns answer.
    """
    start_time = time.time()
    
    try:
        # 1. Retrieve Context
        vector = get_embedding(request.query)
        
        # Optional file type filter
        filter_conditions = None
        if request.file_types:
            from qdrant_client.http import models
            filter_conditions = models.Filter(
                must=[
                    models.FieldCondition(
                        key="file_type",
                        match=models.MatchAny(any=request.file_types)
                    )
                ]
            )
            
        search_results = qdrant_manager.advanced_search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=request.limit,
            score_threshold=request.min_score,
            filter_conditions=filter_conditions,
        )
        
        # Format sources for the response
        sources = []
        context_chunks = []
        
        for res in search_results:
            chunk_data = {
                "text": res.payload.get("text", ""),
                "filename": res.payload.get("filename", "unknown"),
                "score": res.score,
                "file_url": res.payload.get("file_url"),
                "page": res.payload.get("page_number") # If available
            }
            sources.append(chunk_data)
            context_chunks.append(chunk_data)
            
        # 2. Execute Workflow
        if not context_chunks:
            return ChatResponse(
                answer="I couldn't find any relevant information in your Second Brain to answer that question.",
                sources=[],
                processing_time=time.time() - start_time
            )
            
        workflow_result = await workflow_client.execute_workflow(
            query=request.query,
            context=context_chunks
        )
        
        # Parse Workflow Response
        # Expecting format: {"text": "answer", ...} or {"output": "answer"} or just raw JSON
        answer = workflow_result.get("text") or workflow_result.get("output") or workflow_result.get("answer") or str(workflow_result)
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            processing_time=time.time() - start_time,
            workflow_response=workflow_result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
