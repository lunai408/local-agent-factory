# MCP Servers

Model Context Protocol (MCP) servers for extending agent capabilities.

## Overview

| Server | Port | Description |
|--------|------|-------------|
| PDF Generator | 3001 | Create PDFs from Markdown |
| ComfyUI Image | 3002 | Generate images via ComfyUI |
| Chart Generator | 3003 | Create data visualizations |

## Quick Start

```bash
cd mcp
uv sync

# Run individual servers
uv run pdf-generator-mcp
uv run comfy-image-mcp
uv run chart-generator-mcp

# Or use Task
task mcp:pdf
task mcp:comfy
task mcp:chart
```

## Docker Deployment

```bash
# Build and start all MCP servers
docker compose --profile mcp up -d --build

# Or start full stack
docker compose --profile full up -d --build
```

### Docker Images

| Server | Dockerfile | Size |
|--------|------------|------|
| PDF Generator | `Dockerfile.pdf` | ~1.5GB (includes LaTeX) |
| Chart Generator | `Dockerfile.chart` | ~500MB |
| ComfyUI Image | `Dockerfile.comfy` | ~200MB |

## Environment Variables

```env
# PDF Generator
PDFS_DIR=./data/generated_pdfs

# Chart Generator
CHARTS_DIR=./data/generated_charts

# ComfyUI Image Generator
GENERATED_IMAGES_DIR=./data/generated_images
COMFY_URL=http://localhost:8188
COMFY_TIMEOUT=1800
```

---

## PDF Generator (Port 3001)

Generate PDFs from Markdown content using Pandoc and LaTeX.

### Prerequisites

- Pandoc installed
- LaTeX distribution (texlive)

### Tools

| Tool | Description |
|------|-------------|
| `generate_pdf` | Create PDF from Markdown |
| `list_generated_pdfs` | List saved PDFs |
| `list_styles` | Available PDF styles |
| `check_pandoc_status` | Check dependencies |

### Styles

- `default` - Standard document
- `academic` - Academic paper format
- `modern` - Clean modern design
- `minimal` - Minimal styling

### Example

```python
# Generate a PDF
result = await generate_pdf(
    content="# My Document\n\nThis is content.",
    style="modern",
    title="My Report"
)
```

---

## Chart Generator (Port 3003)

Create charts and visualizations with Matplotlib and Seaborn.

### Tools

| Tool | Description |
|------|-------------|
| `create_line_chart` | Line charts |
| `create_bar_chart` | Bar charts |
| `create_pie_chart` | Pie charts |
| `create_scatter_plot` | Scatter plots |
| `create_heatmap` | Heatmaps |
| `list_generated_charts` | List saved charts |

### Output Formats

- PNG (default)
- SVG
- PDF

### Example

```python
# Create a bar chart
result = await create_bar_chart(
    data={"A": 10, "B": 20, "C": 15},
    title="Sales by Category",
    format="png"
)
```

---

## ComfyUI Image Generator (Port 3002)

Generate images using ComfyUI with Z-Image Turbo model.

### Prerequisites

ComfyUI must be running on host at `http://localhost:8188`.

```bash
task comfy:start
```

### Tools

| Tool | Description |
|------|-------------|
| `generate_image` | Single image from prompt |
| `generate_variants` | Multiple images with different seeds |
| `list_generated_images` | List recent images |
| `check_comfy_status` | Check ComfyUI availability |

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `prompt` | required | Text description |
| `width` | 1024 | Image width |
| `height` | 1024 | Image height |
| `seed` | random | Random seed |
| `steps` | 9 | Inference steps |

### Example

```python
# Generate an image
result = await generate_image(
    prompt="A beautiful sunset over mountains",
    width=1024,
    height=1024
)
```

### Response

```json
{
  "success": true,
  "image_path": "/path/to/image.png",
  "image_url": "file:///path/to/image.png",
  "metadata": {
    "seed": 123456,
    "width": 1024,
    "height": 1024,
    "steps": 9,
    "model": "z_image_turbo_bf16"
  }
}
```

---

## Claude Code Integration

Add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "pdf-generator": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp", "run", "pdf-generator-mcp"]
    },
    "chart-generator": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp", "run", "chart-generator-mcp"]
    },
    "comfy-image": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp", "run", "comfy-image-mcp"],
      "env": {
        "COMFY_URL": "http://localhost:8188"
      }
    }
  }
}
```

## Storage

Generated files are stored by conversation ID:

```
mcp/data/
├── generated_pdfs/
│   ├── _shared/
│   └── {conversation_id}/
├── generated_charts/
│   ├── _shared/
│   └── {conversation_id}/
└── generated_images/
    ├── _shared/
    └── {conversation_id}/
```

## Development

### Test with MCP Inspector

```bash
# PDF Generator
uv run mcp dev pdf_generator/server.py

# Chart Generator
uv run mcp dev chart_generator/server.py

# ComfyUI Image
uv run mcp dev comfy_image/server.py
```

### Run with HTTP Transport

```bash
# Useful for debugging
uv run python -m pdf_generator.server --transport streamable-http --port 3001
```

## Dependencies

See `pyproject.toml`:

- `mcp[cli]>=1.0.0` - MCP framework
- `matplotlib>=3.8.0` - Charts
- `seaborn>=0.13.0` - Statistical plots
- `httpx>=0.28.0` - HTTP client
- `python-dotenv>=1.0.0` - Environment loading
