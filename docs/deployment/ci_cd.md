# CI/CD Pipeline & Automated Release Guide

**InterviewSage AI GitHub Actions Pipeline**

---

## 1. Pipeline Overview (`.github/workflows/backend.yml`)

The CI/CD pipeline triggers on every `push` or `pull_request` to `main`, `master`, or `develop` branches:

```
[ Git Push / PR ]
       │
       ├──────> Job 1: Code Quality & Type Check (Ruff, Black, MyPy)
       │
       ├──────> Job 2: Unit & Integration Test Suite (Pytest + 80% Coverage)
       │
       └──────> Job 3: Docker Build & Image Validation (Backend + Frontend)
```

---

## 2. Pipeline Stage Specifications

### Stage 1: Code Quality & Type Check
- **Ruff**: Fast Python linter enforcing PEP8 & import sorting (`ruff check backend/app`).
- **Black**: Opinionated code formatting validation (`black --check backend/app`).
- **MyPy**: Static type annotation validation (`mypy backend/app`).

### Stage 2: Automated Testing & Coverage
- Runs full 200-test suite across unit, route, security, checkpointing, and observability tests.
- Enforces strict minimum **80% line coverage** requirement.

### Stage 3: Container Build Validation
- Builds multi-stage Docker images for both `backend/` and `frontend/` using `docker/build-push-action@v5`.
- Validates Dockerfile syntax, dependency installation, and container healthchecks.
