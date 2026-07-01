FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    LOG_FORMAT=json \
    DXCON_DOCKER=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 dxcon \
    && useradd --uid 10001 --gid 10001 --create-home dxcon

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R dxcon:dxcon /app

USER 10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${PORT:-8000}/live || exit 1

STOPSIGNAL SIGTERM

CMD ["gunicorn", "-c", "gunicorn.conf.py", "run:app"]
