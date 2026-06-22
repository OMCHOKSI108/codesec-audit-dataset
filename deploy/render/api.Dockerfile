FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY config/ config/
COPY review_engine/ review_engine/
COPY review_store/ review_store/
COPY api/ api/

RUN pip install --no-cache-dir -e ".[api]" && \
    rm -rf /root/.cache

COPY deploy/render/api_start.sh /api_start.sh
RUN chmod +x /api_start.sh

EXPOSE 8003

CMD ["/api_start.sh"]
