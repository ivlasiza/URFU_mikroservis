import pika  # Импортируем библиотеку для работы с RabbitMQ
import json  # Импортируем библиотеку для работы с JSON-данными
import os  # Импортируем библиотеку для работы с операционной системой (например, пути файлов)
import csv  # Импортируем библиотеку для работы с CSV-файлами

# Константы для путей к логам
LOG_DIR = "logs"  # Указываем директорию для хранения логов
LOG_FILE = os.path.join(
    LOG_DIR, "metrics_log.csv"
)  # Указываем путь к CSV-файлу, в который будут записываться логи

# Убедимся, что директория логов существует
# Если папки для логов нет, создаем её
if not os.path.isdir(LOG_DIR):
    os.makedirs(LOG_DIR)  # Создание папки для логов
    print(
        f"Директория {LOG_DIR} создана для хранения логов."
    )  # Информируем, что директория создана

# Создание CSV-файла с заголовками, если он ещё не существует
# Если файл логов ещё не создан, создаем его и записываем в него заголовки
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode="w", newline="") as log_file:
        # Создаем CSV writer, записываем заголовки в файл
        csv.writer(log_file).writerow(
            ["message_id", "actual", "predicted", "absolute_error"]
        )
    print(
        f"Создан файл лога: {LOG_FILE} с необходимыми заголовками."
    )  # Информируем, что файл с заголовками создан

# Настройка соединения с RabbitMQ
# Устанавливаем подключение к серверу RabbitMQ с указанием параметров хоста и учетных данных
mq_connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host="rabbitmq",  # Адрес хоста RabbitMQ
        credentials=pika.PlainCredentials(
            "user", "password"
        ),  # Учетные данные для подключения
    )
)
# Создаем канал для обмена сообщениями с RabbitMQ
mq_channel = mq_connection.channel()

# Объявление очередей для обработки данных
# Создаем очереди, если они ещё не существуют
mq_channel.queue_declare(queue="y_actual")  # Очередь для целевых значений (actual)
mq_channel.queue_declare(
    queue="y_pred"
)  # Очередь для предсказанных значений (predicted)

# Временное хранилище для сообщений
# Используем словарь для хранения данных по каждому сообщению до того, как оно будет обработано
message_store = {}


# Функция записи метрик в лог-файл
# Добавляет запись в CSV-файл лога с переданными параметрами
def append_to_log(message_id, actual_value, predicted_value, error):
    with open(LOG_FILE, mode="a", newline="") as log_file:
        # Открываем файл в режиме добавления (append) и записываем строку с данными
        csv.writer(log_file).writerow(
            [message_id, actual_value, predicted_value, error]
        )
    print(
        f"Лог записан: ID={message_id}, Actual={actual_value}, Predicted={predicted_value}, Error={error}"
    )  # Информируем о записи в лог


# Функция обратного вызова для обработки входящих сообщений
# Эта функция вызывается, когда новое сообщение поступает в одну из очередей
def process_message(channel, method, properties, body):
    try:
        # Декодируем сообщение из формата JSON
        msg = json.loads(body)
        msg_id = msg.get("id")  # Извлекаем идентификатор сообщения
        value = msg.get("body")  # Извлекаем тело сообщения (значение)

        # Проверка на наличие обязательных полей в сообщении
        if msg_id is None or value is None:
            raise ValueError(
                "Сообщение не содержит обязательных полей 'id' и 'body'."
            )  # Если поле отсутствует, вызываем исключение

        # Определяем источник сообщения (какая очередь его отправила)
        source_queue = method.routing_key

        # В зависимости от того, из какой очереди пришло сообщение, сохраняем данные
        if source_queue == "y_actual":  # Если сообщение из очереди actual
            message_store.setdefault(msg_id, {})[  # Если ключа нет, создаем его
                "actual"
            ] = value  # Сохраняем значение actual
            print(f"Получено actual значение: {value} для ID: {msg_id}")
        elif source_queue == "y_pred":  # Если сообщение из очереди predicted
            message_store.setdefault(msg_id, {})[  # Если ключа нет, создаем его
                "predicted"
            ] = value  # Сохраняем значение predicted
            print(f"Получено predicted значение: {value} для ID: {msg_id}")

        # Проверяем, готовы ли оба значения для вычисления ошибки
        if "actual" in message_store[msg_id] and "predicted" in message_store[msg_id]:
            actual = message_store[msg_id]["actual"]  # Получаем actual значение
            predicted = message_store[msg_id][
                "predicted"
            ]  # Получаем predicted значение

            # Вычисляем абсолютную ошибку
            error = abs(actual - predicted)
            print(
                f"Рассчитана ошибка для ID {msg_id}: Actual={actual}, Predicted={predicted}, Error={error}"
            )

            # Записываем результат в лог
            append_to_log(msg_id, actual, predicted, error)

            # Удаляем запись из временного хранилища после обработки
            del message_store[msg_id]

    except json.JSONDecodeError:
        print(
            "Ошибка: невозможно декодировать сообщение в формате JSON."
        )  # Если ошибка при декодировании JSON
    except Exception as ex:
        print(f"Ошибка обработки сообщения: {ex}")  # Ловим другие ошибки


# Подписка на очереди RabbitMQ
# Подписываемся на очереди 'y_actual' и 'y_pred', чтобы получать сообщения из этих очередей
mq_channel.basic_consume(
    queue="y_actual", on_message_callback=process_message, auto_ack=True
)  # Для очереди y_actual
mq_channel.basic_consume(
    queue="y_pred", on_message_callback=process_message, auto_ack=True
)  # Для очереди y_pred

print(
    "Сервис обработки метрик запущен. Ожидание сообщений... Для завершения нажмите CTRL+C."
)  # Информируем, что сервис запущен и ждем сообщений

# Запуск обработки сообщений
# Ожидаем новые сообщения и передаем их в функцию обработки
mq_channel.start_consuming()
