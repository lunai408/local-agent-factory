"""
MCP Tools configuration for Agno agents.

Uses Agno's built-in MCPTools with streamable-http transport.
"""

from __future__ import annotations

from dataclasses import dataclass

from agno.tools.mcp import MCPTools, StreamableHTTPClientParams


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server connection."""

    name: str  # Short name for identification (e.g., "chart", "pdf", "comfy")
    url: str  # Base URL (e.g., "http://localhost:3000")
    enabled: bool = True


def create_mcp_tools(
    server: MCPServerConfig,
    session_id: str | None = None,
    timeout: float = 60.0,
) -> MCPTools:
    """
    Create an MCPTools instance for a server.

    Args:
        server: Server configuration
        session_id: Session ID to send as X-Conversation-ID header
        timeout: Timeout for operations in seconds

    Returns:
        Configured MCPTools instance (not yet connected)
    """
    # Build streamable-http URL (endpoint is /mcp)
    mcp_url = f"{server.url.rstrip('/')}/mcp"

    # Build headers with conversation ID
    headers = {}
    if session_id:
        headers["X-Conversation-ID"] = session_id

    # Create streamable-http client params with headers
    server_params = StreamableHTTPClientParams(
        url=mcp_url,
        headers=headers if headers else None,
        timeout=timeout,
    )

    return MCPTools(server_params=server_params, transport="streamable-http")


def create_mcp_tools_list(
    servers: list[MCPServerConfig],
    session_id: str | None = None,
    timeout: float = 60.0,
) -> list[MCPTools]:
    """
    Create MCPTools instances for multiple servers.

    Args:
        servers: List of server configurations
        session_id: Session ID to send as X-Conversation-ID header
        timeout: Timeout for operations in seconds

    Returns:
        List of configured MCPTools instances (not yet connected)
    """
    return [
        create_mcp_tools(server, session_id, timeout)
        for server in servers
        if server.enabled
    ]
