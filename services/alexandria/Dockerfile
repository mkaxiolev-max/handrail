FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpoppler-cpp-dev && rm -rf /var/lib/apt/lists/*
RUN pip install fastapi uvicorn psycopg2-binary pdfplumber python-multipart
COPY services/alexandria /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9001"]
