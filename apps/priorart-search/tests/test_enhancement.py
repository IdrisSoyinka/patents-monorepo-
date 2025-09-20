"""Tests for the enhancement node fallback behaviour."""

from src.patent_search_agent.nodes.enhancement import enhancement_node


class _FailingLLM:
    """LLM stub that always raises to trigger the fallback path."""

    def with_structured_output(self, schema):  # noqa: D401 - simple stub
        raise RuntimeError("LLM unavailable")


def test_enhancement_node_returns_original_keywords_on_failure():
    """The node should preserve validated keywords when enhancement fails."""

    state = {
        "validated_keywords": {
            "problem_purpose": ["alpha"],
            "object_system": ["beta"],
            "environment_field": ["gamma"],
        },
        "messages": ["existing-message"],
        "errors": [],
    }

    result = enhancement_node(state, _FailingLLM())

    assert result["enhanced_keywords"] == state["validated_keywords"]
    assert result["messages"] == state["messages"]
    assert result["errors"][-1] == "LLM unavailable"


def test_enhancement_node_handles_missing_validated_keywords():
    """Fallback should handle states without validated keywords."""

    state = {
        "validated_keywords": None,
    }

    result = enhancement_node(state, _FailingLLM())

    assert result["enhanced_keywords"] == {}
    assert result["errors"][-1] == "LLM unavailable"
