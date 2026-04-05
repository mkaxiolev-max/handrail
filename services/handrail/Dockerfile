FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates curl patch \
  && rm -rf /var/lib/apt/lists/*

# Install modern docker CLI + compose v2 plugin (works with Docker Desktop API >= 1.44)
ARG DOCKER_VERSION=26.1.4
ARG COMPOSE_VERSION=v2.27.1

RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
      arm64) darch="aarch64"; carch="aarch64" ;; \
      amd64) darch="x86_64";  carch="x86_64"  ;; \
      *) echo "unsupported arch: $arch" && exit 1 ;; \
    esac; \
    curl -fsSL "https://download.docker.com/linux/static/stable/${darch}/docker-${DOCKER_VERSION}.tgz" -o /tmp/docker.tgz; \
    tar -xzf /tmp/docker.tgz -C /tmp; \
    mv /tmp/docker/docker /usr/local/bin/docker; \
    rm -rf /tmp/docker /tmp/docker.tgz; \
    mkdir -p /usr/local/lib/docker/cli-plugins; \
    curl -fsSL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-${carch}" \
      -o /usr/local/lib/docker/cli-plugins/docker-compose; \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose; \
    \
    # Compatibility: Handrail code calls 'docker-compose'
    printf '#!/bin/sh\nexec docker compose "$@"\n' > /usr/local/bin/docker-compose; \
    chmod +x /usr/local/bin/docker-compose

WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn pydantic pytest httpx jsonschema
# Build context is project root — copy all packages needed at container startup
COPY services/handrail/handrail ./handrail
COPY services/handrail/tests    ./tests
COPY abi                        ./abi
EXPOSE 8011
CMD ["uvicorn", "handrail.server:app", "--host", "0.0.0.0", "--port", "8011"]
