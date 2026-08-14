"""
Application configuration module.
Loads and validates environment variables using Pydantic BaseSettings.
Strict enterprise security validation enforced at startup.
"""


from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Known weak / placeholder secret patterns to reject
REJECTED_SECRET_PATTERNS = [
    "dev-secret-key-interviewsage-2026",
    "your-secret-key-here-change-in-production",
    "dev-secret-key-change-in-production",
    "change-this-insecure-production-secret-key",
    "your_secret_key",
    "change_in_production",
    "dev-secret-key-placeholder",
    "secret_key_placeholder",
    "change_this_secret",
]


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables with strict startup validation.
    """

    # Application
    app_name: str = Field(default="InterviewSage AI", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # Server
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Database
    database_url: str = Field(
        default="sqlite:///./interviewsage.db", alias="DATABASE_URL"
    )

    # Security — REQUIRED (No insecure default fallback!)
    secret_key: str = Field(alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=10080, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Local LLM & Ollama Configuration
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    llm_model_name: str = Field(default="qwen3:instruct", alias="LLM_MODEL_NAME")
    ollama_base_url: str = Field(
        default="http://localhost:11434", alias="OLLAMA_BASE_URL"
    )
    llm_api_key: str | None = Field(default="local-ollama-key", alias="LLM_API_KEY")
    llm_temperature: float = Field(default=0.4, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2000, alias="LLM_MAX_TOKENS")
    llm_fallback_model: str = Field(
        default="qwen2.5:latest", alias="LLM_FALLBACK_MODEL"
    )

    # Voice & Speech Engine Configuration (Sprint 13)
    whisper_model: str = Field(default="base", alias="WHISPER_MODEL")
    whisper_device: str = Field(default="cpu", alias="WHISPER_DEVICE")
    tts_provider: str = Field(default="kokoro", alias="TTS_PROVIDER")
    voice: str = Field(default="en", alias="VOICE")
    voice_speed: float = Field(default=1.0, alias="VOICE_SPEED")
    stream_audio: bool = Field(default=True, alias="STREAM_AUDIO")
    audio_sample_rate: int = Field(default=16000, alias="AUDIO_SAMPLE_RATE")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ORIGINS",
    )

    # File Upload
    max_upload_size: int = Field(default=10485760, alias="MAX_UPLOAD_SIZE")  # 10MB
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="./logs/app.log", alias="LOG_FILE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string to list."""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins if isinstance(self.cors_origins, list) else []

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Enforce minimum 32 character length and reject weak/placeholder values."""
        if not v or not v.strip():
            raise ValueError(
                "SECRET_KEY cannot be empty. Provide a secure key of at least 32 characters."
            )
        val = v.strip()
        if len(val) < 32:
            raise ValueError(
                f"SECRET_KEY must be at least 32 characters long. Provided key has length {len(val)}."
            )
        val_lower = val.lower()
        for pattern in REJECTED_SECRET_PATTERNS:
            if pattern.lower() in val_lower:
                raise ValueError(
                    "SECRET_KEY matches a known insecure development secret or placeholder pattern. "
                    "Provide a cryptographically secure key (e.g. `openssl rand -hex 32`)."
                )
        return val

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment name."""
        allowed = {"development", "dev", "test", "testing", "staging", "production", "prod"}
        if not v or v.lower() not in allowed:
            raise ValueError(
                f"ENVIRONMENT must be one of {sorted(allowed)}. Got '{v}'."
            )
        return v.lower()

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate DATABASE_URL is non-empty and has a valid scheme."""
        if not v or not v.strip():
            raise ValueError("DATABASE_URL cannot be empty.")
        val = v.strip()
        valid_schemes = ("sqlite://", "postgresql://", "postgresql+psycopg2://", "postgresql+asyncpg://")
        if not any(val.startswith(scheme) for scheme in valid_schemes):
            raise ValueError(
                f"DATABASE_URL scheme unsupported. Must start with one of {valid_schemes}."
            )
        return val

    @model_validator(mode="after")
    def validate_debug_for_environment(self) -> "Settings":
        """Strictly prohibit DEBUG=True in production or staging environments."""
        env = (self.environment or "").lower()
        if env in {"production", "prod", "staging"} and self.debug:
            raise ValueError(
                f"DEBUG=True is strictly prohibited when ENVIRONMENT is '{self.environment}'. "
                "Set DEBUG=False in production/staging environments."
            )
        return self


# Global settings instance
settings = Settings()
