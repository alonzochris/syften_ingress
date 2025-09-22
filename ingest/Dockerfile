FROM ghcr.io/astral-sh/uv:python3.12-bookworm

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

ENV PORT=8080
ENV GRPC_VERBOSITY=ERROR
ENV GRPC_TRACE=""
EXPOSE 8080

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
