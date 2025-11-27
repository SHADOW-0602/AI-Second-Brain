from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union, Literal
from datetime import datetime
from enum import Enum

class FileType(str, Enum):
    """Supported file types."""
    PDF = ".pdf"
    DOCX = ".docx"
    TXT = ".txt"
    MD = ".md"
    CSV = ".csv"
    JSON = ".json"
    PYTHON = ".py"
    JAVASCRIPT = ".js"
    HTML = ".html"
    XML = ".xml"

class ProcessingStatus(str, Enum):
    """Processing status types."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    PROCESSING = "processing"

class DocumentMetadata(BaseModel):
    """Comprehensive document metadata."""
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    file_type: str = Field(..., description="File extension type")
    char_count: int = Field(..., ge=0, description="Character count")
    word_count: int = Field(..., ge=0, description="Word count")
    processed_at: str = Field(..., description="Processing timestamp")
    content_hash: str = Field(..., min_length=8, max_length=64)

class IngestResponse(BaseModel):
    """Enhanced ingestion response."""
    filename: str
    document_id: str = Field(..., description="Unique document identifier")
    chunks_count: int = Field(..., ge=0)
    total_chars: int = Field(..., ge=0)
    processing_time: float = Field(..., ge=0, description="Processing time in seconds")
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class SearchRequest(BaseModel):
    """Advanced search request."""
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(5, ge=1, le=100, description="Maximum results to return")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity score")
    file_types: Optional[List[str]] = Field(None, description="Filter by file types")
    include_metadata: bool = Field(True, description="Include chunk metadata")

class SearchResult(BaseModel):
    """Enhanced search result."""
    text: str = Field(..., description="Matched text content")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    chunk_id: str = Field(..., description="Unique chunk identifier")
    filename: str = Field(..., description="Source filename")
    file_type: str = Field(..., description="File type")
    chunk_index: int = Field(..., ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SearchResponse(BaseModel):
    """Comprehensive search response."""
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(default_factory=list)
    total_found: int = Field(..., ge=0, description="Total matches found")
    search_time: float = Field(..., ge=0, description="Search time in seconds")

class ChatRequest(BaseModel):
    """Chat request with context."""
    message: str = Field(..., min_length=1, max_length=2000)
    workflow_id: str = Field("default", description="Lamatic workflow ID")
    context_limit: int = Field(3, ge=1, le=10, description="Number of context chunks")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Response creativity")
    ai_provider: Optional[str] = Field(None, description="AI provider: 'mistral' or 'lamatic' (optional, uses AI_PROVIDER env if not set)")

class ChatResponse(BaseModel):
    """Enhanced chat response."""
    response: str = Field(..., description="AI response")
    context_used: List[SearchResult] = Field(default_factory=list)
    confidence: float = Field(0.8, ge=0.0, le=1.0, description="Response confidence")
    processing_time: float = Field(..., ge=0)
    workflow_id: str = Field(..., description="Used workflow ID")
    ai_provider: str = Field(..., description="AI provider used: 'mistral' or 'lamatic'")
    model_used: Optional[str] = Field(None, description="Specific model/workflow used")

class SystemHealth(BaseModel):
    """System health status."""
    status: str = Field(..., description="System status")
    uptime: float = Field(..., ge=0, description="Uptime in seconds")
    vector_db_status: bool = Field(..., description="Vector database connectivity")
    lamatic_status: bool = Field(..., description="Lamatic API status")
    last_check: str = Field(..., description="Last health check timestamp")
    errors: List[str] = Field(default_factory=list)

class BulkIngestRequest(BaseModel):
    """Bulk file processing request."""
    file_paths: List[str] = Field(..., min_items=1, max_items=100)
    batch_size: int = Field(10, ge=1, le=50)
    parallel_processing: bool = Field(True)
    skip_duplicates: bool = Field(True)

class AnalyticsResponse(BaseModel):
    """System analytics and insights."""
    total_documents: int = Field(..., ge=0)
    total_chunks: int = Field(..., ge=0)
    file_type_distribution: Dict[str, int] = Field(default_factory=dict)
    storage_size: int = Field(..., ge=0, description="Total storage in bytes")
    top_topics: List[str] = Field(default_factory=list)
    processing_stats: Dict[str, Any] = Field(default_factory=dict)