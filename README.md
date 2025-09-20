# Patent Search Multi-Agent System

A multi-agent system for patent prior art search using LangGraph. This system processes patent descriptions and finds similar patents through a comprehensive search workflow.

## Overview

The system consists of 8 specialized agents that work together to analyze patent descriptions and find similar patents:

1. **Concept Extraction**: Extracts key concepts from patent descriptions
2. **Keyword Generation**: Generates seed keywords from extracted concepts
3. **Human-in-the-Loop Validation**: Allows user approval/editing of keywords
4. **Enhancement Phase**: Expands keywords using web search
5. **IPC Classification**: Gets IPC codes for the patent
6. **Query Generation**: Creates Boolean search queries
7. **Patent Search**: Searches for patents using Google Patents
8. **Crawl and Evaluation**: Crawls and evaluates found patents

## Architecture

![Patent Search Workflow](static/workflow.png)

## Getting Started

### Prerequisites

- Python 3.11+
- Poetry for dependency management
- API keys for various services

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd patent-search-agent
```

2. Install dependencies:
```bash
poetry install
```

3. Set up environment variables:
```bash
cp .env.example .env
```

4. Configure your API keys in `.env`:
   - `ANTHROPIC_API_KEY`: For Claude models
   - `TAVILY_API_KEY`: For web search
   - `GOOGLE_API_KEY`: For Google Patents search
   - `GOOGLE_CSE_ID`: Google Custom Search Engine ID
   - `IPCCAT_API_URL`: IPC classification service

### Usage

#### Using LangGraph Studio

1. Open the project in LangGraph Studio
2. Input your patent description in the `patent_description` field
3. Run the workflow and interact with the human-in-the-loop validation

#### Using Python API

```python
from src.patent_search_agent.graph import create_graph

# Create the graph
app = create_graph()

# Run the workflow
result = app.invoke({
    "patent_description": "Your patent description here...",
    "max_results": 10
})
```

## Configuration

The system can be configured through:

1. **Environment variables** (`.env` file)
2. **LangGraph configuration** (`langgraph.json`)
3. **Runtime parameters** (when invoking the graph)

### Key Configuration Options

- `model`: LLM model to use (default: "anthropic/claude-3-5-sonnet-20240620")
- `max_results`: Maximum number of patents to find
- `search_depth`: Depth of patent search
- `similarity_threshold`: Minimum similarity score for results

## System Components

### State Management

The system uses a centralized state object that flows through all nodes:

```python
class PatentSearchState(TypedDict):
    patent_description: str
    concept_matrix: Dict[str, Any]
    seed_keywords: Dict[str, List[str]]
    validated_keywords: Dict[str, List[str]]
    enhanced_keywords: Dict[str, List[str]]
    ipc_codes: List[str]
    search_queries: List[str]
    search_results: List[Dict[str, Any]]
    final_results: List[Dict[str, Any]]
    # ... other fields
```

### Nodes

Each node is a specialized function that:
1. Takes the current state as input
2. Performs its specific task
3. Updates and returns the modified state

### Human-in-the-Loop

The system includes a human validation node where users can:
- Approve generated keywords
- Edit keywords
- Reject keywords
- Add new keywords

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

```bash
poetry run black src/
poetry run flake8 src/
```

### Type Checking

```bash
poetry run mypy src/
```

## Project Structure

```
patent-search-agent/
├── src/
│   └── patent_search_agent/
│       ├── __init__.py
│       ├── graph.py              # Main workflow graph
│       ├── state.py              # State definitions
│       ├── nodes/                # Individual agent nodes
│       │   ├── __init__.py
│       │   ├── concept_extraction.py
│       │   ├── keyword_generation.py
│       │   ├── human_validation.py
│       │   ├── enhancement.py
│       │   ├── ipc_classification.py
│       │   ├── query_generation.py
│       │   ├── patent_search.py
│       │   └── evaluation.py
│       ├── tools/                # External API tools
│       │   ├── __init__.py
│       │   ├── tavily_search.py
│       │   ├── google_patents.py
│       │   ├── ipccat_api.py
│       │   └── patent_crawler.py
│       └── utils/                # Utility functions
│           ├── __init__.py
│           ├── prompts.py
│           └── helpers.py
├── tests/
├── static/
├── .env.example
├── .gitignore
├── langgraph.json
├── pyproject.toml
└── README.md
```

## API Reference

### Main Graph

The main graph is defined in `src/patent_search_agent/graph.py` and can be customized by:

1. Adding new nodes
2. Modifying the workflow edges
3. Updating the state schema
4. Configuring conditional routing

### Tools

The system includes several tools for external API integration:

- **Tavily Search**: Web search for keyword enhancement
- **Google Patents API**: Patent search functionality
- **IPCCAT API**: IPC code classification
- **Patent Crawler**: Extract detailed patent information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
