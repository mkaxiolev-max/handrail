FROM python:3.11-slim

WORKDIR /app

# deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# source
COPY adapter_core/ ./adapter_core/
COPY dignity_kernel/ ./dignity_kernel/
COPY macos_driver/ ./macos_driver/
COPY server.py .

# artifacts dir
RUN mkdir -p /app/artifacts

ENV ADAPTER_ARTIFACTS_ROOT=/app/artifacts
ENV PYTHONPATH=/app

EXPOSE 9911

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "9911"]
