"""
Staging Configuration Profile for InterviewSage AI.
"""

from typing import Dict, Any

STAGING_CONFIG: Dict[str, Any] = {
    "ENVIRONMENT": "staging",
    "DEBUG": False,
    "LOG_LEVEL": "INFO",
    "LOG_FORMAT": "json",
    "DB_POOL_SIZE": 10,
    "DB_MAX_OVERFLOW": 20,
    "ACCESS_TOKEN_EXPIRE_MINUTES": 120,
}
