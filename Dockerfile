FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
  netcat-openbsd \
  && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN addgroup --system cashevide && adduser --system --group cashevide

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY --chown=cashevide:cashevide ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY --chown=cashevide:cashevide . .

USER cashevide

ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "cashevide_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
