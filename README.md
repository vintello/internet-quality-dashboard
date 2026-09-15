# Internet Quality & Uptime Dashboard

Веб-приложение на Flask и Pandas для анализа логов устойчивости интернет-соединения. Позволяет отслеживать время работы (uptime), периоды простоя, частоту обрывов и просматривать детальные логи за каждый день.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-orange.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)

---

## Возможности

* **Агрегированная статистика:** Расчет процента доступности сети (uptime), общего времени работы и времени сбоев.
* **Категоризация сбоев:** Автоматическое разделение обрывов на кратковременные ($\le 10$ сек) и длительные ($> 10$ сек).
* **Сводка по дням:** Таблица ежедневной активности с подсчетом процента аптайма и количества разрывов.
* **Детализация в новой вкладке:** Просмотр полного списка событий (подключений и разрывов) за конкретный день по клику на кнопку.
* **Адаптивный интерфейс:** Современный дашборд на базе Bootstrap 5.

---

## Требования

* Python 3.9 или выше
* Файл лога `internet_history.log` в корневой директории приложения

Формат записей в `internet_history.log`:
```text
Было с 2026-09-14 10:25:49 по 2026-09-14 10:28:12
Не было с 2026-09-14 10:28:12 по 2026-09-14 10:28:17
```

## Быстрый старт
1. Клонирование репозитория
    
        git clone https://github.com/vintello/internet-quality-dashboard
        cd internet-quality-dashboard
   
2. Создание виртуального окружения
    
   * Linux / macOS
    
            python3 -m venv venv
            source venv/bin/activate

   * Windows

          python -m venv venv
          venv\Scripts\activate

3. Установка зависимостей

        pip install -r requirements.txt

4. Запуск приложения

   * Локально
   
       python main.py
       python web_morda.py
   
   * Демонизация линукс
   
       sudo nano /etc/systemd/system/internet-web.service
       sudo nano /etc/systemd/system/internet-tracker.service

       sudo systemctl daemon-reload
   
       sudo systemctl enable internet-tracker.service
       sudo systemctl enable internet-web.service
   
       sudo systemctl start internet-tracker.service
       sudo systemctl enable internet-web.service
   

Приложение будет доступно в браузере по адресу: http://localhost:5000

## Лицензия

Проект распространяется под лицензией MIT.

