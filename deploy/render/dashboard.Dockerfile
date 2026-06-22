FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY ui/dashboard.py ui/dashboard.py

RUN pip install --no-cache-dir -e ".[ui]" && \
    rm -rf /root/.cache

COPY deploy/render/dashboard_start.sh /dashboard_start.sh
RUN chmod +x /dashboard_start.sh

EXPOSE 8502

CMD ["/dashboard_start.sh"]
