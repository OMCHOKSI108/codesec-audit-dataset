ARG INSTALL_RAG=false

FROM python:3.11-slim

ARG INSTALL_RAG
ENV CODESEC_ENABLE_RAG=${INSTALL_RAG}

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

RUN pip install --no-cache-dir -e ".[api,ui,website]"

COPY review_engine/ review_engine/
COPY review_store/ review_store/
COPY api/ api/
COPY ui/ ui/
COPY website/ website/
COPY scripts/ scripts/
COPY examples/ examples/
COPY docs/ docs/
COPY deploy/render/website_start.sh /website_start.sh
RUN chmod +x /website_start.sh

RUN if [ "$INSTALL_RAG" = "true" ]; then \
        pip install --no-cache-dir -e ".[rag]"; \
    fi

RUN pip install --no-cache-dir gunicorn

COPY render_entrypoint.sh /render_entrypoint.sh
RUN chmod +x /render_entrypoint.sh

EXPOSE 8003 8501 8502

ENTRYPOINT ["/render_entrypoint.sh"]
