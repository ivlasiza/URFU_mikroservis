import time  # Импортируем библиотеку для работы со временем
import pandas as pd  # Импортируем pandas для работы с данными
import matplotlib.pyplot as plt  # Импортируем matplotlib для построения графиков
import os  # Импортируем библиотеку для работы с операционной системой (например, пути файлов)

# Путь к CSV-файлу с метриками
LOG_FILE = "/app/logs/metrics_log.csv"  # Абсолютный путь внутри контейнера

# Путь для сохранения гистограммы
OUTPUT_PLOT = "/app/logs/error_distribution.png"  # Абсолютный путь внутри контейнера

# Интервал обновления графика в секундах
SLEEP_TIME = 5  # Настраиваемый интервал


def plot_error_distribution():
    """Функция для периодического построения и сохранения гистограммы распределения ошибок."""
    while True:
        try:
            # Проверяем существование файла с метриками
            if os.path.exists(LOG_FILE):
                # Загрузка данных из CSV
                df = pd.read_csv(LOG_FILE)
                errors = df[
                    "absolute_error"
                ]  # Извлекаем значения ошибок из столбца 'absolute_error'

                if not errors.empty:
                    # Построение гистограммы с использованием другого стиля
                    plt.style.use(
                        "fivethirtyeight"
                    )  # Используем стиль fivethirtyeight для графиков
                    plt.figure(figsize=(10, 6))  # Устанавливаем размер графика
                    plt.hist(
                        errors, bins=20, edgecolor="black", color="lightcoral"
                    )  # Строим гистограмму
                    plt.title(
                        "Распределение абсолютных ошибок", fontsize=16
                    )  # Заголовок графика

                    # Переименованы подписи для осей
                    plt.xlabel("Ошибки предсказания", fontsize=14)  # Подпись для оси X
                    plt.ylabel("Частота ошибок", fontsize=14)  # Подпись для оси Y
                    plt.grid(
                        True, linestyle="-", alpha=0.7
                    )  # Включаем сетку с измененным стилем

                    # Сохранение графика в файл
                    plt.savefig(OUTPUT_PLOT)
                    plt.close()  # Закрытие графика после сохранения
                    print(f"Гистограмма успешно сохранена в {OUTPUT_PLOT}")
                else:
                    print("Данные для построения графика отсутствуют.")
            else:
                print(f"Файл с метриками {LOG_FILE} не найден.")
        except Exception as e:
            # Ловим все исключения и выводим их
            print(f"Ошибка при построении графика: {e}")

        # Задержка перед следующим обновлением
        time.sleep(SLEEP_TIME)


if __name__ == "__main__":
    print("Сервис построения графиков запущен...")  # Информируем, что сервис запущен
    plot_error_distribution()  # Запуск функции построения графиков
