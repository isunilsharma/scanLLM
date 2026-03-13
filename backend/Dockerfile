FROM python:3.11-slim

WORKDIR /app

# Install git (needed for GitPython repo cloning)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .

# config.py resolves config dir as 3 levels up from /app/core/config.py -> /config
COPY config/ /config/

# Initialize database
RUN python -c "from core.database import init_db; init_db()"

EXPOSE 8001

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
