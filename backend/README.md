# Backend - Agno OS

The AI agent backend built with [Agno](https://github.com/agno-agi/agno) framework and FastAPI.

## Quick Start

```bash
# Install dependencies
uv sync

# Run in development mode
uv run uvicorn agentos:app --reload --port 7777

# Or use Task
task backend:dev
```

## Project Structure

```
backend/
├── agentos.py            # Main entry point (Agno OS)
├── agents/               # Agent definitions
│   ├── basic_agent/      # Basic agent implementation
│   │   ├── agent.py      # Agent creation functions
│   │   ├── builder.py    # Core builder with MCP integration
│   │   └── prompts/      # System prompts
│   └── deep_research/    # Multi-agent research team
│       ├── agents.py     # Specialist agents
│       └── team.py       # Team orchestration
├── tools/                # Custom tools
│   └── knowledge_tool.py # Knowledge base tool
├── utils/                # Shared utilities
│   ├── database.py       # SurrealDB connection
│   ├── models.py         # Model provider selector
│   ├── storage.py        # File storage
│   └── readers.py        # Document readers
└── data/                 # Persistent storage
    └── knowledge_files/  # Cached documents
```

## Adding a New Agent

### 1. Create Agent Directory

```bash
mkdir -p agents/my_agent
touch agents/my_agent/__init__.py
touch agents/my_agent/agent.py
```

### 2. Define the Agent

```python
# agents/my_agent/agent.py
from agno.agent import Agent
from utils.models import get_model

def create_my_agent():
    return Agent(
        name="My Agent",
        agent_id="my-agent",
        description="What this agent does",
        model=get_model(),
        instructions=[
            "You are a helpful assistant.",
            "Always be concise and accurate.",
        ],
    )
```

### 3. Register in Agno OS

```python
# agentos.py
from agents.my_agent import create_my_agent

my_agent = create_my_agent()

agent_os = AgentOS(
    agents=[..., my_agent],
)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/health` | GET | Health check |
| `/v1/agents` | GET | List agents |
| `/v1/agents/{id}` | GET | Get agent details |
| `/v1/agents/{id}/runs` | POST | Start a run |
| `/v1/sessions` | GET | List sessions |

## Environment Variables

See `.env.example` for all options:

```env
MODEL_PROVIDER=local        # local or openai
OLLAMA_BASE_URL=http://localhost:11434
SURREALDB_URL=ws://localhost:8000
```

## Docker

```bash
# Build image
docker build -t local-agent-memory-backend .

# Run container
docker run -p 7777:7777 \
  -e SURREALDB_URL=ws://host.docker.internal:8000 \
  local-agent-memory-backend
```

## Dependencies

Key dependencies (see `pyproject.toml`):

- `agno>=2.3.12` - AI agent framework
- `fastapi>=0.124.4` - Web framework
- `surrealdb>=1.0.7` - Database client
- `ollama>=0.6.1` - Local LLM
- `openai>=2.11.0` - OpenAI API
- `mcp>=1.0.0` - Model Context Protocol
