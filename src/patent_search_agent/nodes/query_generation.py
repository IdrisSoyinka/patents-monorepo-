"""Query Generation Node - Creates search queries using structured output."""

import logging
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_core.language_models import BaseChatModel

from ..state import PatentSearchState
from ..schemas import SearchQueries, SeedKeywords
from ..utils.prompts import QUERY_GENERATION_PROMPT


def query_generation_node(state: PatentSearchState, llm: BaseChatModel) -> Dict[str, Any]:
    print("\U0001f50d Running query_generation_node...")
    """
    Generate Boolean search queries using structured output.
    
    This node creates optimized search queries from enhanced keywords and IPC codes.
    
    Args:
        state: Current state containing enhanced keywords and IPC codes
        llm: Language model for query generation
        
    Returns:
        Updated state with search_queries_structured
    """
    try:
        # Get data from state
        enhanced_keywords = state.get("enhanced_keywords")
        
        # Get IPC codes
        ipc_codes = state.get("ipc_codes")
        
        # Bind SearchQueries as a tool for structured output
        tools = [SearchQueries]
        model_with_tools = llm.bind_tools(tools, tool_choice="any")
        
        # Format data for prompt
        keywords_text = _format_keywords_data(enhanced_keywords)
        ipc_text = ', '.join(ipc_codes)
        
        # Create messages for LLM
        messages = [
            SystemMessage(content=QUERY_GENERATION_PROMPT + """

You MUST respond by calling the SearchQueries tool with the generated queries.
Create search queries ready to use in Google Patents search:

Guidelines:
- Use exact phrase matching with quotes for key terms
- Combine keywords with Boolean operators strategically
- Include IPC codes using format: (G06F OR G06Q50/00) AND "machine learning" (Each query can include multi IPC code)
- Balance specificity with recall
- Target Google Patents search syntax
"""),
            HumanMessage(content=f"""
Keywords by Category:
{keywords_text}

IPC Codes: {ipc_text}

Generate optimized search queries for patent databases that will find similar patents.
Create diverse queries targeting different aspects of the invention.
""")
        ]
        
        # Get LLM response with forced tool calling
        response = model_with_tools.invoke(messages)
        print(f"Response: {response}")
        
        # Extract structured output from tool call
        if response.tool_calls and response.tool_calls[0]["name"] == "SearchQueries":
            tool_call = response.tool_calls[0]
            search_queries = SearchQueries(**tool_call["args"])

            # Create required tool message response
            tool_message = ToolMessage(
                content="Search queries generated successfully",
                tool_call_id=tool_call["id"]
            )
            success = True
        else:
            # Fallback query generation
            logging.warning("SearchQueries tool call failed, using fallback queries.")
            search_queries = ""
            success = False
        
        return {
            **state,
            "search_queries": search_queries,
            "messages": state.get("messages", []) + [
                AIMessage(content=f"{response}")] + [tool_message
            ]
        }
        
    except Exception as e:
        error_msg = f"Error in query generation: {str(e)}"
        print(e)
        return {
            **state,
            "errors": state.get("errors", []) + [error_msg],
        }


def _format_keywords_data(keywords_data: Dict[str, Any]) -> str:
    """Format keywords data for display in prompt."""
    formatted_lines = []
    for category, keywords in keywords_data.items():
        if keywords:
            category_name = category.replace('_', ' ').title()
            formatted_lines.append(f"{category_name}: {', '.join(keywords)}")  # Show all
    return '\n'.join(formatted_lines)
