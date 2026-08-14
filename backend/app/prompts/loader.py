"""
Prompt template loader.
Loads versioned prompt modules by agent name and version string.
"""

import importlib


def load_prompt(agent_name: str, version: str = "v1") -> object | None:
    """
    Load a prompt module for the given agent and version.

    Args:
        agent_name: e.g. "resume_agent", "evaluation_agent"
        version:    e.g. "v1", "v2"

    Returns:
        The prompt module (with .SYSTEM, .DEVELOPER, .VERSION attributes),
        or None if not found.
    """
    module_path = f"app.prompts.{agent_name}.{version}"
    try:
        return importlib.import_module(module_path)
    except ModuleNotFoundError:
        return None


def get_system_prompt(agent_name: str, version: str = "v1") -> str:
    mod = load_prompt(agent_name, version)
    if mod and hasattr(mod, "SYSTEM"):
        return mod.SYSTEM
    return f"You are the {agent_name} for InterviewSage AI."


def get_developer_prompt(agent_name: str, version: str = "v1") -> str:
    mod = load_prompt(agent_name, version)
    if mod and hasattr(mod, "DEVELOPER"):
        return mod.DEVELOPER
    return ""
