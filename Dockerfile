# Stage 1: Install dependencies
FROM python:3.11-slim AS builder

WORKDIR /code
COPY ./requirements.txt /code/requirements.txt

# Install dependencies system-wide to /usr/local
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Stage 2: Final Image
FROM python:3.11-slim

# Create a non-root user
RUN useradd -m knowme-ai-user

WORKDIR /code
RUN chown -R knowme-ai-user:knowme-ai-user /code

# Switch to the non-root user
USER knowme-ai-user

# Copy installed dependencies from the builder stage
COPY --from=builder /usr/local /usr/local

# Copy application code
COPY --chown=knowme-ai-user:knowme-ai-user ./app /code/app

# Expose the port
EXPOSE 7000

# Set the maintainer
LABEL maintainer="Jenslee Dsouza <dsouzajenslee@gmail.com>"

# Start Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7000", "--proxy-headers"]
