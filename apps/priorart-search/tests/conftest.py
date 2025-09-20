"""Test configuration and fixtures for Patent Search Agent."""

import pytest
import os
from typing import Dict, Any


@pytest.fixture
def sample_patent_description():
    """Sample patent description for testing."""
    return """
    A smart water bottle system that monitors hydration levels using IoT sensors.
    The bottle includes temperature sensors, volume measurement capabilities,
    and connects to a mobile app via Bluetooth to track daily water intake
    and provide personalized hydration recommendations based on user activity
    and environmental conditions.
    """


@pytest.fixture
def sample_concept_matrix():
    """Sample concept matrix for testing."""
    return {
        "problem_purpose": ["monitoring", "measurement", "tracking"],
        "object_system": ["sensor", "container", "mobile_application"],
        "environment_field": ["iot", "healthcare", "mobile_technology"]
    }


@pytest.fixture
def sample_keywords():
    """Sample keywords for testing."""
    return {
        "problem_purpose": ["hydration monitoring", "fluid intake tracking", "health monitoring"],
        "object_system": ["smart bottle", "iot sensor", "mobile app", "bluetooth device"],
        "environment_field": ["iot healthcare", "mobile health", "wearable technology"]
    }


@pytest.fixture
def sample_search_results():
    """Sample patent search results for testing."""
    return [
        {
            "title": "Smart Water Bottle with Sensors",
            "url": "https://patents.google.com/patent/US1234567",
            "patent_number": "US1234567",
            "abstract": "A water bottle with built-in sensors for monitoring consumption",
            "publication_date": "2023-01-01",
            "inventors": "John Doe, Jane Smith",
            "assignee": "Smart Bottle Corp",
            "ipc_codes": ["G06F", "A61B"],
            "search_query": '"smart bottle" AND "sensor"'
        },
        {
            "title": "IoT Health Monitoring Device",
            "url": "https://patents.google.com/patent/US7654321",
            "patent_number": "US7654321",
            "abstract": "IoT device for health parameter monitoring",
            "publication_date": "2022-12-15",
            "inventors": "Alice Johnson",
            "assignee": "Health Tech Inc",
            "ipc_codes": ["H04W", "A61B"],
            "search_query": '"iot" AND "health monitoring"'
        }
    ]


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    class MockResponse:
        def __init__(self, content: str):
            self.content = content
    
    return MockResponse


@pytest.fixture
def test_state():
    """Basic test state for workflow testing."""
    return {
        "patent_description": "Test patent description",
        "max_results": 5,
        "messages": [],
        "validation_complete": False,
        "current_node": None,
        "next_node": None,
        "errors": []
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    test_env = {
        "ANTHROPIC_API_KEY": "test_anthropic_key",
        "OPENAI_API_KEY": "test_openai_key", 
        "TAVILY_API_KEY": "test_tavily_key",
        "GOOGLE_API_KEY": "test_google_key",
        "GOOGLE_CSE_ID": "test_cse_id",
        "IPCCAT_API_URL": "https://test-ipccat-api.com"
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    
    return test_env


# Test utilities

def create_test_patent_data() -> Dict[str, Any]:
    """Create test patent data structure."""
    return {
        "patent_number": "US1234567",
        "title": "Test Patent Title",
        "abstract": "Test patent abstract describing the invention",
        "description": "Detailed test patent description",
        "claims": ["Claim 1: A method for...", "Claim 2: The method of claim 1..."],
        "inventors": "Test Inventor",
        "assignee": "Test Company",
        "publication_date": "2023-01-01",
        "ipc_codes": ["G06F", "H04W"],
        "url": "https://patents.google.com/patent/US1234567"
    }


def assert_valid_state_structure(state: Dict[str, Any]) -> None:
    """Assert that state has valid structure."""
    required_fields = ["patent_description", "messages"]
    for field in required_fields:
        assert field in state, f"Missing required field: {field}"
    
    # Check messages is a list
    assert isinstance(state["messages"], list), "messages must be a list"
    
    # Check current_node is string if present
    if "current_node" in state and state["current_node"] is not None:
        assert isinstance(state["current_node"], str), "current_node must be string"
