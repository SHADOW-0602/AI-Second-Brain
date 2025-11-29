import os
import logging
import google.generativeai as genai
from langsmith import traceable

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-2.5-pro"
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment")
            self.model = None
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)

    @traceable(run_type="llm", name="gemini_chat")
    async def chat_with_context(self, query: str, context: str) -> str:
        if not self.model:
            return "Gemini client not initialized."

        try:
            prompt = f"""You are a helpful AI assistant.
Use the following context to answer the user's question.
If the context is not relevant or empty, answer based on your general knowledge.

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

    @traceable(run_type="tool", name="gemini_intent_analysis")
    async def analyze_intent(self, query: str) -> dict:
        """
        Analyze user intent using a separate, fast Gemini model instance.
        Uses GEMINI_API_2 to avoid rate limits/conflicts with main chat.
        """
        try:
            # Use secondary API key for this specific task
            api_key_2 = os.getenv("GEMINI_API_2")
            if not api_key_2:
                logger.warning("GEMINI_API_2 not set, skipping intent analysis")
                return {"intent": "chat", "keywords": [], "needs_context": True}

            # Configure a separate client instance for this call
            # We use direct REST API or a separate configure call if possible.
            # Since genai.configure is global, we might need to be careful.
            # Actually, we can pass api_key to GenerativeModel in some versions, 
            # or just re-configure (but that's thread-unsafe).
            # SAFEST APPROACH: Use simple HTTP request for this specific isolated task
            # to guarantee no interference with the global `genai` object used by the main chat.
            
            import aiohttp
            import json
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key_2}"
            
            prompt = f"""You are an Intent Classifier. Analyze the user query.
            
            QUERY: "{query}"
            
            Classify into one of these INTENTS:
            1. "summarize": User wants a summary of the active document (e.g., "summarize this", "tl;dr").
            2. "search": User is asking a specific question that needs facts (e.g., "what is the capital?", "how does X work?").
            3. "chat": General conversation, greeting, or question not needing specific documents (e.g., "hello", "tell me a joke").
            
            Extract KEYWORDS for search (if intent is search/summarize).
            
            Output JSON ONLY:
            {{
                "intent": "summarize" | "search" | "chat",
                "keywords": ["keyword1", "keyword2"]
            }}
            """
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "response_mime_type": "application/json"
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Gemini Intent API failed: {await response.text()}")
                        return {"intent": "chat", "keywords": [], "needs_context": True}
                    
                    result = await response.json()
                    text_response = result['candidates'][0]['content']['parts'][0]['text']
                    return json.loads(text_response)
                    
        except Exception as e:
            logger.error(f"Intent Analysis Error: {e}")
            return {"intent": "chat", "keywords": [], "needs_context": True}

gemini_client = GeminiClient()
