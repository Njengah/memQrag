# Backend image for the memQrag FastAPI app.
#
# Build context is the repository root (needs pyproject.toml + memQrag/).
# See docs/DECISIONS.md ("Docker Compose Topology For The Local Full Stack")
# for image and volume choices.

FROM python:3.12-slim

WORKDIR /app

# Copy only what pip needs to install the package first, for better layer
# caching when application code changes but dependencies do not.
COPY pyproject.toml README.md ./
COPY memQrag ./memQrag

RUN pip install --no-cache-dir .

# Placeholder mount point for future SQLite persistence (Phase 4). The
# directory must exist so the bind-mounted volume has somewhere to attach.
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "memQrag.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
