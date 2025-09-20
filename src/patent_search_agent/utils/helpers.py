"""Helper functions for the Patent Search Agent."""

from typing import Dict, Any, List
import re
from difflib import SequenceMatcher


def calculate_similarity_score(text1: str, text2: str) -> float:
    """
    Calculate similarity score between two text documents.
    
    This is a template implementation that should be replaced with
    your existing similarity calculation logic.
    
    Args:
        text1: First text document
        text2: Second text document
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    try:
        # Simple implementation using SequenceMatcher
        # In practice, you would use more sophisticated methods like:
        # - TF-IDF cosine similarity
        # - Sentence embeddings (BERT, etc.)
        # - Custom patent similarity algorithms
        
        if not text1 or not text2:
            return 0.0
        
        # Normalize texts
        text1_norm = _normalize_text(text1)
        text2_norm = _normalize_text(text2)
        
        # Calculate sequence similarity
        sequence_sim = SequenceMatcher(None, text1_norm, text2_norm).ratio()
        
        # Calculate keyword overlap similarity
        keyword_sim = _calculate_keyword_similarity(text1_norm, text2_norm)
        
        # Combine similarities (weighted average)
        final_similarity = (sequence_sim * 0.3 + keyword_sim * 0.7)
        
        return min(final_similarity, 1.0)
        
    except Exception as e:
        print(f"Error calculating similarity: {str(e)}")
        return 0.0


def _normalize_text(text: str) -> str:
    """Normalize text for similarity comparison."""
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep alphanumeric and spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'among', 'this', 'that',
        'these', 'those', 'is', 'was', 'are', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'said', 'says'
    }
    
    words = text.split()
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    return ' '.join(filtered_words)


def _calculate_keyword_similarity(text1: str, text2: str) -> float:
    """Calculate similarity based on keyword overlap."""
    try:
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
        
    except Exception:
        return 0.0


def extract_technical_terms(text: str) -> List[str]:
    """
    Extract technical terms from patent text.
    
    Args:
        text: Input text
        
    Returns:
        List of technical terms
    """
    try:
        # Simple technical term extraction
        # In practice, this could use NLP libraries or domain-specific dictionaries
        
        words = text.lower().split()
        
        # Filter for potential technical terms
        technical_terms = []
        
        for word in words:
            # Clean word
            clean_word = re.sub(r'[^\w]', '', word)
            
            # Criteria for technical terms
            if (len(clean_word) > 4 and 
                not clean_word.isdigit() and
                _is_likely_technical_term(clean_word)):
                technical_terms.append(clean_word)
        
        # Remove duplicates and return
        return list(set(technical_terms))
        
    except Exception:
        return []


def _is_likely_technical_term(word: str) -> bool:
    """Check if a word is likely a technical term."""
    # Simple heuristics for technical terms
    technical_patterns = [
        r'.*tion$',  # -tion endings (function, detection, etc.)
        r'.*ment$',  # -ment endings (measurement, etc.)
        r'.*ing$',   # -ing endings (processing, etc.)
        r'.*ic$',    # -ic endings (electronic, etc.)
        r'.*ology$', # -ology endings (technology, etc.)
        r'.*ware$',  # -ware endings (software, hardware)
    ]
    
    # Check for technical patterns
    for pattern in technical_patterns:
        if re.match(pattern, word):
            return True
    
    # Check for compound technical words
    if any(tech_part in word for tech_part in ['tech', 'system', 'device', 'sensor', 'data']):
        return True
    
    return False


def format_patent_results(results: List[Dict[str, Any]]) -> str:
    """
    Format patent search results for display.
    
    Args:
        results: List of patent result dictionaries
        
    Returns:
        Formatted string representation
    """
    if not results:
        return "No patent results found."
    
    formatted_lines = []
    formatted_lines.append(f"Found {len(results)} patent results:\n")
    
    for i, result in enumerate(results, 1):
        title = result.get("title", "Unknown Title")
        patent_number = result.get("patent_number", "Unknown")
        similarity = result.get("similarity_score", 0.0)
        url = result.get("url", "")
        
        formatted_lines.append(f"{i}. {title}")
        formatted_lines.append(f"   Patent: {patent_number}")
        formatted_lines.append(f"   Similarity: {similarity:.2f}")
        if url:
            formatted_lines.append(f"   URL: {url}")
        formatted_lines.append("")
    
    return "\n".join(formatted_lines)


def validate_ipc_code(ipc_code: str) -> bool:
    """
    Validate IPC code format.
    
    Args:
        ipc_code: IPC code to validate
        
    Returns:
        True if valid format
    """
    if not ipc_code:
        return False
    
    # IPC code pattern: Letter + 2 digits + Letter + optional digits/slashes
    pattern = r'^[A-H]\d{2}[A-Z]\d*(?:/\d+)*$'
    return bool(re.match(pattern, ipc_code.upper()))


def clean_search_query(query: str) -> str:
    """
    Clean and validate search query.
    
    Args:
        query: Raw search query
        
    Returns:
        Cleaned search query
    """
    if not query:
        return ""
    
    # Remove excessive whitespace
    query = re.sub(r'\s+', ' ', query.strip())
    
    # Balance quotes
    quote_count = query.count('"')
    if quote_count % 2 != 0:
        query += '"'  # Add closing quote if unbalanced
    
    # Basic validation for Boolean operators
    query = re.sub(r'\s+(AND|OR|NOT)\s+', r' \1 ', query, flags=re.IGNORECASE)
    
    return query


def merge_keyword_lists(list1: List[str], list2: List[str]) -> List[str]:
    """
    Merge two keyword lists, removing duplicates and maintaining order.
    
    Args:
        list1: First keyword list
        list2: Second keyword list
        
    Returns:
        Merged list without duplicates
    """
    if not list1:
        return list2 or []
    if not list2:
        return list1
    
    seen = set()
    merged = []
    
    # Add from first list
    for keyword in list1:
        if keyword.lower() not in seen:
            merged.append(keyword)
            seen.add(keyword.lower())
    
    # Add from second list
    for keyword in list2:
        if keyword.lower() not in seen:
            merged.append(keyword)
            seen.add(keyword.lower())
    
    return merged


def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    Truncate text to maximum length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


def count_tokens_estimate(text: str) -> int:
    """
    Estimate token count for text (rough approximation).
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    # Rough estimation: ~4 characters per token
    return len(text) // 4
