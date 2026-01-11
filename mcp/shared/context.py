"""
Context utilities for MCP servers.

Provides conversation ID extraction from request context.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import Context

logger = logging.getLogger(__name__)

DEFAULT_CONV_ID = "_shared"


def get_conversation_id(ctx: "Context") -> str:
    """
    Extract conversation ID from MCP request context.

    Retrieves the X-Conversation-ID header from HTTP requests.
    For stdio transport or missing headers, returns DEFAULT_CONV_ID.

    Args:
        ctx: MCP Context object containing request information

    Returns:
        Sanitized conversation ID or "_shared" as fallback
    """
    conv_id = DEFAULT_CONV_ID

    try:
        if ctx.request_context and ctx.request_context.request:
            raw_conv_id = ctx.request_context.request.headers.get("X-Conversation-ID")
            if raw_conv_id:
                # Sanitize: only allow alphanumeric, hyphens, and underscores
                # This prevents path traversal attacks
                conv_id = "".join(
                    c if c.isalnum() or c in "-_" else "_"
                    for c in raw_conv_id[:64]  # Limit length
                )
                logger.debug("Conversation ID from header: %s", conv_id)
    except Exception as e:
        logger.warning("Failed to extract conversation ID: %s", e)

    return conv_id
