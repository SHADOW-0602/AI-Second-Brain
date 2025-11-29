from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from database import qdrant_manager
from r2_storage import r2_storage
from datetime import datetime, timedelta
import os
import io

router = APIRouter()







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
        
        # Show files for session or all files if no session specified
        if not session_id:
            scroll_result = client.scroll(
                collection_name="second_brain",
                limit=1000,
                with_payload=True
            )
        else:
        
            # Get points filtered by session_id
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue
            
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
            file_type = point.payload.get("file_type")
            if filename and file_type != "memory" and file_type != "generated_note":
                if filename not in files:
                    files[filename] = {
                        "filename": filename,
                        "file_type": point.payload.get("file_type", "unknown"),
                        "file_url": point.payload.get("file_url"),
                        "file_size": point.payload.get("file_size", 0),
                        "processed_at": point.payload.get("processed_at", "unknown"),
                        "excluded": point.payload.get("excluded", False),
                        "chunks": 0
                    }
                files[filename]["chunks"] += 1
        
        # Get exclusion status from first chunk of each file
        for filename in files:
            first_chunk = client.scroll(
                collection_name="second_brain",
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="session_id", match=MatchValue(value=session_id)),
                        FieldCondition(key="filename", match=MatchValue(value=filename))
                    ]
                ),
                limit=1,
                with_payload=True
            )
            if first_chunk[0]:
                files[filename]["excluded"] = first_chunk[0][0].payload.get("excluded", False)
            else:
                files[filename]["excluded"] = False
        
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
            print(f"DEBUG: File not found in Qdrant: {filename}")
            # Try searching with 'note_' prefix or partial match if it's a note
            if "note_" in filename:
                 print(f"DEBUG: Attempting loose search for note: {filename}")
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        file_url = scroll_result[0][0].payload.get("file_url")
        if not file_url:
            # Fallback for smart notes which use r2_url
            file_url = scroll_result[0][0].payload.get("r2_url")
            
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

@router.get("/debug/sessions")
async def debug_sessions():
    """Debug endpoint to see all session IDs and files."""
    try:
        from database import get_qdrant_client
        client = get_qdrant_client()
        
        # Get all points
        scroll_result = client.scroll(
            collection_name="second_brain",
            limit=1000,
            with_payload=True
        )
        
        sessions = {}
        for point in scroll_result[0]:
            session_id = point.payload.get("session_id")
            filename = point.payload.get("filename")
            file_type = point.payload.get("file_type")
            
            if session_id and filename and file_type != "memory":
                if session_id not in sessions:
                    sessions[session_id] = []
                if filename not in [f["filename"] for f in sessions[session_id]]:
                    sessions[session_id].append({
                        "filename": filename,
                        "file_type": file_type
                    })
        
        return {"sessions": sessions}
    except Exception as e:
        return {"error": str(e)}

@router.patch("/files/{filename}/exclude")
async def toggle_file_exclusion(filename: str, exclude: bool = True):
    """Toggle file exclusion from AI without deleting it."""
    try:
        from database import get_qdrant_client
        from qdrant_client.http import models
        client = get_qdrant_client()
        
        # Update all points for this filename
        client.set_payload(
            collection_name="second_brain",
            payload={"excluded": exclude},
            points=models.FilterSelector(
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
        
        status = "excluded from" if exclude else "included in"
        return {"message": f"File '{filename}' {status} AI access"}
    except Exception as e:
        return {"error": str(e)}