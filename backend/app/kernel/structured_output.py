from __future__ import annotations

import json
import re
from typing import Any, Type, TypeVar
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class StructuredOutputParser:
    """
    Structured Output & Validation Subsystem.
    Parses, validates, and estimates confidence for model responses against Pydantic schemas.
    """

    @staticmethod
    def extract_json_block(raw_text: str) -> str:
        """
        Extract JSON substring from model text (handles markdown ```json blocks).
        """
        if not raw_text:
            return ""

        # Check for ```json ... ``` markdown code block
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Check for raw JSON object bounds { ... }
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return raw_text[start : end + 1].strip()

        return raw_text.strip()

    def parse(self, raw_text: str, schema_class: Type[T]) -> tuple[T | None, float, str | None]:
        """
        Parse raw model text into a validated Pydantic schema instance.
        Returns: (parsed_instance, confidence_score, error_message)
        """
        json_str = self.extract_json_block(raw_text)
        if not json_str:
            return None, 0.0, "No JSON structure found in output text."

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            return None, 0.0, f"JSON Syntax Error: {str(exc)}"

        try:
            instance = schema_class.model_validate(data)
            confidence = self.estimate_confidence(data)
            return instance, confidence, None
        except ValidationError as val_err:
            return None, 0.2, f"Schema Validation Error: {str(val_err)}"

    @staticmethod
    def estimate_confidence(parsed_data: dict[str, Any]) -> float:
        """
        Estimate structural confidence score (0.0 to 1.0) based on payload completeness.
        """
        if not parsed_data:
            return 0.0

        total_keys = len(parsed_data)
        non_null_keys = sum(1 for v in parsed_data.values() if v not in (None, "", [], {}))

        base_ratio = non_null_keys / total_keys if total_keys > 0 else 0.0
        # High confidence baseline for valid parsed dicts
        return round(0.5 + (0.5 * base_ratio), 2)
