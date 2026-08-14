"""
Database migration script to add `status` column to `resumes` and `job_descriptions` tables.
Applies data migration for existing rows.
"""

from sqlalchemy import text

from app.core.database import engine


def migrate():
    print("[MIGRATION] Starting PostgreSQL status column migration...")
    with engine.connect() as conn:
        conn.execute(
            text(
                "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'PROCESSING';"
            )
        )
        conn.execute(
            text(
                "ALTER TABLE job_descriptions ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'PROCESSING';"
            )
        )

        # Migrate existing rows containing valid parsed skills or experience
        conn.execute(
            text(
                "UPDATE resumes SET status = 'COMPLETED' WHERE (parsed_skills IS NOT NULL AND parsed_skills != '[]') OR (parsed_experience IS NOT NULL AND parsed_experience != '[]' AND parsed_experience != '{}');"
            )
        )
        conn.execute(
            text(
                "UPDATE job_descriptions SET status = 'COMPLETED' WHERE (required_skills IS NOT NULL AND required_skills != '[]');"
            )
        )

        conn.commit()
    print("[MIGRATION] PostgreSQL status column migration COMPLETED successfully!")


if __name__ == "__main__":
    migrate()
