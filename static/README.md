# Static Assets for Patent Search Agent

This directory contains static assets including diagrams and documentation images.

## Workflow Diagram

The patent search workflow follows this sequence:

```
┌─────────────────┐
│  Start: Patent  │
│   Description   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ 1. Concept      │
│   Extraction    │ ──► Extract: Problem/Purpose, Object/System, Environment/Field
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ 2. Keyword      │
│   Generation    │ ──► Generate seed keywords from concepts
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ 3. Human        │
│   Validation    │ ──► User approves/edits/rejects keywords
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ 4. Enhancement  │
│     Phase       │ ──► Web search for synonyms & related terms
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ 5. IPC          │
│ Classification  │ ──► Get patent classification codes
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ 6. Query        │
│  Generation     │ ──► Create Boolean search queries
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ 7. Patent       │
│    Search       │ ──► Search Google Patents
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ 8. Crawl &      │
│   Evaluation    │ ──► Analyze similarity scores
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   Final         │
│   Results       │
└─────────────────┘
```

## Node Details

### 1. Concept Extraction
- **Input**: Patent description text
- **Process**: LLM analysis to extract key concepts
- **Output**: Concept matrix with three categories
- **Technology**: LangChain + LLM (Claude/GPT)

### 2. Keyword Generation  
- **Input**: Concept matrix
- **Process**: Generate search keywords per category
- **Output**: Seed keywords dictionary
- **Technology**: LLM-based keyword generation

### 3. Human Validation
- **Input**: Seed keywords
- **Process**: Human-in-the-loop review
- **Output**: Validated keywords
- **Technology**: LangGraph human interrupts

### 4. Enhancement Phase
- **Input**: Validated keywords
- **Process**: Web search for expansion
- **Output**: Enhanced keywords with synonyms
- **Technology**: Tavily Search API + LLM

### 5. IPC Classification
- **Input**: Patent description + web context
- **Process**: Generate summary and get IPC codes
- **Output**: IPC classification codes
- **Technology**: IPCCAT API + Tavily Search

### 6. Query Generation
- **Input**: Enhanced keywords + IPC codes
- **Process**: Create Boolean search queries
- **Output**: Optimized search queries
- **Technology**: LLM-based query construction

### 7. Patent Search
- **Input**: Search queries
- **Process**: Search patent databases
- **Output**: Patent search results
- **Technology**: Google Patents via Custom Search API

### 8. Crawl & Evaluation
- **Input**: Patent URLs and metadata
- **Process**: Extract details and compute similarity
- **Output**: Ranked similar patents
- **Technology**: Web crawling + similarity algorithms

## Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                    LangGraph                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │    Node     │  │    Node     │  │    Node     │   │
│  │     1       │─▶│     2       │─▶│     3       │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
│           │               │               │          │
│           ▼               ▼               ▼          │
│  ┌─────────────────────────────────────────────────┐ │
│  │              Shared State                       │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────┐
│                   External APIs                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   Tavily    │  │   Google    │  │   IPCCAT    │   │
│  │   Search    │  │   Patents   │  │     API     │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
└──────────────────────────────────────────────────────┘
```

## Human-in-the-Loop Integration

The system implements human validation using LangGraph's interrupt mechanism:

```
┌─────────────────┐
│ Keywords Ready  │
│ for Validation  │
└─────────┬───────┘
          │
          ▼
    ┌──────────┐
    │ Interrupt│ ──► Present keywords to user
    │ Workflow │
    └─────┬────┘
          │
          ▼
┌─────────────────┐
│ User Action:    │
│ • Approve       │ ──► Continue to enhancement
│ • Edit          │ ──► Apply changes, then continue
│ • Reject        │ ──► Regenerate keywords
└─────────────────┘
```

## Technology Stack

- **Workflow Engine**: LangGraph
- **LLM Models**: Anthropic Claude, OpenAI GPT
- **Web Search**: Tavily API
- **Patent Search**: Google Custom Search API  
- **IPC Classification**: IPCCAT API
- **Web Crawling**: BeautifulSoup + Requests
- **State Management**: TypedDict + LangGraph State
- **Development**: Python 3.11+, Poetry

## Configuration

The system supports flexible configuration through:

1. **Environment Variables** (.env)
2. **LangGraph Configuration** (langgraph.json)
3. **Runtime Parameters** (when invoking)

## Deployment Options

- **Local Development**: Run with Python + Poetry
- **LangGraph Studio**: Interactive development and debugging
- **LangGraph Cloud**: Production deployment
- **Custom Deployment**: Docker, AWS, etc.

## Error Handling

Each node implements comprehensive error handling:

```
try:
    # Node processing logic
    result = process_data(state)
    return updated_state(result)
except Exception as e:
    return error_state(e)
```

Errors are captured in the state and can trigger:
- Fallback processing
- Alternative workflows  
- User notifications
- Retry mechanisms
