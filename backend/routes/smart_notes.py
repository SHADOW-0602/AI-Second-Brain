from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import time
import uuid
import logging
import hashlib
import os

# Import Clients
from groq_client import groq_client
from database import qdrant_manager
from ingestion import get_embedding
from r2_storage import r2_storage

logger = logging.getLogger(__name__)
print("DEBUG: LOADING SMART_NOTES ROUTER MODULE")

router = APIRouter()

# Ensure indexes exist for filtering
try:
    COLLECTION_NAME = os.getenv('QDRANT_COLLECTION_NAME', 'second_brain')
    from qdrant_client.http.models import PayloadSchemaType
    # Create index for is_deleted (bool)
    qdrant_manager.create_payload_index(COLLECTION_NAME, "is_deleted", PayloadSchemaType.BOOL)
    # Ensure other useful indexes exist
    qdrant_manager.create_payload_index(COLLECTION_NAME, "file_type", PayloadSchemaType.KEYWORD)
    qdrant_manager.create_payload_index(COLLECTION_NAME, "session_id", PayloadSchemaType.KEYWORD)
except Exception as e:
    logger.warning(f"Could not ensure indexes for smart notes: {e}")

class GenerateNoteRequest(BaseModel):
    text: Optional[str] = ""
    filename: str
    source_filename: Optional[str] = None
    session_id: Optional[str] = None

class NoteResponse(BaseModel):
    note_content: str
    r2_url: Optional[str]
    message: str

async def generate_note_logic(text: str) -> str:
    """
    Generate structured notes from text using chunked approach for large documents.
    """
    try:
        if not groq_client.client:
            raise HTTPException(status_code=500, detail="Groq client not initialized. Please check GROQ_API_KEY.")
            
        CHUNK_SIZE = 6000
        model_name = "llama-3.1-8b-instant"
        
        if len(text) <= CHUNK_SIZE:
            return await process_single_chunk(text, model_name)
        
        # Process large documents in chunks
        chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
        logger.info(f"Processing large document in {len(chunks)} chunks")
        
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            summary = await process_chunk_summary(chunk, i+1, len(chunks), model_name)
            chunk_summaries.append(summary)
        
        combined_text = "\n\n".join(chunk_summaries)
        return await create_final_note(combined_text, model_name)
        
    except Exception as e:
        logger.error(f"Note generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI Generation failed: {str(e)}")

async def process_single_chunk(text: str, model_name: str) -> str:
    prompt = f"""Create structured notes in Markdown:

# Executive Summary
- [Key points]

## Main Topics  
- [Important topics]

## Key Insights
- [Notable insights]

DOCUMENT:
{text}"""
    
    completion = groq_client.client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model_name,
        temperature=0.3,
        max_tokens=1200
    )
    return completion.choices[0].message.content

async def process_chunk_summary(chunk: str, chunk_num: int, total_chunks: int, model_name: str) -> str:
    prompt = f"""Extract key points from Part {chunk_num}/{total_chunks}:

## Key Points from Part {chunk_num}
- [Extract 3-5 most important points]

SECTION:
{chunk}"""
    
    completion = groq_client.client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model_name,
        temperature=0.2,
        max_tokens=800
    )
    return completion.choices[0].message.content

async def create_final_note(combined_summaries: str, model_name: str) -> str:
    prompt = f"""Create comprehensive structured note:

# Executive Summary
- [Overall key points]

## Main Topics
- [Primary themes]

## Key Insights
- [Important findings]

SECTION SUMMARIES:
{combined_summaries}"""
    
    completion = groq_client.client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model_name,
        temperature=0.3,
        max_tokens=1500
    )
    return completion.choices[0].message.content

@router.post("/notes/generate", response_model=NoteResponse)
async def generate_note(request: GenerateNoteRequest):
    """
    Generate notes, store in R2, and index in Qdrant.
    """
    try:
        # 1. Fetch Full Document Content from Qdrant
        full_text = request.text
        
        # Determine search mode
        search_filename = request.source_filename or request.filename
        
        # If source_filename is explicitly None/Empty but session_id is present, 
        # it implies "Session Summary" mode (all files).
        is_session_summary = not request.source_filename and request.session_id
        
        if not full_text and (search_filename or is_session_summary) and request.session_id:
            try:
                from qdrant_client.http.models import Filter, FieldCondition, MatchValue
                
                must_conditions = [
                    FieldCondition(key="session_id", match=MatchValue(value=request.session_id))
                ]
                
                # Only filter by filename if we are NOT doing a session summary
                if not is_session_summary:
                    must_conditions.append(
                        FieldCondition(key="filename", match=MatchValue(value=search_filename))
                    )
                
                filter_condition = Filter(must=must_conditions)
                
                # Retrieve chunks (limit to reasonable amount, e.g., 150 chunks ~ 30-40k tokens)
                results = qdrant_manager.client.scroll(
                    collection_name=os.getenv('QDRANT_COLLECTION_NAME', 'second_brain'),
                    scroll_filter=filter_condition,
                    limit=150,
                    with_payload=True,
                    with_vectors=False
                )
                
                if results and results[0]:
                    # Sort by chunk_index to reconstruct document in order
                    # Note: For session summary, this might mix files, but that's acceptable for a summary.
                    # Ideally we'd sort by filename then chunk_index, but simple sort is okay for now.
                    chunks = sorted(results[0], key=lambda x: (x.payload.get('filename', ''), x.payload.get('chunk_index', 0)))
                    
                    full_text = ""
                    current_file = ""
                    for chunk in chunks:
                        fname = chunk.payload.get('filename', 'Unknown')
                        if fname != current_file:
                            full_text += f"\n\n--- FILE: {fname} ---\n\n"
                            current_file = fname
                        full_text += chunk.payload.get('text', '') + "\n"
                        
                    logger.info(f"Retrieved text for {'session ' + request.session_id if is_session_summary else search_filename}: {len(full_text)} chars")
                else:
                    logger.warning(f"No chunks found for session {request.session_id}")
            except Exception as e:
                logger.error(f"Failed to retrieve document content: {e}")
        
        # 2. Generate Note Content
        note_content = await generate_note_logic(full_text)
        
        # 2. Upload to Cloudflare R2 (optional)
        # Create a unique filename for the note
        note_filename = f"note_{request.filename}_{int(time.time())}.md"
        content_bytes = note_content.encode('utf-8')
        content_hash = hashlib.md5(content_bytes).hexdigest()
        
        r2_url = None
        try:
            r2_url = r2_storage.upload_file(content_bytes, note_filename, content_hash)
        except Exception as e:
            logger.warning(f"Failed to upload note to R2: {e}, proceeding with Qdrant only.")
        
        # 3. Index in Qdrant
        vector = get_embedding(note_content)
        doc_id = str(uuid.uuid4())
        
        payload = {
            "text": note_content,
            "source_filename": request.filename,
            "filename": note_filename,
            "type": "generated_note",
            "r2_url": r2_url,
            "timestamp": time.time(),
            "session_id": request.session_id  # Keep session_id for UI filtering
        }
        
        from qdrant_client.http.models import PointStruct
        point = PointStruct(id=doc_id, vector=vector, payload=payload)
        
        collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'second_brain')
        
        try:
            qdrant_manager.client.upsert(
                collection_name=collection_name,
                points=[point],
                wait=True
            )
            logger.info(f"Successfully stored note with ID: {doc_id}")
        except Exception as e:
            logger.error(f"Failed to store note in Qdrant: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to store note: {str(e)}")
        
        return NoteResponse(
            note_content=note_content,
            r2_url=r2_url,
            message=f"Note generated and stored successfully. ID: {doc_id}"
        )
        
    except Exception as e:
        logger.error(f"Generate note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notes/by-file/{filename}")
async def get_notes(filename: str):
    """
    Retrieve generated notes for a specific file.
    """
    try:
        collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'second_brain')
        
        # Search for notes linked to this filename
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        
        filter_condition = Filter(
            must=[
                FieldCondition(key="source_filename", match=MatchValue(value=filename)),
                FieldCondition(key="type", match=MatchValue(value="generated_note"))
            ],
            must_not=[
                FieldCondition(key="is_deleted", match=MatchValue(value=True))
            ]
        )
        
        results = qdrant_manager.client.scroll(
            collection_name=collection_name,
            scroll_filter=filter_condition,
            limit=10,
            with_payload=True,
            with_vectors=False
        )
        
        notes = []
        if results and results[0]:
            for point in results[0]:
                notes.append({
                    "content": point.payload.get("text"),
                    "timestamp": point.payload.get("timestamp"),
                    "r2_url": point.payload.get("r2_url")
                })
        
        # Sort by timestamp desc
        notes.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {"notes": notes}
        
    except Exception as e:
        logger.error(f"Get notes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notes/list")
async def list_all_notes(session_id: str = None):
    """List generated notes for current session only (UI filtering)."""
    try:
        collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'second_brain')
        
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        
        # Filter by session_id for UI display
        filter_conditions = [
            FieldCondition(key="type", match=MatchValue(value="generated_note"))
        ]
        
        if session_id:
            filter_conditions.append(
                FieldCondition(key="session_id", match=MatchValue(value=session_id))
            )
        
        filter_condition = Filter(
            must=filter_conditions,
            must_not=[
                FieldCondition(key="is_deleted", match=MatchValue(value=True))
            ]
        )
        
        results = qdrant_manager.client.scroll(
            collection_name=collection_name,
            scroll_filter=filter_condition,
            limit=100,
            with_payload=True,
            with_vectors=False
        )
        
        notes = []
        if results and results[0]:
            for point in results[0]:
                notes.append({
                    "id": point.id,
                    "title": point.payload.get("filename", "Untitled Note"),
                    "content": point.payload.get("text", "")[:200] + "...",
                    "created_at": point.payload.get("timestamp"),
                    "source_file": point.payload.get("source_filename")
                })
        
        notes.sort(key=lambda x: x["created_at"] or 0, reverse=True)
        return {"notes": notes}
        
    except Exception as e:
        logger.error(f"List notes error: {e}")
        return {"notes": []}

@router.get("/notes/{note_id}")
async def get_note_by_id(note_id: str):
    """Get specific note by ID."""
    try:
        collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'second_brain')
        
        result = qdrant_manager.client.retrieve(
            collection_name=collection_name,
            ids=[note_id],
            with_payload=True,
            with_vectors=False
        )
        
        if result and len(result) > 0:
            point = result[0]
            # Check if deleted
            if point.payload.get("is_deleted"):
                 raise HTTPException(status_code=404, detail="Note not found (deleted)")
                 
            return {
                "id": point.id,
                "title": point.payload.get("filename", "Untitled Note"),
                "content": point.payload.get("text", ""),
                "created_at": point.payload.get("timestamp"),
                "source_file": point.payload.get("source_filename")
            }
        else:
            raise HTTPException(status_code=404, detail="Note not found")
            
    except Exception as e:
        logger.error(f"Get note by ID error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    """Delete a smart note (Soft delete from Memory, Hard delete from R2)."""
    try:
        collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'second_brain')
        
        # Check if note exists first
        result = qdrant_manager.client.retrieve(
            collection_name=collection_name,
            ids=[note_id],
            with_payload=True,
            with_vectors=False
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Note not found")
            
        # Delete from R2 if URL exists
        try:
            point = result[0]
            r2_url = point.payload.get("r2_url")
            if r2_url:
                # Extract object key from URL
                from config import R2_PUBLIC_URL
                if R2_PUBLIC_URL in r2_url:
                    object_key = r2_url.replace(f"{R2_PUBLIC_URL}/", "")
                    r2_storage.delete_file(object_key)
                    logger.info(f"Deleted R2 file: {object_key}")
        except Exception as e:
            logger.error(f"Failed to delete R2 file for note {note_id}: {e}")
            
        # Soft Delete from Qdrant (Update payload)
        try:
            qdrant_manager.client.set_payload(
                collection_name=collection_name,
                payload={"is_deleted": True},
                points=[note_id],
                wait=True
            )
            logger.info(f"Soft deleted note {note_id} (marked is_deleted=True)")
        except Exception as e:
             logger.error(f"Failed to soft delete note in Qdrant: {e}")
             raise
        
        return {"message": "Note deleted successfully", "id": note_id}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
