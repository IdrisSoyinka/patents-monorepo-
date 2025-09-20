"""Concept Extraction Node - Extracts key concepts using structured output (bind as tool)."""

import logging
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_core.language_models import BaseChatModel

from ..state import PatentSearchState
from ..schemas import ConceptMatrix
from ..utils.prompts import CONCEPT_EXTRACTION_PROMPT


def concept_extraction_node(state: PatentSearchState, llm: BaseChatModel) -> Dict[str, Any]:
    print("\U0001f50d Running concept_extraction_node...")
    """
    Extract concept matrix from patent description using structured output.
    
    This node uses the "bind as tool" approach for guaranteed structured output.
    The ConceptMatrix schema is bound as a tool that the LLM must call.
    
    Args:
        state: Current state containing patent_description
        llm: Language model for concept extraction
        
    Returns:
        Updated state with concept_matrix_structured
    """
    try:
        patent_description = state["patent_description"]
        
        model = llm.with_structured_output(ConceptMatrix)
        
        # Create messages for LLM
        messages = [
            SystemMessage(content=CONCEPT_EXTRACTION_PROMPT + """

You MUST respond by calling the ConceptMatrix tool with the extracted concepts.
Analyze the patent description and organize concepts into exactly three categories:
1. problem_purpose: Problems being solved and main objectives  
2. object_system: Technical components, devices, and systems
3. environment_field: Technical field and application domain

Each category should have 2-7 specific, technical concepts.
"""),
            HumanMessage(content=f"Patent Description:\n{patent_description}")
        ]
            # Get LLM response with forced tool calling
        concept_matrix = model.invoke(messages)
        print(concept_matrix)

        return {
            **state,
            "concept_matrix": concept_matrix,
            "messages": state.get("messages", []) + [
                AIMessage(content=concept_matrix)
            ]
        }
        
    except Exception as e:
        error_msg = f"Error in concept extraction: {str(e)}"
        # Fallback to basic extraction
        fallback_matrix = _fallback_concept_extraction(state["patent_description"])
        
        return {
            **state,
            "concept_matrix": fallback_matrix,
            "errors": state.get("errors", []) + [error_msg],
        }


def _fallback_concept_extraction(patent_description: str) -> ConceptMatrix:
    """
    Fallback concept extraction when structured output fails.
    
    Args:
        patent_description: Original patent description
        
    Returns:
        Basic ConceptMatrix based on simple keyword analysis
    """
    
    # Simple keyword-based extraction
    problem_purpose = []
    object_system = []
    environment_field = []
    
    # Ensure minimum items
    if not problem_purpose:
        problem_purpose = ["invention_purpose"]
    if not object_system:
        object_system = ["technical_system"]
    if not environment_field:
        environment_field = ["technology_field"]
    
    return ConceptMatrix(
        problem_purpose=problem_purpose[0],
        object_system=object_system[0],
        environment_field=environment_field[0]
    )


# Function to check if concept extraction should continue to next node
def should_continue_from_concept_extraction(state: PatentSearchState) -> str:
    """
    Determine if concept extraction is complete and ready for next node.
    
    Args:
        state: Current state
        
    Returns:
        Next node name
    """
    if state.get("concept_matrix"):
        return "keyword_generation"
    else:
        # If no structured output, stay in concept extraction or handle error
        return "concept_extraction"
