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
        validated_keywords = _ensure_keywords_dict(state.get("validated_keywords"))

        # Create structured LLM
        structured_llm = llm.with_structured_output(EnhancedKeywords)

        # Collect web search context
        enhanced_keywords = {
            "problem_purpose": validated_keywords.get("problem_purpose", []).copy(),
            "object_system": validated_keywords.get("object_system", []).copy(),
            "environment_field": validated_keywords.get("environment_field", []).copy(),
        }

        messages = list(state.get("messages", []))
        concept_matrix = _concept_matrix_to_dict(state.get("concept_matrix"))
        formatted_concepts = _format_concepts_for_enhancement(concept_matrix)

        for category, keywords in validated_keywords.items():
            for keyword in keywords:
                search_context = get_synonyms_context(keyword)

                human_prompt = f"""
Concept matrix:
{formatted_concepts}

Seed Keyword belong to {category} extracted from concept matrix:
{keyword}

Web Search Context for Synonyms:
{search_context}


Enhance this keyword with synonyms and related terms optimized for patent searches using web search context.
Ensure enhanced keywords maintain technical accuracy and searchability.
"""

                prompt_messages = [
                    SystemMessage(content=KEYWORD_ENHANCEMENT_PROMPT),
                    HumanMessage(content=human_prompt),
                ]

                # Get structured enhancement
                response = structured_llm.invoke(prompt_messages)
                enhanced_keywords.setdefault(category, [])
                enhanced_keywords[category].extend(response.synonyms)
                enhanced_keywords[category].extend(response.related_terms)
                enhanced_keywords[category].extend(response.patent_terminology)
                enhanced_keywords[category].extend(response.technical_variations)

                messages.append(AIMessage(content=str(response)))

        print(enhanced_keywords)
        return {
            **state,
            "enhanced_keywords": enhanced_keywords,
            "messages": messages,
        }

    except Exception as e:
        # Structured error handling
        logging.error(f"Enhancement error: {str(e)}")
        logging.warning("Falling back to original keywords without enhancement.")

        # Fallback enhancement
        validated_keywords = _ensure_keywords_dict(state.get("validated_keywords"))
        fallback_result = _fallback_enhancement(validated_keywords)

        errors = list(state.get("errors", []))
        errors.append(str(e))

        return {
            **state,
            "enhanced_keywords": fallback_result,
            "errors": errors,
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


def _ensure_keywords_dict(keywords: Any) -> Dict[str, List[str]]:
    """Normalise keyword structures to a plain dictionary."""
    if not keywords:
        return {}
    if hasattr(keywords, "model_dump"):
        return keywords.model_dump()
    if hasattr(keywords, "dict"):
        return keywords.dict()
    if isinstance(keywords, dict):
        return keywords
    return {}


def _concept_matrix_to_dict(concept_matrix: Any) -> Dict[str, str]:
    """Convert concept matrix object into a dictionary for formatting."""
    if not concept_matrix:
        return {}
    if hasattr(concept_matrix, "model_dump"):
        return concept_matrix.model_dump()
    if hasattr(concept_matrix, "dict"):
        return concept_matrix.dict()
    if isinstance(concept_matrix, dict):
        return concept_matrix
    return {}
