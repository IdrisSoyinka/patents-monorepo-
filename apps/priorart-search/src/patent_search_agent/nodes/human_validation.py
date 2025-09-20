"""Human Validation Node - Allows human-in-the-loop validation of keywords."""

from typing import Dict, Any
from langchain_core.messages import HumanMessage
from langgraph.types import interrupt, Command
from langgraph.graph import StateGraph, START, END
from typing import Literal, List

from ..state import PatentSearchState

# Command[Literal["process_feedback", "__end__"]]:
def human_validation_node(state: PatentSearchState) -> Command[Literal["keyword_generation", "enhancement"]]:
    print("\U0001f50d Running human_validation_node...")
    """
    Human-in-the-loop validation of generated keywords using LangGraph interrupt.
    
    This node implements the "Review and Edit State" pattern from LangGraph.
    Uses interrupt() to pause the workflow and wait for human input.
    
    Args:
        state: Current state containing seed_keywords
        
    Returns:
        Updated state with validated_keywords
    """
    # try:
    seed_keywords = state.get("seed_keywords")
    
    if not seed_keywords:
        return {
            **state,
            "errors": state.get("errors", []) + ["No seed keywords found for validation"],
            "validated_keywords": {}
        }
    
    # Format keywords for human review
    formatted_keywords = _format_keywords_for_display(seed_keywords)
    
    # Use interrupt to pause workflow and get human input
    # This will pause the graph execution until resumed with Command(resume=human_input)
    description = """
#\U0001f4dd Review and edit the generated keywords for patent search

## Current keywords:
{formatted_keywords}

---
Please review the keywords below and provide your feedback:

Actions you can take:
- ✅ **Approve**: Accept all keywords as-is
- ✏️ **Edit**: Provide modified keywords in the same structure  
- \U0001f6ab **Reject**: Reject all keywords (re-run)
- \U0001f4ac **Feedback**: Improve keywords with feedback (re-run)

If editing, please provide the modified keywords in this format:
Command(resume=[{
"type": "edit",
"args": {
        "keywords": {
            "problem_purpose": ["keyword1", "keyword2", ...],
            "object_system": ["keyword1", "keyword2", ...],
            "environment_field": ["keyword1", "keyword2", ...]
        }
}
}])
"""

    request = {
        "action_request": {
            "action": "review",
            "args": {
                "keywords": {
                    "problem_purpose": seed_keywords.problem_purpose.copy(),
                    "object_system": seed_keywords.object_system.copy(),
                    "environment_field": seed_keywords.environment_field.copy()
                }
            }
        },
        "config": {
            "allow_accept": True,      # Approve
            "allow_edit": True,        # Edit
            "allow_reject": True,      # Reject  
            "allow_respond": True      # Feedback
        },
        "description": description
    }
    # Process human input
    print(request['description'])
    response = interrupt([request])[0]

    forward = _process_human_input(response, seed_keywords, state)

    return Command(goto=forward[0], update=forward[1])
        
    # except Exception as e:
    #     error_msg = f"Error in human validation: {str(e)}"
    #     print(error_msg)
    #     # Fallback: use original keywords if validation fails
    #     fallback_keywords = state.get("seed_keywords", {})
    #     msg = {
    #         "role": "human",
    #         "content": "HITL error. Use fallback..."
    #     }
    #     update = {
    #         **state,
    #         "validated_keywords": fallback_keywords,
    #         "messages": state.get("messages", []) + [msg]
    #     }
    #     goto = "enhancement"
    #     return Command(goto=goto, update=update)


def _format_keywords_for_display(seed_keywords) -> str:
    """Format keywords for human-readable display."""
    if not seed_keywords:
        return "No keywords generated."
    
    formatted = []
    categories = ["problem_purpose", "object_system", "environment_field"]
    
    for category in categories:
        keywords = getattr(seed_keywords, category, [])
        if keywords:
            formatted.append(f"\n{category.replace('_', ' ').title()}:")
            for i, keyword in enumerate(keywords, 1):
                formatted.append(f"  {i}. {keyword}")
    
    return "\n".join(formatted)


def _process_human_input(response: Any, seed_keywords, state):
    """Process human input and return validated keywords."""
    if response["type"] == "accept":
        # Approve
        validated_keywords = {
            "problem_purpose": seed_keywords.problem_purpose,
            "object_system": seed_keywords.object_system,
            "environment_field": seed_keywords.environment_field
        }
        msg = {
            "role": "human",
            "content": "User accepted keywords."
        }
        update = {
            **state,
            "validated_keywords": validated_keywords,
            "messages": state.get("messages", []) + [msg]
        }
        goto = "enhancement"
        
    elif response["type"] == "edit":
        # Edit - cập nhật text và tiếp tục
        validated_keywords = response["args"]["keywords"]
        msg = {
            "role": "human",
            "content": "User edited keywords."
        }
        update = {
            **state,
            "validated_keywords": validated_keywords,
            "messages": state.get("messages", []) + [msg]
        }
        goto = "enhancement"
        
    elif response["type"] == "reject":
        # validated_keywords = response["args"]["keywords"]
        msg = {
            "role": "human",
            "content": "User rejected keywords."
        }
        update = {
            **state,
            "messages": state.get("messages", []) + [msg]
        }
        goto = "keyword_generation"
        
    # elif response["type"] == "response":
    #     # Feedback - ghi nhận và tiếp tục review
    #     feedback = response["args"]
    #     update = {
    #         "step_count": step_count,
    #         "review_history": state.review_history + [{
    #             "step": step_count,
    #             "action": "feedback",
    #             "comment": feedback,
    #             "timestamp": "2025-09-04 04:34:03"
    #         }]
    #     }
    #     goto = "process_feedback"
    
    else:
        raise ValueError(f"Unknown response type: {response['type']}")
    
    # return Command(goto=goto, update=update)
    return goto, update
