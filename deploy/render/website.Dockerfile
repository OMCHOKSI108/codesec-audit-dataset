FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY review_engine/ review_engine/
COPY website/ website/
COPY config/ config/

RUN pip install --no-cache-dir -e ".[website]"

COPY deploy/render/website_start.sh /website_start.sh
RUN chmod +x /website_start.sh

EXPOSE 10000

CMD ["/website_start.sh"]
