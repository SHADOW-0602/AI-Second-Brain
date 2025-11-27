import httpx
import logging
from typing import List, Dict, Optional, Any
from config import WORKFLOW_WEBHOOK_URL, WORKFLOW_API_KEY

logger = logging.getLogger(__name__)

class WorkflowClient:
    """Client for executing external workflows (n8n, Flowise, Lamatic) via Webhook."""
    
    def __init__(self):
        self.webhook_url = WORKFLOW_WEBHOOK_URL
        self.api_key = WORKFLOW_API_KEY
        
    async def execute_workflow(self, query: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute the external workflow with the user query and retrieved context.
        
        Args:
            query: The user's question.
            context: List of retrieved chunks from Qdrant.
            
        Returns:
            Dict containing the workflow response.
        """
        if not self.webhook_url:
            raise ValueError("WORKFLOW_WEBHOOK_URL is not configured")
            
        # Format context into a single string for the LLM
        context_text = "\n\n".join([
            f"Source: {c.get('filename', 'Unknown')}\nContent: {c.get('text', '')}"
            for c in context
        ])
        
        payload = {
            "query": query,
            "question": query,
            "context": context_text,
            # Flowise specific: Pass variables in overrideConfig -> promptValues
            "overrideConfig": {
                "promptValues": {
                    "context": context_text,
                    "question": query
                }
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Workflow execution failed with status {e.response.status_code}: {e.response.text}")
            raise ValueError(f"Workflow execution failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Workflow execution error: {str(e)}")
            raise e

# Global instance
workflow_client = WorkflowClient()
