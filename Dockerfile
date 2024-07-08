FROM python:3.11-bookworm
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="/root/.local/bin:$PATH"

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

# Install dependencies
COPY poetry.lock pyproject.toml ./
RUN poetry install --without dev --no-root --no-interaction --no-ansi --all-extras

# Install app
COPY . .
RUN poetry install --only-root --no-interaction --no-ansi --all-extras

# Run application
CMD ["poetry", "run", "uvicorn", "dojo.app:app", "--reload", "--host", "0.0.0.0"]
