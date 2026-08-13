"""
Production Hardened Configuration Profile for InterviewSage AI.
"""

from typing import Dict, Any

PRODUCTION_CONFIG: Dict[str, Any] = {
    "ENVIRONMENT": "production",
    "DEBUG": False,
    "LOG_LEVEL": "INFO",
    "LOG_FORMAT": "json",
    "DB_POOL_SIZE": 20,
    "DB_MAX_OVERFLOW": 30,
    "DB_POOL_TIMEOUT": 30,
    "DB_POOL_RECYCLE": 3600,
    "ACCESS_TOKEN_EXPIRE_MINUTES": 60,
    "LANGCHAIN_TRACING_V2": True,
}
