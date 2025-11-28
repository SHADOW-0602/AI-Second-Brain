import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
import os
import uuid

from qdrant_client.http import models
from database import qdrant_manager

class AnalyticsTracker:
    """Analytics tracker using Qdrant for storage instead of SQLite."""
    
    def __init__(self):
        from config import ANALYTICS_SEARCH_COLLECTION, ANALYTICS_FILE_ACCESS_COLLECTION, ANALYTICS_METRICS_COLLECTION
        self.search_collection = ANALYTICS_SEARCH_COLLECTION
        self.file_access_collection = ANALYTICS_FILE_ACCESS_COLLECTION
        self.metrics_collection = ANALYTICS_METRICS_COLLECTION
        self.init_collections()
    
    def init_collections(self):
        """Initialize Qdrant collections for analytics data."""
        # Create collections without vectors (payload-only storage)
        # We'll use a minimal vector config but store empty vectors
        collections_config = [
            (self.search_collection, "Search history analytics"),
            (self.file_access_collection, "File access tracking"),
            (self.metrics_collection, "Usage metrics")
        ]
        
        for collection_name, description in collections_config:
            try:
                # Check if collection exists
                collections = qdrant_manager.client.get_collections()
                existing_names = [col.name for col in collections.collections]
                
                if collection_name not in existing_names:
                    # Create collection with minimal vector size (we won't use vectors)
                    # Using size=1 as the minimum to satisfy Qdrant's requirements
                    qdrant_manager.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(
                            size=1,
                            distance=models.Distance.COSINE
                        )
                    )
                    
                    # Create payload indexes for efficient filtering
                    if collection_name == self.search_collection:
                        qdrant_manager.create_payload_index(collection_name, "timestamp", models.PayloadSchemaType.FLOAT)
                        qdrant_manager.create_payload_index(collection_name, "user_id", models.PayloadSchemaType.KEYWORD)
                    elif collection_name == self.file_access_collection:
                        qdrant_manager.create_payload_index(collection_name, "timestamp", models.PayloadSchemaType.FLOAT)
                        qdrant_manager.create_payload_index(collection_name, "filename", models.PayloadSchemaType.KEYWORD)
                        qdrant_manager.create_payload_index(collection_name, "access_type", models.PayloadSchemaType.KEYWORD)
                    elif collection_name == self.metrics_collection:
                        qdrant_manager.create_payload_index(collection_name, "timestamp", models.PayloadSchemaType.FLOAT)
                        qdrant_manager.create_payload_index(collection_name, "metric_name", models.PayloadSchemaType.KEYWORD)
                        
            except Exception as e:
                print(f"Error initializing collection {collection_name}: {e}")
    
    def track_search(self, query: str, results_count: int, response_time: float, user_id: str = "anonymous"):
        """Track search queries and performance."""
        try:
            point = models.PointStruct(
                id=str(uuid.uuid4()),
                vector=[0.0],  # Minimal placeholder vector
                payload={
                    "query": query,
                    "results_count": results_count,
                    "response_time": response_time,
                    "user_id": user_id,
                    "timestamp": datetime.now().timestamp()
                }
            )
            
            qdrant_manager.client.upsert(
                collection_name=self.search_collection,
                points=[point]
            )
        except Exception as e:
            print(f"Error tracking search: {e}")
    
    def track_file_access(self, filename: str, access_type: str, user_id: str = "anonymous"):
        """Track file access (upload, search, view, delete)."""
        try:
            point = models.PointStruct(
                id=str(uuid.uuid4()),
                vector=[0.0],  # Minimal placeholder vector
                payload={
                    "filename": filename,
                    "access_type": access_type,
                    "user_id": user_id,
                    "timestamp": datetime.now().timestamp()
                }
            )
            
            qdrant_manager.client.upsert(
                collection_name=self.file_access_collection,
                points=[point]
            )
        except Exception as e:
            print(f"Error tracking file access: {e}")
    
    def get_search_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get search analytics for the last N days."""
        try:
            cutoff_timestamp = (datetime.now() - timedelta(days=days)).timestamp()
            
            # Scroll through all search history points within the time range
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="timestamp",
                        range=models.Range(gte=cutoff_timestamp)
                    )
                ]
            )
            
            points, _ = qdrant_manager.client.scroll(
                collection_name=self.search_collection,
                scroll_filter=filter_condition,
                limit=10000,
                with_payload=True,
                with_vectors=False
            )
            
            if not points:
                return {
                    "popular_queries": [],
                    "avg_response_time": 0,
                    "daily_searches": [],
                    "total_searches": 0
                }
            
            # Process data
            queries = [p.payload["query"] for p in points]
            response_times = [p.payload["response_time"] for p in points]
            
            # Most searched queries
            query_counts = Counter(queries)
            popular_queries = [{"query": q, "count": c} for q, c in query_counts.most_common(10)]
            
            # Average response time
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Daily searches
            daily_data = defaultdict(int)
            for p in points:
                date = datetime.fromtimestamp(p.payload["timestamp"]).strftime("%Y-%m-%d")
                daily_data[date] += 1
            
            daily_searches = [{"date": d, "count": c} for d, c in sorted(daily_data.items())]
            
            return {
                "popular_queries": popular_queries,
                "avg_response_time": round(avg_response_time, 3),
                "daily_searches": daily_searches,
                "total_searches": len(points)
            }
            
        except Exception as e:
            print(f"Error getting search analytics: {e}")
            return {
                "popular_queries": [],
                "avg_response_time": 0,
                "daily_searches": [],
                "total_searches": 0
            }
    
    def get_file_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get file usage analytics."""
        try:
            cutoff_timestamp = (datetime.now() - timedelta(days=days)).timestamp()
            
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="timestamp",
                        range=models.Range(gte=cutoff_timestamp)
                    )
                ]
            )
            
            points, _ = qdrant_manager.client.scroll(
                collection_name=self.file_access_collection,
                scroll_filter=filter_condition,
                limit=10000,
                with_payload=True,
                with_vectors=False
            )
            
            if not points:
                return {
                    "popular_files": [],
                    "upload_activity": []
                }
            
            # Most accessed files (search/view only)
            access_files = [p.payload["filename"] for p in points 
                          if p.payload["access_type"] in ["search", "view"]]
            file_counts = Counter(access_files)
            popular_files = [{"filename": f, "access_count": c} for f, c in file_counts.most_common(10)]
            
            # Upload activity by day
            upload_data = defaultdict(int)
            for p in points:
                if p.payload["access_type"] == "upload":
                    date = datetime.fromtimestamp(p.payload["timestamp"]).strftime("%Y-%m-%d")
                    upload_data[date] += 1
            
            upload_activity = [{"date": d, "uploads": u} for d, u in sorted(upload_data.items())]
            
            return {
                "popular_files": popular_files,
                "upload_activity": upload_activity
            }
            
        except Exception as e:
            print(f"Error getting file analytics: {e}")
            return {
                "popular_files": [],
                "upload_activity": []
            }
    
    def get_search_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent search history."""
        try:
            points, _ = qdrant_manager.client.scroll(
                collection_name=self.search_collection,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # Sort by timestamp (most recent first)
            sorted_points = sorted(points, key=lambda p: p.payload["timestamp"], reverse=True)
            
            return [
                {
                    "query": p.payload["query"],
                    "timestamp": datetime.fromtimestamp(p.payload["timestamp"]).isoformat(),
                    "results_count": p.payload["results_count"],
                    "response_time": p.payload["response_time"]
                }
                for p in sorted_points[:limit]
            ]
            
        except Exception as e:
            print(f"Error getting search history: {e}")
            return []
    
    def save_search_to_history(self, query: str, results: List[Dict]) -> str:
        """Save search query and results for later retrieval."""
        search_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save to file-based history for complex results
        history_dir = "search_history"
        os.makedirs(history_dir, exist_ok=True)
        
        history_data = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "results_count": len(results)
        }
        
        with open(f"{history_dir}/{search_id}.json", "w") as f:
            json.dump(history_data, f, indent=2)
        
        return search_id
    
    def load_search_from_history(self, search_id: str) -> Optional[Dict[str, Any]]:
        """Load saved search results."""
        try:
            with open(f"search_history/{search_id}.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return None

# Global instance
analytics_tracker = AnalyticsTracker()