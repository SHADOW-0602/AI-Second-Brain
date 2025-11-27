from mistralai import Mistral
import logging
import os

logger = logging.getLogger(__name__)

class MistralAIClient:
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.model = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
        
        if not self.api_key:
            logger.warning("MISTRAL_API_KEY not found in environment")
            self.client = None
        else:
            self.client = Mistral(api_key=self.api_key)
    
    async def chat_with_context(self, user_message: str, context: list[str]) -> dict:
        """
        Generate AI response using Mistral with context from your documents.
        
        Args:
            user_message: The user's question
            context: List of relevant text chunks from Qdrant
            
        Returns:
            dict with 'output' key containing the response
        """
        if not self.client:
            return {"error": "Mistral client not initialized - check API key"}
            
        try:
            # Build context-aware system prompt
            context_text = "\n\n".join([
                f"Document Chunk {i+1}:\n{chunk}" 
                for i, chunk in enumerate(context)
            ])
            
            system_prompt = f"""You are an AI assistant with access to the user's personal knowledge base.
Use the following context from their stored documents to answer their question accurately.
If the context doesn't contain relevant information, say so clearly.

CONTEXT FROM USER'S DOCUMENTS:
{context_text}

Answer the user's question based on this context. Be specific and cite which document chunks you're using."""

            # Create messages for Mistral (v1.9+ API)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Call Mistral API
            response = self.client.chat.complete(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return {
                "output": response.choices[0].message.content,
                "model": self.model,
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
            }
            
        except Exception as e:
            logger.error(f"Mistral API error: {e}")
            return {"error": str(e)}
    
    async def summarize_documents(self, texts: list[str]) -> dict:
        """
        Summarize multiple document chunks using Mistral.
        """
        if not self.client:
            return {"error": "Mistral client not initialized - check API key"}
            
        try:
            combined_text = "\n\n".join(texts[:20])  # Limit to avoid token limits
            
            messages = [
                {
                    "role": "user", 
                    "content": f"Summarize the following documents concisely:\n\n{combined_text}"
                }
            ]
            
            response = self.client.chat.complete(
                model=self.model,
                messages=messages,
                temperature=0.5
            )
            
            return {
                "output": response.choices[0].message.content
            }
            
        except Exception as e:
            logger.error(f"Mistral summarization error: {e}")
            return {"error": str(e)}

# Global instance
mistral_client = MistralAIClient()
