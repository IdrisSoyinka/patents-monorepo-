"""State definition for the Patent Search Agent."""

from typing import Dict, List, Any, Optional, Annotated
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from .schemas import (
    ConceptMatrix, SeedKeywords, EnhancedKeywords, SearchQueries
)


class PatentSearchState(TypedDict):
    """State for the patent search workflow."""
    
    # Input
    patent_description: str
    max_results: Optional[int]
    
    # Messages for communication between nodes
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Node 1: Concept Extraction - Structured Output
    concept_matrix: Optional[ConceptMatrix]
    
    # Node 2: Keyword Generation - Structured Output  
    seed_keywords: Optional[SeedKeywords]
    
    # Node 3: Human Validation
    validated_keywords: Optional[SeedKeywords]
    
    # Node 4: Enhancement Phase - Structured Output
    enhanced_keywords: Optional[SeedKeywords]
    
    # Node 5: IPC Classification - Structured Output
    ipc_codes: Optional[str]
    
    # Node 6: Query Generation - Structured Output
    search_queries: Optional[SearchQueries]
    
    # Node 7: Patent Search - Structured Output
    # search_results: Optional[PatentSearchResults]
    
    # # Node 8: Crawl and Evaluation - Structured Output
    # similarity_evaluations: Optional[List[SimilarityEvaluation]]
    # final_results: Optional[FinalResults]
    
    # Error handling
    errors: Optional[List[str]]
