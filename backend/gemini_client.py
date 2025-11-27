import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-2.5-pro"
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment")
            self.model = None
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)

    async def chat_with_context(self, query: str, context: str) -> str:
        if not self.model:
            return "Gemini client not initialized."

        try:
            prompt = f"""You are a helpful AI assistant.
Use the following context to answer the user's question.

CONTEXT:
{context}

QUESTION:
{query}
"""
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return f"Gemini Error: {str(e)}"

gemini_client = GeminiClient()
