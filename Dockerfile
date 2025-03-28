FROM python:3.11-bookworm AS base
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# Install poetry
RUN pip install poetry

WORKDIR /app

# Install dependencies
COPY poetry.lock pyproject.toml ./
RUN poetry install --without dev --no-root --no-interaction --no-ansi --all-extras

# Install app
COPY . .
RUN poetry install --only-root --no-interaction --no-ansi

FROM python:3.11-bookworm AS production

WORKDIR /app

COPY --from=base /app /app

ENTRYPOINT ["/app/.venv/bin/uvicorn", "dojo.app:app", "--reload", "--host", "0.0.0.0"]
