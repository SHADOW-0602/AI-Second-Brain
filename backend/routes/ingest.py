from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from database import qdrant_manager, get_qdrant_client
from ingestion import processor
from models import IngestResponse, DocumentMetadata
from pydantic import BaseModel
from r2_storage import r2_storage
from qdrant_client.http import models
import uuid

from config import QDRANT_COLLECTION_NAME, VECTOR_SIZE, BATCH_SIZE

router = APIRouter()
client = get_qdrant_client()
COLLECTION_NAME = QDRANT_COLLECTION_NAME

# Ensure collection exists with professional configuration
try:
    qdrant_manager.ensure_collection(COLLECTION_NAME, vector_size=VECTOR_SIZE)
    # Create required indexes
    from qdrant_client.http.models import PayloadSchemaType
    qdrant_manager.create_payload_index(COLLECTION_NAME, "excluded", PayloadSchemaType.BOOL)
    qdrant_manager.create_payload_index(COLLECTION_NAME, "session_id", PayloadSchemaType.KEYWORD)
    qdrant_manager.create_payload_index(COLLECTION_NAME, "file_type", PayloadSchemaType.KEYWORD)
    qdrant_manager.create_payload_index(COLLECTION_NAME, "chunk_index", PayloadSchemaType.INTEGER)
except Exception as e:
    print(f"Warning: Could not ensure collection {COLLECTION_NAME}: {e}")

@router.post("/ingest", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...), session_id: str = Form(None)):
    import time
    start_time = time.time()
    
    try:
        content = await file.read()
        text, metadata = processor.parse_file(content, file.filename)
        
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        # Upload raw file to R2 (optional)
        file_url = None
        try:
            file_url = r2_storage.upload_file(content, file.filename, metadata['content_hash'])
        except Exception as e:
            print(f"Warning: R2 upload failed: {e}")
            file_url = None
        
        chunks = processor.chunk_text(text)
        points = []
        
        for chunk_data in chunks:
            vector = processor.get_embedding(chunk_data['text'])
            points.append(models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "filename": file.filename,
                    "text": chunk_data['text'],
                    "chunk_index": chunk_data['chunk_index'],
                    "chunk_hash": chunk_data['hash'],
                    "file_type": metadata['file_type'],
                    "file_size": metadata['file_size'],
                    "file_url": file_url,  # R2 URL
                    "processed_at": metadata['processed_at'],
                    "session_id": session_id,  # Session isolation
                    "type": "file"
                }
            ))
            
        if points:
            batch_result = qdrant_manager.batch_upsert(
                collection_name=COLLECTION_NAME,
                points=points,
                batch_size=BATCH_SIZE
            )
            
            if "error" in batch_result:
                raise HTTPException(status_code=500, detail=f"Batch upsert failed: {batch_result['error']}")
            
            # Add batch statistics to metadata
            metadata["batch_stats"] = batch_result
            
        import time
        processing_time = time.time() - start_time if 'start_time' in locals() else 0.0
        
        return IngestResponse(
            filename=file.filename,
            document_id=metadata['content_hash'],
            chunks_count=len(points),
            total_chars=metadata['char_count'],
            processing_time=processing_time,
            status="success",
            metadata={**metadata, "file_url": file_url, "preview_text": text[:50000]}, # Return text for frontend (truncated safe limit)
            errors=[],
            warnings=[] if file_url else ["File uploaded to Qdrant but R2 upload failed"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
