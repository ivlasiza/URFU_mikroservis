FROM python:3.9-slim

# Устанавливаем рабочую директорию для приложения внутри контейнера
# Все последующие команды будут выполняться относительно этой директории
WORKDIR /app

# Обновляем список пакетов и устанавливаем netcat для проверки подключения
# netcat используется для ожидания готовности RabbitMQ перед запуском основного приложения
RUN apt-get update && \
    apt-get install -y netcat-openbsd && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Копируем файл с зависимостями (requirements.txt) в контейнер
# Файл должен быть в том же каталоге, где находится Dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения
COPY ./src /app
COPY wait-for-rabbitmq.sh ./wait-for-rabbitmq.sh

# Делаем скрипт запуска исполняемым
RUN chmod +x wait-for-rabbitmq.sh

# Устанавливаем команду по умолчанию
CMD ["./wait-for-rabbitmq.sh", "rabbitmq", "python", "features.py"]
