"""
Configurable agent with MCP tools support.

Usage:
    from agents.basic_agent import create_agent, MCPServersConfig, MCPServerConfig

    # Simple agent without MCP
    agent = create_agent(name="Assistant")

    # Agent with MCP tools
    agent = create_agent(
        name="Data Analyst",
        mcp_servers=MCPServersConfig(
            chart_generator=MCPServerConfig("chart", "http://localhost:3003", enabled=True),
            pdf_generator=MCPServerConfig("pdf", "http://localhost:3001", enabled=True),
        ),
        session_id="user-session-123",
    )
"""

from __future__ import annotations

import os

from agno.agent import Agent

from agents.basic_agent.builder import create_agent, MCPServersConfig
from agents.basic_agent.prompts.data_analyst import DATA_ANALYST_INSTRUCTIONS
from tools.mcp_tools import MCPServerConfig


def create_data_analyst_agent(
    user_id: str | None = None,
    session_id: str | None = None,
    chart_url: str | None = None,
    pdf_url: str | None = None,
    tools: list = [],
) -> Agent:
    """
    Create a Data Analyst agent with chart and PDF generation capabilities.

    Args:
        user_id: Optional user ID for memory persistence
        session_id: Optional session ID (used for resource isolation)
        chart_url: Chart generator MCP server URL (defaults to MCP_CHART_URL env var)
        pdf_url: PDF generator MCP server URL (defaults to MCP_PDF_URL env var)
        tools: List of additional tools to include

    Returns:
        Configured Agent instance
    """
    chart_url = chart_url or os.environ.get("MCP_CHART_URL", "http://localhost:3003")
    pdf_url = pdf_url or os.environ.get("MCP_PDF_URL", "http://localhost:3001")

    return create_agent(
        name="Data Analyst",
        description="An agent that analyzes data and generates visualizations and reports.",
        instructions=[DATA_ANALYST_INSTRUCTIONS],
        mcp_servers=MCPServersConfig(
            chart_generator=MCPServerConfig(
                name="chart",
                url=chart_url,
                enabled=True,
            ),
            pdf_generator=MCPServerConfig(
                name="pdf",
                url=pdf_url,
                enabled=True,
            ),
        ),
        user_id=user_id,
        session_id=session_id,
        tools=tools,
    )


def create_creative_agent(
    user_id: str | None = None,
    session_id: str | None = None,
    comfy_url: str | None = None,
    chart_url: str | None = None,
    pdf_url: str | None = None,
    tools: list = [],
) -> Agent:
    """
    Create a Creative agent with all generation capabilities.

    Args:
        user_id: Optional user ID for memory persistence
        session_id: Optional session ID (used for resource isolation)
        comfy_url: ComfyUI MCP server URL (defaults to MCP_COMFY_URL env var)
        chart_url: Chart generator MCP server URL (defaults to MCP_CHART_URL env var)
        pdf_url: PDF generator MCP server URL (defaults to MCP_PDF_URL env var)
        tools: List of additional tools to include

    Returns:
        Configured Agent instance
    """
    comfy_url = comfy_url or os.environ.get("MCP_COMFY_URL", "http://localhost:3002")
    chart_url = chart_url or os.environ.get("MCP_CHART_URL", "http://localhost:3003")
    pdf_url = pdf_url or os.environ.get("MCP_PDF_URL", "http://localhost:3001")

    return create_agent(
        name="Creative Agent",
        description="An agent that can generate images, charts, and documents.",
        instructions=[
            "You are a creative assistant with powerful generation capabilities.",
            "You can generate images using the comfy_generate_image tool.",
            "You can create charts using the chart_generate_chart tool.",
            "You can produce PDF documents using the pdf_generate_pdf tool.",
            "Be creative and help users visualize their ideas.",
        ],
        mcp_servers=MCPServersConfig(
            chart_generator=MCPServerConfig(
                name="chart",
                url=chart_url,
                enabled=True,
            ),
            pdf_generator=MCPServerConfig(
                name="pdf",
                url=pdf_url,
                enabled=True,
            ),
            comfy_image=MCPServerConfig(
                name="comfy",
                url=comfy_url,
                enabled=True,
            ),
        ),
        user_id=user_id,
        session_id=session_id,
        tools=tools,
    )
