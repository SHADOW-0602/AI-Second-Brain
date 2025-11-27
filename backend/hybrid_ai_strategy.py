"""
Hybrid AI Strategy: Using Mistral + Lamatic Together
Demonstrates when to use each provider for optimal results
"""
import asyncio
from mistral_client import mistral_client
from lamatic_client import lamatic_workflow_client
from database import qdrant_manager
from ingestion import get_embedding

COLLECTION_NAME = "second_brain"

class HybridAIOrchestrator:
    """Intelligently routes requests to Mistral or Lamatic based on complexity"""
    
    def __init__(self):
        self.mistral = mistral_client
        self.lamatic = lamatic_workflow_client
    
    async def answer_question(self, question: str, complexity: str = "auto"):
        """
        Answer question using best provider
        
        Args:
            question: User's question
            complexity: "simple", "complex", or "auto" (auto-detect)
        """
        # Get context from Qdrant
        vector = get_embedding(question)
        search_results = qdrant_manager.advanced_search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=3
        )
        context = [res.payload.get("text", "") for res in search_results]
        
        # Auto-detect complexity if needed
        if complexity == "auto":
            complexity = self._detect_complexity(question)
        
        if complexity == "simple":
            # Use Mistral for fast, simple Q&A
            print("🚀 Using Mistral (fast, simple)")
            result = await self.mistral.chat_with_context(
                user_message=question,
                context=context
            )
            return result
        else:
            # Use Lamatic for complex multi-step reasoning
            print("🔄 Using Lamatic (complex workflow)")
            result = await self.lamatic.trigger_workflow(
                workflow_id="qa_with_verification",
                inputs={
                    "question": question,
                    "context": context,
                    "min_confidence": 0.7
                }
            )
            return result
    
    def _detect_complexity(self, question: str) -> str:
        """Auto-detect if question is simple or complex"""
        # Simple heuristics
        complex_keywords = [
            "compare", "analyze", "explain in detail", "step by step",
            "comprehensive", "research", "investigate", "verify"
        ]
        
        question_lower = question.lower()
        if any(keyword in question_lower for keyword in complex_keywords):
            return "complex"
        
        if len(question.split()) > 15:
            return "complex"
        
        return "simple"
    
    async def multi_step_research(self, topic: str):
        """
        Complex research workflow using Lamatic
        Best for: Deep analysis, multi-step reasoning
        """
        print("🔬 Multi-step Research Workflow")
        
        # Step 1: Initial search
        vector = get_embedding(topic)
        initial_results = qdrant_manager.advanced_search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=5
        )
        context = [res.payload.get("text", "") for res in initial_results]
        
        # Step 2: Execute multi-step workflow
        result = await self.lamatic.execute_multi_step(
            steps=[
                {
                    "name": "initial_analysis",
                    "workflow_id": "research_assistant",
                    "inputs": {
                        "user_message": f"Analyze: {topic}",
                        "context": context,
                        "depth": "initial"
                    }
                },
                {
                    "name": "deep_dive",
                    "workflow_id": "research_assistant",
                    "inputs": {
                        "depth": "comprehensive"
                    }
                },
                {
                    "name": "synthesis",
                    "workflow_id": "document_summarization",
                    "inputs": {
                        "summary_type": "comprehensive"
                    }
                }
            ],
            context={"topic": topic, "context": context}
        )
        
        return result
    
    async def parallel_analysis(self, topic: str):
        """
        Parallel analysis using Lamatic
        Best for: Multiple perspectives, comprehensive coverage
        """
        print("⚡ Parallel Analysis Workflow")
        
        vector = get_embedding(topic)
        search_results = qdrant_manager.advanced_search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=10
        )
        context = [res.payload.get("text", "") for res in search_results]
        
        # Execute multiple analyses in parallel
        result = await self.lamatic.execute_parallel(
            workflows=[
                {
                    "name": "fact_extraction",
                    "workflow_id": "parallel_analysis",
                    "inputs": {"task": "extract_facts"}
                },
                {
                    "name": "theme_identification",
                    "workflow_id": "parallel_analysis",
                    "inputs": {"task": "identify_themes"}
                },
                {
                    "name": "insight_generation",
                    "workflow_id": "parallel_analysis",
                    "inputs": {"task": "generate_insights"}
                }
            ],
            shared_context={"topic": topic, "context": context}
        )
        
        return result
    
    async def quick_summary(self, texts: list):
        """
        Quick summarization using Mistral
        Best for: Fast, simple summaries
        """
        print("⚡ Quick Summary (Mistral)")
        result = await self.mistral.summarize_documents(texts)
        return result

# Example usage
async def demo():
    """Demonstrate hybrid AI strategy"""
    orchestrator = HybridAIOrchestrator()
    
    print("=" * 60)
    print("🤖 Hybrid AI Strategy Demo")
    print("=" * 60 + "\n")
    
    # Example 1: Simple question → Mistral
    print("\n1️⃣ Simple Question (Auto-routed to Mistral)")
    result1 = await orchestrator.answer_question(
        "What is machine learning?",
        complexity="auto"
    )
    print(f"Answer: {result1.get('output', 'No response')[:100]}...\n")
    
    # Example 2: Complex question → Lamatic
    print("\n2️⃣ Complex Question (Auto-routed to Lamatic)")
    result2 = await orchestrator.answer_question(
        "Compare and analyze the different approaches to machine learning",
        complexity="auto"
    )
    print(f"Answer: {result2.get('output', 'No response')[:100]}...\n")
    
    # Example 3: Multi-step research → Lamatic
    print("\n3️⃣ Multi-step Research (Lamatic Workflow)")
    result3 = await orchestrator.multi_step_research(
        "Deep learning architectures"
    )
    print(f"Steps completed: {len(result3.get('steps', []))}")
    print(f"Status: {result3.get('status')}\n")
    
    print("=" * 60)
    print("✅ Demo Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(demo())
