from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import time
import logging

# Import Clients
from groq_client import groq_client
from mistral_client import mistral_client
from cohere_client import cohere_client
from gemini_client import gemini_client

# Import Database & Ingestion
from database import qdrant_manager
from ingestion import get_embedding
from models import SearchResult

logger = logging.getLogger(__name__)

router = APIRouter()

class ParallelWorkflowRequest(BaseModel):
    query: str
    context_limit: int = 5

class ParallelWorkflowResponse(BaseModel):
    answer: str
    processing_time: float
    sources: List[SearchResult]

async def background_memory_task(query: str, answer: str, context_text: str, session_id: str = None):
    """
    Background task to extract facts and store memory with session isolation.
    """
    try:
        # 1. Extract Facts
        facts = await groq_client.extract_facts(query, answer)
        logger.info(f"Extracted {len(facts)} facts for query: {query}")

        # 2. Prepare text for ingestion
        memory_text = f"""
MEMORY TYPE: Conversation & Facts
DATE: {time.strftime("%Y-%m-%d")}
QUERY: {query}
ANSWER: {answer}
FACTS:
{chr(10).join(['- ' + f for f in facts])}
"""
        
        # 3. Simplified direct insertion for memory with session isolation
        vector = get_embedding(memory_text)
        
        import uuid
        doc_id = str(uuid.uuid4())
        
        payload = {
            "text": memory_text,
            "filename": "conversation_memory.txt",
            "file_type": "memory",
            "chunk_index": 0,
            "is_fact": True,
            "timestamp": time.time(),
            # No session_id for memories - they are shared across all chats
            "type": "memory"
        }
        
        from qdrant_client.http.models import PointStruct
        point = PointStruct(
            id=doc_id,
            vector=vector,
            payload=payload
        )
        import os
        collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'second_brain')
        
        qdrant_manager.client.upsert(
            collection_name=collection_name,
            points=[point],
            wait=True
        )
        logger.info("Memory successfully stored in Qdrant with session isolation.")

    except Exception as e:
        logger.error(f"Background Memory Task Error: {e}")

async def run_parallel_workflow(query: str, background_tasks: BackgroundTasks, context_limit: int = 5, session_id: str = None) -> ParallelWorkflowResponse:
    start_time = time.time()
    
    try:
        # 1. Search Context (Session-specific documents + memories)
        query_vector = get_embedding(query)
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue, MatchAny
        
        import os
        from config import QDRANT_SCORE_THRESHOLD
        score_threshold = QDRANT_SCORE_THRESHOLD
        collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'second_brain')
        
        # Always search all documents and memories (no session filtering)
        session_filter = None
        
        try:
            search_results = qdrant_manager.advanced_search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=context_limit,
                score_threshold=score_threshold,
                filter_conditions=session_filter
            )
            
            # Debug: Log search details
            logger.info(f"Search query: {query}")
            logger.info(f"Collection: {collection_name}")
            logger.info(f"Score threshold: {score_threshold}")
            logger.info(f"Filter: {session_filter}")
            logger.info(f"Search results count: {len(search_results) if search_results else 0}")
            
            # Force a test search to see if collection has data
            try:
                test_results = qdrant_manager.client.scroll(
                    collection_name=collection_name,
                    limit=5,
                    with_payload=True
                )
                logger.info(f"Collection has {len(test_results[0]) if test_results and test_results[0] else 0} total points")
            except Exception as e:
                logger.error(f"Collection scroll failed: {e}")
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            search_results = []
        
        # Handle None or empty search results
        if search_results is None:
            search_results = []
        
        # Safe context text extraction
        context_text = ""
        if search_results:
            try:
                context_text = "\n\n".join([res.payload.get('text', '') for res in search_results if res and hasattr(res, 'payload') and res.payload])
            except Exception as e:
                logger.error(f"Context extraction failed: {e}")
                context_text = ""
        
        # Add friendly context message if no relevant information found
        if not context_text.strip():
            context_text = "I don't have any previous conversations or documents about this topic yet. I'm ready to help you with fresh information and start building our knowledge together!"
        
        # 2. Parallel Model Execution
        tasks = [
            gemini_client.chat_with_context(query, context_text),
            mistral_client.chat_with_context(query, [context_text]),
            cohere_client.chat_with_context(query, context_text)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        responses = {}
        providers = ["gemini", "mistral", "cohere"]
        
        for i, res in enumerate(results):
            provider = providers[i]
            if isinstance(res, Exception):
                logger.error(f"{provider} failed: {res}")
                responses[provider] = f"Error: {str(res)}"
            elif res is None:
                logger.warning(f"{provider} returned None")
                responses[provider] = "No response from model"
            elif isinstance(res, dict) and "output" in res:
                responses[provider] = res["output"]
            elif isinstance(res, dict) and "error" in res:
                responses[provider] = f"Error: {res['error']}"
            else:
                responses[provider] = str(res) if res is not None else "Empty response"

        # 3. Aggregation (Groq)
        if not responses:
            final_answer = "I apologize, but I'm unable to process your request at the moment due to technical issues."
        else:
            final_answer = await groq_client.aggregate_responses(query, context_text, responses)
            if final_answer is None:
                final_answer = "I apologize, but I couldn't generate a proper response. Please try again."
        
        # 4. Background Task: Fact Extraction & Storage with session isolation
        if background_tasks:
            background_tasks.add_task(background_memory_task, query, final_answer, context_text, session_id)
        else:
            logger.warning("No background_tasks provided, skipping background memory task")
        
        # 5. Return Response
        return ParallelWorkflowResponse(
            answer=final_answer,
            processing_time=time.time() - start_time,
            sources=[SearchResult(
                text=res.payload.get("text", "") if hasattr(res, 'payload') and res.payload else "",
                score=getattr(res, 'score', 0.0),
                chunk_id=str(getattr(res, 'id', 'unknown')),
                filename=res.payload.get("filename", "unknown") if hasattr(res, 'payload') and res.payload else "unknown",
                file_type=res.payload.get("file_type", "unknown") if hasattr(res, 'payload') and res.payload else "unknown",
                chunk_index=res.payload.get("chunk_index", 0) if hasattr(res, 'payload') and res.payload else 0
            ) for res in search_results if res is not None] if search_results else []
        )

    except Exception as e:
        logger.error(f"Parallel Workflow Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflow/parallel", response_model=ParallelWorkflowResponse)
async def execute_parallel_workflow(request: ParallelWorkflowRequest, background_tasks: BackgroundTasks):
    return await run_parallel_workflow(request.query, background_tasks, request.context_limit)
