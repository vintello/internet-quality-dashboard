import time
import subprocess
from datetime import datetime

LOG_FILE = "internet_history.log"
TARGET_HOST = "1.1.1.1"
CHECK_INTERVAL = 5  # Интервал проверки в секундах


def check_internet(host=TARGET_HOST):
    """Проверяет доступность узла через ping (1 пакет, таймаут 2 сек)."""
    try:
        # Для Linux/macOS параметр -c, таймаут -W
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except Exception:
        return False


def format_time(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def log_interval(status, start_time, end_time):
    """Записывает сформированный интервал в файл и выводит в консоль."""
    start_str = format_time(start_time)
    end_str = format_time(end_time)

    if status:
        message = f"Было с {start_str} по {end_str}"
    else:
        message = f"Не было с {start_str} по {end_str}"

    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")


def main():
    print("Запуск мониторинга сети...")
    current_status = check_internet()
    period_start = datetime.now()

    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            new_status = check_internet()

            # Если статус изменился
            if new_status != current_status:
                period_end = datetime.now()
                log_interval(current_status, period_start, period_end)

                # Обновляем состояние для нового периода
                current_status = new_status
                period_start = period_end

    except KeyboardInterrupt:
        # При ручной остановке (Ctrl+C) фиксируем текущий неполный интервал
        log_interval(current_status, period_start, datetime.now())
        print("\nМониторинг остановлен.")


if __name__ == "__main__":
    main()