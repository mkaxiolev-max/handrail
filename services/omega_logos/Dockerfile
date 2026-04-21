# AXIOLEV Holdings LLC © 2026
FROM python:3.12-slim
WORKDIR /app
COPY services/omega_logos /app/services/omega_logos
RUN pip install --no-cache-dir fastapi uvicorn pydantic
EXPOSE 9010
CMD ["python", "-m", "services.omega_logos"]
