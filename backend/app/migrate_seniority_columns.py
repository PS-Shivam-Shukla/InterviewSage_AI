"""
PostgreSQL Migration Script
Adds seniority_score, total_experience_months, relevant_experience_months, and seniority_breakdown columns to `resumes` table.
"""

from sqlalchemy import text
from app.core.database import engine

def migrate():
    print("[MIGRATION] Starting PostgreSQL Seniority columns migration...")
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS seniority_score INT NOT NULL DEFAULT 0;"))
        conn.execute(text("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS total_experience_months INT NOT NULL DEFAULT 0;"))
        conn.execute(text("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS relevant_experience_months INT NOT NULL DEFAULT 0;"))
        conn.execute(text("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS seniority_breakdown TEXT NOT NULL DEFAULT '{}';"))
        conn.commit()
    print("[MIGRATION] Seniority columns migration COMPLETED successfully!")

if __name__ == "__main__":
    migrate()
