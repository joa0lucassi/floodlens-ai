FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt .

RUN python -m pip install --upgrade pip

RUN python -m pip install \
    --no-cache-dir \
    torch==2.14.1+cpu \
    torchvision==0.29.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

RUN python -m pip install \
    --no-cache-dir \
    -r requirements-prod.txt

COPY src ./src
COPY models ./models

RUN useradd --create-home --uid 10001 floodlens
USER 10001:10001

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--limit-concurrency", "16", "--timeout-keep-alive", "5", "--no-access-log"]