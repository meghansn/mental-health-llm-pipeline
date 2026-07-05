FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu "torch>=2.0.0" \
    && pip install --no-cache-dir -r requirements.txt

COPY redact_pipeline.py .

CMD ["python", "redact_pipeline.py"]
