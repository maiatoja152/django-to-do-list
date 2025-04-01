FROM python:3.13

# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /usr/src/app

RUN useradd -m -r appuser
RUN chown -R appuser:appuser .
USER appuser

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --compile-bytecode --no-install-project

COPY . ./
# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

RUN mkdir static
EXPOSE 8000
CMD ["./startup.sh"]