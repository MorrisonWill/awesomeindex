FROM python:3.12-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies: uv, curl, libgcc and copy MeiliSearch
RUN pip install uv && apk add --no-cache curl libgcc
COPY --from=getmeili/meilisearch:v1.15 /bin/meilisearch /usr/local/bin/meilisearch

# Copy uv files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create data directories for volume mounts
RUN mkdir -p /app/data /app/data/meili_data

# Copy start script
COPY start.sh .
RUN chmod +x start.sh

# Expose ports
EXPOSE 8000 7700

# Run both services
CMD ["./start.sh"]
