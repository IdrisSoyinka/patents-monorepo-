"""IPC Classification Node - Gets IPC codes for patent classification."""

from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from src.patent_search_agent.schemas import PatentSummary

from ..state import PatentSearchState
from ..tools.tavily_search import search_web_for_summary
from ..tools.ipccat_api import get_ipc_classification
from ..utils.prompts import PATENT_SUMMARY_PROMPT


def ipc_classification_node(state: PatentSearchState, llm: BaseChatModel) -> Dict[str, Any]:
    print("\U0001f50d Running ipc_classification_node...")
    """
    Get IPC (International Patent Classification) codes using structured output.
    
    This node:
    1. Summarizes the patent description using web search for context
    2. Calls IPCCAT API to get IPC classification codes
    
    Args:
        state: Current state containing patent_description
        llm: Language model for summarization
        
    Returns:
        Updated state with patent_summary and ipc_codes
    """
    patent_description = state["patent_description"]
    
    # Step 1: Create comprehensive summary using structured output
    patent_summary = _create_patent_summary(patent_description, llm)
    
    # Step 2: Get IPC classification using the summary
    ipc_codes = get_ipc_classification(patent_summary)

    print(ipc_codes)
    return {
        **state,
        "ipc_codes": ipc_codes,
        "messages": state.get("messages", []) + [
            HumanMessage(content="Generated IPC classification")
        ]
    }


def _create_patent_summary(description: str, llm: BaseChatModel) -> PatentSummary:
    """
    Create a structured patent summary using LLM with web search context.
    
    Args:
        description: Original patent description
        llm: Language model for summarization
        
    Returns:
        Structured patent summary
    """
    try:
        # Search web for additional context
        web_context = search_web_for_summary(description)
        
        # Create structured LLM
        structured_llm = llm.with_structured_output(PatentSummary)
        
        # Create comprehensive summary using LLM
        messages = [
            SystemMessage(content=PATENT_SUMMARY_PROMPT),
            HumanMessage(content=f"""
Original Patent Description:
{description}

Additional Web Context:
{web_context}

Create a comprehensive technical summary that includes:
1. Technical field and problem being solved
2. Key technical features and innovations
3. Specific components and systems involved
4. Applications and use cases
5. Technical advantages and benefits

Focus on technical terminology that would be useful for patent classification.
""")
        ]
        
        response = structured_llm.invoke(messages)
        return response.content
        
    except Exception as e:
        # Fallback to basic summary structure
        return description[:400] if len(description) > 400 else description
