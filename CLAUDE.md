# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an ACP (Agent Communication Protocol) demonstration project that showcases multi-agent email classification and response generation using CrewAI, OpenAI, and the ACP SDK.

## Key Commands

### Environment Setup
```bash
# Install dependencies using uv
uv sync

# Alternative: Install with pip
pip install -r requirements.txt
```

### Running the Application
```bash
# Start all three ACP agent servers (run in separate terminals)
python src/email_classifier_crew/acp_server.py    # Port 8002 - Email Classification
python src/strategy_agent/acp_server.py           # Port 8003 - Strategy Planning  
python src/response_generator/acp_server.py       # Port 8004 - Response Generation

# Run the complete end-to-end orchestrator
python src/orchestrator/main.py                   # Full workflow orchestration

# Test individual agents
python src/email_classifier_crew/acp_server.py test
python src/strategy_agent/acp_server.py test
python src/response_generator/acp_server.py test

# Process a single email via orchestrator
python src/orchestrator/main.py single "Subject" "Email content" "Sender Name" "sender@email.com"
```

### Testing
```bash
# Test individual components directly
python src/email_classifier_crew/main.py      # CrewAI email classification
python src/strategy_agent/main.py             # LangGraph strategy planning
python src/response_generator/main.py         # OpenAI response generation
python src/orchestrator/main.py               # Complete end-to-end workflow

# Run tests if available
python -m pytest tests/ -v
```

## Architecture

### Core Components

1. **Email Classification Agent** (`src/email_classifier_crew/`)
   - **ACP Server**: `acp_server.py` - Wraps CrewAI crew for ACP communication (port 8002)
   - **CrewAI Workflow**: `crew.py` - Uses GPT-4o-mini for email classification
   - **Categories**: sales, support, spam, personal, urgent
   - **Output**: Structured JSON with confidence scores and reasoning

2. **Strategy Planning Agent** (`src/strategy_agent/`)
   - **ACP Server**: `acp_server.py` - Wraps LangGraph workflow for ACP communication (port 8003)
   - **LangGraph Workflow**: `workflow.py` - Uses GPT-4o-mini for strategy planning
   - **Strategies**: immediate, delayed, escalate, auto_reply
   - **Output**: Strategy recommendations with response templates and next steps

3. **Response Generation Agent** (`src/response_generator/`)
   - **ACP Server**: `acp_server.py` - Wraps OpenAI client for ACP communication (port 8004)
   - **OpenAI Integration**: `generator.py` - Uses GPT-4o-mini for response generation
   - **Features**: Multiple response variants, tone adaptation, human review flags
   - **Output**: Generated email responses with confidence scores and review requirements

4. **Workflow Orchestrator** (`src/orchestrator/`)
   - **Main Orchestrator**: `main.py` - Complete end-to-end workflow management
   - **ACP Client**: `acp_client.py` - Communicates with all three agents via ACP protocol
   - **Workflow Engine**: `workflow.py` - State-based workflow orchestration
   - **Human Review**: `human_review.py` - Interactive human-in-the-loop interface
   - **Features**: End-to-end processing, human review, error handling, workflow tracking

5. **Configuration System**
   - `config/agents.yaml`: Agent role definitions and backstories (email classifier)
   - `config/tasks.yaml`: Task descriptions and expected outputs (email classifier)
   - Environment variables via `.env` file

### Key Design Patterns

- **Agent Communication Protocol (ACP)**: Enables structured inter-agent communication
- **Multi-Framework Integration**: CrewAI + LangGraph + OpenAI working together via ACP
- **Workflow Orchestration**: Central orchestrator manages complete email processing pipeline
- **Human-in-the-Loop**: Interactive review and approval at key decision points
- **Defensive Error Handling**: Graceful degradation when dependencies unavailable
- **JSON-First Communication**: Structured data exchange between agents
- **State-Based Workflows**: LangGraph uses TypedDict states for complex decision routing

### Tools and Custom Components

#### Email Classification Agent
- **EmailClassificationTool**: Input validation and content cleaning
- **ValidationTool**: JSON format validation and field verification
- **CrewAI Configuration**: Agent and task definitions via YAML

#### Strategy Planning Agent
- **Pydantic Models**: Structured data models for decisions and recommendations
- **LangGraph Workflow**: State-based graph with conditional routing
- **Strategy Handlers**: Specialized nodes for different response strategies
- **Confidence-Based Routing**: Decisions based on classification confidence levels

#### Response Generation Agent
- **OpenAI Integration**: Direct GPT-4o-mini API calls for response generation
- **Response Variants**: Generate multiple response options for comparison
- **Quality Assessment**: Confidence scoring and human review recommendations
- **Template System**: Dynamic response templates based on strategy and tone
- **Business Context**: Configurable company information and brand voice

#### Workflow Orchestrator
- **ACP Client**: Async HTTP client for communicating with all agents
- **Workflow State Management**: Complete tracking of email processing pipeline
- **Human Review Interface**: CLI-based review and approval system
- **Error Recovery**: Graceful handling of agent failures with fallback responses
- **Workflow History**: Complete audit trail of all processing steps

## Environment Variables

Required environment variables (create `.env` file):
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Development Notes

- The project uses `uv` for dependency management
- ACP SDK integration allows for agent discovery and communication
- CrewAI crew execution is wrapped in try-catch for error handling
- Agent responses are structured JSON with confidence scores and reasoning
- The server can run in test mode for development verification

## Project Structure

```
src/
├── email_classifier_crew/
│   ├── acp_server.py      # ACP protocol server wrapper (port 8002)
│   ├── crew.py            # CrewAI crew implementation
│   ├── tools.py           # Custom tools for email processing
│   ├── main.py            # Direct crew execution
│   ├── __init__.py        # Package initialization
│   └── config/
│       ├── agents.yaml    # Agent configurations
│       └── tasks.yaml     # Task definitions
├── strategy_agent/
│   ├── acp_server.py      # ACP protocol server wrapper (port 8003)
│   ├── workflow.py        # LangGraph strategy planning workflow
│   ├── models.py          # Pydantic data models
│   ├── main.py            # Direct workflow execution
│   └── __init__.py        # Package initialization
├── response_generator/
│   ├── acp_server.py      # ACP protocol server wrapper (port 8004)
│   ├── generator.py       # OpenAI response generation engine
│   ├── models.py          # Pydantic data models
│   ├── main.py            # Direct generator execution
│   └── __init__.py        # Package initialization
└── orchestrator/
    ├── main.py            # End-to-end workflow orchestration
    ├── workflow.py        # Workflow engine and state management
    ├── acp_client.py      # ACP client for agent communication
    ├── human_review.py    # Human-in-the-loop review interface
    ├── models.py          # Workflow data models
    └── __init__.py        # Package initialization
```

## ACP Integration Points

### Email Classification Agent (Port 8002)
- Agent manifest: `http://localhost:8002/agents`
- Input: Email content in text/plain or JSON format
- Output: Email classification with type, priority, confidence, reasoning

### Strategy Planning Agent (Port 8003)
- Agent manifest: `http://localhost:8003/agents`
- Input: Email classification results in JSON format
- Output: Strategy recommendations with response templates and next steps

### Response Generation Agent (Port 8004)
- Agent manifest: `http://localhost:8004/agents`
- Input: Email context + strategy recommendations in JSON format
- Output: Generated email responses with variants and human review flags

### Workflow Orchestrator
- **Endpoint**: Local execution via `python src/orchestrator/main.py`
- **Input**: Raw email content and metadata
- **Output**: Final approved email responses with complete workflow audit trail
- **Features**: Human review, error handling, state tracking, multi-agent coordination

### Complete Email Processing Pipeline
```
Raw Email → Orchestrator → Classification Agent → Strategy Agent → Response Generator → Human Review → Final Response
```

**Key Features**:
- End-to-end processing with comprehensive error handling
- Human-in-the-loop review at critical decision points  
- Complete audit trail of all processing steps
- Configurable confidence thresholds and auto-approval rules
- Multi-agent coordination via ACP protocol

## Reference Materials

The `references/` directory contains complete implementations for learning:
- `references/crewAI/`: Complete CrewAI framework source code and examples
- `references/acp/`: ACP protocol implementation and integration examples
- `references/langgraph/`: LangGraph framework source code and examples
- `references/ACP_ANALYSIS.md`: Comprehensive ACP protocol analysis