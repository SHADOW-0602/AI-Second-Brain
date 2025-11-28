from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uuid
import time
from datetime import datetime
from database import qdrant_manager, get_qdrant_client
from config import QDRANT_URL, QDRANT_API_KEY
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, PointStruct
from groq_client import groq_client
from r2_storage import r2_storage
import json

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
    
    workflow_res = await run_parallel_workflow(req.message, background_tasks, req.context_limit, req.session_id)
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
    
    # Store conversation in R2
    if background_tasks:
        background_tasks.add_task(store_conversation_to_r2, req.session_id, payload_user, payload_assistant)
    
    # Generate chat title based on first message
    chat_title = None
    if background_tasks:
        background_tasks.add_task(generate_chat_title, req.session_id, req.message)

    return {
        "response": response_content,
        "ai_provider": ai_provider_used,
        "model_used": model_used,
        "processing_time": 0.0, # Placeholder
        "chat_title": chat_title
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
        import os
        history_limit = int(os.getenv('CHAT_HISTORY_LIMIT', '1000'))
        
        results = qdrant_manager.client.query_points(
            collection_name=COLLECTION_NAME,
            query=[0.0], # Dummy vector for query
            query_filter=filter_cond,
            limit=history_limit,
            with_payload=True,
            with_vectors=False,
        )
        points = results.points if hasattr(results, 'points') else results
        # Sort by timestamp
        sorted_points = sorted(points, key=lambda p: p.payload.get("timestamp", ""))
        history = [
            {"role": p.payload.get("role"), "content": p.payload.get("content"), "timestamp": p.payload.get("timestamp")}
            for p in sorted_points
        ]
        return {"session_id": session_id, "history": history}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in get_chat_history: {e}")
        print(f"Results type: {type(results) if 'results' in locals() else 'Not defined'}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_chat_title(session_id: str, first_message: str):
    """Generate a descriptive title for the chat session based on first message."""
    try:
        # Use Groq to generate a short, descriptive title
        title_prompt = f"Generate a short, descriptive title (max 4 words) for a chat that starts with: '{first_message}'. Only return the title, nothing else."
        
        import os
        title_temperature = float(os.getenv('CHAT_TITLE_TEMPERATURE', '0.3'))
        max_tokens = int(os.getenv('CHAT_TITLE_MAX_TOKENS', '20'))
        
        completion = groq_client.client.chat.completions.create(
            messages=[
                {"role": "user", "content": title_prompt}
            ],
            model=groq_client.extractor_model,
            max_tokens=max_tokens,
            temperature=title_temperature
        )
        
        title = completion.choices[0].message.content.strip().replace('"', '')
        
        # Store title in a simple collection or return it
        # For now, we'll store it as metadata in the session
        dummy_vector = [0.0]
        title_payload = {
            "session_id": session_id,
            "role": "system",
            "content": f"CHAT_TITLE: {title}",
            "timestamp": datetime.utcnow().isoformat(),
            "is_title": True
        }
        
        point_title = PointStruct(
            id=str(uuid.uuid4()),
            vector=dummy_vector,
            payload=title_payload,
        )
        
        qdrant_manager.client.upsert(COLLECTION_NAME, points=[point_title], wait=True)
        
    except Exception as e:
        print(f"Failed to generate chat title: {e}")

async def store_conversation_to_r2(session_id: str, user_payload: dict, assistant_payload: dict):
    """Store conversation exchange in R2 storage as JSON."""
    try:
        # Create conversation object
        conversation = {
            "session_id": session_id,
            "exchange": {
                "user": user_payload,
                "assistant": assistant_payload
            },
            "stored_at": datetime.utcnow().isoformat()
        }
        
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"conversations/{session_id}/{timestamp}_{uuid.uuid4().hex[:8]}.json"
        
        # Convert to JSON bytes
        json_content = json.dumps(conversation, indent=2).encode('utf-8')
        
        # Upload to R2
        r2_url = r2_storage.upload_file(
            file_content=json_content,
            filename=filename,
            content_hash=f"conv_{session_id}_{timestamp}"
        )
        
        print(f"Conversation stored in R2: {r2_url}")
        
    except Exception as e:
        print(f"Failed to store conversation in R2: {e}")

@router.get("/chat/title/{session_id}")
async def get_chat_title(session_id: str):
    """Get the generated title for a chat session."""
    try:
        # Search for title in the session
        filter_cond = Filter(
            must=[
                FieldCondition(
                    key="session_id",
                    match=MatchValue(value=session_id),
                ),
                FieldCondition(
                    key="is_title",
                    match=MatchValue(value=True),
                )
            ]
        )
        
        import os
        title_limit = int(os.getenv('CHAT_TITLE_LIMIT', '1'))
        
        results = qdrant_manager.client.query_points(
            collection_name=COLLECTION_NAME,
            query=[0.0],
            query_filter=filter_cond,
            limit=title_limit,
            with_payload=True,
            with_vectors=False,
        )
        
        if results and len(results) > 0:
            content = results[0].payload.get("content", "")
            title_prefix = os.getenv('CHAT_TITLE_PREFIX', 'CHAT_TITLE')
            title = content.replace(f"{title_prefix}: ", "")
            return {"title": title}
        
        return {"title": f"Chat {session_id[:8]}"}
        
    except Exception as e:
        return {"title": f"Chat {session_id[:8]}"}

@router.get("/chat/sessions")
async def get_all_chat_sessions():
    """Get all chat sessions (shared across all users)."""
    try:
        import os
        scroll_limit = int(os.getenv('CHAT_SESSIONS_LIMIT', '1000'))
        
        results = qdrant_manager.client.scroll(
            collection_name=COLLECTION_NAME,
            limit=scroll_limit,
            with_payload=True,
            with_vectors=False,
        )
        
        sessions = {}
        for point in results[0]:
            session_id = point.payload.get("session_id")
            timestamp = point.payload.get("timestamp")
            is_title = point.payload.get("is_title", False)
            
            if session_id and session_id not in sessions:
                sessions[session_id] = {
                    "id": session_id,
                    "title": f"Chat {session_id[:8]}",
                    "created": timestamp,
                    "last_message": timestamp
                }
            
            if session_id and is_title:
                content = point.payload.get("content", "")
                title_prefix = os.getenv('CHAT_TITLE_PREFIX', 'CHAT_TITLE')
                title = content.replace(f"{title_prefix}: ", "")
                sessions[session_id]["title"] = title
        
        sorted_sessions = sorted(sessions.values(), key=lambda x: x["last_message"] or "", reverse=True)
        return {"sessions": sorted_sessions}
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting chat sessions: {e}")
        return {"sessions": []}
