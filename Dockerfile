FROM python:3.11-bookworm
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="/root/.local/bin:$PATH"

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

# Install dependencies
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.in-project true
RUN poetry install --without dev --no-root --no-interaction --no-ansi --all-extras
RUN poetry run pip install --upgrade setuptools

# Install app
COPY . .
RUN poetry install --only-root --no-interaction --no-ansi --all-extras

# Run application
ENTRYPOINT ["poetry", "run", "uvicorn", "dojo.app:app", "--reload", "--host", "0.0.0.0"]
