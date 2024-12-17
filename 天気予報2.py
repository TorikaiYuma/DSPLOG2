import sqlite3
import requests
import json

# 気象庁APIのURL (例: 天気予報の地域コードに合わせて調整可能)
BASE_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"
AREA_CODES = ["130000", "140000"]  # 東京、神奈川などの地域コード

# データベースのセットアップ
def setup_database():
    conn = sqlite3.connect("weather_forecast.db")
    cursor = conn.cursor()

    # 地域テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS area (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL
        )
    ''')

    # 天気データテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forecast (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            weather_code TEXT NOT NULL,
            weather_description TEXT NOT NULL,
            FOREIGN KEY(area_id) REFERENCES area(id)
        )
    ''')

    conn.commit()
    return conn

# 天気データを取得し、DBに保存
def fetch_and_store_weather_data(conn):
    cursor = conn.cursor()

    for code in AREA_CODES:
        # 天気データの取得
        url = BASE_URL.format(code)
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch data for area code {code}")
            continue

        data = response.json()
        area_name = data[0]["publishingOffice"]
        
        # 地域情報の保存
        cursor.execute('''
            INSERT OR IGNORE INTO area (code, name) VALUES (?, ?)
        ''', (code, area_name))
        
        area_id = cursor.execute('''
            SELECT id FROM area WHERE code = ?
        ''', (code,)).fetchone()[0]

        # 天気予報データの保存
        for time_series in data[0]["timeSeries"]:
            if "timeDefines" in time_series and "areas" in time_series:
                times = time_series["timeDefines"]
                weather_descriptions = time_series["areas"][0].get("weathers", [])
                weather_codes = time_series["areas"][0].get("weatherCodes", [])

                for i, time in enumerate(times):
                    if i < len(weather_descriptions) and i < len(weather_codes):
                        cursor.execute('''
                            INSERT INTO forecast (area_id, date, weather_code, weather_description)
                            VALUES (?, ?, ?, ?)
                        ''', (area_id, time, weather_codes[i], weather_descriptions[i]))

    conn.commit()

# DBから天気データを取得して表示
def display_weather_forecast(conn):
    cursor = conn.cursor()

    cursor.execute('''
        SELECT a.name, f.date, f.weather_description
        FROM forecast f
        JOIN area a ON f.area_id = a.id
        ORDER BY a.name, f.date
    ''')

    results = cursor.fetchall()
    for row in results:
        print(f"地域: {row[0]} | 日付: {row[1]} | 天気: {row[2]}")

def main():
    conn = setup_database()
    fetch_and_store_weather_data(conn)
    display_weather_forecast(conn)
    conn.close()

if __name__ == "__main__":
    main()
