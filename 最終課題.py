import requests
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
import re

# SQLiteデータベース名
db_name = "suumo_data.db"

# データベース初期化
def initialize_database():
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS properties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area TEXT,
        name TEXT,
        rent REAL,
        station TEXT
    )
    """)
    conn.commit()
    conn.close()

# データベースに保存
def save_to_database(properties):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    for prop in properties:
        cursor.execute("""
        INSERT INTO properties (area, name, rent, station) VALUES (?, ?, ?, ?)
        """, (prop["area"], prop["name"], prop["rent"], prop["station"]))
    conn.commit()
    conn.close()

# スーモをスクレイピング
def scrape_suumo(url, area):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    properties = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        
        # 物件情報を取得
        items = soup.find_all("div", class_="cassetteitem")
        for item in items:
            try:
                # 物件名
                name = item.find("div", class_="cassetteitem_content-title").text.strip()
                
                # 最寄り駅
                station = item.find("div", class_="cassetteitem_detail-text").text.strip()
                
                # 賃料を複数取得する
                rows = item.find_all("tr", class_="js-cassette_link")
                for row in rows:
                    try:
                        rent_text = row.find("span", class_="cassetteitem_other-emphasis")
                        rent = float(re.sub("[^0-9.]", "", rent_text.text.strip())) * 10000 if rent_text else None  # 家賃（万円 → 円）

                        # 家賃が取得できない、または0円以下の場合はスキップ
                        if rent and rent > 1000:  # 家賃が1000円（0.1万円）以下を除外
                            # デバッグ用出力
                            print(f"[{area}] 物件: {name}, 最寄り駅: {station}, 家賃: {rent} 円")

                            # データを追加
                            properties.append({
                                "area": area,
                                "name": name,
                                "rent": rent,
                                "station": station
                            })
                    except Exception as e:
                        print(f"賃料データ取得エラー: {e}")
            except Exception as e:
                print(f"データ取得エラー: {e}")
    else:
        print(f"ページ取得エラー: {response.status_code}")

    return properties

# エリアごとの平均家賃を計算
def analyze_rent_by_area():
    conn = sqlite3.connect(db_name)
    df = pd.read_sql_query("SELECT * FROM properties", conn)
    conn.close()

    # エリアごとの平均家賃を計算
    avg_rent_by_area = df.groupby("area")["rent"].mean()

    print("\nエリアごとの平均家賃:")
    print(avg_rent_by_area)

# 実行フロー
def main():
    # データベース初期化
    initialize_database()

    # 各エリアのURL（スーモの検索結果ページ）
    urls = {
        "新宿": "https://suumo.jp/chintai/tokyo/sc_shinjuku/",
        "三鷹": "https://suumo.jp/chintai/tokyo/sc_mitaka/",
        "立川": "https://suumo.jp/chintai/tokyo/sc_tachikawa/"
    }

    # スクレイピング
    for area, url in urls.items():
        print(f"{area}の物件情報をスクレイピング中...")
        properties = scrape_suumo(url, area)

        if properties:
            print(f"{area}の取得物件数: {len(properties)}")
            
            # データベースに保存
            save_to_database(properties)
            print(f"{area}のデータをデータベースに保存しました！")
        else:
            print(f"{area}の物件情報が取得できませんでした。")

    # エリアごとの平均家賃を計算
    analyze_rent_by_area()

# 実行
if __name__ == "__main__":
    main()



