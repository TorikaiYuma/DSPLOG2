import flet as ft
import requests

WEATHER_CODES = {
    "100": {"name": "晴れ", "icon": ft.icons.WB_SUNNY},
    "101": {"name": "晴れ 時々 くもり", "icon": ft.icons.CLOUD_QUEUE},
    "103": {"name": "晴れ 時々 雨", "icon": ft.icons.UMBRELLA},
    "105": {"name": "晴れ 時々 雪", "icon": ft.icons.AC_UNIT},
    "111": {"name": "晴れ のち くもり", "icon": ft.icons.CLOUD_QUEUE},
    "200": {"name": "くもり", "icon": ft.icons.CLOUD},
    "201": {"name": "くもり 時々 晴れ", "icon": ft.icons.WB_SUNNY},
    "203": {"name": "くもり 時々 雨", "icon": ft.icons.UMBRELLA},
    "205": {"name": "くもり 時々 雪", "icon": ft.icons.AC_UNIT},
    "206": {"name": "くもり のち 雨", "icon": ft.icons.UMBRELLA},
    "260": {"name": "くもり のち 時々 雨", "icon": ft.icons.UMBRELLA},
    "300": {"name": "雨", "icon": ft.icons.UMBRELLA},
    "301": {"name": "雨 時々 晴れ", "icon": ft.icons.WB_SUNNY},
    "303": {"name": "雨 時々 雪", "icon": ft.icons.AC_UNIT},
    "306": {"name": "大雨", "icon": ft.icons.WATER_DROP},
    "400": {"name": "雪", "icon": ft.icons.AC_UNIT},
    "401": {"name": "雪 時々 晴れ", "icon": ft.icons.WB_SUNNY},
    "402": {"name": "雪 時々止む", "icon": ft.icons.STOP},
    "403": {"name": "雪 時々 雨", "icon": ft.icons.UMBRELLA},
    "405": {"name": "大雪", "icon": ft.icons.AC_UNIT},
}
def get_weather_info(code):
    return WEATHER_CODES.get(code, {"name": "不明", "icon": ft.icons.HELP})

def get_region_data():
    URL = "http://www.jma.go.jp/bosai/common/const/area.json"
    try:
        region_json = requests.get(URL).json()
        return region_json
    except Exception as e:
        print(f"地域データの取得エラー: {e}")
        return None

def get_weather_data(region_code):
    URL = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{region_code}.json"
    try:
        weather_json = requests.get(URL).json()
        return weather_json
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"天気データの取得エラー (コード: {region_code}): 404 Not Found")
        else:
            print(f"天気データの取得エラー (コード: {region_code}): {e}")
        return None
    except Exception as e:
        print(f"その他のエラー (コード: {region_code}): {e}")
        return None

# 天気カードを作成
def create_weather_card(date, weather_code, max_temp, min_temp):
    weather_info = get_weather_info(weather_code)
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        date.split("-")[0] + "-" + date.split("-")[1] + "-" + date.split("-")[2],
                        weight="bold",
                        size=14,
                        color="#2B2B2B"
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(
                                    weather_info["icon"],
                                    size=32,
                                    color="#FF9800"  
                                ),
                                ft.Container(width=8),  
                                ft.Icon(
                                    ft.icons.CLOUD,
                                    size=28,
                                    color="#78909C"  
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        margin=ft.margin.symmetric(vertical=10),
                    ),
                    ft.Text(
                        weather_info["name"],
                        size=14,
                        color="#2B2B2B",
                        weight="w500"
                    ),
                    ft.Container(height=8),  
                    ft.Row(
                        [
                            ft.Text(
                                f"{min_temp}°C",
                                size=14,
                                color="#1976D2",  
                                weight="bold"
                            ),
                            ft.Text(
                                " / ",
                                size=14,
                                color="#757575",
                            ),
                            ft.Text(
                                f"{max_temp}°C",
                                size=14,
                                color="#D32F2F",  
                                weight="bold"
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=ft.padding.all(16),
            width=140,
            height=160,
            bgcolor=ft.colors.WHITE,
            border_radius=16,
        ),
        elevation=0,  
    )

def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.padding = 10
    page.theme_mode = ft.ThemeMode.LIGHT

    region_data = get_region_data()
    if not region_data:
        page.add(ft.Text("地域データの取得に失敗しました"))
        return

    weather_grid = ft.GridView(
        expand=True,
        runs_count=3,
        spacing=10,
        run_spacing=10,
    )

    def create_sidebar():
        sidebar = ft.Column(spacing=10)
        for region_code, region_info in region_data["centers"].items():
            region_tile = ft.ExpansionTile(
                title=ft.Text(region_info["name"], color="white"),
                controls=[
                    ft.ListTile(
                        title=ft.Column([
                            ft.Text(
                                region_data["offices"].get(sub_region, {}).get("name", "不明"),
                                color="white",
                                size=16
                            ),
                            ft.Text(
                                sub_region,
                                color="white70",
                                size=12
                            )
                        ], spacing=2),
                        on_click=lambda e, code=sub_region: show_weather(code)
                    )
                    for sub_region in region_info["children"]
                ],
            )
            sidebar.controls.append(region_tile)
        return sidebar

    def show_weather(region_code):
        weather_data = get_weather_data(region_code)
        if not weather_data or len(weather_data) < 2:
            weather_grid.controls = [ft.Text("天気データの取得に失敗しました")]
            page.update()
            return

        forecasts = weather_data[1]["timeSeries"][0]
        dates = forecasts["timeDefines"]
        areas = forecasts["areas"]

        area = areas[0]

        temp_data = weather_data[1]["timeSeries"][1]
        temp_area = temp_data["areas"][0]

        cards = []
        for i in range(len(dates)):
            max_temp = temp_area.get("tempsMax", [None])[i] if "tempsMax" in temp_area else None
            min_temp = temp_area.get("tempsMin", [None])[i] if "tempsMin" in temp_area else None
            
            cards.append(
                create_weather_card(
                    date=dates[i].split("T")[0],
                    weather_code=area["weatherCodes"][i],
                    max_temp=max_temp,
                    min_temp=min_temp
                )
            )

        weather_grid.controls = cards
        page.update()

    sidebar_container = ft.Container(
        content=create_sidebar(),
        width=250,
        bgcolor="#455A64",
        padding=10,
        border_radius=10,
    )

    page.add(
        ft.Row(
            [
                sidebar_container,
                ft.VerticalDivider(width=1),
                weather_grid,
            ],
            expand=True,
        )
    )

ft.app(target=main)

