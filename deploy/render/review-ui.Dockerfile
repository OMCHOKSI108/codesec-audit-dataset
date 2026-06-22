FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY ui/app.py ui/app.py

RUN pip install --no-cache-dir -e ".[ui]" && \
    rm -rf /root/.cache

COPY deploy/render/review_ui_start.sh /review_ui_start.sh
RUN chmod +x /review_ui_start.sh

EXPOSE 8501

CMD ["/review_ui_start.sh"]
