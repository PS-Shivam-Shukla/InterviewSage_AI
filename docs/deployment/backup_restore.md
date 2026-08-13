# Database Backup, Recovery & Disaster Recovery Guide

**InterviewSage AI Database Operations**

---

## 1. Backup Strategy Overview

InterviewSage AI relies on PostgreSQL as the primary source of truth for candidate records, interview blueprints, answers, evaluations, agent logs, and LangGraph checkpoints.

### Backup Schedule
- **Full Automated Backup**: Daily at 02:00 UTC using `pg_dump`.
- **Retention Policy**: Keep daily backups for 30 days, weekly backups for 90 days.
- **Storage Location**: Offsite S3/GCS encrypted bucket (`AES-256`).

---

## 2. Automated PostgreSQL Dump Script

```bash
#!/usr/bin/env bash
# backup_postgres.sh — Automated daily database backup script

SET_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/postgres"
BACKUP_FILE="${BACKUP_DIR}/interviewsage_backup_${SET_DATE}.sql.gz"

mkdir -p ${BACKUP_DIR}

docker exec -t interviewsage-postgres pg_dump -U interviewsage_user interviewsage_db | gzip > ${BACKUP_FILE}

echo "Database backup completed successfully: ${BACKUP_FILE}"
```

---

## 3. Database Restore Procedure

To restore database state from a compressed backup file:

```bash
# 1. Stop backend service to prevent write conflicts
docker compose stop backend

# 2. Drop existing database and restore from backup file
gunzip -c /var/backups/postgres/interviewsage_backup_20260805.sql.gz | \
docker exec -i interviewsage-postgres psql -U interviewsage_user -d interviewsage_db

# 3. Run Alembic migration check
docker compose exec backend alembic upgrade head

# 4. Restart backend service
docker compose start backend
```
