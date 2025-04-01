# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Create a non-root user
RUN useradd -m knowme-ai-user

# Set the working directory to /code and change ownership
WORKDIR /code
RUN chown -R knowme-ai-user:knowme-ai-user /code

# Switch to the non-root user
USER knowme-ai-user

# Copy and install dependencies
COPY --chown=knowme-ai-user:knowme-ai-user ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt --user --no-warn-script-location # Install in user directory

# Copy application code
COPY --chown=knowme-ai-user:knowme-ai-user ./app /code/app

# Ensure user-installed packages are in PATH
ENV PATH="/home/knowme-ai-user/.local/bin:${PATH}"

# Expose the port
EXPOSE 9000

# Set the maintainer
LABEL maintainer="Jenslee Dsouza <dsouzajenslee@gmail.com>"

# Start Uvicorn with the root path
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7000", "--proxy-headers"]