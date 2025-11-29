import os
import logging
import cohere
from langsmith import traceable

logger = logging.getLogger(__name__)

class CohereClient:
    def __init__(self):
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        self.api_key = os.getenv("COHERE_API_KEY")
        
        if not self.api_key:
            logger.warning("COHERE_API_KEY not found in environment")
            self.client = None
        else:
            self.client = cohere.Client(self.api_key)

    @traceable(run_type="llm", name="cohere_chat")
    async def chat_with_context(self, query: str, context: str) -> str:
        if not self.client:
            return "Cohere client not initialized."

        try:
            # Cohere's Chat API
            response = self.client.chat(
                model="command-r-plus-08-2024", # Updated to latest stable model
                message=query,
                preamble="You are a helpful AI assistant. Answer the user's question based on the provided context. If the context is not relevant, answer based on your general knowledge.",
                documents=[{"text": context[:4000]}], # Cohere RAG style
                temperature=0.7
            )
            return response.text
        except Exception as e:
            logger.error(f"Cohere API Error: {e}")
            return f"Cohere Error: {str(e)}"

cohere_client = CohereClient()
