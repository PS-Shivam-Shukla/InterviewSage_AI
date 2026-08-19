"""
Answer Sanity Guard (Section 10.12)
Deterministic Python pre-evaluator for intercepting EMPTY, NO_ANSWER, GIBBERISH, or OFF_TOPIC
candidate responses BEFORE calling the LLM EvaluationAgent.

Rules:
- Empty / whitespace answers -> EMPTY (Score 0/10, 0%)
- "I don't know", "idk", "not sure", "no idea" -> NO_ANSWER (Score 0/10, 0%)
- Repeated characters / low entropy -> GIBBERISH (Score 0/10, 0%)
- Valid technical answers -> VALID_ANSWER (Proceeds to LLM EvaluationAgent)
"""

import re

from pydantic import BaseModel, Field

# Phrase set for explicit candidate non-answers
NON_ANSWER_PHRASES = {
    "i dont know",
    "i don't know",
    "idk",
    "not sure",
    "no idea",
    "i have no idea",
    "i don't have experience",
    "no experience",
    "can't answer",
    "cannot answer",
    "don't know",
    "dont know",
    "i do not know",
    "i am not sure",
    "haven't used this",
    "have not used this",
    "skip",
    "pass",
    "no answer",
    "n/a",
    "na",
}


class SanityGuardResult(BaseModel):
    is_valid_answer: bool
    answer_quality: str  # EMPTY | NO_ANSWER | GIBBERISH | VALID_ANSWER
    score_1_10: int = Field(ge=0, le=10)
    score_pct: int = Field(ge=0, le=100)
    reason: str
    needs_llm_eval: bool


class AnswerSanityGuard:

    @classmethod
    def evaluate(cls, answer_text: str | None, round_type: str | None = None) -> SanityGuardResult:
        """
        Deterministically evaluates answer sanity before any LLM processing.
        Allows category-aware evaluation for APTITUDE / numeric / boolean / symbolic answers.
        """
        if not answer_text or not isinstance(answer_text, str):
            return SanityGuardResult(
                is_valid_answer=False,
                answer_quality="EMPTY",
                score_1_10=0,
                score_pct=0,
                reason="Candidate submitted an empty response.",
                needs_llm_eval=False,
            )

        clean = answer_text.strip()
        if not clean:
            return SanityGuardResult(
                is_valid_answer=False,
                answer_quality="EMPTY",
                score_1_10=0,
                score_pct=0,
                reason="Candidate submitted whitespace only.",
                needs_llm_eval=False,
            )

        lower_clean = clean.lower()

        # Prompt Injection Guardrail Check
        from app.kernel.guardrails import Guardrails
        guard = Guardrails()
        is_injection, _ = guard.scan_prompt_injection(clean)
        if is_injection:
            return SanityGuardResult(
                is_valid_answer=False,
                answer_quality="INVALID_FORMAT",
                score_1_10=0,
                score_pct=0,
                reason="Prompt injection detected in candidate input.",
                needs_llm_eval=False,
            )

        # 1. Exact or phrase match for explicit "I don't know" non-answers
        if lower_clean in NON_ANSWER_PHRASES or any(lower_clean == p for p in NON_ANSWER_PHRASES):
            return SanityGuardResult(
                is_valid_answer=False,
                answer_quality="NO_ANSWER",
                score_1_10=0,
                score_pct=0,
                reason="Candidate explicitly indicated they do not know the answer.",
                needs_llm_eval=False,
            )

        # Regex match for common variations like "i really dont know" or "i'm not sure about this"
        if re.search(
            r"\b(i\s*(don'?t|dont)\s*know|idk|no\s*idea|not\s*sure|no\s*experience)\b", lower_clean
        ):
            # If the response is short (< 50 chars) and contains a non-answer phrase, classify as NO_ANSWER
            if len(clean) < 50:
                return SanityGuardResult(
                    is_valid_answer=False,
                    answer_quality="NO_ANSWER",
                    score_1_10=0,
                    score_pct=0,
                    reason="Candidate indicated lack of knowledge or experience for this question.",
                    needs_llm_eval=False,
                )

        # Aptitude response pattern check (numeric, currency, boolean, ratio, options, fractions, units)
        is_aptitude_round = (round_type or "").upper() == "APTITUDE"
        is_numeric_or_boolean_format = bool(
            re.match(
                r"^[\$\€\£\₹]?\s*-?\d+(\.\d+)?\s*[\$\€\£\₹\%\s]*(km/h|km|h|days?|hours?|years?|rupees|dollars|percent)?$",
                lower_clean,
            )
            or lower_clean in {"true", "false", "yes", "no"}
            or lower_clean in {"a", "b", "c", "d", "option a", "option b", "option c", "option d"}
            or re.match(r"^\d+\s*:\s*\d+$", lower_clean)  # ratio like 8:15
            or re.match(r"^\d+\s*/\s*\d+$", lower_clean)  # fraction like 1/2
            or re.match(
                r"^\d+%\s*(increase|decrease)?$", lower_clean
            )  # percentage like 4% decrease
        )

        # For Aptitude round, if response is not a valid quantitative or option format, flag as GIBBERISH/OFF_TOPIC
        if is_aptitude_round and not is_numeric_or_boolean_format:
            return SanityGuardResult(
                is_valid_answer=False,
                answer_quality="GIBBERISH",
                score_1_10=0,
                score_pct=0,
                reason="Candidate response is not a valid quantitative or option answer for an aptitude question.",
                needs_llm_eval=False,
            )

        # 2. Repeated character, repeating substring, or low-entropy gibberish check
        no_space = lower_clean.replace(" ", "")
        if no_space:
            unique_chars = len(set(no_space))
            unique_char_ratio = unique_chars / float(len(no_space))

            # Detect repeated short patterns (e.g., "asdfasdfasdf", "abcabc", "aaaaaaaa")
            pattern_match = False
            for pat_len in range(1, 6):
                if len(no_space) >= pat_len * 2:
                    pat = no_space[:pat_len]
                    if (
                        pat * (len(no_space) // pat_len)
                        == no_space[: pat_len * (len(no_space) // pat_len)]
                    ):
                        pattern_match = True
                        break

            # If it's a valid numeric/boolean/aptitude answer, do NOT flag low-entropy or unique_chars <= 4 as gibberish!
            if is_aptitude_round or is_numeric_or_boolean_format:
                # Only flag as gibberish if repeating pattern ("aaaaa", "asdfasdf") or single repeated character
                if pattern_match and unique_chars <= 2:
                    return SanityGuardResult(
                        is_valid_answer=False,
                        answer_quality="GIBBERISH",
                        score_1_10=0,
                        score_pct=0,
                        reason="Candidate response contains repeated character gibberish.",
                        needs_llm_eval=False,
                    )
            else:
                if len(clean) < 80 and (
                    unique_char_ratio < 0.25 or pattern_match or unique_chars <= 4
                ):
                    return SanityGuardResult(
                        is_valid_answer=False,
                        answer_quality="GIBBERISH",
                        score_1_10=0,
                        score_pct=0,
                        reason="Candidate response contains low-entropy or repeated character gibberish.",
                        needs_llm_eval=False,
                    )

        # 3. Known single-word non-technical filler (only for non-aptitude)
        filler_words = {
            "test",
            "abc",
            "asdf",
            "qwerty",
            "hello",
            "hi",
            "hey",
            "lol",
            "haha",
            "ok",
            "okay",
        }
        if lower_clean in filler_words and not is_aptitude_round:
            return SanityGuardResult(
                is_valid_answer=False,
                answer_quality="GIBBERISH",
                score_1_10=0,
                score_pct=0,
                reason="Response contains non-technical filler words.",
                needs_llm_eval=False,
            )

        # Valid answer -> proceed to evaluation
        return SanityGuardResult(
            is_valid_answer=True,
            answer_quality="VALID_ANSWER",
            score_1_10=0,
            score_pct=0,
            reason="Answer contains valid candidate text; proceeding to evaluation.",
            needs_llm_eval=True,
        )
