"""
JSON Validator & Structured Output Repair Subsystem for AI Gateway.
Validates LLM response JSON structure, repairs malformed JSON syntax, and auto-closes unclosed brackets.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional, Tuple
from app.core.logging import get_logger

logger = get_logger(__name__)


class JSONValidator:
    """
    Validates, cleans, and repairs structured JSON responses returned by LLM inference engines.
    """

    @staticmethod
    def strip_code_fences(text: str) -> str:
        """Strip markdown ```json and ``` code block wrappers."""
        if not text:
            return ""

        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        return cleaned

    @staticmethod
    def fix_trailing_commas(text: str) -> str:
        """Fix invalid trailing commas before closing braces or brackets."""
        text = re.sub(r",\s*([\}\]])", r"\1", text)
        return text

    @staticmethod
    def auto_close_json(text: str) -> str:
        """Auto-close missing closing braces or brackets in truncated JSON strings."""
        open_braces = text.count("{") - text.count("}")
        open_brackets = text.count("[") - text.count("]")

        repaired = text
        if open_brackets > 0:
            repaired += "]" * open_brackets
        if open_braces > 0:
            repaired += "}" * open_braces

        return repaired

    @staticmethod
    def extract_embedded_json(text: str) -> Optional[str]:
        """Extract first valid embedded JSON object or array string from text."""
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            return match.group(1)
        return None

    @classmethod
    def validate_and_repair(cls, raw_output: str) -> Tuple[bool, Optional[Dict[str, Any]], bool]:
        """
        Validate and repair raw LLM output.
        Returns (is_valid, parsed_dict, repair_performed).
        """
        if not raw_output or not raw_output.strip():
            return False, None, False

        # Attempt 1: Direct JSON parse
        try:
            parsed = json.loads(raw_output)
            if isinstance(parsed, dict):
                return True, parsed, False
        except Exception:
            pass

        # Attempt 2: Strip code fences
        cleaned = cls.strip_code_fences(raw_output)
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return True, parsed, True
        except Exception:
            pass

        # Attempt 3: Fix trailing commas
        cleaned = cls.fix_trailing_commas(cleaned)
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return True, parsed, True
        except Exception:
            pass

        # Attempt 4: Extract embedded JSON
        embedded = cls.extract_embedded_json(cleaned)
        if embedded:
            try:
                parsed = json.loads(embedded)
                if isinstance(parsed, dict):
                    return True, parsed, True
            except Exception:
                pass

        # Attempt 5: Auto-close truncated JSON
        closed_json = cls.auto_close_json(cleaned)
        try:
            parsed = json.loads(closed_json)
            if isinstance(parsed, dict):
                return True, parsed, True
        except Exception:
            pass

        logger.warning(f"JSONValidator failed to parse or repair structured output: {raw_output[:100]}...")
        return False, None, False
