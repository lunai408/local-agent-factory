# Local Agent Memory

A fully self-hosted AI agent platform with persistent memory. Run intelligent agents locally using Ollama, ComfyUI, and SurrealDB - no cloud dependencies required.

## Features

- **Local LLMs** - Run inference with Ollama (Mistral, Llama, etc.)
- **Local Image Generation** - Generate images with ComfyUI and Z-Image Turbo
- **Persistent Memory** - Agent memories and sessions stored in SurrealDB
- **MCP Tools** - PDF generation, chart creation, and image generation via MCP protocol
- **Modern UI** - Next.js chat interface (Agent UI)
- **Multi-Agent Teams** - Orchestrate multiple agents for complex tasks
- **Plug & Play** - Docker Compose setup for quick deployment

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Agent UI (3000)                         │
│                      Next.js Chat Interface                     │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────┐
│                        Backend (7777)                           │
│                    Agno OS - FastAPI                            │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Agents    │  │    Teams    │  │         Tools           │  │
│  │ Basic Agent │  │   Deep      │  │ DuckDuckGo, YFinance,   │  │
│  │ Data Analyst│  │   Research  │  │ Reasoning, Knowledge    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└───────┬─────────────────┬───────────────────┬───────────────────┘
        │                 │                   │
┌───────▼───────┐ ┌───────▼───────┐ ┌─────────▼─────────┐
│   SurrealDB   │ │  MCP Servers  │ │   Host Services   │
│    (8000)     │ │               │ │                   │
│   Memories    │ │ PDF    (3001) │ │ Ollama   (11434)  │
│   Sessions    │ │ ComfyUI(3002) │ │ ComfyUI  (8188)   │
│   Knowledge   │ │ Charts (3003) │ │                   │
└───────────────┘ └───────────────┘ └───────────────────┘
```

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- [Task](https://taskfile.dev/installation/) (go-task) for automation
- (Optional) [Ollama](https://ollama.com/) for local LLMs
- (Optional) [ComfyUI](https://github.com/comfyanonymous/ComfyUI) for local image generation

### 1. Clone & Configure

```bash
git clone https://github.com/yourusername/local-agent-memory.git
cd local-agent-memory

# Copy environment template
cp .env.example .env

# Edit .env with your configuration (optional)
```

### 2. Start Services

**Option A: Full Docker Stack**

```bash
# Start everything (SurrealDB + Backend + UI + MCP servers)
task docker:full

# Or without Task:
docker compose --profile full up -d
```

**Option B: Development Mode (Recommended)**

```bash
# Full setup: Ollama + ComfyUI + Docker services
task setup

# Then in separate terminals:
task backend:dev   # Backend with hot reload
task ui:dev        # Frontend with hot reload
```

### 3. Access the Application

| Service     | URL                    | Description      |
| ----------- | ---------------------- | ---------------- |
| Agent UI    | http://localhost:3000  | Chat interface   |
| Backend API | http://localhost:7777  | Agno OS API      |
| SurrealDB   | http://localhost:8000  | Database         |
| Ollama      | http://localhost:11434 | Local LLMs       |
| ComfyUI     | http://localhost:8188  | Image generation |

## Configuration

### Model Provider

Set `MODEL_PROVIDER` in `.env`:

```env
# Use local Ollama (default)
MODEL_PROVIDER=local
OLLAMA_INFER_MODEL=ministral-3:3b
OLLAMA_EMBED_MODEL=nomic-embed-text

# Or use OpenAI
MODEL_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL_ID=gpt-4o
```

### Key Environment Variables

| Variable             | Default            | Description                  |
| -------------------- | ------------------ | ---------------------------- |
| `MODEL_PROVIDER`     | `local`            | `local` (Ollama) or `openai` |
| `OLLAMA_INFER_MODEL` | `ministral-3:3b`   | LLM for inference            |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Model for embeddings         |
| `SURREALDB_PORT`     | `8000`             | Database port                |
| `BACKEND_PORT`       | `7777`             | Backend API port             |
| `AGENT_UI_PORT`      | `3000`             | Frontend port                |

See `.env.example` for all options.

## Project Structure

```
local-agent-memory/
├── agent-ui/              # Next.js frontend
├── backend/               # Agno OS backend
│   ├── agents/            # Agent definitions
│   │   ├── basic_agent/   # Basic agent
│   │   └── deep_research/ # Multi-agent research team
│   ├── tools/             # Custom tools
│   └── utils/             # Utilities (DB, models)
├── mcp/                   # MCP servers
│   ├── pdf_generator/     # PDF creation
│   ├── chart_generator/   # Chart/graph creation
│   └── comfy_image/       # Image generation
├── database/              # SurrealDB config
│   ├── migrations/        # Schema definitions
│   └── seeds/             # Sample data
├── models/                # Local model scripts
│   ├── ollama/            # Ollama setup
│   └── comfy/             # ComfyUI setup
├── docker-compose.yml     # Docker services
├── Taskfile.yml           # Automation tasks
└── .env.example           # Environment template
```

## Task Commands

### Docker

| Command               | Description             |
| --------------------- | ----------------------- |
| `task docker:up`      | Start SurrealDB only    |
| `task docker:full`    | Start all services      |
| `task docker:app`     | Start backend + UI      |
| `task docker:mcp`     | Start MCP servers       |
| `task docker:down`    | Stop all services       |
| `task docker:migrate` | Run database migrations |

### Local Development

| Command            | Description              |
| ------------------ | ------------------------ |
| `task backend:dev` | Backend with hot reload  |
| `task ui:dev`      | Frontend with hot reload |
| `task mcp:pdf`     | PDF generator MCP        |
| `task mcp:chart`   | Chart generator MCP      |
| `task mcp:comfy`   | ComfyUI image MCP        |

### Ollama

| Command              | Description            |
| -------------------- | ---------------------- |
| `task ollama:setup`  | Full Ollama setup      |
| `task ollama:start`  | Start Ollama           |
| `task ollama:pull`   | Pull configured models |
| `task ollama:doctor` | Check Ollama health    |

### ComfyUI

| Command             | Description          |
| ------------------- | -------------------- |
| `task comfy:setup`  | Full ComfyUI setup   |
| `task comfy:start`  | Start ComfyUI        |
| `task comfy:pull`   | Download models      |
| `task comfy:doctor` | Check ComfyUI health |

### Global

| Command      | Description             |
| ------------ | ----------------------- |
| `task setup` | Full initial setup      |
| `task start` | Start all services      |
| `task stop`  | Stop all services       |
| `task dev`   | Development environment |

## Documentation

- [Backend Guide](backend/README.md) - Agent development
- [MCP Servers](mcp/README.md) - Tool servers
- [Database](database/README.md) - SurrealDB schema
- [Models](models/README.md) - Ollama & ComfyUI setup

## Tech Stack

| Component  | Technology                       |
| ---------- | -------------------------------- |
| Backend    | Python 3.13, Agno, FastAPI       |
| Frontend   | Next.js 15, React 18, TypeScript |
| Database   | SurrealDB                        |
| Local LLM  | Ollama                           |
| Image Gen  | ComfyUI, Z-Image Turbo           |
| MCP        | Model Context Protocol           |
| Automation | Task (go-task)                   |

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Built with [Agno](https://github.com/agno-agi/agno) and [SurrealDB](https://surrealdb.com/)
