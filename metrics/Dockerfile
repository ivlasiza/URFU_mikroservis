FROM python:3.9-slim

# Устанавливаем рабочую директорию для приложения внутри контейнера
# Все последующие команды будут выполняться относительно этой директории
WORKDIR /app

# Обновление системы и установка необходимых утилит
# Выполняем обновление списка пакетов, устанавливаем netcat для проверки подключения
# netcat необходим для того, чтобы ждать, пока RabbitMQ будет доступен
RUN apt-get update && \
    apt-get install -y netcat-openbsd && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей requirements.txt в контейнер
# Он должен быть в том же каталоге, что и Dockerfile, и будет использоваться для установки зависимостей
COPY requirements.txt .  

# Устанавливаем зависимости Python
# Обновляем pip и устанавливаем все зависимости, указанные в requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt  

# Копируем исходный код приложения
COPY ./src /app  

# Копируем скрипт wait-for-rabbitmq.sh в контейнер
# Этот скрипт используется для ожидания запуска RabbitMQ перед запуском основного приложения
COPY wait-for-rabbitmq.sh ./wait-for-rabbitmq.sh  

# Делаем скрипт wait-for-rabbitmq.sh исполняемым, чтобы его можно было запускать
RUN chmod +x wait-for-rabbitmq.sh  

# Устанавливаем команду по умолчанию, которая будет выполнена при запуске контейнера
# Скрипт wait-for-rabbitmq.sh будет ждать, пока RabbitMQ станет доступным,
# а затем будет запущен Python-скрипт metrics.py
CMD ["./wait-for-rabbitmq.sh", "rabbitmq", "python", "metrics.py"]

