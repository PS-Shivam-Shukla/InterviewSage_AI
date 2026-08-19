"""
Official MCP Server CLI Entrypoint — STDIO Transport.

Run as a standalone process:
    python -m app.mcp.cli

Exposes application MCP tools and resources over standard input/output (stdio)
conforming to the official Model Context Protocol specification.
"""

from __future__ import annotations

import asyncio
import sys

from mcp.server.stdio import stdio_server

from app.mcp import mcp_server


async def main() -> None:
    official_server = mcp_server.official_server
    async with stdio_server() as (read_stream, write_stream):
        await official_server.run(
            read_stream,
            write_stream,
            official_server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
