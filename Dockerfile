FROM python:3.11-slim

# системные утилиты (nc для ожидания БД, gcc не обязателен)
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# entrypoint должен быть исполняемым
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# Всегда выполняем подготовку окружения:
ENTRYPOINT ["/app/entrypoint.sh"]

# А это — дефолтный запуск uvicorn (слушает на 0.0.0.0!)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]