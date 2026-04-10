FROM python:3.11-slim
WORKDIR /app
COPY services/omega/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY services/omega /app
COPY services/shared /app/shared
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9010"]
