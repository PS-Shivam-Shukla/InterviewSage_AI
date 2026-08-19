import asyncio
import pytest
from anyio import create_memory_object_stream
from mcp.client.session import ClientSession

from app.mcp import mcp_server
from app.mcp.client import mcp_protocol_client
from app.tools.executor import tool_executor


@pytest.mark.asyncio
async def test_mcp_protocol_client_session_handshake():
    """Verify official ClientSession initialization handshake and transport communication."""
    client_send, server_receive = create_memory_object_stream(100)
    server_send, client_receive = create_memory_object_stream(100)

    official_server = mcp_server.official_server

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

    server_task = asyncio.create_task(run_server())

    async with client_receive, client_send:
        async with ClientSession(client_receive, client_send) as session:
            # 1. Initialization Handshake
            init_res = await session.initialize()
            assert init_res is not None

            # 2. List tools over protocol session
            tools_res = await session.list_tools()
            tool_names = [t.name for t in tools_res.tools]
            assert "score_answer_rubric" in tool_names

            # 3. Call tool over protocol session
            call_res = await session.call_tool(
                "score_answer_rubric",
                {"question_type": "behavioral", "seniority_level": "SENIOR"},
            )
            assert call_res is not None
            assert call_res.is_error is False
            assert len(call_res.content) > 0

    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass


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
        },
    )
    assert call_res["success"] is True
    assert "output" in call_res
    output = call_res["output"]
    assert "technical" in output or "rubric" in str(output).lower() or len(output) > 0


@pytest.mark.asyncio
async def test_mcp_protocol_tools_call_unknown_tool():
    """Verify official MCP tools/call protocol returns error result on unknown tool name."""
    call_res = await mcp_protocol_client.call_tool_protocol(
        "unknown_nonexistent_tool", {"arg": "val"}
    )
    assert call_res["success"] is False
    assert call_res["error"] is not None
    assert "Unknown tool" in call_res["error"]


def test_tool_executor_observation_normalization():
    """Verify ToolExecutor converts real MCP ClientSession results into structured Observations."""
    obs = tool_executor.execute_tool(
        "score_answer_rubric",
        {"question_type": "fundamentals", "seniority_level": "JUNIOR"},
    )
    assert obs.tool_name == "score_answer_rubric"
    assert obs.success is True
    assert obs.output is not None
    assert obs.error is None
    assert obs.latency_ms >= 0


@pytest.mark.asyncio
async def test_mcp_stdio_subprocess_interop():
    """Finding 11: Interoperability test proving ClientSession over stdio subprocess transport with app.mcp.cli."""
    import sys
    from mcp.client.stdio import StdioServerParameters, stdio_client

    server_params = StdioServerParameters(
        command=sys.executable, args=["-m", "app.mcp.cli"], env=None
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            init_res = await session.initialize()
            assert init_res is not None

            tools_res = await session.list_tools()
            tool_names = [t.name for t in tools_res.tools]
            assert "score_answer_rubric" in tool_names
            assert "generate_report_pdf" in tool_names

            call_res = await session.call_tool(
                "score_answer_rubric",
                {"question_type": "technical", "seniority_level": "SENIOR"},
            )
            assert call_res is not None
            assert call_res.is_error is False
            assert len(call_res.content) > 0

