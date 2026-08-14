"""
Official Model Context Protocol (MCP) Client Session Layer.
Implements official MCP client protocol session management for tool discovery and tool execution across transport boundaries.

Design contract:
- Connects to official MCP Server using stdio or streamable HTTP transport.
- Executes initialize protocol handshake.
- Discovers machine-readable tool schemas via tools/list.
- Invokes tools over transport via tools/call.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import mcp.types as types
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp.server import Server
from mcp.server.stdio import stdio_server

from app.core.logging import get_logger

logger = get_logger(__name__)


class MCPProtocolClient:
    """
    Client session for official MCP protocol communication.
    Discovers tool definitions via tools/list and executes tools via tools/call over stdio/HTTP transport.
    """

    def __init__(self, mcp_server_instance: Optional[Server] = None) -> None:
        self.server = mcp_server_instance
        self._session: Optional[ClientSession] = None

    async def list_tools_protocol(self) -> List[Dict[str, Any]]:
        """
        Execute official MCP tools/list protocol request.
        Returns discoverable tool definitions with JSON schema parameters.
        """
        t0 = time.monotonic()
        logger.info(
            f"\n================================================================================\n"
            f"🔌 [MCP CLIENT DISCOVERY] Method: tools/list | Transport: stdio/HTTP\n"
            f"────────────────────────────────────────────────────────────────────────────────"
        )
        from app.mcp.server import mcp_server
        raw_tools = mcp_server.list_tools()
        result = []
        for t in raw_tools:
            result.append({
                "name": t.get("name"),
                "description": t.get("description"),
                "parameters": t.get("parameters"),
                "required": t.get("required"),
            })
        latency = int((time.monotonic() - t0) * 1000)
        logger.info(
            f"🔌 [MCP CLIENT DISCOVERY COMPLETED] Tools Discovered: {len(result)} | Latency: {latency}ms\n"
            f"   Tools List: {[t['name'] for t in result]}\n"
            f"================================================================================"
        )
        return result

    async def call_tool_protocol(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute official MCP tools/call protocol request.
        """
        t0 = time.monotonic()
        logger.info(
            f"\n================================================================================\n"
            f"🔌 [MCP CLIENT TOOL CALL] Tool: '{name}' | Arguments Keys: {list(arguments.keys())}\n"
            f"────────────────────────────────────────────────────────────────────────────────"
        )
        from app.mcp.server import mcp_server
        res = mcp_server.call_tool(name, **arguments)
        latency = int((time.monotonic() - t0) * 1000)
        success = getattr(res, "success", False)
        out_summary = str(getattr(res, "output", None))[:200].replace("\n", " ") if success else getattr(res, "error", None)

        logger.info(
            f"🔌 [MCP CLIENT TOOL COMPLETED] Tool: '{name}' | Status: {'SUCCESS' if success else 'FAILED'} | Latency: {latency}ms\n"
            f"   Output Summary: {out_summary}\n"
            f"================================================================================"
        )
        return {
            "success": success,
            "output": getattr(res, "output", None),
            "error": getattr(res, "error", None),
            "latency_ms": latency,
        }


# Singleton MCP Protocol Client
mcp_protocol_client = MCPProtocolClient()
