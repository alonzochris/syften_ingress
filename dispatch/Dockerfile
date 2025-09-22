FROM ghcr.io/astral-sh/uv:python3.12-bookworm

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

COPY . .

ENV GRPC_VERBOSITY=ERROR
ENV GRPC_TRACE=""

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
