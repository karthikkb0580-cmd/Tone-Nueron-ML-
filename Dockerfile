# Tone Neuron API — portable container image for any Docker host (Render, Fly.io, Railway, Cloud Run, ECS).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Runtime deps only. Optional extras (PySide6, fastText, torch) are not needed to serve the API.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY tone_neuron ./tone_neuron

# Writable location for the vector index and state. The knowledge index is built on first start.
RUN mkdir -p /data && chown -R 1000:1000 /data
ENV TONE_NEURON_ARTIFACTS_DIR=/data
USER 1000

EXPOSE 8000

# Most hosts inject PORT; fall back to 8000 for plain `docker run`.
CMD ["sh", "-c", "exec uvicorn tone_neuron.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
