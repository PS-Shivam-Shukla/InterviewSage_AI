"""
LLM Client unit tests — all tests use FakeLLMClient (zero real API calls).
"""

import pytest
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from app.core.config import settings
from app.core.llm_client import FakeLLMClient, LLMClient, _build_chat_model
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


class TestBuildChatModel:
    def test_ollama_provider_creates_chat_ollama(self, monkeypatch):
        monkeypatch.setattr(settings, "llm_provider", "ollama")
        model = _build_chat_model("qwen3:0.6b", 0.1, 2000)
        from langchain_ollama import ChatOllama
        from langchain_openai import ChatOpenAI

        assert isinstance(model, ChatOllama)
        assert not isinstance(model, ChatOpenAI)

    def test_openai_provider_creates_chat_openai(self, monkeypatch):
        monkeypatch.setattr(settings, "llm_provider", "openai")
        model = _build_chat_model("gpt-4o", 0.1, 2000)
        from langchain_ollama import ChatOllama
        from langchain_openai import ChatOpenAI

        assert isinstance(model, ChatOpenAI)
        assert not isinstance(model, ChatOllama)

    def test_unsupported_provider_raises_value_error(self, monkeypatch):
        monkeypatch.setattr(settings, "llm_provider", "unknown_provider")
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            _build_chat_model("some-model", 0.1, 2000)

    def test_ollama_structured_output_binding_uses_chat_ollama(self, monkeypatch):
        monkeypatch.setattr(settings, "llm_provider", "ollama")
        client = LLMClient(model_name="qwen3:0.6b")
        from langchain_ollama import ChatOllama
        from langchain_openai import ChatOpenAI

        assert isinstance(client._primary, ChatOllama)
        assert not isinstance(client._primary, ChatOpenAI)
        assert isinstance(client._fallback, ChatOllama)
        assert not isinstance(client._fallback, ChatOpenAI)

        structured_model = client._primary.with_structured_output(SampleOutput)
        first_stage = structured_model.first
        bound_model = getattr(first_stage, "bound", first_stage)
        assert isinstance(bound_model, ChatOllama)
        assert not isinstance(bound_model, ChatOpenAI)

