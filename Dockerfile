# Если основной Dockerfile не работает, используйте этот упрощенный вариант
FROM python:3.11

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Копирование и установка зависимостей
COPY requirements.simple.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY app/ ./app/

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
