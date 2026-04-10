FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn httpx pydantic
COPY services /app/services
ENV PYTHONPATH=/app/services
CMD ["uvicorn", "ns_api.app.main:app", "--host", "0.0.0.0", "--port", "9011"]
