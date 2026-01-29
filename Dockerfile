FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install --no-cache-dir poetry

# Copy project files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not create a virtualenv inside the container
RUN poetry config virtualenvs.create false \
    && poetry install --without dev --no-root --no-interaction --no-ansi

# Copy source code
COPY . .

# Expose Streamlit port
EXPOSE 3005

# Run streamlit
CMD ["streamlit", "run", "src/ui/app.py", "--server.port", "3005", "--server.address", "0.0.0.0"]
