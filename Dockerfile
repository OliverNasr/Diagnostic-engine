# =============================================================================
# Stage 1 — dependency builder
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools (needed by some wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# =============================================================================
# Stage 2 — runtime image
# =============================================================================
FROM python:3.11-slim AS runtime

# Non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY app/ ./app/

# Copy the dataset
COPY data/ ./data/

# Set permissions
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
