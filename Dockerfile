
# Production-ready minimal image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    WORKSPACE=/core/app \
    MEM_DB=/app/data/mem.db \
    CORS_ORIGINS=http://162.19.220.29:8080/ \
    RL_DISABLE=0 \
    RL_RPM_LIMIT=60

WORKDIR /app
COPY package*.json ./
RUN npm ci || npm i

RUN npm i -D eslint @eslint/js typescript typescript-eslint \
    eslint-plugin-react eslint-plugin-react-hooks eslint-plugin-import eslint-plugin-simple-import-sort

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY requirements-dev.txt /app/requirements-dev.txt
RUN if [ -f requirements-dev.txt ]; then pip install --no-cache-dir -r requirements-dev.txt || true; fi

COPY . .

EXPOSE 8080
CMD ["python", "app.py"]
