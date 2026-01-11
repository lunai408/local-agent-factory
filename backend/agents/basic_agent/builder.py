"""
Configurable agent with MCP tools support.

Usage:
    from agents.basic_agent import create_agent, MCPServersConfig, MCPServerConfig

    # Simple agent without MCP
    agent = create_agent(name="Assistant")

    # Agent with MCP tools (session_id passed via RunContext at execution time)
    agent = create_agent(
        name="Data Analyst",
        mcp_servers=MCPServersConfig(
            chart_generator=MCPServerConfig("chart", "http://localhost:3003", enabled=True),
            pdf_generator=MCPServerConfig("pdf", "http://localhost:3001", enabled=True),
        ),
    )
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.tools.knowledge import KnowledgeTools

from utils.models import get_llm_model

from tools.knowledge_tool import KnowledgeTool
from tools.mcp_tools import MCPServerConfig, DynamicMCPTools
from utils import get_db_manager


@dataclass
class MCPServersConfig:
    """Configuration for MCP servers to connect."""

    chart_generator: MCPServerConfig | None = None
    pdf_generator: MCPServerConfig | None = None
    comfy_image: MCPServerConfig | None = None


# Default MCP server configurations (all disabled by default)
# URLs are read from environment variables for Docker/local flexibility
DEFAULT_MCP_SERVERS = MCPServersConfig(
    chart_generator=MCPServerConfig(
        name="chart",
        url=os.environ.get("MCP_CHART_URL", "http://localhost:3003"),
        enabled=False,
    ),
    pdf_generator=MCPServerConfig(
        name="pdf",
        url=os.environ.get("MCP_PDF_URL", "http://localhost:3001"),
        enabled=False,
    ),
    comfy_image=MCPServerConfig(
        name="comfy",
        url=os.environ.get("MCP_COMFY_URL", "http://localhost:3002"),
        enabled=False,
    ),
)


def create_agent(
    name: str = "Assistant",
    description: str = "A helpful assistant",
    instructions: list[str] | None = None,
    mcp_servers: MCPServersConfig | None = None,
    enable_knowledge: bool = False,
    knowledge_name: str = "default_kb",
    knowledge_collection: str = "default",
    user_id: str | None = None,
    session_id: str | None = None,
    model_id: str | None = None,
    tools: list[Any] | None = None,
    **agent_kwargs: Any,
) -> Agent:
    """
    Create a configurable agent with optional MCP tools.

    MCP tools use DynamicMCPTools which automatically passes the session_id
    from RunContext as X-Conversation-ID header at execution time. This enables
    session-based file isolation in MCP servers.

    Args:
        name: Agent name
        description: Agent description
        instructions: System instructions for the agent
        mcp_servers: MCP servers configuration (chart, pdf, comfy)
        enable_knowledge: Whether to enable knowledge base tools
        knowledge_name: Name for the knowledge base
        knowledge_collection: Vector DB collection name
        user_id: User ID for memory persistence
        session_id: Session ID for memory persistence
        model_id: LLM model ID
        tools: Additional tools to include
        **agent_kwargs: Additional arguments passed to Agent

    Returns:
        Configured Agent instance
    """
    db = get_db_manager()
    agent_tools: list[Any] = list(tools) if tools else []
    knowledge = None

    # Configure knowledge tools if enabled
    if enable_knowledge:
        knowledge = Knowledge(
            name=knowledge_name,
            description=f"{name} knowledge base",
            contents_db=db.agno_db,
            vector_db=db.get_vector_db(knowledge_collection),
        )

        knowledge_tool = KnowledgeTool(knowledge=knowledge)
        agno_knowledge_tools = KnowledgeTools(
            knowledge=knowledge,
            enable_think=True,
            enable_search=True,
            enable_analyze=True,
            add_few_shot=True,
        )
        agent_tools.extend([knowledge_tool, agno_knowledge_tools])

    # Configure MCP tools if servers provided
    # Uses DynamicMCPTools which gets session_id from RunContext at execution time
    if mcp_servers:
        if mcp_servers.chart_generator and mcp_servers.chart_generator.enabled:
            agent_tools.append(
                DynamicMCPTools(
                    server_url=mcp_servers.chart_generator.url,
                    name="chart_generator",
                )
            )
        if mcp_servers.pdf_generator and mcp_servers.pdf_generator.enabled:
            agent_tools.append(
                DynamicMCPTools(
                    server_url=mcp_servers.pdf_generator.url,
                    name="pdf_generator",
                )
            )
        if mcp_servers.comfy_image and mcp_servers.comfy_image.enabled:
            agent_tools.append(
                DynamicMCPTools(
                    server_url=mcp_servers.comfy_image.url,
                    name="comfy_image",
                )
            )

    return Agent(
        name=name,
        description=description,
        db=db.agno_db,
        model=get_llm_model(model_id),
        knowledge=knowledge,
        tools=agent_tools if agent_tools else None,
        search_knowledge=enable_knowledge,
        instructions=instructions or [],
        add_history_to_context=True,
        num_history_runs=3,
        read_chat_history=True,
        enable_user_memories=True,
        enable_session_summaries=True,
        add_datetime_to_context=True,
        add_name_to_context=True,
        add_memories_to_context=True,
        user_id=user_id,
        session_id=session_id,
        markdown=True,
        **agent_kwargs,
    )
