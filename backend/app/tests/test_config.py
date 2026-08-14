"""
Tests for application configuration validation and security enforcement.
Phase 1 - Sprint 1 Security Audit Compliance.
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_valid_configuration(monkeypatch):
    """Test that a valid configuration instantiates cleanly."""
    monkeypatch.setenv("SECRET_KEY", "valid-secret-key-that-is-at-least-32-characters-long-and-secure!")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")

    cfg = Settings()
    assert cfg.secret_key == "valid-secret-key-that-is-at-least-32-characters-long-and-secure!"
    assert cfg.environment == "development"
    assert cfg.debug is True
    assert cfg.database_url == "sqlite:///./test.db"


def test_missing_secret_key(monkeypatch):
    """Test that missing SECRET_KEY raises a ValidationError."""
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    assert "secret_key" in str(exc_info.value).lower() or "field required" in str(exc_info.value).lower()


def test_weak_secret_key_too_short(monkeypatch):
    """Test that SECRET_KEY under 32 characters raises a ValidationError."""
    monkeypatch.setenv("SECRET_KEY", "short-key-under-32-chars")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    assert "at least 32 characters" in str(exc_info.value)


def test_placeholder_secret_key_rejected(monkeypatch):
    """Test that known development/placeholder secret patterns are rejected."""
    placeholders = [
        "dev-secret-key-interviewsage-2026",
        "your-secret-key-here-change-in-production-1234567890",
        "dev-secret-key-change-in-production-1234567890",
        "change-this-insecure-production-secret-key-32bytes",
    ]
    for key in placeholders:
        monkeypatch.setenv("SECRET_KEY", key)
        with pytest.raises(ValidationError) as exc_info:
            Settings(_env_file=None)
        assert "known insecure development secret" in str(exc_info.value) or "pattern" in str(exc_info.value)


def test_debug_true_in_production_rejected(monkeypatch):
    """Test that DEBUG=True in production or staging environment raises a ValidationError."""
    monkeypatch.setenv("SECRET_KEY", "valid-secret-key-that-is-at-least-32-characters-long-and-secure!")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEBUG", "True")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    assert "strictly prohibited" in str(exc_info.value)


def test_debug_true_in_staging_rejected(monkeypatch):
    """Test that DEBUG=True in staging environment raises a ValidationError."""
    monkeypatch.setenv("SECRET_KEY", "valid-secret-key-that-is-at-least-32-characters-long-and-secure!")
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("DEBUG", "True")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    assert "strictly prohibited" in str(exc_info.value)


def test_invalid_database_url_scheme(monkeypatch):
    """Test that unsupported DATABASE_URL schemes raise a ValidationError."""
    monkeypatch.setenv("SECRET_KEY", "valid-secret-key-that-is-at-least-32-characters-long-and-secure!")
    monkeypatch.setenv("DATABASE_URL", "invalid_scheme://localhost/db")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    assert "scheme unsupported" in str(exc_info.value)


def test_invalid_environment_name(monkeypatch):
    """Test that invalid ENVIRONMENT values raise a ValidationError."""
    monkeypatch.setenv("SECRET_KEY", "valid-secret-key-that-is-at-least-32-characters-long-and-secure!")
    monkeypatch.setenv("ENVIRONMENT", "invalid_env_name")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    assert "ENVIRONMENT must be one of" in str(exc_info.value)
