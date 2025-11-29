import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
from config import QDRANT_URL, QDRANT_API_KEY, DB_TIMEOUT, CLEANUP_BATCH_SIZE

logger = logging.getLogger(__name__)

class QdrantManager:
    """Professional Qdrant database manager with connection pooling and error handling."""
    
    def __init__(self, url: str, api_key: str, timeout: int = 30):
        from config import DB_CONNECTION_POOL_SIZE, DB_RETRY_ATTEMPTS
        self.url = url
        self.api_key = api_key
        self.timeout = timeout
        self._client = None
        self._connection_pool_size = DB_CONNECTION_POOL_SIZE
        self._retry_attempts = DB_RETRY_ATTEMPTS
        
    @property
    def client(self) -> QdrantClient:
        """Lazy initialization of Qdrant client."""
        if self._client is None:
            self._client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
                timeout=self.timeout,
                prefer_grpc=False,  # Better compatibility
                # grpc_port=6334
            )
        return self._client
    
    def health_check(self) -> Dict[str, Any]:
        """Check Qdrant cluster health."""
        try:
            collections = self.client.get_collections()
            
            return {
                "status": "healthy",
                "collections_count": len(collections.collections),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def ensure_collection(self, collection_name: str, vector_size: int = None, 
                         distance: models.Distance = models.Distance.COSINE) -> bool:
        from config import VECTOR_SIZE
        if vector_size is None:
            vector_size = VECTOR_SIZE
        """Ensure collection exists with proper configuration."""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            existing_names = [col.name for col in collections.collections]
            
            if collection_name in existing_names:
                # Verify collection configuration
                collection_info = self.client.get_collection(collection_name)
                if collection_info.config.params.vectors.size != vector_size:
                    logger.warning(f"Collection {collection_name} has wrong vector size")
                    return False
                return True
            
            # Create collection with optimized settings
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=distance
                ),
                optimizers_config={
                    "deleted_threshold": 0.2,
                    "vacuum_min_vector_number": 1000,
                    "default_segment_number": 2,
                    "max_segment_size": 20000,
                    "memmap_threshold": 20000,
                    "indexing_threshold": 20000,
                    "flush_interval_sec": 5,
                    "max_optimization_threads": 2
                },
                hnsw_config={
                    "m": 16,
                    "ef_construct": 100,
                    "full_scan_threshold": 10000,
                    "max_indexing_threads": 2
                },
                quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8,
                        quantile=0.99,
                        always_ram=True
                    )
                )
            )
            
            logger.info(f"Created collection {collection_name} with vector size {vector_size}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure collection {collection_name}: {e}")
            return False
    
    def batch_upsert(self, collection_name: str, points: List[models.PointStruct], 
                    batch_size: int = None) -> Dict[str, Any]:
        from config import BATCH_SIZE
        if batch_size is None:
            batch_size = BATCH_SIZE
        """Batch upsert with retry logic and performance optimization."""
        total_points = len(points)
        successful_batches = 0
        failed_batches = 0
        
        try:
            # Process in batches
            for i in range(0, total_points, batch_size):
                batch = points[i:i + batch_size]
                
                for attempt in range(self._retry_attempts):
                    try:
                        operation_info = self.client.upsert(
                            collection_name=collection_name,
                            points=batch,
                            wait=True  # Ensure consistency
                        )
                        
                        if operation_info.status == models.UpdateStatus.COMPLETED:
                            successful_batches += 1
                            break
                        else:
                            logger.warning(f"Batch {i//batch_size + 1} status: {operation_info.status}")
                            
                    except (ResponseHandlingException, UnexpectedResponse) as e:
                        if attempt == self._retry_attempts - 1:
                            logger.error(f"Failed batch {i//batch_size + 1} after {self._retry_attempts} attempts: {e}")
                            failed_batches += 1
                        else:
                            logger.warning(f"Retry {attempt + 1} for batch {i//batch_size + 1}: {e}")
                            asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
            
            return {
                "total_points": total_points,
                "successful_batches": successful_batches,
                "failed_batches": failed_batches,
                "success_rate": successful_batches / (successful_batches + failed_batches) if (successful_batches + failed_batches) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Batch upsert failed: {e}")
            return {"error": str(e), "total_points": total_points}
    
    def advanced_search(self, collection_name: str, query_vector: List[float], 
                       limit: int = 10, score_threshold: float = 0.0,
                       filter_conditions: Optional[models.Filter] = None,
                       with_payload: bool = True, with_vectors: bool = False) -> List[models.ScoredPoint]:
        """Advanced search with filtering and optimization."""
        # Session filtering is now supported
        # if filter_conditions and hasattr(filter_conditions, 'must'):
        #     has_session_filter = any(
        #         hasattr(condition, 'key') and condition.key == "session_id" 
        #         for condition in filter_conditions.must
        #     )
        #     
        #     if has_session_filter:
        #         logger.warning("Session filtering not supported, searching all documents")
        #         # Remove session_id filter
        #         non_session_conditions = [
        #             condition for condition in filter_conditions.must 
        #             if not (hasattr(condition, 'key') and condition.key == "session_id")
        #         ]
        #         filter_conditions = models.Filter(must=non_session_conditions) if non_session_conditions else None
        
        try:
            # Use query_points method for compatibility
            results = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                query_filter=filter_conditions,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=with_payload,
                with_vectors=with_vectors
            )
            
            # Handle all possible return types
            if results is None:
                return []
            
            # If it has points attribute, extract it
            if hasattr(results, 'points'):
                points = results.points
                if points is None:
                    return []
                # Ensure it's iterable
                try:
                    return list(points)
                except (TypeError, AttributeError):
                    return []
            
            # If results is directly iterable
            try:
                return list(results)
            except (TypeError, AttributeError):
                return []
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get comprehensive collection statistics."""
        try:
            collection_info = self.client.get_collection(collection_name)
            
            return {
                "points_count": collection_info.points_count,
                "segments_count": collection_info.segments_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "status": collection_info.status,
                "optimizer_status": collection_info.optimizer_status,
                "disk_data_size": getattr(collection_info, 'disk_data_size', 0),
                "ram_data_size": getattr(collection_info, 'ram_data_size', 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}
    
    def create_payload_index(self, collection_name: str, field_name: str, 
                           field_type: models.PayloadSchemaType = models.PayloadSchemaType.KEYWORD) -> bool:
        """Create payload index for faster filtering."""
        try:
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=field_type
            )
            logger.info(f"Created payload index for {field_name} in {collection_name}")
            return True
            
        except Exception as e:
            # Index might already exist, which is fine
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                logger.debug(f"Payload index for {field_name} already exists")
                return True
            logger.error(f"Failed to create payload index: {e}")
            return False
    
    def cleanup_old_points(self, collection_name: str, days_old: int = None) -> Dict[str, Any]:
        from config import CLEANUP_DAYS_OLD
        if days_old is None:
            days_old = CLEANUP_DAYS_OLD
        """Clean up old points based on timestamp."""
        try:
            cutoff_date = datetime.utcnow().timestamp() - (days_old * 24 * 3600)
            
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="processed_at",
                        range=models.Range(lt=cutoff_date)
                    )
                ]
            )
            
            # Get points to delete
            old_points = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=filter_condition,
                limit=CLEANUP_BATCH_SIZE,
                with_payload=False
            )[0]
            
            if old_points:
                point_ids = [point.id for point in old_points]
                
                operation_info = self.client.delete(
                    collection_name=collection_name,
                    points_selector=models.PointIdsList(points=point_ids)
                )
                
                return {
                    "deleted_count": len(point_ids),
                    "status": operation_info.status
                }
            
            return {"deleted_count": 0, "status": "no_old_points"}
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {"error": str(e)}

# Global instance
qdrant_manager = QdrantManager(QDRANT_URL, QDRANT_API_KEY, DB_TIMEOUT)

# Backward compatibility
def get_qdrant_client():
    return qdrant_manager.client