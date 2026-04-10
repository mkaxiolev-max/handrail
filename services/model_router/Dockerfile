FROM python:3.11-slim
WORKDIR /app
RUN pip install fastapi uvicorn pydantic httpx \
    "anthropic>=0.20.0" \
    "openai>=1.0.0" \
    "google-generativeai>=0.4.0" \
    "groq>=0.4.0"
COPY services/model_router /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9002"]
