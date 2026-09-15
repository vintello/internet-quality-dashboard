import pandas as pd
import datetime

LOG_FILE = 'internet_history.log'
with open(LOG_FILE, "r", encoding="utf-8") as f:
    log_data = f.read()

lines = [l.strip() for l in log_data.strip().split('\n') if l.strip()]

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

df = pd.DataFrame(records)

# Общая статистика
start_time = df['start'].min()
end_time = df['end'].max()
total_sec = (end_time - start_time).total_seconds()

up_df = df[df['status'] == 1]
down_df = df[df['status'] == 0]

total_up_sec = up_df['duration_sec'].sum()
total_down_sec = down_df['duration_sec'].sum()
uptime_pct = (total_up_sec / (total_up_sec + total_down_sec)) * 100

num_disconnects = len(down_df)

# Анализ времени простоя
short_disconnects = down_df[down_df['duration_sec'] <= 10]
long_disconnects = down_df[down_df['duration_sec'] > 10]

print(f"Начало: {start_time}")
print(f"Конец: {end_time}")
print(f"Общее время: {datetime.timedelta(seconds=total_sec)}")
print(f"Время в сети: {datetime.timedelta(seconds=total_up_sec)}")
print(f"Время без сети: {datetime.timedelta(seconds=total_down_sec)}")
print(f"Аптайм %: {uptime_pct:.2f}%")
print(f"Всего обрывов: {num_disconnects}")
print(f"Кратковременные обрывы (<= 10с): {len(short_disconnects)}")
print(f"Длительные обрывы (> 10с): {len(long_disconnects)}")
print("Детализация длительных обрывов:")
for idx, r in long_disconnects.iterrows():
    print(f"  {r['start']} -> {r['end']} ({r['duration_sec']}с)")

# Статистика по дням
df['date'] = df['start'].dt.date
for date, group in df.groupby('date'):
    up_s = group[group['status'] == 1]['duration_sec'].sum()
    down_s = group[group['status'] == 0]['duration_sec'].sum()
    dc_cnt = len(group[group['status'] == 0])
    pct = (up_s / (up_s + down_s)) * 100
    print(f"\nДата: {date}")
    print(f"  В сети: {datetime.timedelta(seconds=up_s)}")
    print(f"  Без сети: {datetime.timedelta(seconds=down_s)}")
    print(f"  Обрывов: {dc_cnt}")
    print(f"  Аптайм: {pct:.2f}%")