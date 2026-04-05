FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn pydantic

COPY services/atomlex/atomlex ./atomlex

EXPOSE 8080
CMD ["uvicorn", "atomlex.server:app", "--host", "0.0.0.0", "--port", "8080"]
