# syntax=docker/dockerfile:1

# Resolved through nexcraft-conventions/runtimes.yaml: host Python 3.12
# meets the 3.12 floor, so the image is python:3.12-slim. CUDA comes from
# cupy-cuda12x plus only the runtime and NVRTC wheels (RawKernels compile
# at run time) and the host driver (ADR-17); without a GPU the same image
# runs the NumPy path.
ARG PYTHON_MAJOR=3.12

FROM python:${PYTHON_MAJOR}-slim AS build
ENV PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
COPY requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
    && cd /opt/venv/lib/python*/site-packages \
    # Slim the venv: test suites, bytecode, static CUDA archives, the
    # duplicate NVRTC build and the installer itself are never used at run time.
    && find . -depth \( -name tests -o -name test -o -name __pycache__ \) -type d -exec rm -rf {} + \
    && rm -rf nvidia/*/lib/*.a nvidia/cuda_nvrtc/lib/*.alt.* matplotlib/mpl-data/sample_data \
    && rm -rf pip pip-* setuptools* pkg_resources /opt/venv/bin/pip* /opt/venv/bin/activate*

FROM python:${PYTHON_MAJOR}-slim AS runtime
# WeasyPrint needs Pango/HarfBuzz at runtime; nothing else is installed.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libharfbuzz-subset0 libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH \
    HOME=/home/solver \
    MPLCONFIGDIR=/tmp/matplotlib \
    CUPY_CACHE_DIR=/tmp/cupy \
    OPENBLAS_NUM_THREADS=1 \
    DATA_DIR=/data
COPY --from=build /opt/venv /opt/venv
RUN groupadd --gid 10001 solver \
    && useradd --uid 10001 --gid 10001 --create-home --home-dir /home/solver solver \
    && mkdir -p /data && chown 10001:10001 /data
WORKDIR /app
COPY --chown=root:root app ./app
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=4s --start-period=30s --retries=3 \
  CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"
# Configuration comes from the environment the container is started with.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
