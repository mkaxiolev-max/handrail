FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt || true
EXPOSE 9000
CMD ["python", "-m", "uvicorn", "nss.api.server:app", "--host", "0.0.0.0", "--port", "9000"]
