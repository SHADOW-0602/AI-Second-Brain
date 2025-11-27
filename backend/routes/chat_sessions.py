from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uuid
import time
from datetime import datetime
from database import qdrant_manager, get_qdrant_client
from config import QDRANT_URL, QDRANT_API_KEY
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, PointStruct

router = APIRouter()

# Ensure chat_sessions collection exists (vector size 1 for dummy vector)
COLLECTION_NAME = "chat_sessions"
try:
    qdrant_manager.ensure_collection(COLLECTION_NAME, vector_size=1)
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Warning: Could not ensure collection {COLLECTION_NAME}: {e}")

# Simple payload schema: session_id (str), role ("user"|"assistant"), content (str), timestamp (str)

@router.post("/chat/start")
async def start_chat():
    session_id = str(uuid.uuid4())
    # No vectors, just create an empty collection entry (optional)
    return {"session_id": session_id}

class ChatMessageRequest(BaseModel):
    session_id: str = Field(..., description="Chat session identifier")
    message: str = Field(..., description="User message")
    ai_provider: str = Field("mistral", description="AI provider: 'mistral' or 'lamatic'")
    workflow_id: str = Field("default", description="Lamatic workflow ID if used")
    context_limit: int = Field(3, description="Number of context chunks to retrieve")
    temperature: float = Field(0.7, description="Creativity temperature")

@router.post("/chat/message")
async def chat_message(req: ChatMessageRequest, background_tasks: BackgroundTasks = None): # Add background_tasks dependency
    from fastapi import BackgroundTasks # Ensure import if not present at top
    
    # Store user message
    timestamp = datetime.utcnow().isoformat()
    payload_user = {
        "session_id": req.session_id,
        "role": "user",
        "content": req.message,
        "timestamp": timestamp,
    }
    # Qdrant requires a vector; we use a dummy zero‑vector of size 1
    dummy_vector = [0.0]
    point_user = PointStruct(
        id=str(uuid.uuid4()),
        vector=dummy_vector,
        payload=payload_user,
    )
    qdrant_manager.client.upsert(COLLECTION_NAME, points=[point_user], wait=True)

    response_content = ""
    ai_provider_used = "parallel"
    model_used = "groq-llama3-70b-aggregator"

    # Always use Parallel Workflow
    from .workflow import run_parallel_workflow
    
    workflow_res = await run_parallel_workflow(req.message, background_tasks, req.context_limit)
    response_content = workflow_res.answer

    # Store assistant response
    payload_assistant = {
        "session_id": req.session_id,
        "role": "assistant",
        "content": response_content,
        "timestamp": datetime.utcnow().isoformat(),
    }
    point_assistant = PointStruct(
        id=str(uuid.uuid4()),
        vector=dummy_vector,
        payload=payload_assistant,
    )
    qdrant_manager.client.upsert(COLLECTION_NAME, points=[point_assistant], wait=True)

    return {
        "response": response_content,
        "ai_provider": ai_provider_used,
        "model_used": model_used,
        "processing_time": 0.0 # Placeholder
    }

@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    try:
        # Retrieve all points with matching session_id, ordered by timestamp
        filter_cond = Filter(
            must=[
                FieldCondition(
                    key="session_id",
                    match=MatchValue(value=session_id),
                )
            ]
        )
        # Use Qdrant query_points to get all payloads
        # Since we use a dummy vector, we can query with a dummy vector and filter
        results = qdrant_manager.client.query_points(
            collection_name=COLLECTION_NAME,
            query_vector=[0.0], # Dummy vector for query
            query_filter=filter_cond,
            limit=1000,
            with_payload=True,
            with_vectors=False,
        )
        points = results
        # Sort by timestamp
        sorted_points = sorted(points, key=lambda p: p.payload.get("timestamp", ""))
        history = [
            {"role": p.payload.get("role"), "content": p.payload.get("content"), "timestamp": p.payload.get("timestamp")}
            for p in sorted_points
        ]
        return {"session_id": session_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
