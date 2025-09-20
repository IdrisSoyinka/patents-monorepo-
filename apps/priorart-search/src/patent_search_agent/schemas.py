"""Pydantic schemas for structured outputs in Patent Search Agent."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ConceptMatrix(BaseModel):
    """Structured concept matrix extracted from patent description."""
    
    problem_purpose: str = Field(
        description="Problems being solved and main purposes/objectives of the invention",
    )
    object_system: str = Field(
        description="Main technical components, devices, systems, or objects involved",
    )
    environment_field: str = Field(
        description="Technical field, application domain, or usage environment",
    )


class SeedKeywords(BaseModel):
    """Structured seed keywords generated from concept matrix."""
    
    problem_purpose: List[str] = Field(
        description="Search keywords related to problems and purposes",
        min_items=3,
        max_items=6
    )
    object_system: List[str] = Field(
        description="Search keywords related to technical objects and systems",
        min_items=3,
        max_items=6
    )
    environment_field: List[str] = Field(
        description="Search keywords related to technical fields and environments",
        min_items=3,
        max_items=6
    )


class EnhancedKeywords(BaseModel):
    """Enhanced keywords with synonyms and related terms."""
    synonyms: List[str] = Field(
        description="Terms with the same meaning with keyword",
    )
    related_terms: List[str] = Field(
        description="Closely related technical concepts for keyword",
    )
    patent_terminology: List[str] = Field(
        description="Formal patent language and standard industry terms for keyword",
    )
    technical_variations: List[str] = Field(
        description="Different ways to express the same concepts for keyword",
    )


class PatentSummary(BaseModel):
    """Patent summary results."""

    content: str = Field(
        description="Comprehensive technical summary of the patent",
        min_length=100,
        max_length=400,
    )


class SearchQueries(BaseModel):
    """Generated search queries for patent search."""
    
    queries: List[str] = Field(
        description="Generated search queries",
        min_items=5,
        max_items=8
    )


class PatentSearchResults(BaseModel):
    """Patent search results with metadata."""
    
    total_found: int = Field(
        description="Total number of patents found"
    )
    search_queries_used: List[str] = Field(
        description="Search queries that were executed"
    )
    patents: List[Dict[str, Any]] = Field(
        description="List of patent results with metadata"
    )
    execution_time: Optional[float] = Field(
        description="Time taken for search execution",
        default=None
    )


class SimilarityEvaluation(BaseModel):
    """Patent similarity evaluation results."""
    
    patent_id: str = Field(
        description="Patent identifier (number or URL)"
    )
    similarity_score: float = Field(
        description="Overall similarity score (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    technical_similarity: float = Field(
        description="Technical concept similarity score",
        ge=0.0,
        le=1.0
    )
    problem_domain_similarity: float = Field(
        description="Problem domain similarity score",
        ge=0.0,
        le=1.0
    )
    innovation_overlap: float = Field(
        description="Innovation overlap score",
        ge=0.0,
        le=1.0
    )
    justification: str = Field(
        description="Brief justification for the similarity scores"
    )


class FinalResults(BaseModel):
    """Final patent search and evaluation results."""
    
    input_summary: str = Field(
        description="Summary of the input patent description"
    )
    total_patents_found: int = Field(
        description="Total number of patents found and evaluated"
    )
    top_similar_patents: List[SimilarityEvaluation] = Field(
        description="Top similar patents ranked by similarity score",
        max_items=20
    )
    search_statistics: Dict[str, Any] = Field(
        description="Statistics about the search process"
    )
    recommendations: List[str] = Field(
        description="Recommendations for further prior art analysis"
    )
