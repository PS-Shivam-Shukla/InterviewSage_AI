"""
Development Configuration Profile for InterviewSage AI.
"""

from typing import Dict, Any

DEVELOPMENT_CONFIG: Dict[str, Any] = {
    "ENVIRONMENT": "development",
    "DEBUG": True,
    "LOG_LEVEL": "DEBUG",
    "LOG_FORMAT": "text",
    "DB_POOL_SIZE": 5,
    "DB_MAX_OVERFLOW": 10,
    "ACCESS_TOKEN_EXPIRE_MINUTES": 1440,
}
