from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import time
from datetime import datetime

from advanced_search import advanced_search
from content_analysis import content_analyzer
from analytics import analytics_tracker
from database import get_qdrant_client

router = APIRouter()

class AdvancedSearchRequest(BaseModel):
    query: str
    search_type: str = "hybrid"  # hybrid, semantic, keyword, boolean
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10
    save_to_history: bool = True
    summarize: bool = False

class ContentAnalysisRequest(BaseModel):
    text: str
    analysis_types: List[str] = ["entities", "keywords", "summary", "questions"]



@router.post("/search/advanced")
async def advanced_search_endpoint(request: AdvancedSearchRequest):
    """Advanced search with multiple algorithms and filters"""
    start_time = time.time()
    
    try:
        client = get_qdrant_client()
        from ingestion import get_embedding
        
        if request.search_type == "hybrid":
            results = advanced_search.hybrid_search(
                request.query, 
                request.limit, 
                request.filters
            )
        elif request.search_type == "boolean":
            results = advanced_search.boolean_search(request.query, request.limit)
        else:
            # Basic semantic search
            vector = get_embedding(request.query)
            from database import qdrant_manager
            search_results = qdrant_manager.advanced_search(
                collection_name="second_brain",
                query_vector=vector,
                limit=request.limit
            )
            results = [{"point": r, "combined_score": r.score, "semantic_score": r.score, "keyword_score": 0} for r in search_results]
        
        response_time = time.time() - start_time
        
        # Track analytics
        analytics_tracker.track_search(
            request.query, 
            len(results), 
            response_time
        )
        
        # Format results
        formatted_results = []
        for result in results:
            point = result["point"]
            formatted_results.append({
                "text": point.payload.get("text", ""),
                "filename": point.payload.get("filename", ""),
                "file_type": point.payload.get("file_type", ""),
                "chunk_index": point.payload.get("chunk_index", 0),
                "semantic_score": result.get("semantic_score", 0),
                "keyword_score": result.get("keyword_score", 0),
                "combined_score": result.get("combined_score", 0),
                "metadata": {k: v for k, v in point.payload.items() 
                           if k not in ["text", "filename", "file_type", "chunk_index"]}
            })

        # AI Summarization
        ai_summary = None
        if request.summarize:
            try:
                # Prepare context from top results (limit to top 5 for summary)
                context_texts = [r["text"] for r in formatted_results[:5]]
                
                if context_texts:
                    from mistral_client import mistral_client
                    
                    summary_prompt = f"Based on the following search results for the query '{request.query}', provide a concise and professional summary. Focus on answering the user's intent directly.\n\nContext:\n" + "\n\n".join(context_texts)
                    
                    # We can use the chat_with_context method or a direct completion
                    # Using chat_with_context for consistency
                    ai_response = await mistral_client.chat_with_context(
                        user_message=request.query,
                        context=context_texts
                    )
                    
                    if "error" not in ai_response:
                        ai_summary = ai_response.get("output", "Could not generate summary.")
                    else:
                        print(f"Mistral summary error: {ai_response.get('error')}")
            except Exception as e:
                print(f"Summarization failed: {e}")

        # Save to history if requested
        search_id = None
        if request.save_to_history:
            # Save summary along with results if available
            # Note: save_search_to_history might need update to store summary, 
            # but for now we just save the search results structure
            search_id = analytics_tracker.save_search_to_history(request.query, formatted_results)
        
        return {
            "query": request.query,
            "search_type": request.search_type,
            "results": formatted_results,
            "ai_summary": ai_summary,
            "total_found": len(formatted_results),
            "response_time": response_time,
            "search_id": search_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/history")
async def get_search_history(limit: int = 50):
    """Get search history"""
    try:
        history = analytics_tracker.get_search_history(limit)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/history/{search_id}")
async def get_saved_search(search_id: str):
    """Retrieve saved search results"""
    try:
        search_data = analytics_tracker.load_search_from_history(search_id)
        if not search_data:
            raise HTTPException(status_code=404, detail="Search not found")
        return search_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/content/analyze")
async def analyze_content(request: ContentAnalysisRequest):
    """Analyze content for entities, keywords, summary, etc."""
    try:
        results = {}
        
        if "entities" in request.analysis_types:
            results["entities"] = content_analyzer.extract_entities(request.text)
        
        if "keywords" in request.analysis_types:
            results["keywords"] = content_analyzer.extract_keywords(request.text)
        
        if "summary" in request.analysis_types:
            results["summary"] = content_analyzer.generate_summary(request.text)
        
        if "questions" in request.analysis_types:
            results["questions"] = content_analyzer.generate_questions(request.text)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/analytics/search")
async def get_search_analytics(days: int = 30):
    """Get search analytics"""
    try:
        analytics = analytics_tracker.get_search_analytics(days)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/files")
async def get_file_analytics(days: int = 30):
    """Get file usage analytics"""
    try:
        analytics = analytics_tracker.get_file_analytics(days)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/content-gaps")
async def analyze_content_gaps():
    """Analyze knowledge gaps in the content"""
    try:
        client = get_qdrant_client()
        
        # Get all document texts
        scroll_result = client.scroll(
            collection_name="second_brain",
            limit=1000,
            with_payload=True
        )
        
        all_texts = [point.payload.get("text", "") for point in scroll_result[0]]
        gaps_analysis = content_analyzer.analyze_content_gaps(all_texts)
        
        return gaps_analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/content/auto-analyze/{filename}")
async def auto_analyze_document(filename: str):
    """Auto-analyze uploaded document"""
    try:
        client = get_qdrant_client()
        
        # Get document chunks
        from qdrant_client.http import models
        search_results = client.scroll(
            collection_name="second_brain",
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="filename",
                        match=models.MatchValue(value=filename)
                    )
                ]
            ),
            limit=100,
            with_payload=True
        )
        
        # Combine all chunks
        full_text = " ".join([
            point.payload.get("text", "") 
            for point in search_results[0]
        ])
        
        # Perform analysis
        if content_analyzer:
            analysis = {
                "entities": content_analyzer.extract_entities(full_text),
                "keywords": content_analyzer.extract_keywords(full_text, 15),
                "summary": content_analyzer.generate_summary(full_text, 5),
                "questions": content_analyzer.generate_questions(full_text, 8)
            }
        else:
            # Fallback analysis
            import re
            words = re.findall(r'\b\w+\b', full_text.lower())
            analysis = {
                "entities": {"persons": [], "organizations": [], "dates": []},
                "keywords": [{"term": word, "frequency": 1} for word in list(set(words))[:15]],
                "summary": full_text[:500] + "..." if len(full_text) > 500 else full_text,
                "questions": ["What is this document about?", "What are the main topics?"]
            }
        
        # Track file access
        analytics_tracker.track_file_access(filename, "analyze")
        
        return {
            "filename": filename,
            "analysis": analysis,
            "analyzed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))