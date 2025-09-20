"""Enhancement Node - Expands keywords using web search for synonyms and related terms."""

import logging
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.language_models import BaseChatModel

from ..state import PatentSearchState
from ..tools.bs4_crawler import get_synonyms_context
from ..utils.prompts import KEYWORD_ENHANCEMENT_PROMPT
from ..schemas import EnhancedKeywords


def enhancement_node(state: PatentSearchState, llm: BaseChatModel) -> Dict[str, Any]:
    print("\U0001f50d Running enhancement_node...")
    """
    Enhance keywords by finding synonyms and related terms using structured output.
    
    Args:
        state: Current state containing validated_keywords
        llm: Language model for enhancement
        
    Returns:
        Updated state with enhanced_keywords, synonyms, and related_terms
    """
    try:
        validated_keywords = state.get("validated_keywords", {})

        
        # Create structured LLM
        structured_llm = llm.with_structured_output(EnhancedKeywords)
        
        # Collect web search context
        search_context = ""
        sources_used = []
        
        enhanced_keywords = {
            "problem_purpose": validated_keywords.get("problem_purpose", []).copy(),
            "object_system": validated_keywords.get("object_system", []).copy(),
            "environment_field": validated_keywords.get("environment_field", []).copy()
        }

        for category, keywords in validated_keywords.items():
            for keyword in keywords:
                search_context = get_synonyms_context(keyword)

                # Create enhancement prompt
                messages = [
                    SystemMessage(content=KEYWORD_ENHANCEMENT_PROMPT),
                    HumanMessage(content=f"""
Concept matrix:
{_format_concepts_for_enhancement(state.get("concept_matrix", {}).dict())}

Seed Keyword belong to {category} extracted from concept matrix:
{keyword}  

Web Search Context for Synonyms:
{search_context}


Enhance this keyword with synonyms and related terms optimized for patent searches using web search context.
Ensure enhanced keywords maintain technical accuracy and searchability. 
""")
                ]
                # Get structured enhancement
                response = structured_llm.invoke(messages)
                enhanced_keywords[category].extend(response.synonyms)
                enhanced_keywords[category].extend(response.related_terms)
                enhanced_keywords[category].extend(response.patent_terminology)
                enhanced_keywords[category].extend(response.technical_variations)

                msg = state.get("messages", []) + [AIMessage(content=f"{response}")]
        print(enhanced_keywords)
        return {
            **state,
            "enhanced_keywords": enhanced_keywords,
            "messages": msg
        }
        
    except Exception as e:
        # Structured error handling
        logging.error(f"Enhancement error: {str(e)}")
        logging.warning("Falling back to original keywords without enhancement.")
        
        # Fallback enhancement
        fallback_result = _fallback_enhancement(state.get("validated_keywords", {}))

        return {
            **state,
            "enhanced_keywords": fallback_result["enhanced"],
            "errors": state.get("errors", []) + [str(e)],
        }


def _format_concepts_for_enhancement(concept_dict: Dict[str, str]) -> str:
    """Format keywords for enhancement prompt."""
    formatted = []
    for category, concept in concept_dict.items():
        if concept:
            formatted.append(f"{category.replace('_', ' ').title()}: {concept}")
    return '\n'.join(formatted)


def _fallback_enhancement(validated_keywords: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Structured fallback enhancement when LLM fails.
    
    Args:
        validated_keywords: Original validated keywords
        
    Returns:
        Structured enhancement result
    """
    return validated_keywords
