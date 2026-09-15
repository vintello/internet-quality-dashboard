import os
import datetime
import pandas as pd
from flask import Flask, render_template, request, session, redirect, url_for
from translations import TRANSLATIONS

app = Flask(__name__)
app.secret_key = 'super-secret-key-change-me'
LOG_FILE = 'internet_history.log'

@app.context_processor
def inject_i18n():
    # Меняем значение по умолчанию на 'uk'
    lang = session.get('lang', 'uk')
    def translate(key):
        # В качестве резервного словаря (fallback) также указываем 'uk'
        return TRANSLATIONS.get(lang, TRANSLATIONS['uk']).get(key, key)
    return dict(_=translate, current_lang=lang)

@app.route('/set_lang/<lang>')
def set_lang(lang):
    if lang in TRANSLATIONS:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

def get_parsed_df():
    if not os.path.exists(LOG_FILE):
        return None, 'file_not_found'

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
        return None, 'file_empty'

    return pd.DataFrame(records), None

@app.route('/')
def index():
    df, error_key = get_parsed_df()
    if error_key:
        return render_template('index.html', error_key=error_key)

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
    long_disconnects = [
        {
            'start': r['start'].strftime("%Y-%m-%d %H:%M:%S"),
            'end': r['end'].strftime("%Y-%m-%d %H:%M:%S"),
            'duration_sec': int(r['duration_sec'])
        }
        for _, r in long_df.iterrows()
    ]

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

    return render_template(
        'index.html',
        metrics=metrics,
        long_disconnects=long_disconnects,
        daily_stats=daily_stats,
        error_key=None
    )

@app.route('/day/<date_str>')
def day_detail(date_str):
    df, error_key = get_parsed_df()
    if error_key:
        return render_template('day_detail.html', error_key=error_key, date_str=date_str)

    df['date_str'] = df['start'].dt.strftime("%Y-%m-%d")
    day_df = df[df['date_str'] == date_str]

    events = []
    for _, r in day_df.iterrows():
        dur = int(r['duration_sec'])
        #dur_str = str(datetime.timedelta(seconds=dur)) if dur >= 60 else f"{dur} " + _('sec')
        events.append({
            'status': r['status'],
            'start': r['start'].strftime("%H:%M:%S"),
            'end': r['end'].strftime("%H:%M:%S"),
            'duration_sec': int(r['duration_sec'])
        })

    return render_template('day_detail.html', date_str=date_str, events=events)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)