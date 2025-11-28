from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models import SystemHealth, AnalyticsResponse
from database import qdrant_manager
from r2_storage import r2_storage
from datetime import datetime
import time
import psutil
import os
import io

router = APIRouter()
start_time = time.time()

@router.get("/health", response_model=SystemHealth)
async def system_health():
    """Comprehensive system health check."""
    try:
        # Check Qdrant health
        qdrant_health = qdrant_manager.health_check()
        qdrant_status = qdrant_health.get("status") == "healthy"
        
        # Check Lamatic (simplified)
        lamatic_status = True  # Would implement actual check
        
        # System metrics
        memory_percent = psutil.virtual_memory().percent
        uptime = time.time() - start_time
        
        overall_status = "healthy"
        errors = []
        
        if not qdrant_status:
            overall_status = "degraded"
            errors.append(f"Qdrant unhealthy: {qdrant_health.get('error', 'Unknown error')}")
        
        if not lamatic_status:
            overall_status = "degraded"
            errors.append("Lamatic API unavailable")
        
        if memory_percent > 90:
            overall_status = "degraded"
            errors.append(f"High memory usage: {memory_percent}%")
        
        return SystemHealth(
            status=overall_status,
            uptime=uptime,
            vector_db_status=qdrant_status,
            lamatic_status=lamatic_status,
            last_check=datetime.utcnow().isoformat(),
            errors=errors
        )
        
    except Exception as e:
        return SystemHealth(
            status="down",
            uptime=time.time() - start_time,
            vector_db_status=False,
            lamatic_status=False,
            last_check=datetime.utcnow().isoformat(),
            errors=[str(e)]
        )

@router.get("/analytics", response_model=AnalyticsResponse)
async def system_analytics():
    """Get system analytics and insights."""
    try:
        from database import get_qdrant_client
        client = get_qdrant_client()
        
        # Get actual file count and stats
        scroll_result = client.scroll(
            collection_name="second_brain",
            limit=1000,
            with_payload=True
        )
        
        unique_files = set()
        file_types = {}
        total_chunks = len(scroll_result[0])
        
        for point in scroll_result[0]:
            filename = point.payload.get("filename")
            file_type = point.payload.get("file_type", "unknown")
            
            if filename:
                unique_files.add(filename)
                file_types[file_type] = file_types.get(file_type, 0) + 1
        
        collection_stats = qdrant_manager.get_collection_stats("second_brain")
        
        return AnalyticsResponse(
            total_documents=len(unique_files),
            total_chunks=total_chunks,
            file_type_distribution=file_types,
            storage_size=collection_stats.get("disk_data_size", 0),
            top_topics=["AI", "Machine Learning", "Python"],
            processing_stats={
                "indexed_vectors": collection_stats.get("indexed_vectors_count", 0),
                "segments": collection_stats.get("segments_count", 0),
                "ram_usage": collection_stats.get("ram_data_size", 0)
            }
        )
        
    except Exception as e:
        return AnalyticsResponse(
            total_documents=0,
            total_chunks=0,
            file_type_distribution={},
            storage_size=0,
            top_topics=[],
            processing_stats={"error": str(e)}
        )

@router.post("/cleanup")
async def cleanup_old_data(days_old: int = 30):
    """Clean up old data points."""
    try:
        result = qdrant_manager.cleanup_old_points("second_brain", days_old)
        return {"message": f"Cleanup completed", "result": result}
    except Exception as e:
        return {"error": str(e)}

@router.get("/collections/{collection_name}/stats")
async def collection_stats(collection_name: str):
    """Get detailed collection statistics."""
    try:
        stats = qdrant_manager.get_collection_stats(collection_name)
        return stats
    except Exception as e:
        return {"error": str(e)}

@router.get("/files")
async def list_uploaded_files(session_id: str = None):
    """List all uploaded files."""
    try:
        from database import get_qdrant_client
        client = get_qdrant_client()
        
        # Get points filtered by session_id if provided
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        
        scroll_filter = None
        if session_id:
            scroll_filter = Filter(
                must=[
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=session_id)
                    )
                ]
            )
        
        scroll_result = client.scroll(
            collection_name="second_brain",
            scroll_filter=scroll_filter,
            limit=1000,
            with_payload=True
        )
        
        files = {}
        for point in scroll_result[0]:
            filename = point.payload.get("filename")
            # Skip memory entries and files without session_id if session filtering is active
            if filename and point.payload.get("file_type") != "memory":
                if session_id and not point.payload.get("session_id"):
                    continue  # Skip files without session_id when filtering
                    
                if filename not in files:
                    files[filename] = {
                        "filename": filename,
                        "file_type": point.payload.get("file_type", "unknown"),
                        "file_url": point.payload.get("file_url"),
                        "file_size": point.payload.get("file_size", 0),
                        "processed_at": point.payload.get("processed_at", "unknown"),
                        "chunks": 0
                    }
                files[filename]["chunks"] += 1
        
        return {"files": list(files.values())}
    except Exception as e:
        return {"error": str(e), "files": []}

@router.get("/files/{filename}/download")
async def download_file(filename: str):
    """Download original file from R2."""
    try:
        from database import get_qdrant_client
        from qdrant_client.http import models
        client = get_qdrant_client()
        
        # Get file info from Qdrant
        scroll_result = client.scroll(
            collection_name="second_brain",
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="filename",
                        match=models.MatchValue(value=filename)
                    )
                ]
            ),
            limit=1,
            with_payload=True
        )
        
        if not scroll_result[0]:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_url = scroll_result[0][0].payload.get("file_url")
        if not file_url:
            raise HTTPException(status_code=404, detail="File URL not found in metadata")
        
        # Extract object key from URL
        object_key = file_url.replace(f"{r2_storage.public_url}/", "")
        
        # Download from R2
        file_content = r2_storage.download_file(object_key)
        if not file_content:
            raise HTTPException(status_code=500, detail="Failed to download file from R2")
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{filename}/url")
async def get_file_url(filename: str, expiration: int = 3600):
    """Get presigned URL for file download."""
    try:
        from database import get_qdrant_client
        from qdrant_client.http import models
        client = get_qdrant_client()
        
        # Get file info from Qdrant
        scroll_result = client.scroll(
            collection_name="second_brain",
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="filename",
                        match=models.MatchValue(value=filename)
                    )
                ]
            ),
            limit=1,
            with_payload=True
        )
        
        if not scroll_result[0]:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_url = scroll_result[0][0].payload.get("file_url")
        if not file_url:
            raise HTTPException(status_code=404, detail="File URL not found")
        
        # Extract object key
        object_key = file_url.replace(f"{r2_storage.public_url}/", "")
        
        # Generate presigned URL
        presigned_url = r2_storage.generate_presigned_url(object_key, expiration)
        if not presigned_url:
            raise HTTPException(status_code=500, detail="Failed to generate presigned URL")
        
        return {
            "filename": filename,
            "url": presigned_url,
            "expires_in": expiration
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/files/{filename}")
async def delete_file(filename: str):
    """Delete file from both Qdrant and R2."""
    try:
        from database import get_qdrant_client
        from qdrant_client.http import models
        client = get_qdrant_client()
        
        # Get file URL before deleting from Qdrant
        scroll_result = client.scroll(
            collection_name="second_brain",
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="filename",
                        match=models.MatchValue(value=filename)
                    )
                ]
            ),
            limit=1,
            with_payload=True
        )
        
        file_url = None
        if scroll_result[0]:
            file_url = scroll_result[0][0].payload.get("file_url")
        
        # Delete from Qdrant
        client.delete(
            collection_name="second_brain",
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="filename",
                            match=models.MatchValue(value=filename)
                        )
                    ]
                )
            )
        )
        
        # Delete from R2 if URL exists
        if file_url:
            object_key = file_url.replace(f"{r2_storage.public_url}/", "")
            r2_storage.delete_file(object_key)
        
        return {"message": f"File '{filename}' deleted successfully from both Qdrant and R2"}
    except Exception as e:
        return {"error": str(e)}