"""
PostgreSQL Migration Script
Adds `target_role` and `target_company` columns to `interviews` table.
"""

from sqlalchemy import text
from app.core.database import engine

def migrate():
    print("[MIGRATION] Starting PostgreSQL Interview role columns migration...")
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE interviews ADD COLUMN IF NOT EXISTS target_role VARCHAR(255);"))
        conn.execute(text("ALTER TABLE interviews ADD COLUMN IF NOT EXISTS target_company VARCHAR(255);"))
        conn.commit()
    print("[MIGRATION] Interview role columns migration COMPLETED successfully!")

if __name__ == "__main__":
    migrate()
