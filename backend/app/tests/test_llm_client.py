"""
LLM Client unit tests — all tests use FakeLLMClient (zero real API calls).
"""

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from app.core.llm_client import FakeLLMClient, LLMClient
from app.prompts.loader import get_developer_prompt, get_system_prompt, load_prompt


class SampleOutput(BaseModel):
    message: str
    score: int


class TestFakeLLMClient:
    def test_invoke_returns_preset_response(self):
        client = FakeLLMClient(responses=["Hello from LLM!"])
        msgs = [HumanMessage(content="Hi")]
        result = client.invoke(msgs)
        assert result == "Hello from LLM!"

    def test_invoke_returns_default_when_exhausted(self):
        client = FakeLLMClient(responses=["first"])
        client.invoke([HumanMessage(content="1")])
        result = client.invoke([HumanMessage(content="2")])
        assert result == "Fake LLM response"

    def test_invoke_structured_with_pydantic_instance(self):
        expected = SampleOutput(message="hi", score=9)
        client = FakeLLMClient(responses=[expected])
        result = client.invoke_structured([HumanMessage(content="x")], SampleOutput)
        assert isinstance(result, SampleOutput)
        assert result.score == 9

    def test_invoke_structured_with_dict(self):
        client = FakeLLMClient(responses=[{"message": "ok", "score": 7}])
        result = client.invoke_structured([HumanMessage(content="x")], SampleOutput)
        assert result.score == 7

    def test_calls_recorded(self):
        client = FakeLLMClient(responses=["a", "b"])
        client.invoke([HumanMessage(content="one")])
        client.invoke([HumanMessage(content="two")])
        assert len(client.calls) == 2

    def test_build_messages_with_system_only(self):
        msgs = LLMClient.build_messages(
            system_prompt="You are a bot.",
            user_content="Hello",
        )
        assert any(isinstance(m, SystemMessage) for m in msgs)
        assert any(isinstance(m, HumanMessage) for m in msgs)

    def test_build_messages_with_developer(self):
        msgs = LLMClient.build_messages(
            system_prompt="System",
            user_content="User content",
            developer_prompt="Developer instructions",
        )
        # Should have 2 SystemMessage + 1 HumanMessage
        system_msgs = [m for m in msgs if isinstance(m, SystemMessage)]
        assert len(system_msgs) == 2


class TestPromptLoader:
    def test_load_resume_agent_v1(self):
        mod = load_prompt("resume_agent", "v1")
        assert mod is not None
        assert hasattr(mod, "SYSTEM")
        assert hasattr(mod, "DEVELOPER")
        assert mod.VERSION == "v1"

    def test_load_nonexistent_returns_none(self):
        mod = load_prompt("nonexistent_agent", "v99")
        assert mod is None

    def test_get_system_prompt_known(self):
        prompt = get_system_prompt("evaluation_agent", "v1")
        assert "Evaluation Agent" in prompt

    def test_get_system_prompt_fallback(self):
        prompt = get_system_prompt("does_not_exist", "v1")
        assert "does_not_exist" in prompt

    def test_get_developer_prompt_known(self):
        prompt = get_developer_prompt("resume_agent", "v1")
        assert len(prompt) > 10

    def test_competency_mapping_has_sum_rule(self):
        prompt = get_developer_prompt("competency_mapping_agent", "v1")
        assert "100" in prompt
