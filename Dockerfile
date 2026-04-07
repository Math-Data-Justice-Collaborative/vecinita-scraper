FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir .

EXPOSE 10000

CMD ["sh", "-c", "uvicorn vecinita_scraper.api.server:app --host 0.0.0.0 --port ${PORT:-10000}"]