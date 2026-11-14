# syntax=docker/dockerfile:1

# Resolved through nexcraft-conventions/runtimes.yaml (floor: Python >= 3.12).
ARG PYTHON_MAJOR=3.12

# ---- build ----
# Wheels are built here so compilers and headers never reach the runtime image.
FROM python:${PYTHON_MAJOR}-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt ./
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---- runtime ----
FROM python:${PYTHON_MAJOR}-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DATA_DIR=/data

# Runtime requirements only: never requirements-dev.txt.
COPY --from=build /wheels /wheels
COPY requirements.txt ./
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

WORKDIR /app
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# Non-root uid/gid 10001 (shared with the solver on the rafaga-data volume).
RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid 10001 --create-home appuser \
    && mkdir -p /data \
    && chown -R 10001:10001 /app /data
USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status==200 else 1)"

# Configuration comes from the environment; no .env lives in the image.
# Migrations run before the server starts, so /health turns healthy only
# once the schema (and job_contract_version) exists.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
