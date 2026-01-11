# Models - Local AI Models

Configuration and scripts for local model providers.

## Why Host-Based?

Ollama and ComfyUI run on the host machine (not in Docker) to:

- **GPU Access** - Direct CUDA/Metal acceleration
- **Shared Weights** - Models available to all projects
- **Simpler Setup** - No Docker GPU passthrough complexity
- **Easy Management** - Native CLI tools

Docker services connect via `host.docker.internal`.

## Ollama (LLM Inference)

### Quick Setup

```bash
task ollama:setup
```

This will:
1. Install Ollama
2. Start the daemon
3. Pull configured models
4. Verify connectivity

### Manual Setup

```bash
# Install (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Start daemon
ollama serve

# Pull models
ollama pull ministral-3:3b
ollama pull nomic-embed-text
```

### Available Commands

| Command | Description |
|---------|-------------|
| `task ollama:install` | Install Ollama |
| `task ollama:start` | Start daemon |
| `task ollama:pull` | Pull models |
| `task ollama:doctor` | Health check |
| `task ollama:stop` | Stop daemon |
| `task ollama:uninstall` | Uninstall |

### Configuration

```env
OLLAMA_HOST=127.0.0.1:11434
OLLAMA_INFER_MODEL=ministral-3:3b
OLLAMA_EMBED_MODEL=nomic-embed-text
```

### Recommended Models

| Model | Size | Use Case |
|-------|------|----------|
| `ministral-3:3b` | 2GB | Fast inference |
| `llama3.2:3b` | 2GB | General purpose |
| `nomic-embed-text` | 274MB | Embeddings |

## ComfyUI (Image Generation)

### Quick Setup

```bash
task comfy:setup
```

This will:
1. Install comfy-cli
2. Download Z-Image Turbo models
3. Start ComfyUI
4. Verify setup

### Manual Setup

```bash
# Install comfy-cli
pipx install comfy-cli

# Ensure PATH is updated
pipx ensurepath && exec $SHELL -l

# Install ComfyUI
comfy install

# Download models (see pull_models.sh)
# Start ComfyUI
comfy launch
```

### Available Commands

| Command | Description |
|---------|-------------|
| `task comfy:install` | Install comfy-cli |
| `task comfy:pull` | Download models |
| `task comfy:start` | Start ComfyUI |
| `task comfy:doctor` | Health check |
| `task comfy:stop` | Stop server |
| `task comfy:uninstall` | Uninstall |

### Configuration

```env
COMFY_PRESET=z_image_turbo
COMFY_VRAM_MODE=auto          # auto/lowvram/normalvram/highvram/novram/cpu
COMFY_ACCELERATOR=auto        # auto/cuda/mps/cpu
```

### VRAM Modes

| Mode | GPU Memory | Description |
|------|------------|-------------|
| `auto` | Varies | Automatic detection |
| `lowvram` | <4GB | Aggressive offloading |
| `normalvram` | 4-8GB | Standard mode |
| `highvram` | >8GB | Keep in VRAM |
| `novram` | - | CPU offload |
| `cpu` | - | CPU only |

### Z-Image Turbo Models

| File | Size | Description |
|------|------|-------------|
| `qwen_3_4b.safetensors` | ~8GB | Text encoder |
| `z_image_turbo_bf16.safetensors` | ~12GB | Diffusion model |
| `ae.safetensors` | ~500MB | VAE |

Models are downloaded from Hugging Face. URLs configured in `.env`.

## Structure

```
models/
├── ollama/
│   └── scripts/
│       ├── install.sh / install.ps1
│       ├── start.sh / start.ps1
│       ├── pull.sh / pull.ps1
│       ├── doctor.sh / doctor.ps1
│       └── uninstall.sh / uninstall.ps1
└── comfy/
    └── scripts/
        ├── install.sh / install.ps1
        ├── start.sh / start.ps1
        ├── pull_models.sh / pull_models.ps1
        ├── doctor.sh / doctor.ps1
        └── uninstall.sh / uninstall.ps1
```

## Troubleshooting

### Ollama

```bash
# Check if running
curl http://localhost:11434/api/tags

# View logs (macOS)
cat ~/.ollama/logs/server.log

# Restart
task ollama:stop && task ollama:start
```

### ComfyUI

```bash
# Check if running
curl http://localhost:8188/system_stats

# Common issues:
# - "comfy not found" → Run: pipx ensurepath && exec $SHELL -l
# - GPU not detected → Check CUDA/Metal drivers
# - Out of VRAM → Set COMFY_VRAM_MODE=lowvram
```
