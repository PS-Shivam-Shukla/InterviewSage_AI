"""
Question Relevance Service (Section 10.6)
Deterministic Python service for technology entity normalization, 4-tier skill classification,
lexical/paraphrase duplicate detection, and multi-gate question validation.

Responsibilities:
1. Entity Normalization: Postgres -> PostgreSQL, JS -> JavaScript, TS -> TypeScript, etc.
2. Skill Tiering: STRONG_MATCH (Work Experience), POSSIBLE_MATCH (Skills List), JD_GAP (JD required), UNRELATED.
3. Lexical Similarity & Duplicate Detection: N-gram character overlap & TF-IDF Cosine similarity.
4. Hard Validation Gates: Difficulty Ceiling -> Tech Safety -> Experience Evidence -> Paraphrase Duplicates.
"""

import math
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from pydantic import BaseModel, Field


# Controlled technology alias dictionary for deterministic normalization
TECH_ALIASES: Dict[str, str] = {
    "postgres": "PostgreSQL",
    "postgresql db": "PostgreSQL",
    "postgres db": "PostgreSQL",
    "js": "JavaScript",
    "ts": "TypeScript",
    "react.js": "React",
    "reactjs": "React",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "fast api": "FastAPI",
    "fastapi": "FastAPI",
    "rest api": "REST",
    "restful api": "REST",
    "restful": "REST",
    "py": "Python",
    "python3": "Python",
    "k8s": "Kubernetes",
    "docker.js": "Docker",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "azure": "Azure",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",
    "spring": "Spring",
    "java": "Java",
    "golang": "Go",
    "go": "Go",
    "rust": "Rust",
    "vue": "Vue",
    "vue.js": "Vue",
    "angular": "Angular",
    "c#": "C#",
}


class TechEntityNormalizer:

    @classmethod
    def normalize_entity(cls, text: str) -> str:
        """Normalizes technology terms using controlled dictionary."""
        if not text:
            return ""
        clean = text.strip()
        lower = clean.lower()
        if lower in TECH_ALIASES:
            return TECH_ALIASES[lower]
        return clean

    @classmethod
    def extract_and_normalize_entities(cls, text: str) -> Set[str]:
        """Extracts technology entities from text and normalizes them."""
        if not text:
            return set()
        
        entities = set()
        # Check against known aliases
        lower_text = text.lower()
        for alias, normalized in TECH_ALIASES.items():
            pattern = r"\b" + re.escape(alias) + r"\b"
            if re.search(pattern, lower_text):
                entities.add(normalized)

        # Standard technical word extractor
        tokens = re.findall(r"\b[A-Za-z0-9\+\#\.\-]{2,}\b", text)
        for token in tokens:
            norm = cls.normalize_entity(token)
            if norm:
                entities.add(norm)
        return entities


class SkillClassification(BaseModel):
    skill_name: str
    tier: str  # STRONG_MATCH | POSSIBLE_MATCH | JD_GAP | UNRELATED
    weight: float
    evidence_found: bool = False


class QuestionRelevanceResult(BaseModel):
    accepted: bool
    reason: str
    skill_tier: str  # STRONG_MATCH | POSSIBLE_MATCH | JD_GAP | UNRELATED
    matched_entities: List[str] = Field(default_factory=list)
    unmatched_entities: List[str] = Field(default_factory=list)
    lexical_score: float = 0.0
    keyword_score: float = 0.0
    experience_evidence_score: float = 0.0
    duplicate_score: float = 0.0
    difficulty_allowed: bool = True


class LexicalSimilarityEngine:

    @classmethod
    def _clean_text(cls, text: str) -> str:
        """Strips common non-technical question starters and stop words for robust duplicate checking."""
        if not text:
            return ""
        stop_words = {
            "what", "is", "a", "an", "the", "how", "do", "does", "you", "explain", "in",
            "and", "why", "it", "used", "to", "for", "with", "can", "work", "works"
        }
        words = re.findall(r"\w+", text.lower())
        meaningful = [w for w in words if w not in stop_words and len(w) > 1]
        return " ".join(meaningful) if meaningful else text.lower()

    @classmethod
    def char_ngram_similarity(cls, text1: str, text2: str, n: int = 3) -> float:
        """Calculates character N-gram Jaccard similarity for lexical paraphrase detection."""
        c1 = cls._clean_text(text1)
        c2 = cls._clean_text(text2)
        if not c1 or not c2:
            return 0.0
        if c1 == c2:
            return 1.0

        ngrams1 = set(c1[i : i + n] for i in range(len(c1) - n + 1))
        ngrams2 = set(c2[i : i + n] for i in range(len(c2) - n + 1))

        if not ngrams1 or not ngrams2:
            return 0.0

        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)
        return intersection / float(union) if union > 0 else 0.0

    @classmethod
    def word_tfidf_cosine(cls, text1: str, text2: str) -> float:
        """Calculates word-level cosine similarity on cleaned technical tokens."""
        c1 = cls._clean_text(text1)
        c2 = cls._clean_text(text2)
        if not c1 or not c2:
            return 0.0

        words1 = re.findall(r"\w+", c1)
        words2 = re.findall(r"\w+", c2)

        if not words1 or not words2:
            return 0.0

        freq1: Dict[str, int] = {}
        freq2: Dict[str, int] = {}
        for w in words1:
            freq1[w] = freq1.get(w, 0) + 1
        for w in words2:
            freq2[w] = freq2.get(w, 0) + 1

        all_words = set(freq1.keys()) | set(freq2.keys())
        dot_product = sum(freq1.get(w, 0) * freq2.get(w, 0) for w in all_words)
        mag1 = math.sqrt(sum(v ** 2 for v in freq1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in freq2.values()))

        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot_product / (mag1 * mag2)

    @classmethod
    def word_ngram_similarity(cls, text1: str, text2: str, n: int = 2) -> float:
        """Calculates word N-gram Jaccard similarity for phrase matching."""
        if not text1 or not text2:
            return 0.0
        words1 = re.findall(r"\w+", text1.lower())
        words2 = re.findall(r"\w+", text2.lower())

        if len(words1) < n or len(words2) < n:
            set1 = set(words1)
            set2 = set(words2)
            if not set1 or not set2:
                return 0.0
            return len(set1 & set2) / float(len(set1 | set2))

        ngrams1 = set(tuple(words1[i : i + n]) for i in range(len(words1) - n + 1))
        ngrams2 = set(tuple(words2[i : i + n]) for i in range(len(words2) - n + 1))

        if not ngrams1 or not ngrams2:
            return 0.0

        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)
        return intersection / float(union) if union > 0 else 0.0

    @classmethod
    def compute_hybrid_duplicate_score(cls, new_question: str, existing_questions: List[Dict[str, Any]]) -> Tuple[float, Optional[str]]:
        """
        Computes maximum lexical duplicate score across past questions.
        Returns (max_score, matching_question_text).
        """
        max_score = 0.0
        matched_q = None

        for q in existing_questions:
            old_text = q.get("question_text", "")
            if not old_text:
                continue

            char_sim = cls.char_ngram_similarity(new_question, old_text)
            word_sim = cls.word_ngram_similarity(new_question, old_text, n=2)
            cosine_sim = cls.word_tfidf_cosine(new_question, old_text)
            hybrid = max(char_sim, word_sim, cosine_sim)

            if hybrid > max_score:
                max_score = hybrid
                matched_q = old_text

        return max_score, matched_q


class QuestionRelevanceService:

    @classmethod
    def classify_skills(
        cls,
        candidate_skills: List[str],
        work_experience_bullets: List[str],
        jd_required_skills: List[str],
    ) -> Dict[str, SkillClassification]:
        """
        Classifies skills into STRONG_MATCH, POSSIBLE_MATCH, JD_GAP, or UNRELATED.
        """
        classified: Dict[str, SkillClassification] = {}
        exp_text_combined = " ".join(work_experience_bullets).lower()

        # Normalize lists
        norm_cand_skills = {TechEntityNormalizer.normalize_entity(s) for s in candidate_skills if s}
        norm_jd_skills = {TechEntityNormalizer.normalize_entity(s) for s in jd_required_skills if s}

        # 1. Candidate Skills
        for skill in norm_cand_skills:
            if not skill:
                continue
            lower_s = skill.lower()
            if lower_s in exp_text_combined or re.search(r"\b" + re.escape(lower_s) + r"\b", exp_text_combined):
                classified[skill] = SkillClassification(
                    skill_name=skill, tier="STRONG_MATCH", weight=1.0, evidence_found=True
                )
            else:
                classified[skill] = SkillClassification(
                    skill_name=skill, tier="POSSIBLE_MATCH", weight=0.6, evidence_found=False
                )

        # 2. JD Skills not in Candidate Skills
        for skill in norm_jd_skills:
            if not skill:
                continue
            if skill not in classified:
                classified[skill] = SkillClassification(
                    skill_name=skill, tier="JD_GAP", weight=0.4, evidence_found=False
                )

        return classified

    @classmethod
    def validate_question(
        cls,
        question_text: str,
        question_difficulty: str,
        relevant_experience_months: int,
        seniority_level: str,
        candidate_skills: List[str],
        work_experience_bullets: List[str],
        jd_required_skills: List[str],
        questions_asked: List[Dict[str, Any]],
        round_type: str = "technical",
    ) -> QuestionRelevanceResult:
        """
        Executes multi-gate validation pipeline.
        Gate Order:
        1. Difficulty Ceiling Check (QuestionDifficultyPolicy)
        2. Technology Entity Normalization & Safety Check (Rejects UNRELATED tech)
        3. Experience Evidence Check
        4. JD Relationship Check
        5. Lexical & Paraphrase Duplicate Check
        """
        # --- GATE 1: Difficulty Ceiling Check ---
        from app.services.difficulty_policy import QuestionDifficultyPolicy
        is_valid_diff, diff_reason = QuestionDifficultyPolicy.validate_question_difficulty(
            question_difficulty=question_difficulty,
            relevant_experience_months=relevant_experience_months,
            seniority_level=seniority_level,
        )
        if not is_valid_diff:
            return QuestionRelevanceResult(
                accepted=False,
                reason=f"GATE 1 FAILED (Difficulty Ceiling): {diff_reason}",
                skill_tier="UNRELATED",
                difficulty_allowed=False,
            )

        # --- GATE 2: Technology Entity Safety & Skill Classification ---
        classifications = cls.classify_skills(candidate_skills, work_experience_bullets, jd_required_skills)
        extracted_entities = TechEntityNormalizer.extract_and_normalize_entities(question_text)

        matched_entities = []
        unmatched_entities = []
        highest_tier = "UNRELATED"

        for entity in extracted_entities:
            if entity in classifications:
                matched_entities.append(entity)
                tier = classifications[entity].tier
                if tier == "STRONG_MATCH":
                    highest_tier = "STRONG_MATCH"
                elif tier == "POSSIBLE_MATCH" and highest_tier != "STRONG_MATCH":
                    highest_tier = "POSSIBLE_MATCH"
                elif tier == "JD_GAP" and highest_tier not in ("STRONG_MATCH", "POSSIBLE_MATCH"):
                    highest_tier = "JD_GAP"
            else:
                # Check if entity is a recognized technology alias (e.g., React, Spring Boot, Angular, Java)
                if entity.lower() in TECH_ALIASES or entity in TECH_ALIASES.values():
                    unmatched_entities.append(entity)

        # Reject UNRELATED technology if question introduces completely un-demonstrated/un-requested tech
        # (Allow general questions with 0 tech entities)
        if unmatched_entities and not matched_entities and round_type != "behavioral":
            return QuestionRelevanceResult(
                accepted=False,
                reason=f"GATE 2 FAILED (Unrelated Tech): Question references un-demonstrated technology {unmatched_entities}.",
                skill_tier="UNRELATED",
                unmatched_entities=unmatched_entities,
            )

        if not highest_tier or highest_tier == "UNRELATED":
            if matched_entities:
                highest_tier = "POSSIBLE_MATCH"
            elif round_type in ("behavioral", "company"):
                highest_tier = "STRONG_MATCH"  # Non-technical rounds valid without tech entities

        # --- GATE 3 & 4: Experience Evidence & JD Gap Policy Check ---
        if highest_tier == "JD_GAP":
            # JD Gap questions allowed only if difficulty stays strictly <= BASIC for intern/junior
            if relevant_experience_months <= 3 and question_difficulty.upper() not in ("BASIC", "EASY"):
                return QuestionRelevanceResult(
                    accepted=False,
                    reason=f"GATE 4 FAILED (JD Gap Ceiling): JD Gap skill question '{question_text[:50]}' exceeds BASIC ceiling for 2-month candidate.",
                    skill_tier="JD_GAP",
                    matched_entities=matched_entities,
                )

        # --- GATE 5: Lexical & Paraphrase Duplicate Check ---
        dup_score, matched_q = LexicalSimilarityEngine.compute_hybrid_duplicate_score(question_text, questions_asked)
        if dup_score > 0.35:
            return QuestionRelevanceResult(
                accepted=False,
                reason=f"GATE 5 FAILED (Paraphrase Duplicate): Question is too similar (score {dup_score:.2f}) to previous question '{matched_q}'.",
                skill_tier=highest_tier,
                matched_entities=matched_entities,
                duplicate_score=dup_score,
            )

        # All Gates Passed -> ACCEPTED
        return QuestionRelevanceResult(
            accepted=True,
            reason=f"Question ACCEPTED. Validated tier={highest_tier}, difficulty={question_difficulty}, duplicate_score={dup_score:.2f}.",
            skill_tier=highest_tier,
            matched_entities=matched_entities,
            unmatched_entities=unmatched_entities,
            lexical_score=0.85 if matched_entities else 0.5,
            keyword_score=1.0 if matched_entities else 0.5,
            experience_evidence_score=1.0 if highest_tier == "STRONG_MATCH" else 0.6,
            duplicate_score=dup_score,
            difficulty_allowed=True,
        )
