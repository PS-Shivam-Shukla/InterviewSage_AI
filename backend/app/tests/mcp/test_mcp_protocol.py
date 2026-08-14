"""
Official MCP Protocol & Interoperability Integration Tests.
Verifies official MCP protocol client and server capabilities:
1. Tool discovery via tools/list protocol.
2. Tool execution via tools/call protocol.
3. Schema integrity and parameter validation.
"""

import pytest
import asyncio
from app.mcp.client import mcp_protocol_client
from app.mcp.server import mcp_server


@pytest.mark.asyncio
async def test_mcp_protocol_tools_list():
    """Verify official MCP tools/list protocol returns registered application tool schemas."""
    tools = await mcp_protocol_client.list_tools_protocol()
    assert len(tools) > 0

    tool_names = [t["name"] for t in tools]
    assert "score_answer_rubric" in tool_names
    assert "generate_report_pdf" in tool_names
    assert "persist_agent_output" in tool_names

    rubric_tool = next(t for t in tools if t["name"] == "score_answer_rubric")
    assert rubric_tool["description"] != ""
    assert isinstance(rubric_tool["parameters"], dict)


@pytest.mark.asyncio
async def test_mcp_protocol_tools_call_success():
    """Verify official MCP tools/call protocol executes registered tool handler and returns valid result."""
    call_res = await mcp_protocol_client.call_tool_protocol(
        "score_answer_rubric",
        {
            "question_type": "technical",
            "seniority_level": "MID",
        }
    )
    assert call_res["success"] is True
    assert "output" in call_res
    output = call_res["output"]
    assert "technical" in output or "rubric" in str(output).lower() or len(output) > 0


@pytest.mark.asyncio
async def test_mcp_protocol_tools_call_unknown_tool():
    """Verify official MCP tools/call protocol returns error result on unknown tool name."""
    call_res = await mcp_protocol_client.call_tool_protocol(
        "unknown_nonexistent_tool",
        {"arg": "val"}
    )
    assert call_res["success"] is False
    assert call_res["error"] is not None
    assert "Unknown tool" in call_res["error"]
