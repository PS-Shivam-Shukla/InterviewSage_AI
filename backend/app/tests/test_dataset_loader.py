"""
Unit Tests for GoldenDatasetManager Subsystem.
Verifies dataset loading, sample parsing, and edge case retrieval.
"""

from app.evaluation.datasets import GoldenDatasetManager


def test_dataset_manager_load_questions():
    """Verify dataset manager loads interview questions from golden_dataset JSON files."""
    mgr = GoldenDatasetManager()
    questions = mgr.get_interview_questions()

    assert len(questions) > 0
    assert any(q.id == "q101" for q in questions)
    assert questions[0].question is not None
    assert isinstance(questions[0].target_concepts, list)


def test_dataset_manager_load_edge_cases():
    """Verify dataset manager loads edge cases."""
    mgr = GoldenDatasetManager()
    edge_cases = mgr.get_edge_cases()

    assert len(edge_cases) > 0
    assert any(c.id == "edge_001" for c in edge_cases)


def test_dataset_manager_full_benchmark_dataset():
    """Verify full benchmark dataset combines standard questions and edge cases."""
    mgr = GoldenDatasetManager()
    full_ds = mgr.load_full_benchmark_dataset()

    assert len(full_ds) >= len(mgr.get_interview_questions())
