import pika  # Импортируем библиотеку для работы с RabbitMQ
import pickle  # Импортируем библиотеку для работы с сериализацией объектов (pickle)
import numpy as np  # Импортируем numpy для работы с массивами
import json  # Импортируем json для работы с JSON-форматом данных

# Загрузка предварительно обученной модели из файла
# Открываем файл с моделью и загружаем её с помощью pickle
with open("myfile.pkl", "rb") as model_file:
    regressor = pickle.load(model_file)  # Загружаем модель в переменную regressor

# Настройка подключения к RabbitMQ
# Устанавливаем соединение с сервером RabbitMQ с указанием хоста и учетных данных
mq_connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host="rabbitmq",  # Указываем адрес хоста RabbitMQ
        credentials=pika.PlainCredentials(
            username="user", password="password"
        ),  # Учетные данные
    )
)
mq_channel = mq_connection.channel()  # Создаем канал для общения с сервером RabbitMQ

# Объявление необходимых очередей
# Создаем две очереди: одну для признаков ("features"), другую для предсказанных значений ("y_pred")
mq_channel.queue_declare(queue="features")  # Очередь для признаков
mq_channel.queue_declare(queue="y_pred")  # Очередь для предсказанных значений


# Обработчик сообщений из очереди "features"
def process_features(ch, method, properties, body):
    print(f"Получено сообщение: {body}")  # Выводим сообщение, полученное из очереди

    try:
        # Десериализация JSON-сообщения
        incoming_message = json.loads(
            body
        )  # Преобразуем тело сообщения из JSON в Python-словарь

        # Извлечение ID и вектора признаков
        msg_id = incoming_message.get("id")  # Извлекаем уникальный ID сообщения
        feature_vector = incoming_message.get("body")  # Извлекаем вектор признаков

        # Проверка на наличие обязательных полей в сообщении
        if not msg_id or feature_vector is None:
            raise ValueError(
                "Отсутствуют обязательные поля 'id' или 'body' в сообщении."
            )  # Если данных нет — выбрасываем ошибку

        # Преобразование признаков в массив numpy
        features_np = np.array(feature_vector).reshape(
            1, -1
        )  # Преобразуем вектор признаков в одномерный массив numpy

        # Выполнение предсказания с использованием модели
        prediction = regressor.predict(features_np)[
            0
        ]  # Получаем предсказание из модели

        # Округление результата предсказания
        prediction_rounded = int(
            round(prediction)
        )  # Округляем предсказание до целого числа

        # Формирование нового сообщения с предсказанием
        prediction_message = {
            "id": msg_id,  # Используем тот же ID
            "body": prediction_rounded,  # Результат предсказания
        }

        # Сериализация сообщения в JSON
        prediction_json = json.dumps(
            prediction_message
        )  # Преобразуем сообщение обратно в JSON

        # Публикация предсказания в очередь "y_pred"
        mq_channel.basic_publish(
            exchange="",  # Без обмена
            routing_key="y_pred",  # В очередь "y_pred"
            body=prediction_json,  # Отправляем сериализованное сообщение
        )

        print(
            f"Отправлено предсказание: {prediction_rounded} для ID {msg_id}"
        )  # Выводим результат

    except json.JSONDecodeError:
        print(
            "Ошибка: некорректный JSON в сообщении."
        )  # Обработка ошибки, если не удается декодировать JSON
    except Exception as ex:
        print(f"Ошибка обработки сообщения: {ex}")  # Обработка других ошибок


# Настройка потребителя очереди "features"
# Устанавливаем обработчик для получения сообщений из очереди "features"
mq_channel.basic_consume(
    queue="features",  # Подписка на очередь "features"
    on_message_callback=process_features,  # Указываем функцию-обработчик
    auto_ack=True,  # Автоматически подтверждаем получение сообщений
)

print(
    "Сервис предсказаний запущен. Ожидание сообщений..."
)  # Информируем, что сервис запущен и ожидает сообщения

# Запуск основного цикла обработки
# Блокируем выполнение, ожидаем новых сообщений и передаем их в функцию обработки
mq_channel.start_consuming()
