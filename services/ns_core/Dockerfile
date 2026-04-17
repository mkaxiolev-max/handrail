FROM python:3.11-slim
WORKDIR /app
RUN pip install fastapi uvicorn psycopg2-binary redis httpx python-multipart anthropic openai groq pydantic
COPY services/ns_core /app
COPY canon /app/canon
COPY tests/pi/never_events /app/tests/pi/never_events
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
