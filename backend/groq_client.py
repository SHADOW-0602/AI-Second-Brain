import os
import logging
from groq import Groq
import json
from langsmith import traceable

logger = logging.getLogger(__name__)

class GroqClient:
    def __init__(self):
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        self.api_key = os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found in environment")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
            self._initialize_models()

    def _initialize_models(self):
        """Initialize with currently working models."""
        # Use the models we confirmed are working
        self.aggregator_model = "llama-3.3-70b-versatile"  # Latest 70B model
        self.extractor_model = "llama-3.1-8b-instant"      # Fast 8B model
        
        logger.info(f"Using models: {self.aggregator_model}, {self.extractor_model}")
        
        # Test the model on initialization
        self.test_model()
    
    def test_model(self):
        """Test if the model is working."""
        if not self.client:
            logger.error("Groq client not initialized")
            return False
            
        try:
            completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": "Say 'Hello' in one word."}],
                model=self.extractor_model,
                temperature=0.1,
                max_tokens=10
            )
            response = completion.choices[0].message.content
            logger.info(f"Groq model test successful: {response}")
            return True
        except Exception as e:
            logger.error(f"Groq model test failed: {e}")
            return False

    @traceable(run_type="llm", name="groq_aggregation")
    async def aggregate_responses(self, query: str, context: str, responses: dict) -> str:
        """
        Aggregates responses from multiple models and selects/synthesizes the best answer.
        """
        if not self.client:
            return "Groq client not initialized."

        # Format the inputs for the aggregator
        inputs_text = ""
        for provider, response in responses.items():
            inputs_text += f"\n--- RESPONSE FROM {provider.upper()} ---\n{response}\n"

        system_prompt = f"""You are an expert AI Aggregator and Judge.
You have received responses from multiple AI models (Gemini, Mistral, Cohere) to the user's query.
Your goal is to provide the SINGLE BEST ANSWER to the user.

USER QUERY: {query}

CONTEXT FROM KNOWLEDGE BASE:
{context[:2000]}... (truncated)

MODEL RESPONSES:
{inputs_text}

INSTRUCTIONS:
1. Analyze the responses.
2. Select the most accurate, comprehensive, and clear information.
3. Synthesize a final, high-quality answer.
4. Do NOT mention "Model A said this" or "Gemini said that". Just give the final answer as if it came from one expert source.
5. If all models failed or gave bad info, rely on the Context and your own knowledge to answer.
"""

        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Please provide the final best answer."}
                ],
                model=self.aggregator_model,
                temperature=0.5,
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq Aggregation Error: {e}")
            return f"Error during aggregation: {str(e)}"

    @traceable(run_type="tool", name="groq_fact_extraction")
    async def extract_facts(self, query: str, answer: str) -> list:
        """
        Extracts key facts from the final answer for long-term memory.
        """
        if not self.client:
            return []

        system_prompt = """You are a Memory Assistant.
Extract key FACTS, DECISIONS, or CODE SNIPPETS from the provided Q&A.
Output ONLY a valid JSON object with a "facts" array of strings.
Ignore conversational filler.
Example: {"facts": ["Server port changed to 3000", "Database migration failed due to timeout"]}
"""
        
        user_content = f"Query: {query}\n\nAnswer: {answer}"

        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                model=self.extractor_model,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            content = completion.choices[0].message.content
            result = json.loads(content)
            facts = result.get("facts", [])
            return facts if isinstance(facts, list) else []
        except Exception as e:
            logger.error(f"Groq Fact Extraction Error: {e}")
            return []

groq_client = GroqClient()