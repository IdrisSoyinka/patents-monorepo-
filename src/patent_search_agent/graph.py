"""Main graph with structured output nodes for Patent Search Agent."""
import logging
import os
from typing import Literal

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_ollama import ChatOllama
from langgraph.types import interrupt, Command
import uuid

from .state import PatentSearchState
from .nodes.concept_extraction import concept_extraction_node
from .nodes.keyword_generation import keyword_generation_node
from .nodes.query_generation import query_generation_node
from .nodes.human_validation import human_validation_node
from .nodes.enhancement import enhancement_node
from .nodes.ipc_classification import ipc_classification_node
from .nodes.patent_search import patent_search_node
from .nodes.evaluation import evaluation_node

# Load environment variables
load_dotenv()


def create_llm(model_name: str = "qwen3:4b-instruct-2507-fp16"):
    """Create LLM instance based on model name."""
    try:
        return ChatOllama(
            model=model_name,
            temperature=0.7,
            num_predict=4096,
            num_ctx=20480,
            reasoning=True,
        )
    except Exception as e:
        logging.error(f"Error creating LLM: {e}")


def create_graph(
    model_name: str = "qwen3:4b-instruct-2507-fp16",
    checkpointer=None
) -> StateGraph:
    """
    Create the patent search workflow graph with structured outputs.
    
    This graph uses the "bind as tool" approach for structured outputs,
    ensuring consistent data formats throughout the workflow.
    """
    
    # Create LLM instance
    llm = create_llm(model_name)
    
    # Create checkpointer if not provided
    if checkpointer is None:
        checkpointer = InMemorySaver()
    
    # Create the graph
    workflow = StateGraph(PatentSearchState)
    
    # Add structured nodes
    workflow.add_node("concept_extraction", lambda state: concept_extraction_node(state, llm))
    workflow.add_node("keyword_generation", lambda state: keyword_generation_node(state, llm))
    workflow.add_node("human_validation", human_validation_node)
    workflow.add_node("enhancement", lambda state: enhancement_node(state, llm))
    workflow.add_node("ipc_classification", lambda state: ipc_classification_node(state, llm))
    workflow.add_node("query_generation", lambda state: query_generation_node(state, llm))
    workflow.add_node("patent_search", patent_search_node)
    workflow.add_node("evaluation", evaluation_node)
    
    # Define the workflow edges
    workflow.add_edge(START, "concept_extraction")
    workflow.add_edge("concept_extraction", "keyword_generation")
    workflow.add_edge("keyword_generation", "human_validation")
    
    workflow.add_edge("enhancement", "ipc_classification")
    workflow.add_edge("ipc_classification", "query_generation")
    
    # workflow.add_edge("evaluation", END)
    workflow.add_edge("query_generation", END)
    
    # Compile the graph
    app = workflow.compile(checkpointer=checkpointer)
    
    return app


def run_patent_search(
    patent_description: str,
    max_results: int = 10,
    model_name: str = "qwen3:4b-instruct-2507-fp16"
) -> dict:
    """
    Run the patent search workflow with structured outputs.
    
    Args:
        patent_description: Description of the patent to search for
        max_results: Maximum number of results to return
        model_name: LLM model to use
        
    Returns:
        Final state with structured results
    """
    
    app = create_graph(model_name=model_name)
    
    initial_state = {
        "patent_description": patent_description,
        "max_results": max_results,
        "messages": [],
    }
    
    # Create a thread for this run
    # Tạo thread config
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Run the workflow
    example1 = Command(resume=[{
        "type": "edit",
        "args": {
                "keywords": {
                    "problem_purpose": ["keyword1", "keyword2", "keyword3"],
                    "object_system": ["keyword1", "keyword2", "keyword3"],
                    "environment_field": ["keyword1", "keyword2", "keyword3"]
                }
        }
    }])
    example2 = Command(resume=[{
        "type": "accept",
    }])
    example3 = Command(resume=[{
        "type": "reject",
    }])
    print(f"\n\U0001f680 Step 1: Running until first interrupt...")
    print("=" * 50)
    result = app.invoke(initial_state, config=config)
    print(f"\n\U0001f504 First invoke calls - Current state:")
    print(f"   \U0001f4ca Seed keywords: {result.get('seed_keywords')}")
    print(f"   \U0001f4da Messages: {result.get('messages', [])}")
    print("=" * 50)

    print(f"\n\U0001f680 Step 2: Resuming with Rejected")
    print("=" * 50)
    result = app.invoke(example3, config=config)
    print(f"\n\U0001f504 Second invoke calls - Current state:")
    print(f"   \U0001f4ca Seed keywords: {result.get('seed_keywords')}")
    print(f"   \U0001f4da Messages: {result.get('messages', [])}")
    print("=" * 50)

    print(f"\n\U0001f680 Step 3: Resuming with Accepted")
    print("=" * 50)
    result = app.invoke(example2, config=config)
    print(f"\n\U0001f504 Third invoke calls - Current state:")
    print(f"   \U0001f4ca Seed keywords: {result.get('seed_keywords')}")
    print(f"   \U0001f4da Messages: {result.get('messages', [])}")
    print("=" * 50)
    
    return result



if __name__ == "__main__":
    # Example usage with structured outputs
    sample_description = """
    A smart wearable device for continuous health monitoring that integrates multiple biosensors 
    including heart rate, blood oxygen saturation, skin temperature, and motion sensors. The device 
    uses machine learning algorithms to analyze the collected data and predict potential health issues.
    """
    
    print("\U0001f50d Running Patent Search with Structured Outputs...")
    run_patent_search(sample_description)
