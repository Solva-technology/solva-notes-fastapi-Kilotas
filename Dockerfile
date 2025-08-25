FROM python:3.11-slim


RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


RUN chmod +x /app/entrypoint.sh

EXPOSE 8000


ENTRYPOINT ["/app/entrypoint.sh"]


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]