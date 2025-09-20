"""Evaluation Node - Crawls and evaluates patent similarity."""

from typing import Dict, Any, List
from langchain_core.messages import HumanMessage

from ..state import PatentSearchState
from ..tools.patent_crawler import crawl_patent_details
from ..utils.helpers import calculate_similarity_score


def evaluation_node(state: PatentSearchState) -> Dict[str, Any]:
    print("\U0001f50d Running evaluation_node...")
    """
    Crawl patent details and evaluate similarity to input patent.
    
    This is a template implementation. The actual crawling and evaluation
    logic should be implemented based on existing source code.
    
    Args:
        state: Current state containing search_results and patent_urls
        
    Returns:
        Updated state with crawled_patents, similarity_scores, and final_results
    """
    try:
        search_results = state.get("search_results", [])
        patent_urls = state.get("patent_urls", [])
        patent_description = state.get("patent_description", "")
        
        if not search_results:
            return {
                **state,
                "crawled_patents": [],
                "similarity_scores": [],
                "final_results": [],
                "current_node": "evaluation",
                "messages": state.get("messages", []) + [
                    HumanMessage(content="No search results to evaluate")
                ]
            }
        
        # Crawl detailed information for each patent
        crawled_patents = []
        similarity_scores = []
        
        for result in search_results:
            try:
                # Crawl detailed patent information
                detailed_patent = _crawl_patent_result(result)
                crawled_patents.append(detailed_patent)
                
                # Calculate similarity score
                similarity = _calculate_patent_similarity(
                    patent_description, 
                    detailed_patent
                )
                similarity_scores.append({
                    "patent_id": detailed_patent.get("patent_number", "unknown"),
                    "similarity_score": similarity,
                    "title": detailed_patent.get("title", ""),
                    "url": detailed_patent.get("url", "")
                })
                
            except Exception as e:
                # Log error but continue with other patents
                error_msg = f"Error processing patent {result.get('patent_number', 'unknown')}: {str(e)}"
                print(f"Warning: {error_msg}")
        
        # Sort by similarity score and create final results
        similarity_scores.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # Create final results combining crawled data with similarity scores
        final_results = _create_final_results(crawled_patents, similarity_scores)
        
        return {
            **state,
            "crawled_patents": crawled_patents,
            "similarity_scores": similarity_scores,
            "final_results": final_results,
            "current_node": "evaluation",
            "messages": state.get("messages", []) + [
                HumanMessage(content=f"Evaluated {len(final_results)} patents. Top similarity: {similarity_scores[0]['similarity_score']:.2f}" if similarity_scores else "Evaluation completed with no results")
            ]
        }
        
    except Exception as e:
        error_msg = f"Error in patent evaluation: {str(e)}"
        return {
            **state,
            "errors": state.get("errors", []) + [error_msg],
            "current_node": "evaluation",
            "crawled_patents": [],
            "similarity_scores": [],
            "final_results": []
        }


def _crawl_patent_result(search_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crawl detailed information for a patent result.
    
    This is a template - should be replaced with your existing crawling logic.
    
    Args:
        search_result: Basic patent search result
        
    Returns:
        Detailed patent information
    """
    try:
        # Use existing patent crawler tool
        url = search_result.get("url", "")
        patent_number = search_result.get("patent_number", "")
        
        if url:
            detailed_info = crawl_patent_details(url)
        else:
            # Fallback to search result data
            detailed_info = search_result.copy()
        
        # Ensure required fields
        if "patent_number" not in detailed_info:
            detailed_info["patent_number"] = patent_number
        
        if "title" not in detailed_info:
            detailed_info["title"] = search_result.get("title", "")
        
        if "abstract" not in detailed_info:
            detailed_info["abstract"] = search_result.get("abstract", "")
        
        # Add metadata
        detailed_info["crawl_timestamp"] = _get_current_timestamp()
        detailed_info["source_query"] = search_result.get("search_query", "")
        
        return detailed_info
        
    except Exception as e:
        # Return original result if crawling fails
        return {
            **search_result,
            "crawl_error": str(e),
            "crawl_timestamp": _get_current_timestamp()
        }


def _calculate_patent_similarity(
    input_description: str, 
    patent_data: Dict[str, Any]
) -> float:
    """
    Calculate similarity between input description and patent.
    
    This is a template - should be replaced with your existing similarity logic.
    
    Args:
        input_description: Original patent description
        patent_data: Crawled patent data
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    try:
        # Use existing similarity calculation tool
        patent_text = _extract_patent_text(patent_data)
        similarity = calculate_similarity_score(input_description, patent_text)
        return similarity
        
    except Exception as e:
        # Fallback to simple text matching
        return _simple_similarity(input_description, patent_data)


def _extract_patent_text(patent_data: Dict[str, Any]) -> str:
    """
    Extract relevant text from patent data for similarity comparison.
    
    Args:
        patent_data: Patent information dictionary
        
    Returns:
        Combined text for similarity analysis
    """
    text_parts = []
    
    # Title
    if patent_data.get("title"):
        text_parts.append(patent_data["title"])
    
    # Abstract
    if patent_data.get("abstract"):
        text_parts.append(patent_data["abstract"])
    
    # Claims (if available)
    if patent_data.get("claims"):
        if isinstance(patent_data["claims"], list):
            text_parts.extend(patent_data["claims"])
        else:
            text_parts.append(str(patent_data["claims"]))
    
    # Description (if available)
    if patent_data.get("description"):
        text_parts.append(patent_data["description"])
    
    return " ".join(text_parts)


def _simple_similarity(input_description: str, patent_data: Dict[str, Any]) -> float:
    """
    Simple fallback similarity calculation based on keyword overlap.
    
    Args:
        input_description: Input patent description
        patent_data: Patent data dictionary
        
    Returns:
        Simple similarity score
    """
    try:
        # Extract words from input
        input_words = set(input_description.lower().split())
        
        # Extract words from patent
        patent_text = _extract_patent_text(patent_data)
        patent_words = set(patent_text.lower().split())
        
        # Calculate Jaccard similarity
        intersection = len(input_words.intersection(patent_words))
        union = len(input_words.union(patent_words))
        
        if union == 0:
            return 0.0
        
        return intersection / union
        
    except Exception:
        return 0.0


def _create_final_results(
    crawled_patents: List[Dict[str, Any]], 
    similarity_scores: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Create final results by combining crawled data with similarity scores.
    
    Args:
        crawled_patents: List of crawled patent data
        similarity_scores: List of similarity scores
        
    Returns:
        Combined final results
    """
    # Create lookup for patent data
    patent_lookup = {
        patent.get("patent_number", f"idx_{i}"): patent 
        for i, patent in enumerate(crawled_patents)
    }
    
    final_results = []
    
    for score_data in similarity_scores:
        patent_id = score_data["patent_id"]
        patent_data = patent_lookup.get(patent_id, {})
        
        # Combine data
        final_result = {
            **patent_data,
            "similarity_score": score_data["similarity_score"],
            "rank": len(final_results) + 1
        }
        
        final_results.append(final_result)
    
    return final_results


def _get_current_timestamp() -> str:
    """Get current timestamp as string."""
    from datetime import datetime
    return datetime.now().isoformat()
