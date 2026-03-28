FROM python:3.11-slim

WORKDIR /app

# Install git (needed for GitPython repo cloning) and cairo libs (needed for pycairo/xhtml2pdf)
RUN apt-get update && apt-get install -y git pkg-config libcairo2-dev gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy core scanning engine (shared package)
COPY core/ /app/core/

# Copy backend source
COPY backend/ .

# config.py resolves config dir as 3 levels up from /app/core/config.py -> /config
COPY config/ /config/

# Ensure core package is importable
ENV PYTHONPATH="/app:${PYTHONPATH}"

EXPOSE 8001

CMD ["sh", "-c", "python -c 'from core.database import init_db; init_db()' && uvicorn server:app --host 0.0.0.0 --port 8001"]
