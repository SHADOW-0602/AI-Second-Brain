import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from analytics import analytics_tracker

def track_chat(request, provider: str, processing_time: float, user_id: str = "anonymous"):
    """Record a chat interaction for analytics.
    We reuse the same analytics schema as a search, but set results_count to 0.
    """
    analytics_tracker.track_search(
        query=request.message,
        results_count=0,
        response_time=processing_time,
        user_id=user_id,
    )
