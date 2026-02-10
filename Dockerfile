# ──── Stage 1: builder ──────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

COPY pyproject.toml ./
# Install build deps in a venv so we can copy only what we need
RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --no-cache-dir --upgrade pip setuptools wheel

COPY . .
RUN . /opt/venv/bin/activate \
    && pip install --no-cache-dir .

# ──── Stage 2: runtime ─────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="polymarket-bot" \
      description="Polymarket Research & Trading Bot"

RUN groupadd -r botuser && useradd -r -g botuser botuser

WORKDIR /app

# Copy only the installed venv from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create writable dirs for data/logs
RUN mkdir -p /app/data /app/logs /app/reports \
    && chown -R botuser:botuser /app/data /app/logs /app/reports

USER botuser

ENTRYPOINT ["bot"]
CMD ["--help"]
