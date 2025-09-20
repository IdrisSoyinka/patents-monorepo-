"""Patent Search Node - Searches for patents using Google Patents."""

from typing import Dict, Any, List
from langchain_core.messages import HumanMessage

from ..state import PatentSearchState
from ..tools.google_patents import search_google_patents


def patent_search_node(state: PatentSearchState) -> Dict[str, Any]:
    print("\U0001f50d Running patent_search_node...")
    """
    Search for patents using generated queries on Google Patents.
    
    Args:
        state: Current state containing search queries
        
    Returns:
        Updated state with search_results and patent_urls
    """
    try:
        # Get queries from state
        final_queries = state.get("final_queries", [])
        search_queries = state.get("search_queries", [])
        boolean_queries = state.get("boolean_queries", [])
        
        # Use final_queries if available, otherwise combine others
        queries_to_use = final_queries or (search_queries + boolean_queries)
        
        if not queries_to_use:
            raise ValueError("No search queries available")
        
        max_results = state.get("max_results", 10)
        
        # Search with each query
        all_results = []
        patent_urls = []
        
        for query in queries_to_use:
            try:
                results = search_google_patents(
                    query=query,
                    max_results=min(5, max_results // len(queries_to_use) + 1)
                )
                
                # Add query info to results
                for result in results:
                    result["search_query"] = query
                    all_results.append(result)
                    
                    if "url" in result:
                        patent_urls.append(result["url"])
                        
            except Exception as e:
                # Log error but continue with other queries
                error_msg = f"Error searching with query '{query}': {str(e)}"
                print(f"Warning: {error_msg}")
        
        # Remove duplicates and limit results
        unique_results = _deduplicate_results(all_results)
        limited_results = unique_results[:max_results]
        
        return {
            **state,
            "search_results": limited_results,
            "patent_urls": list(set(patent_urls)),
            "current_node": "patent_search",
            "next_node": "evaluation",
            "messages": state.get("messages", []) + [
                HumanMessage(content=f"Found {len(limited_results)} patent results from {len(queries_to_use)} queries")
            ]
        }
        
    except Exception as e:
        error_msg = f"Error in patent search: {str(e)}"
        return {
            **state,
            "errors": state.get("errors", []) + [error_msg],
            "current_node": "patent_search",
            "search_results": [],  # Empty results to continue workflow
            "patent_urls": []
        }


def _deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate patent results based on patent number or URL.
    
    Args:
        results: List of patent search results
        
    Returns:
        Deduplicated list of results
    """
    seen = set()
    unique_results = []
    
    for result in results:
        # Create identifier for deduplication
        identifier = None
        
        # Try patent number first
        if "patent_number" in result and result["patent_number"]:
            identifier = result["patent_number"]
        # Fall back to URL
        elif "url" in result and result["url"]:
            identifier = result["url"]
        # Fall back to title
        elif "title" in result and result["title"]:
            identifier = result["title"].lower().strip()
        
        # Only add if not seen before
        if identifier and identifier not in seen:
            seen.add(identifier)
            unique_results.append(result)
        elif not identifier:
            # Add results without identifiers (shouldn't happen but just in case)
            unique_results.append(result)
    
    return unique_results


def _score_relevance(result: Dict[str, Any], query: str) -> float:
    """
    Score the relevance of a patent result to the search query.
    
    Args:
        result: Patent search result
        query: Search query used
        
    Returns:
        Relevance score (0.0 to 1.0)
    """
    score = 0.0
    query_lower = query.lower()
    
    # Extract query terms (remove operators and quotes)
    query_terms = []
    for term in query_lower.split():
        clean_term = term.strip('"()').replace('and', '').replace('or', '').replace('not', '')
        if clean_term and len(clean_term) > 2:
            query_terms.append(clean_term)
    
    # Score based on title matches
    title = result.get("title", "").lower()
    if title:
        title_matches = sum(1 for term in query_terms if term in title)
        score += (title_matches / len(query_terms)) * 0.4
    
    # Score based on abstract matches
    abstract = result.get("abstract", "").lower()
    if abstract:
        abstract_matches = sum(1 for term in query_terms if term in abstract)
        score += (abstract_matches / len(query_terms)) * 0.3
    
    # Score based on inventors/assignee matches
    inventors = result.get("inventors", "").lower()
    assignee = result.get("assignee", "").lower()
    if inventors or assignee:
        inventor_matches = sum(1 for term in query_terms if term in inventors + assignee)
        score += (inventor_matches / len(query_terms)) * 0.1
    
    # Bonus for recent patents
    publication_date = result.get("publication_date", "")
    if publication_date:
        try:
            year = int(publication_date[:4])
            if year >= 2020:
                score += 0.1
            elif year >= 2015:
                score += 0.05
        except (ValueError, IndexError):
            pass
    
    # Bonus for having IPC codes that match
    ipc_codes = result.get("ipc_codes", [])
    if "ipc:" in query_lower and ipc_codes:
        score += 0.1
    
    return min(score, 1.0)  # Cap at 1.0
