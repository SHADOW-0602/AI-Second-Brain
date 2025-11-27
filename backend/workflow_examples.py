"""
Example Lamatic workflow integrations for AI-Second-Brain
Demonstrates complex multi-step workflows with memory + reasoning
"""
import asyncio
from lamatic_client import lamatic_client
from database import qdrant_manager
from ingestion import get_embedding

COLLECTION_NAME = "second_brain"

async def research_assistant_workflow(user_query: str):
    """
    Multi-step research workflow:
    1. Search memory for relevant docs
    2. Analyze findings
    3. Search again if needed
    4. Generate comprehensive report
    """
    # Step 1: Initial search
    vector = get_embedding(user_query)
    initial_results = qdrant_manager.advanced_search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        limit=5
    )
    
    context = [res.payload.get("text", "") for res in initial_results]
    
    # Step 2: Trigger Lamatic workflow
    result = await lamatic_client.trigger_workflow(
        workflow_id="research_assistant",
        inputs={
            "user_message": user_query,
            "context": context,
            "memory_chunks": len(context),
            "task_type": "research",
            "depth": "comprehensive"
        }
    )
    
    return result

async def document_summarization_pipeline(document_ids: list):
    """
    Multi-level summarization workflow:
    1. Analyze each document chunk
    2. Extract themes
    3. Cross-reference documents
    4. Generate comprehensive summary
    """
    # Gather all document chunks
    all_chunks = []
    for doc_id in document_ids:
        # Search for chunks from this document
        results = qdrant_manager.search_by_metadata(
            collection_name=COLLECTION_NAME,
            metadata_filter={"document_id": doc_id},
            limit=50
        )
        all_chunks.extend([res.payload.get("text", "") for res in results])
    
    # Trigger summarization workflow
    result = await lamatic_client.trigger_workflow(
        workflow_id="document_summarization",
        inputs={
            "chunks": all_chunks,
            "num_documents": len(document_ids),
            "summary_type": "comprehensive",
            "include_themes": True,
            "include_action_items": True
        }
    )
    
    return result

async def qa_with_verification_workflow(question: str):
    """
    Q&A workflow with source verification:
    1. Search for relevant context
    2. Generate initial answer
    3. Verify against sources
    4. Score confidence
    5. Refine if needed
    """
    # Get context
    vector = get_embedding(question)
    search_results = qdrant_manager.advanced_search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        limit=3
    )
    
    context = [res.payload.get("text", "") for res in search_results]
    sources = [res.payload.get("filename", "unknown") for res in search_results]
    
    # Trigger verification workflow
    result = await lamatic_client.trigger_workflow(
        workflow_id="qa_with_verification",
        inputs={
            "question": question,
            "context": context,
            "sources": sources,
            "min_confidence": 0.7,
            "max_iterations": 2
        }
    )
    
    return result

async def iterative_refinement_workflow(query: str, quality_threshold: float = 0.8):
    """
    Iterative workflow that refines answer until quality threshold met:
    1. Generate initial answer
    2. Evaluate quality
    3. If below threshold, refine and repeat
    4. Return best answer
    """
    vector = get_embedding(query)
    search_results = qdrant_manager.advanced_search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        limit=5
    )
    
    context = [res.payload.get("text", "") for res in search_results]
    
    result = await lamatic_client.trigger_workflow(
        workflow_id="iterative_refinement",
        inputs={
            "query": query,
            "context": context,
            "quality_threshold": quality_threshold,
            "max_iterations": 3,
            "evaluation_criteria": [
                "accuracy",
                "completeness",
                "clarity"
            ]
        }
    )
    
    return result

async def parallel_analysis_workflow(topic: str):
    """
    Parallel processing workflow:
    1. Fork into multiple analysis branches
    2. Each branch analyzes different aspect
    3. Join results into comprehensive overview
    """
    vector = get_embedding(topic)
    search_results = qdrant_manager.advanced_search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        limit=10
    )
    
    context = [res.payload.get("text", "") for res in search_results]
    
    result = await lamatic_client.trigger_workflow(
        workflow_id="parallel_analysis",
        inputs={
            "topic": topic,
            "context": context,
            "parallel_tasks": [
                "extract_facts",
                "identify_themes",
                "find_contradictions",
                "generate_insights"
            ],
            "synthesis_type": "comprehensive"
        }
    )
    
    return result

# Example usage
async def main():
    """Test workflow examples"""
    print("🔄 Testing Lamatic Workflows\n")
    
    # Test 1: Research Assistant
    print("1️⃣ Research Assistant Workflow")
    result1 = await research_assistant_workflow(
        "What are the key findings about machine learning?"
    )
    print(f"Result: {result1.get('output', 'No output')}\n")
    
    # Test 2: Q&A with Verification
    print("2️⃣ Q&A with Verification Workflow")
    result2 = await qa_with_verification_workflow(
        "How does deep learning work?"
    )
    print(f"Result: {result2.get('output', 'No output')}\n")
    
    print("✅ Workflow tests complete!")

if __name__ == "__main__":
    asyncio.run(main())
