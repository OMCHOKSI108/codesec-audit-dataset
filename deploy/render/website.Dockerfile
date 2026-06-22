FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[website]"

COPY website/ website/
COPY deploy/render/website_start.sh /website_start.sh
RUN chmod +x /website_start.sh

EXPOSE 10000

CMD ["/website_start.sh"]
