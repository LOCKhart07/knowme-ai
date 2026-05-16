# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Bring in the uv binary from its official (pinned) image
COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /uvx /bin/

# Create a non-root user
RUN useradd -m knowme-ai-user

# Set the working directory to /code and change ownership
WORKDIR /code
RUN chown -R knowme-ai-user:knowme-ai-user /code

# Switch to the non-root user
USER knowme-ai-user

# uv settings: use the image's Python (don't download one), compile bytecode
# for faster cold starts, and copy (not hardlink) into the venv.
ENV UV_PYTHON_DOWNLOADS=0 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies into /code/.venv from the frozen lock. Done before the
# app copy so this layer is cached unless the lock changes.
COPY --chown=knowme-ai-user:knowme-ai-user pyproject.toml uv.lock /code/
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY --chown=knowme-ai-user:knowme-ai-user ./app /code/app

# Run from the project venv
ENV PATH="/code/.venv/bin:${PATH}"

# Expose the port
EXPOSE 7000

# Set the maintainer
LABEL maintainer="Jenslee Dsouza <dsouzajenslee@gmail.com>"

# Start Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7000", "--proxy-headers"]
