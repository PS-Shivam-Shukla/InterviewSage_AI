"""
Official Model Context Protocol (MCP) Client Session Layer.
Implements official MCP client protocol session management for tool discovery and tool execution across transport boundaries.

Design contract:
- Connects to official MCP Server using stdio or in-memory object stream transport.
- Executes initialize protocol handshake.
- Discovers machine-readable tool schemas via tools/list.
- Invokes tools over transport via tools/call.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import sys
import time
from typing import Any

from anyio import create_memory_object_stream
from mcp.client.session import ClientSession

from app.core.logging import get_logger

logger = get_logger(__name__)


def _run_async(coro):
    """Helper to safely run coroutines from both sync and async execution contexts."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(coro)).result()
    else:
        return asyncio.run(coro)


class MCPProtocolClient:
    """
    Client session for official MCP protocol communication.
    Discovers tool definitions via session.list_tools() and executes tools via session.call_tool()
    over official MCP JSON-RPC 2.0 transport channels.
    """

    def __init__(self, mcp_server_instance: Any | None = None) -> None:
        self._server_instance = mcp_server_instance

    def _get_server(self):
        if self._server_instance is not None:
            return self._server_instance
        from app.mcp.server import mcp_server

        return mcp_server

    async def list_tools_protocol(self) -> list[dict[str, Any]]:
        """
        Execute official MCP tools/list protocol request over a real ClientSession.
        Returns discoverable tool definitions with JSON schema parameters.
        """
        t0 = time.monotonic()
        logger.info(
            "\n================================================================================\n"
            "🔌 [MCP CLIENT DISCOVERY] Method: tools/list | Transport: ClientSession (AnyIO)\n"
            "────────────────────────────────────────────────────────────────────────────────"
        )
        server_obj = self._get_server()
        official_server = (
            getattr(server_obj, "official_server", server_obj)
            if hasattr(server_obj, "official_server")
            else server_obj
        )

        client_send, server_receive = create_memory_object_stream(100)
        server_send, client_receive = create_memory_object_stream(100)

        tools_result = []

        async def run_server():
            async with server_receive, server_send:
                try:
                    await official_server.run(
                        server_receive,
                        server_send,
                        official_server.create_initialization_options(),
                    )
                except Exception:
                    pass

        async def run_client():
            nonlocal tools_result
            async with client_receive, client_send:
                async with ClientSession(client_receive, client_send) as session:
                    await session.initialize()
                    res = await session.list_tools()
                    for t in res.tools:
                        tools_result.append(
                            {
                                "name": t.name,
                                "description": t.description,
                                "parameters": t.input_schema.get("properties", {})
                                if t.input_schema
                                else {},
                                "required": t.input_schema.get("required", [])
                                if t.input_schema
                                else [],
                            }
                        )

        server_task = asyncio.create_task(run_server())
        try:
            await run_client()
        finally:
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass

        latency = int((time.monotonic() - t0) * 1000)
        logger.info(
            f"🔌 [MCP CLIENT DISCOVERY COMPLETED] Tools Discovered: {len(tools_result)} | Latency: {latency}ms\n"
            f"   Tools List: {[t['name'] for t in tools_result]}\n"
            f"================================================================================"
        )
        return tools_result

    async def call_tool_protocol(
        self, name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute official MCP tools/call protocol request over a real ClientSession.
        """
        t0 = time.monotonic()
        logger.info(
            f"\n================================================================================\n"
            f"🔌 [MCP CLIENT TOOL CALL] Tool: '{name}' | Transport: ClientSession (AnyIO)\n"
            f"────────────────────────────────────────────────────────────────────────────────"
        )
        server_obj = self._get_server()
        official_server = (
            getattr(server_obj, "official_server", server_obj)
            if hasattr(server_obj, "official_server")
            else server_obj
        )

        client_send, server_receive = create_memory_object_stream(100)
        server_send, client_receive = create_memory_object_stream(100)

        call_result = None

        async def run_server():
            async with server_receive, server_send:
                try:
                    await official_server.run(
                        server_receive,
                        server_send,
                        official_server.create_initialization_options(),
                    )
                except Exception:
                    pass

        async def run_client():
            nonlocal call_result
            async with client_receive, client_send:
                async with ClientSession(client_receive, client_send) as session:
                    await session.initialize()
                    call_result = await session.call_tool(name, arguments)

        server_task = asyncio.create_task(run_server())
        try:
            await run_client()
        except Exception as exc:
            logger.warning(f"ClientSession call_tool protocol exception: {exc}")
        finally:
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass

        latency = int((time.monotonic() - t0) * 1000)

        if call_result is None or getattr(call_result, "is_error", False):
            err_text = "Tool execution failed on MCP server."
            if call_result and call_result.content:
                err_text = call_result.content[0].text
            logger.warning(
                f"🔌 [MCP CLIENT TOOL FAILED] Tool: '{name}' | Status: FAILED | Latency: {latency}ms\n"
                f"   Error: {err_text}\n"
                f"================================================================================"
            )
            return {
                "success": False,
                "output": None,
                "error": err_text,
                "latency_ms": latency,
            }

        # Parse text content back into Python output payload if JSON formatted
        raw_text = call_result.content[0].text if call_result.content else ""
        try:
            output_val = json.loads(raw_text)
        except Exception:
            output_val = raw_text

        out_summary = str(output_val)[:200].replace("\n", " ")
        logger.info(
            f"🔌 [MCP CLIENT TOOL COMPLETED] Tool: '{name}' | Status: SUCCESS | Latency: {latency}ms\n"
            f"   Output Summary: {out_summary}\n"
            f"================================================================================"
        )
        return {
            "success": True,
            "output": output_val,
            "error": None,
            "latency_ms": latency,
        }

    async def list_tools_stdio_protocol(self) -> list[dict[str, Any]]:
        """
        Execute official MCP tools/list over genuine STDIO subprocess transport (python -m app.mcp.cli).
        """
        from mcp.client.stdio import stdio_client, StdioServerParameters
        import sys

        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "app.mcp.cli"],
            env=None,
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                res = await session.list_tools()
                return [
                    {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.input_schema.get("properties", {}) if t.input_schema else {},
                    }
                    for t in res.tools
                ]

    async def call_tool_stdio_protocol(
        self, name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute official MCP tools/call over genuine STDIO subprocess transport (python -m app.mcp.cli).
        """
        from mcp.client.stdio import stdio_client, StdioServerParameters
        import sys

        t0 = time.monotonic()
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "app.mcp.cli"],
            env=None,
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                call_result = await session.call_tool(name, arguments)
                latency = int((time.monotonic() - t0) * 1000)

                if call_result is None or getattr(call_result, "is_error", False):
                    err_text = call_result.content[0].text if call_result and call_result.content else "Tool execution failed."
                    return {"success": False, "output": None, "error": err_text, "latency_ms": latency}

                raw_text = call_result.content[0].text if call_result.content else ""
                try:
                    output_val = json.loads(raw_text)
                except Exception:
                    output_val = raw_text

                return {"success": True, "output": output_val, "error": None, "latency_ms": latency}

    def list_tools_protocol_sync(self) -> list[dict[str, Any]]:
        """Synchronous wrapper for list_tools_protocol for sync worker threads."""
        return _run_async(self.list_tools_protocol())

    def call_tool_protocol_sync(
        self, name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Synchronous wrapper for call_tool_protocol for sync worker threads."""
        return _run_async(self.call_tool_protocol(name, arguments))


# Singleton MCP Protocol Client
mcp_protocol_client = MCPProtocolClient()
