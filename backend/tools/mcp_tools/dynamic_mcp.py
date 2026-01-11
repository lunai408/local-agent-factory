"""
Dynamic MCP Toolkit that injects session_id from RunContext.

This toolkit discovers MCP tools at startup and creates wrappers that
dynamically pass the X-Conversation-ID header based on the current
RunContext.session_id at execution time.
"""

from __future__ import annotations

import logging
from typing import Any

from agno.run import RunContext
from agno.tools.function import Function
from agno.tools.mcp import MCPTools
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)


class DynamicMCPTools(MCPTools):
    """
    MCP Toolkit that dynamically passes X-Conversation-ID header
    based on RunContext.session_id at execution time.

    Inherits from MCPTools to use Agno's async connection path.
    Unlike MCPTools which sets headers at construction, this toolkit
    creates a fresh connection per tool call with the current session_id.

    Usage:
        toolkit = DynamicMCPTools(
            server_url="http://localhost:3003",
            name="chart_generator",
        )
        # Add to agent tools list - discovery happens on first use
    """

    def __init__(
        self,
        server_url: str,
        name: str = "mcp",
        include_tools: list[str] | None = None,
        exclude_tools: list[str] | None = None,
    ):
        """
        Initialize DynamicMCPTools.

        Args:
            server_url: Base URL of the MCP server (e.g., http://localhost:3003)
            name: Name for this toolkit
            include_tools: Only include these tools (None = all)
            exclude_tools: Exclude these tools
        """
        # Initialize MCPTools with streamable-http transport (no session_id header yet)
        super().__init__(
            url=server_url.rstrip("/") + "/mcp",
            transport="streamable-http",
            include_tools=include_tools,
            exclude_tools=exclude_tools,
            refresh_connection=True,  # Always refresh to get new session_id
        )
        self.name = name
        self.server_url = server_url.rstrip("/")
        self.mcp_url = f"{self.server_url}/mcp"
        self._dynamic_include_tools = include_tools
        self._dynamic_exclude_tools = exclude_tools or []
        self._tool_definitions: dict[str, dict] = {}
        # Override refresh_connection for our dynamic behavior
        self.refresh_connection = False  # We handle refresh ourselves in wrappers

    async def connect(self, force: bool = False) -> None:
        """
        Connect to MCP server and discover available tools.

        This method is called automatically by Agno before tool execution.
        It discovers tools from the MCP server and creates wrapper functions
        that will inject session_id dynamically at call time.
        """
        if self._initialized and not force:
            return

        if force:
            self._tool_definitions = {}
            self.functions = {}
            self._initialized = False

        logger.info("Discovering tools from MCP server: %s", self.server_url)

        try:
            # Connect without session header just to discover tools
            async with streamablehttp_client(url=self.mcp_url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()

                    for tool in tools_result.tools:
                        # Filter tools
                        if self._dynamic_include_tools and tool.name not in self._dynamic_include_tools:
                            continue
                        if tool.name in self._dynamic_exclude_tools:
                            continue

                        # Store tool definition
                        self._tool_definitions[tool.name] = {
                            "name": tool.name,
                            "description": tool.description or "",
                            "input_schema": tool.inputSchema,
                        }

                        # Create and register wrapper function
                        self._register_tool_wrapper(
                            tool.name,
                            tool.description,
                            tool.inputSchema,
                        )

                    logger.info(
                        "Discovered %d tools from %s: %s",
                        len(self._tool_definitions),
                        self.name,
                        list(self._tool_definitions.keys()),
                    )

            # Mark as initialized
            self._initialized = True

        except Exception as e:
            logger.error("Failed to connect to MCP server %s: %s", self.server_url, e)
            raise

    async def close(self) -> None:
        """Close the toolkit (no persistent connections to close)."""
        self._initialized = False
        self._tool_definitions = {}

    async def is_alive(self) -> bool:
        """Check if MCP server is reachable."""
        try:
            async with streamablehttp_client(url=self.mcp_url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return True
        except Exception:
            return False

    def _register_tool_wrapper(
        self,
        tool_name: str,
        description: str | None,
        input_schema: dict,
    ) -> None:
        """
        Create a wrapper function for an MCP tool.

        The wrapper intercepts tool calls and creates a fresh MCP connection
        with the session_id from RunContext as the X-Conversation-ID header.
        """
        # Capture mcp_url in closure
        mcp_url = self.mcp_url

        async def tool_wrapper(
            run_context: RunContext | None = None,
            **kwargs: Any,
        ) -> Any:
            """Execute MCP tool with dynamic session header."""
            session_id = run_context.session_id if run_context else None

            headers = {}
            if session_id:
                headers["X-Conversation-ID"] = session_id

            logger.debug(
                "Calling MCP tool %s with session_id: %s",
                tool_name,
                session_id,
            )

            async with streamablehttp_client(
                url=mcp_url,
                headers=headers if headers else None,
            ) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments=kwargs)

                    # Parse result content
                    if result.content:
                        # Return first text content or all contents
                        for content in result.content:
                            if hasattr(content, "text"):
                                return content.text
                        return [c.model_dump() for c in result.content]
                    return None

        # Set function metadata
        tool_wrapper.__name__ = tool_name
        tool_wrapper.__doc__ = description or f"Execute {tool_name} via MCP"

        # Build parameters from input_schema
        parameters = self._schema_to_parameters(input_schema)

        # Create Function and register
        func = Function(
            name=tool_name,
            entrypoint=tool_wrapper,
            description=description or "",
            parameters=parameters,
            skip_entrypoint_processing=True,
        )
        self.functions[tool_name] = func

    def _schema_to_parameters(self, schema: dict) -> dict:
        """
        Convert JSON schema to Function parameters format.

        Args:
            schema: JSON schema from MCP tool definition

        Returns:
            Parameters dict for Agno Function
        """
        if not schema:
            return {"type": "object", "properties": {}}

        properties = schema.get("properties", {}).copy()
        required = list(schema.get("required", []))

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }
