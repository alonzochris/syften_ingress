FROM ghcr.io/astral-sh/uv:python3.12-bookworm

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

ENV PORT=8080
EXPOSE 8080

CMD ["uv", "run", "uvicorn", "ingest.main:app", "--host", "0.0.0.0", "--port", "8080"]
