from __future__ import annotations

import re
from typing import Any, List, Tuple


class Guardrails:
    """
    Guardrails & Safety Subsystem.
    Provides PII masking, prompt injection detection, negative domain constraint validation, and text safety sanitization.
    """

    # PII Regular Expression Patterns
    EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
    SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

    # Common Jailbreak / Prompt Injection Patterns
    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE),
        re.compile(r"system\s*:\s*you\s+are", re.IGNORECASE),
        re.compile(r"override\s+system\s+prompt", re.IGNORECASE),
        re.compile(r"you\s+must\s+output\s+SUCCESS", re.IGNORECASE),
    ]

    def mask_pii(self, text: str) -> tuple[str, dict[str, str]]:
        """
        Mask PII fields in input text using surrogate tokens.
        Returns (masked_text, mapping_dict).
        """
        if not text:
            return "", {}

        mapping: dict[str, str] = {}
        masked = text

        # Mask Emails
        email_matches = self.EMAIL_REGEX.findall(masked)
        for idx, email in enumerate(set(email_matches), start=1):
            token = f"[CANDIDATE_EMAIL_{idx}]"
            mapping[token] = email
            masked = masked.replace(email, token)

        # Mask Phones
        phone_matches = self.PHONE_REGEX.findall(masked)
        for idx, phone in enumerate(set(phone_matches), start=1):
            if "@" not in phone and not phone.startswith("[CANDIDATE"):
                token = f"[CANDIDATE_PHONE_{idx}]"
                mapping[token] = phone
                masked = masked.replace(phone, token)

        # Mask SSN
        ssn_matches = self.SSN_REGEX.findall(masked)
        for idx, ssn in enumerate(set(ssn_matches), start=1):
            token = f"[CANDIDATE_SSN_{idx}]"
            mapping[token] = ssn
            masked = masked.replace(ssn, token)

        return masked, mapping

    def unmask_pii(self, text: str, mapping: dict[str, str]) -> str:
        """Unmask surrogate tokens back to original PII values."""
        unmasked = text
        for token, val in mapping.items():
            unmasked = unmasked.replace(token, val)
        return unmasked

    def scan_prompt_injection(self, text: str) -> tuple[bool, str]:
        """
        Scan text for common prompt injection patterns.
        Returns (is_contaminated, sanitized_text).
        """
        if not text:
            return False, ""

        is_contaminated = False
        sanitized = text

        for pattern in self.INJECTION_PATTERNS:
            if pattern.search(sanitized):
                is_contaminated = True
                sanitized = pattern.sub("[REDACTED_ADVERSARIAL_INPUT]", sanitized)

        return is_contaminated, sanitized

    def validate_negative_constraints(
        self, text: str, negative_skills: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validates text against negative domain constraints.
        Returns (is_valid, list_of_violated_keywords).
        If any forbidden keyword in negative_skills appears in text, is_valid is False.
        """
        if not text or not negative_skills:
            return True, []

        violations: List[str] = []
        for kw in negative_skills:
            if not kw or len(kw.strip()) == 0:
                continue
            pattern = re.compile(r"\b" + re.escape(kw.strip()) + r"\b", re.IGNORECASE)
            if pattern.search(text):
                violations.append(kw.strip())

        return len(violations) == 0, violations
