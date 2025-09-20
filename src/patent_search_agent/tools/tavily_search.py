"""Tavily search tool for web research and keyword enhancement."""

import os
from typing import List, Dict, Any
from tavily import TavilyClient

def search_web_for_summary(description: str) -> str:
    """
    Search web for additional context to create comprehensive patent summary.
    
    Args:
        description: Original patent description
        
    Returns:
        Web search results for summary context
    """
    try:
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            return _fallback_summary_context(description)

        client = TavilyClient(api_key=tavily_api_key)
        
        # Create search query focusing on technical aspects
        query = f"Summary following patent description:\n {description}"

        # Search with Tavily
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=3
        )
        
        # Format results for summary context
        formatted_results = []
        for result in response.get("results", []):
            title = result.get("title", "")
            content = result.get("content", "")
            
            if title and content:
                formatted_results.append(f"Source: {title}")
                formatted_results.append(f"Info: {content[:1000]}...")
                formatted_results.append("---")
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        print(f"Error in Tavily search for summary: {str(e)}")
        return _fallback_summary_context(description)

def _fallback_summary_context(description: str) -> str:
    """
    Fallback context for patent summary when Tavily API is not available.
    
    Args:
        key_terms: Key terms from patent
        
    Returns:
        Basic context string
    """
    return f""
