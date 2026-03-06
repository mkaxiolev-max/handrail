FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir uvicorn fastapi
EXPOSE 8788
CMD ["python", "-m", "uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8788"]
