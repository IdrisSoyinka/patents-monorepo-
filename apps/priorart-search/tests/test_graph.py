"""Test the main graph workflow."""

import pytest
from src.patent_search_agent.graph import create_graph, run_patent_search
from src.patent_search_agent.state import PatentSearchState


class TestGraphWorkflow:
    """Test the main workflow graph."""
    
    def test_create_graph(self):
        """Test graph creation."""
        graph = create_graph()
        assert graph is not None
        
    def test_graph_compilation(self):
        """Test that graph compiles without errors."""
        try:
            graph = create_graph()
            assert hasattr(graph, 'invoke')
        except Exception as e:
            pytest.fail(f"Graph compilation failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_basic_workflow(self, sample_patent_description, mock_env_vars):
        """Test basic workflow execution."""
        # This would need mocking of external APIs for full testing
        try:
            result = run_patent_search(
                patent_description=sample_patent_description,
                max_results=3,
                model_name="anthropic/claude-3-5-sonnet-20240620"
            )
            
            # Basic structure checks
            assert isinstance(result, dict)
            assert "patent_description" in result
            assert result["patent_description"] == sample_patent_description
            
        except Exception as e:
            # Expected to fail without real API keys
            assert "API" in str(e) or "key" in str(e) or "authentication" in str(e).lower()


class TestWorkflowNodes:
    """Test individual workflow components."""
    
    def test_workflow_state_structure(self, test_state):
        """Test that state structure is maintained."""
        from tests.conftest import assert_valid_state_structure
        assert_valid_state_structure(test_state)
    
    def test_state_updates(self, test_state):
        """Test state update functionality."""
        # Test adding concept matrix
        test_state["concept_matrix"] = {
            "problem_purpose": ["test"],
            "object_system": ["test"],
            "environment_field": ["test"]
        }
        
        assert "concept_matrix" in test_state
        assert isinstance(test_state["concept_matrix"], dict)
        
    def test_error_handling(self, test_state):
        """Test error handling in state."""
        test_state["errors"] = ["Test error"]
        assert len(test_state["errors"]) == 1
        assert test_state["errors"][0] == "Test error"


class TestWorkflowConditions:
    """Test workflow conditional logic."""
    
    def test_validation_condition(self):
        """Test human validation condition logic."""
        from src.patent_search_agent.graph import should_continue_validation
        
        # Test incomplete validation
        state_incomplete = {"validation_complete": False}
        result = should_continue_validation(state_incomplete)
        assert result == "human_validation"
        
        # Test complete validation
        state_complete = {"validation_complete": True}
        result = should_continue_validation(state_complete)
        assert result == "enhancement"
    
    def test_workflow_condition(self):
        """Test workflow continuation condition."""
        from src.patent_search_agent.graph import should_continue_workflow
        
        # Test with results
        state_with_results = {"search_results": [{"title": "test"}]}
        result = should_continue_workflow(state_with_results)
        assert result == "evaluation"
        
        # Test without results
        state_no_results = {"search_results": []}
        result = should_continue_workflow(state_no_results)
        assert result == "__end__"
