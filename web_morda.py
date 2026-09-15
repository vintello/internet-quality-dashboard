import os
import datetime
import pandas as pd
from flask import Flask, render_template_string

app = Flask(__name__)
LOG_FILE = 'internet_history.log'

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Мониторинг Интернет-Соединения</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container py-4">
        <h1 class="mb-4">Дашборд качества связи</h1>

        {% if error %}
            <div class="alert alert-danger">{{ error }}</div>
        {% else %}
        <!-- Карточки с ключевыми метриками -->
        <div class="row g-3 mb-4">
            <div class="col-md-3">
                <div class="card text-center border-0 shadow-sm">
                    <div class="card-body">
                        <div class="text-muted small">Аптайм</div>
                        <div class="display-6 fw-bold text-success">{{ "%.2f"|format(metrics.uptime_pct) }}%</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center border-0 shadow-sm">
                    <div class="card-body">
                        <div class="text-muted small">Всего обрывов</div>
                        <div class="display-6 fw-bold text-danger">{{ metrics.num_disconnects }}</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center border-0 shadow-sm">
                    <div class="card-body">
                        <div class="text-muted small">Время в сети</div>
                        <div class="h5 mt-2 mb-0 fw-bold">{{ metrics.total_up_str }}</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center border-0 shadow-sm">
                    <div class="card-body">
                        <div class="text-muted small">Время без сети</div>
                        <div class="h5 mt-2 mb-0 fw-bold text-secondary">{{ metrics.total_down_str }}</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row g-3 mb-4">
            <div class="col-md-6">
                <div class="card border-0 shadow-sm h-100">
                    <div class="card-body">
                        <h5 class="card-title mb-3">Типы сбоев</h5>
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Кратковременные (<= 10 сек)
                                <span class="badge bg-warning text-dark rounded-pill">{{ metrics.short_count }}</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Длительные (> 10 сек)
                                <span class="badge bg-danger rounded-pill">{{ metrics.long_count }}</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card border-0 shadow-sm h-100">
                    <div class="card-body">
                        <h5 class="card-title mb-3">Период мониторинга</h5>
                        <p class="mb-1"><strong>Начало:</strong> {{ metrics.start_time }}</p>
                        <p class="mb-1"><strong>Конец:</strong> {{ metrics.end_time }}</p>
                        <p class="mb-0"><strong>Всего времени:</strong> {{ metrics.total_time_str }}</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Статистика по дням -->
        <div class="card border-0 shadow-sm mb-4">
            <div class="card-header bg-white font-weight-bold fw-bold">Статистика по дням</div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Дата</th>
                                <th>В сети</th>
                                <th>Без сети</th>
                                <th>Обрывов</th>
                                <th>Аптайм</th>
                                <th class="text-end">Действие</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for day in daily_stats %}
                            <tr>
                                <td>{{ day.date }}</td>
                                <td>{{ day.up_time }}</td>
                                <td>{{ day.down_time }}</td>
                                <td><span class="badge bg-secondary">{{ day.dc_cnt }}</span></td>
                                <td><strong>{{ "%.2f"|format(day.pct) }}%</strong></td>
                                <td class="text-end">
                                    <a href="/day/{{ day.date }}" target="_blank" class="btn btn-sm btn-outline-primary">
                                        Просмотреть логи
                                    </a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Детализация длительных обрывов -->
        {% if long_disconnects %}
        <div class="card border-0 shadow-sm">
            <div class="card-header bg-white fw-bold text-danger">Детализация длительных обрывов (> 10с)</div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Начало</th>
                                <th>Конец</th>
                                <th>Длительность</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in long_disconnects %}
                            <tr>
                                <td>{{ row.start }}</td>
                                <td>{{ row.end }}</td>
                                <td><span class="badge bg-danger">{{ row.duration_sec }} сек</span></td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        {% endif %}
        {% endif %}
    </div>
</body>
</html>
"""

DAY_DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Логи за {{ date_str }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container py-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2>Детализация событий за {{ date_str }}</h2>
            <button onclick="window.close()" class="btn btn-secondary">Закрыть страницу</button>
        </div>

        {% if events %}
        <div class="card border-0 shadow-sm">
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>#</th>
                                <th>Статус</th>
                                <th>Начало</th>
                                <th>Конец</th>
                                <th>Длительность</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for e in events %}
                            <tr class="{{ 'table-danger' if e.status == 0 else '' }}">
                                <td>{{ loop.index }}</td>
                                <td>
                                    {% if e.status == 1 %}
                                        <span class="badge bg-success">В сети</span>
                                    {% else %}
                                        <span class="badge bg-danger">Обрыв</span>
                                    {% endif %}
                                </td>
                                <td>{{ e.start }}</td>
                                <td>{{ e.end }}</td>
                                <td><strong>{{ e.duration_str }}</strong></td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        {% else %}
            <div class="alert alert-warning">За выбранную дату нет записей.</div>
        {% endif %}
    </div>
</body>
</html>
"""

def get_parsed_df():
    if not os.path.exists(LOG_FILE):
        return None, "Файл логов не найден."

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    records = []
    for line in lines:
        if line.startswith("Было с "):
            status = 1
            parts = line[len("Было с "):].split(" по ")
        elif line.startswith("Не было с "):
            status = 0
            parts = line[len("Не было с "):].split(" по ")
        else:
            continue

        start_dt = datetime.datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.datetime.strptime(parts[1], "%Y-%m-%d %H:%M:%S")
        duration_sec = (end_dt - start_dt).total_seconds()

        records.append({
            'status': status,
            'start': start_dt,
            'end': end_dt,
            'duration_sec': duration_sec
        })

    if not records:
        return None, "Файл логов пуст или содержит некорректные данные."

    return pd.DataFrame(records), None

@app.route('/')
def index():
    df, error = get_parsed_df()
    if error:
        return render_template_string(INDEX_TEMPLATE, error=error)

    start_time = df['start'].min()
    end_time = df['end'].max()
    total_sec = (end_time - start_time).total_seconds()

    up_df = df[df['status'] == 1]
    down_df = df[df['status'] == 0]

    total_up_sec = up_df['duration_sec'].sum()
    total_down_sec = down_df['duration_sec'].sum()
    uptime_pct = (total_up_sec / (total_up_sec + total_down_sec)) * 100 if (total_up_sec + total_down_sec) > 0 else 0

    metrics = {
        'start_time': start_time.strftime("%Y-%m-%d %H:%M:%S"),
        'end_time': end_time.strftime("%Y-%m-%d %H:%M:%S"),
        'total_time_str': str(datetime.timedelta(seconds=int(total_sec))),
        'total_up_str': str(datetime.timedelta(seconds=int(total_up_sec))),
        'total_down_str': str(datetime.timedelta(seconds=int(total_down_sec))),
        'uptime_pct': uptime_pct,
        'num_disconnects': len(down_df),
        'short_count': len(down_df[down_df['duration_sec'] <= 10]),
        'long_count': len(down_df[down_df['duration_sec'] > 10])
    }

    long_df = down_df[down_df['duration_sec'] > 10]
    long_disconnects = []
    for _, r in long_df.iterrows():
        long_disconnects.append({
            'start': r['start'].strftime("%Y-%m-%d %H:%M:%S"),
            'end': r['end'].strftime("%Y-%m-%d %H:%M:%S"),
            'duration_sec': int(r['duration_sec'])
        })

    df['date'] = df['start'].dt.date
    daily_stats = []
    for date, group in df.groupby('date'):
        up_s = group[group['status'] == 1]['duration_sec'].sum()
        down_s = group[group['status'] == 0]['duration_sec'].sum()
        dc_cnt = len(group[group['status'] == 0])
        pct = (up_s / (up_s + down_s)) * 100 if (up_s + down_s) > 0 else 0
        daily_stats.append({
            'date': str(date),
            'up_time': str(datetime.timedelta(seconds=int(up_s))),
            'down_time': str(datetime.timedelta(seconds=int(down_s))),
            'dc_cnt': dc_cnt,
            'pct': pct
        })

    return render_template_string(
        INDEX_TEMPLATE,
        metrics=metrics,
        long_disconnects=long_disconnects,
        daily_stats=daily_stats,
        error=None
    )

@app.route('/day/<date_str>')
def day_detail(date_str):
    df, error = get_parsed_df()
    if error:
        return f"Ошибка: {error}", 400

    df['date_str'] = df['start'].dt.strftime("%Y-%m-%d")
    day_df = df[df['date_str'] == date_str]

    events = []
    for _, r in day_df.iterrows():
        dur = int(r['duration_sec'])
        dur_str = str(datetime.timedelta(seconds=dur)) if dur >= 60 else f"{dur} сек"
        events.append({
            'status': r['status'],
            'start': r['start'].strftime("%H:%M:%S"),
            'end': r['end'].strftime("%H:%M:%S"),
            'duration_str': dur_str
        })

    return render_template_string(DAY_DETAIL_TEMPLATE, date_str=date_str, events=events)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)