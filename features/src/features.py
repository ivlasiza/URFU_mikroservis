import pika  # Импортируем библиотеку для работы с RabbitMQ
import numpy as np  # Импортируем библиотеку для работы с массивами и случайными числами
import json  # Импортируем библиотеку для работы с JSON-данными
from sklearn.datasets import (
    load_diabetes,
)  # Импортируем функцию для загрузки набора данных о диабете
import time  # Импортируем библиотеку для работы с временными задержками
from datetime import datetime  # Импортируем класс для работы с датами и временем

# Установка случайного состояния для воспроизводимости
np.random.seed(60)

# Загружаем набор данных для анализа диабета
# data - признаки, target - целевая переменная (диабет)
data, target = load_diabetes(return_X_y=True)

# Настройка подключения к серверу RabbitMQ
# Создаем подключение и указываем параметры: адрес хоста и учетные данные для аутентификации
mq_connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host="rabbitmq",  # Адрес сервера RabbitMQ
        credentials=pika.PlainCredentials(
            username="user", password="password"
        ),  # Учетные данные для подключения
    )
)
# Создаем канал для взаимодействия с сервером
mq_channel = mq_connection.channel()

# Объявление необходимых очередей в RabbitMQ
# Это гарантирует, что очереди существуют и готовы для работы
mq_channel.queue_declare(queue="y_actual")  # Очередь для целевых значений
mq_channel.queue_declare(queue="features")  # Очередь для признаков

try:
    while True:  # Бесконечный цикл для отправки данных
        # Выбор случайной строки из данных
        # np.random.randint генерирует случайное целое число в диапазоне от 0 до количества строк в наборе данных
        row_index = np.random.randint(0, data.shape[0])

        # Генерация уникального идентификатора сообщения
        # Используем текущий timestamp для генерации уникального идентификатора
        unique_id = datetime.timestamp(datetime.now())

        # Подготовка данных для очереди y_actual
        # Формируем сообщение для очереди с целевым значением (target)
        actual_message = {
            "id": unique_id,  # Добавляем уникальный идентификатор
            "body": target[row_index],  # Целевое значение для выбранной строки
        }

        # Подготовка данных для очереди features
        # Формируем сообщение для очереди с признаками (data)
        feature_message = {
            "id": unique_id,  # Тот же уникальный идентификатор
            "body": list(data[row_index]),  # Признаки для выбранной строки
        }

        # Публикация сообщения в очередь y_actual
        # Публикуем данные о целевой переменной в соответствующую очередь
        mq_channel.basic_publish(
            exchange="",  # Публикуем без использования обменников
            routing_key="y_actual",  # Указываем имя очереди
            body=json.dumps(actual_message),  # Преобразуем сообщение в формат JSON
        )
        print(
            f"Отправлено сообщение в y_actual: {actual_message}"
        )  # Выводим информацию о отправленном сообщении

        # Публикация сообщения в очередь features
        # Публикуем данные о признаках в соответствующую очередь
        mq_channel.basic_publish(
            exchange="",  # Публикуем без использования обменников
            routing_key="features",  # Указываем имя очереди
            body=json.dumps(feature_message),  # Преобразуем сообщение в формат JSON
        )
        print(
            f"Отправлено сообщение в features: {feature_message}"
        )  # Выводим информацию о отправленном сообщении

        # Задержка между публикациями сообщений
        # time.sleep используется для создания задержки между публикациями сообщений в 2 секунды
        time.sleep(2)

except (
    KeyboardInterrupt
):  # Исключение, которое возникает при прерывании работы (например, Ctrl+C)
    print("Прерывание работы: пользователь остановил выполнение.")

finally:
    # Закрытие соединения с сервером
    # Обязательно закрываем соединение после завершения работы
    mq_connection.close()
    print("Соединение с RabbitMQ закрыто.")
