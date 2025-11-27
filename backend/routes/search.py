from fastapi import APIRouter, HTTPException
from database import qdrant_manager, get_qdrant_client
from ingestion import get_embedding
from models import SearchRequest, SearchResponse, SearchResult

# Analytics tracker
from analytics import analytics_tracker

router = APIRouter()
client = get_qdrant_client()
COLLECTION_NAME = "second_brain"

@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    import time
    start_time = time.time()
    try:
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
        results = qdrant_manager.advanced_search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=request.limit,
            score_threshold=request.min_score,
            filter_conditions=filter_conditions,
        )
        search_time = time.time() - start_time if 'start_time' in locals() else 0.0
        search_results = []
        for i, res in enumerate(results):
            search_results.append(SearchResult(
                text=res.payload.get("text", ""),
                score=res.score,
                chunk_id=str(res.id),
                filename=res.payload.get("filename", "unknown"),
                file_type=res.payload.get("file_type", "unknown"),
                chunk_index=res.payload.get("chunk_index", i),
                metadata={k: v for k, v in res.payload.items() if k not in ["text", "filename", "file_type", "chunk_index"]}
            ))
        # Track analytics
        analytics_tracker.track_search(
            query=request.query,
            results_count=len(search_results),
            response_time=search_time,
            user_id="anonymous",
        )
        return SearchResponse(
            query=request.query,
            results=search_results,
            total_found=len(search_results),
            search_time=search_time,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
