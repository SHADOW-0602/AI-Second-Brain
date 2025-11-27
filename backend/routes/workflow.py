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

async def background_memory_task(query: str, answer: str, context_text: str):
    """
    Background task to extract facts and store memory.
    """
    try:
        # 1. Extract Facts
        facts = await groq_client.extract_facts(query, answer)
        logger.info(f"Extracted {len(facts)} facts for query: {query}")

        # 2. Prepare text for ingestion
        # We ingest the Q&A pair + extracted facts as a new "memory" document
        memory_text = f"""
MEMORY TYPE: Conversation & Facts
DATE: {time.strftime("%Y-%m-%d")}
QUERY: {query}
ANSWER: {answer}
FACTS:
{chr(10).join(['- ' + f for f in facts])}
"""
        # 3. Ingest into Qdrant (using existing logic)
        # We need to chunk and embed this. 
        # For simplicity, we'll treat it as a single chunk if small, or use ingestion logic.
        # Re-using ingestion logic might be complex here without circular imports or refactoring.
        # We will do a direct insertion for now using qdrant_manager if possible, 
        # or better, use the 'ingest' route logic but programmatically.
        
        # Simplified direct insertion for memory
        vector = get_embedding(memory_text)
        
        # Create a unique ID
        import uuid
        doc_id = str(uuid.uuid4())
        
        payload = {
            "text": memory_text,
            "filename": "conversation_memory.txt",
            "file_type": "memory",
            "chunk_index": 0,
            "is_fact": True,
            "timestamp": time.time()
        }
        
        qdrant_manager.upload_vectors(
            collection_name="second_brain",
            vectors=[vector],
            payloads=[payload]
        )
        logger.info("Memory successfully stored in Qdrant.")

    except Exception as e:
        logger.error(f"Background Memory Task Error: {e}")

async def run_parallel_workflow(query: str, background_tasks: BackgroundTasks, context_limit: int = 5) -> ParallelWorkflowResponse:
    start_time = time.time()
    
    try:
        # 1. Search Context (Vector DB)
        query_vector = get_embedding(query)
        search_results = qdrant_manager.advanced_search(
            collection_name="second_brain",
            query_vector=query_vector,
            limit=context_limit,
            score_threshold=0.6
        )
        
        context_text = "\n\n".join([res.payload.get('text', '') for res in search_results])
        
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
            elif isinstance(res, dict) and "output" in res:
                responses[provider] = res["output"]
            else:
                responses[provider] = str(res)

        # 3. Aggregation (Groq)
        final_answer = await groq_client.aggregate_responses(query, context_text, responses)
        
        # 4. Background Task: Fact Extraction & Storage
        if background_tasks:
            background_tasks.add_task(background_memory_task, query, final_answer, context_text)
        else:
            # If no background tasks object (e.g. direct call), run synchronously or skip
            # For now, we'll just log warning, or we could await it if critical
            logger.warning("No background_tasks provided, skipping background memory task")
        
        # 5. Return Response
        return ParallelWorkflowResponse(
            answer=final_answer,
            processing_time=time.time() - start_time,
            sources=[SearchResult(
                text=res.payload.get("text", ""),
                score=res.score,
                chunk_id=str(res.id),
                filename=res.payload.get("filename", "unknown"),
                file_type=res.payload.get("file_type", "unknown"),
                chunk_index=res.payload.get("chunk_index", 0)
            ) for res in search_results]
        )

    except Exception as e:
        logger.error(f"Parallel Workflow Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflow/parallel", response_model=ParallelWorkflowResponse)
async def execute_parallel_workflow(request: ParallelWorkflowRequest, background_tasks: BackgroundTasks):
    return await run_parallel_workflow(request.query, background_tasks, request.context_limit)
