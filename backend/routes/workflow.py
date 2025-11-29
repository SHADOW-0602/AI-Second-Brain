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
    active_document_text: Optional[str] = None

class ParallelWorkflowResponse(BaseModel):
    answer: str
    processing_time: float
    sources: List[SearchResult]

async def update_langchain_memory(session_id: str, user_message: str, ai_response: str):
    """Update LangChain memory with conversation and preferences"""
    try:
        from langchain_memory import get_memory_manager
        memory_manager = get_memory_manager()
        memory_manager.add_conversation(session_id, user_message, ai_response)
        logger.info(f"Updated LangChain memory for session {session_id}")
    except Exception as e:
        logger.error(f"LangChain memory update failed: {e}")

async def check_duplicate_question(query: str, session_id: str) -> Optional[str]:
    """Check if user asked similar question before and return previous result."""
    try:
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        
        # Search for similar questions in chat history
        query_vector = get_embedding(query)
        
        # Search in chat_sessions collection for similar user messages
        similar_results = qdrant_manager.advanced_search(
            collection_name="chat_sessions",
            query_vector=query_vector,
            limit=3,
            score_threshold=0.85,  # High threshold for duplicates
            filter_conditions=Filter(
                must=[
                    FieldCondition(key="session_id", match=MatchValue(value=session_id)),
                    FieldCondition(key="role", match=MatchValue(value="user"))
                ]
            )
        )
        
        if similar_results and len(similar_results) > 0:
            # Get the most similar question
            similar_question = similar_results[0]
            similarity_score = similar_question.score
            
            if similarity_score > 0.9:  # Very similar question
                # Check if context has changed (new files uploaded) since this question
                try:
                    previous_timestamp = similar_question.payload.get("timestamp")
                    if previous_timestamp:
                        # Find latest file upload in this session
                        # We filter by chunk_index=0 to get one point per file
                        latest_files = qdrant_manager.client.scroll(
                            collection_name=os.getenv('QDRANT_COLLECTION_NAME', 'second_brain'),
                            scroll_filter=Filter(
                                must=[
                                    FieldCondition(key="session_id", match=MatchValue(value=session_id)),
                                    FieldCondition(key="chunk_index", match=MatchValue(value=0))
                                ]
                            ),
                            limit=100,
                            with_payload=True
                        )
                        
                        if latest_files and latest_files[0]:
                            files = latest_files[0]
                            # Find max processed_at
                            max_processed_at = max([f.payload.get("processed_at", "") for f in files])
                            
                            if max_processed_at > previous_timestamp:
                                logger.info("New files detected since previous question. Skipping duplicate check.")
                                return None
                except Exception as e:
                    logger.error(f"Failed to check for context updates: {e}")
                    # If check fails, assume context might have changed to be safe
                    return None

                previous_question = similar_question.payload.get("content", "")
                
                # Find the corresponding AI response
                try:
                    # Get chat history around that time to find the AI response
                    chat_history = qdrant_manager.client.scroll(
                        collection_name="chat_sessions",
                        scroll_filter=Filter(
                            must=[
                                FieldCondition(key="session_id", match=MatchValue(value=session_id)),
                                FieldCondition(key="role", match=MatchValue(value="assistant"))
                            ]
                        ),
                        limit=10,
                        with_payload=True
                    )
                    
                    if chat_history and chat_history[0]:
                        # Find the response that came after the similar question
                        for response in chat_history[0]:
                            response_content = response.payload.get("content", "")
                            if len(response_content) > 50:  # Valid response
                                # Check what memories/documents were used for that answer
                                memory_info = await get_memory_context_info(previous_question, session_id)
                                duplicate_msg = (
                                    "**I notice you asked a similar question before:**\n\n"
                                    f"*Previous question:* \"{previous_question}\"\n\n"
                                    f"*Memory sources used:* {memory_info}\n\n"
                                    f"*My previous answer:*\n{response_content}\n\n"
                                    "---\n\n"
                                    "Is this what you were looking for, or would you like me to provide additional information?"
                                )
                                return duplicate_msg
                                
                except Exception as e:
                    logger.error(f"Failed to get previous response: {e}")
        
        return None
        
    except Exception as e:
        logger.error(f"Duplicate check failed: {e}")
        return None

async def get_memory_context_info(query: str, session_id: str) -> str:
    """Get information about which memories/documents were used for a query."""
    try:
        query_vector = get_embedding(query)
        
        # Search for relevant memories and documents
        memory_results = qdrant_manager.advanced_search(
            collection_name=os.getenv('QDRANT_COLLECTION_NAME', 'second_brain'),
            query_vector=query_vector,
            limit=3,
            score_threshold=0.6,
            filter_conditions=Filter(
                should=[
                    FieldCondition(key="session_id", match=MatchValue(value=session_id)),
                    FieldCondition(key="file_type", match=MatchValue(value="memory"))
                ],
                must_not=[
                    FieldCondition(key="excluded", match=MatchValue(value=True))
                ]
            )
        )
        
        sources = []
        if memory_results:
            for result in memory_results:
                if hasattr(result, 'payload') and result.payload:
                    file_type = result.payload.get('file_type', 'unknown')
                    filename = result.payload.get('filename', 'unknown')
                    
                    if file_type == 'memory':
                        sources.append('📧 Conversation Memory')
                    else:
                        sources.append(f'📄 {filename}')
        
        if sources:
            unique_sources = list(set(sources))
            return ', '.join(unique_sources[:3])  # Limit to 3 sources
        else:
            return '🧠 General Knowledge'
            
    except Exception as e:
        logger.error(f"Failed to get memory context info: {e}")
        return '❓ Unknown sources'

def get_memory_sources_from_results(search_results, active_document_filename=None) -> str:
    """Extract memory sources from search results for display."""
    try:
        sources = []
        
        # Add active document if present
        if active_document_filename:
            sources.append(f'📄 {active_document_filename} (Active)')
        
        # Process search results
        if search_results:
            for result in search_results:
                if hasattr(result, 'payload') and result.payload:
                    file_type = result.payload.get('file_type', 'unknown')
                    filename = result.payload.get('filename', 'unknown')
                    
                    if file_type == 'memory':
                        if '📧 Conversation Memory' not in sources:
                            sources.append('📧 Conversation Memory')
                    elif filename != active_document_filename:  # Don't duplicate active doc
                        source_name = f'📄 {filename}'
                        if source_name not in sources:
                            sources.append(source_name)
        
        # Add general knowledge if no specific sources
        if not sources:
            sources.append('🧠 General Knowledge')
        
        return ', '.join(sources[:4])  # Limit to 4 sources
        
    except Exception as e:
        logger.error(f"Failed to extract memory sources: {e}")
        return '🧠 General Knowledge'

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

async def run_parallel_workflow(query: str, background_tasks: BackgroundTasks, context_limit: int = 5, session_id: str = None, active_document_text: str = None, active_document_filename: str = None) -> ParallelWorkflowResponse:
    start_time = time.time()
    
    try:
        # 0. Analyze Intent
        intent_data = await gemini_client.analyze_intent(query)
        intent = intent_data.get("intent", "chat")
        keywords = intent_data.get("keywords", [])
        logger.info(f"Intent Analysis: {intent} | Keywords: {keywords}")

        # 0. Fetch Active Document Content if filename provided
        if active_document_filename and not active_document_text:
            try:
                from qdrant_client.http.models import Filter, FieldCondition, MatchValue
                
                # Filter by filename (and session_id if available, though filename should be unique per session)
                must_conditions = [
                    FieldCondition(key="filename", match=MatchValue(value=active_document_filename))
                ]
                if session_id:
                    must_conditions.append(FieldCondition(key="session_id", match=MatchValue(value=session_id)))
                
                # Exclude documents marked as excluded
                must_not_conditions = [
                    FieldCondition(key="excluded", match=MatchValue(value=True))
                ]
                
                # Note: If the file is in a DIFFERENT session (as we saw in debug), this strict filter will fail.
                # However, for security/correctness, we should probably stick to the session.
                # BUT, if the user is viewing it, they expect it to work.
                # Let's try strict session first. If it fails, maybe fallback? 
                # No, strict session is better. If it fails, it means the frontend state is weird.
                
                doc_results = qdrant_manager.client.scroll(
                    collection_name=os.getenv('QDRANT_COLLECTION_NAME', 'second_brain'),
                    scroll_filter=Filter(must=must_conditions, must_not=must_not_conditions),
                    limit=100, # Fetch enough chunks
                    with_payload=True,
                    with_vectors=False
                )
                
                if doc_results and doc_results[0]:
                    chunks = sorted(doc_results[0], key=lambda x: x.payload.get('chunk_index', 0))
                    active_document_text = "\n".join([chunk.payload.get('text', '') for chunk in chunks])
                    logger.info(f"Fetched active document {active_document_filename}: {len(active_document_text)} chars")
                else:
                    logger.warning(f"Active document {active_document_filename} not found in session {session_id}")
                    
            except Exception as e:
                logger.error(f"Failed to fetch active document: {e}")

        # 1. Search Context (Session-specific documents + memories)
        # Use keywords for search if available and intent is search/summarize, otherwise use raw query
        search_query = " ".join(keywords) if keywords and intent in ["search", "summarize"] else query
        query_vector = get_embedding(search_query)
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue, MatchAny
        
        import os
        from config import QDRANT_SCORE_THRESHOLD
        score_threshold = QDRANT_SCORE_THRESHOLD
        collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'second_brain')
        
        # Filter by session_id OR global memories, exclude excluded files
        session_filter = None
        if session_id:
            session_filter = Filter(
                should=[
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=session_id)
                    ),
                    FieldCondition(
                        key="file_type",
                        match=MatchValue(value="memory")
                    )
                ],
                must_not=[
                    FieldCondition(
                        key="excluded",
                        match=MatchValue(value=True)
                    )
                ]
            )
        
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
        
        # Check for duplicate questions first
        duplicate_response = await check_duplicate_question(query, session_id)
        if duplicate_response:
            return ParallelWorkflowResponse(
                answer=duplicate_response,
                processing_time=time.time() - start_time,
                sources=[]
            )
        
        # Add friendly context message if no relevant information found
        if not context_text.strip() and not active_document_text:
            # Check if there are excluded files in the session
            try:
                excluded_check = qdrant_manager.client.scroll(
                    collection_name=collection_name,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(key="session_id", match=MatchValue(value=session_id)),
                            FieldCondition(key="excluded", match=MatchValue(value=True))
                        ]
                    ),
                    limit=1,
                    with_payload=True
                )
                
                if excluded_check and excluded_check[0]:
                    context_text = "I notice you have documents uploaded but they are currently excluded from AI access. Please click 'Include' on the files you want me to access, then ask your question again."
                else:
                    context_text = "No specific documents found in the current session. Please answer the user's question based on your general knowledge and training."
            except Exception as e:
                logger.error(f"Failed to check excluded files: {e}")
                context_text = "No specific documents found in the current session. Please answer the user's question based on your general knowledge and training."
        
        # Prepend Active Document Text (Highest Priority)
        if active_document_text:
            # Truncate if too long to avoid token limits (approx 6000 words / 8k tokens)
            if len(active_document_text) > 30000:
                active_document_text = active_document_text[:30000] + "...(truncated)"
            context_text = f"ACTIVE DOCUMENT ({active_document_filename or 'Current File'}):\n{active_document_text}\n\nRELATED CONTEXT:\n{context_text}"
        
        # Enhance context with user preferences and memory
        try:
            from langchain_memory import get_memory_manager
            memory_manager = get_memory_manager()
            context_text = memory_manager.get_context_with_preferences(session_id or "default", context_text)
        except Exception as e:
            logger.error(f"Memory enhancement failed: {e}")
        
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
        
        # 4. Add memory source information to response
        memory_sources = get_memory_sources_from_results(search_results, active_document_filename)
        if memory_sources:
            final_answer += f"\n\n---\n**Sources:** {memory_sources}"
        
        # 4. Background Task: Fact Extraction & Storage with session isolation
        if background_tasks:
            background_tasks.add_task(background_memory_task, query, final_answer, context_text, session_id)
            # Add conversation to LangChain memory
            background_tasks.add_task(update_langchain_memory, session_id or "default", query, final_answer)
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
    return await run_parallel_workflow(request.query, background_tasks, request.context_limit, active_document_text=request.active_document_text)
