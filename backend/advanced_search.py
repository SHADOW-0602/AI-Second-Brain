import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from qdrant_client.http import models
from database import get_qdrant_client
from ingestion import get_embedding
import spacy

# Load spaCy model for NLP
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None

class AdvancedSearch:
    def __init__(self):
        self.client = get_qdrant_client()
        self.collection_name = "second_brain"
    
    def hybrid_search(self, query: str, limit: int = 10, filters: Dict = None) -> List[Dict]:
        """Combine semantic and keyword search"""
        # Semantic search
        vector = get_embedding(query)
        from database import qdrant_manager
        semantic_results = qdrant_manager.advanced_search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit,
            filter_conditions=self._build_filter(filters)
        )
        
        # Keyword search (simple implementation)
        keywords = query.lower().split()
        keyword_results = []
        
        # Get all points for keyword matching
        scroll_result = self.client.scroll(
            collection_name=self.collection_name,
            limit=1000,
            with_payload=True,
            scroll_filter=self._build_filter(filters)
        )
        
        for point in scroll_result[0]:
            text = point.payload.get("text", "").lower()
            keyword_score = sum(1 for keyword in keywords if keyword in text) / len(keywords)
            if keyword_score > 0:
                keyword_results.append({
                    "point": point,
                    "keyword_score": keyword_score
                })
        
        # Combine and rank results
        combined_results = self._combine_results(semantic_results, keyword_results)
        return combined_results[:limit]
    
    def boolean_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Handle boolean operators (AND, OR, NOT)"""
        # Simple boolean parser
        if " AND " in query:
            terms = query.split(" AND ")
            return self._and_search(terms, limit)
        elif " OR " in query:
            terms = query.split(" OR ")
            return self._or_search(terms, limit)
        elif " NOT " in query:
            include_term, exclude_term = query.split(" NOT ", 1)
            return self._not_search(include_term.strip(), exclude_term.strip(), limit)
        else:
            return self.hybrid_search(query, limit)
    
    def _build_filter(self, filters: Dict = None) -> Optional[models.Filter]:
        """Build Qdrant filter from search filters"""
        if not filters:
            return None
        
        conditions = []
        
        if filters.get("file_types"):
            conditions.append(
                models.FieldCondition(
                    key="file_type",
                    match=models.MatchAny(any=filters["file_types"])
                )
            )
        
        if filters.get("date_from") or filters.get("date_to"):
            # Date filtering would need timestamp fields
            pass
        
        if filters.get("min_score"):
            # Handled in search parameters
            pass
        
        return models.Filter(must=conditions) if conditions else None
    
    def _combine_results(self, semantic_results, keyword_results):
        """Combine semantic and keyword search results"""
        combined = {}
        
        # Add semantic results
        for result in semantic_results:
            point_id = str(result.id)
            combined[point_id] = {
                "point": result,
                "semantic_score": result.score,
                "keyword_score": 0,
                "combined_score": result.score * 0.7
            }
        
        # Add keyword scores
        for result in keyword_results:
            point_id = str(result["point"].id)
            if point_id in combined:
                combined[point_id]["keyword_score"] = result["keyword_score"]
                combined[point_id]["combined_score"] += result["keyword_score"] * 0.3
            else:
                combined[point_id] = {
                    "point": result["point"],
                    "semantic_score": 0,
                    "keyword_score": result["keyword_score"],
                    "combined_score": result["keyword_score"] * 0.3
                }
        
        # Sort by combined score
        return sorted(combined.values(), key=lambda x: x["combined_score"], reverse=True)
    
    def _and_search(self, terms: List[str], limit: int):
        """Search for documents containing ALL terms"""
        results = []
        for term in terms:
            term_results = self.hybrid_search(term.strip(), limit=100)
            if not results:
                results = term_results
            else:
                # Keep only results that appear in both
                result_ids = {str(r["point"].id) for r in term_results}
                results = [r for r in results if str(r["point"].id) in result_ids]
        return results[:limit]
    
    def _or_search(self, terms: List[str], limit: int):
        """Search for documents containing ANY terms"""
        all_results = {}
        for term in terms:
            term_results = self.hybrid_search(term.strip(), limit=50)
            for result in term_results:
                point_id = str(result["point"].id)
                if point_id not in all_results:
                    all_results[point_id] = result
                else:
                    # Boost score for multiple matches
                    all_results[point_id]["combined_score"] += result["combined_score"] * 0.5
        
        return sorted(all_results.values(), key=lambda x: x["combined_score"], reverse=True)[:limit]
    
    def _not_search(self, include_term: str, exclude_term: str, limit: int):
        """Search for documents containing include_term but NOT exclude_term"""
        include_results = self.hybrid_search(include_term, limit=100)
        exclude_results = self.hybrid_search(exclude_term, limit=100)
        exclude_ids = {str(r["point"].id) for r in exclude_results}
        
        return [r for r in include_results if str(r["point"].id) not in exclude_ids][:limit]

advanced_search = AdvancedSearch()