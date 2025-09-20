"""Google Patents search tool using Google Custom Search API."""

import os
import requests
from typing import List, Dict, Any
from serpapi import GoogleSearch

def search_google_patents(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search Google Patents using Google Custom Search API.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        
    Returns:
        List of patent search results
    """
    try:
        serp_api_key = os.getenv("SERPAPI_API_KEY")
        if not serp_api_key:
            print("Warning: SerpAPI key not found, using fallback results")
            return _fallback_patent_results(query, max_results)
        params = {
            "api_key": serp_api_key,
            "engine": "google_patents",
            "q": f"({query})",
            "num": "10",
            "page": "1"
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Parse results
        parsed_results = []
        for item in results.get("items", []):
            patent_result = _parse_google_result(item)
            if patent_result:
                parsed_results.append(patent_result)

        return parsed_results

    except Exception as e:
        print(f"Error in Google Patents search: {str(e)}")
        return _fallback_patent_results(query, max_results)


def search_google_patents_advanced(
    query: str, 
    ipc_codes: List[str] = None,
    date_range: str = None,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Advanced Google Patents search with additional filters.
    
    Args:
        query: Base search query
        ipc_codes: IPC classification codes to include
        date_range: Date range filter (e.g., "2020..2024")
        max_results: Maximum results
        
    Returns:
        List of patent search results
    """
    try:
        # Build advanced query
        advanced_query = query
        
        # Add IPC codes if provided
        if ipc_codes:
            ipc_filter = " OR ".join(ipc_codes)
            advanced_query += f" ({ipc_filter})"
        
        # Add date range if provided
        if date_range:
            advanced_query += f" after:{date_range.split('..')[0]}"
            if ".." in date_range:
                advanced_query += f" before:{date_range.split('..')[1]}"
        
        return search_google_patents(advanced_query, max_results)
        
    except Exception as e:
        print(f"Error in advanced Google Patents search: {str(e)}")
        return search_google_patents(query, max_results)


def _parse_google_result(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a Google Custom Search result into patent information.
    
    Args:
        item: Google search result item
        
    Returns:
        Parsed patent information
    """
    try:
        url = item.get("link", "")
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        
        # Extract patent number from URL
        patent_number = _extract_patent_number(url)
        
        # Parse additional metadata if available
        meta_tags = item.get("pagemap", {}).get("metatags", [{}])
        meta = meta_tags[0] if meta_tags else {}
        
        result = {
            "title": title,
            "url": url,
            "patent_number": patent_number,
            "abstract": snippet,
            "description": snippet,  # Basic description from snippet
            "publication_date": meta.get("publication_date", ""),
            "source": "google_patents",
            "relevance_score": 1.0  # Default score
        }
        
        return result
        
    except Exception as e:
        print(f"Error parsing Google result: {str(e)}")
        return None


def _extract_patent_number(url: str) -> str:
    """
    Extract patent number from Google Patents URL.
    
    Args:
        url: Google Patents URL
        
    Returns:
        Patent number or empty string
    """
    try:
        # Google Patents URL format: https://patents.google.com/patent/US1234567
        if "/patent/" in url:
            return url.split("/patent/")[-1].split("?")[0]
        return ""
    except Exception:
        return ""



def _fallback_patent_results(query: str, max_results: int) -> List[Dict[str, Any]]:
    """
    Generate fallback patent results when API is not available.
    
    Args:
        query: Search query
        max_results: Number of results to generate
        
    Returns:
        List of mock patent results
    """
    # Generate mock results for development/testing
    results = []
    
    for i in range(min(max_results, 5)):
        result = {
            "title": f"Patent related to: {query} (Example {i+1})",
            "url": f"https://patents.google.com/patent/US{1000000 + i}",
            "patent_number": f"US{1000000 + i}",
            "abstract": f"This patent describes a method and system related to {query}. "
                       f"It includes technical innovations and improvements over existing solutions.",
            "description": f"Detailed description of patent {i+1} related to {query}",
            "publication_date": "2023-01-01",
            "source": "fallback",
            "relevance_score": 1.0 - (i * 0.1)
        }
        results.append(result)
    
    return results
