import requests
import json
import datetime
import os

# ==================== 配置 ====================
APP_ID = os.environ.get("APP_ID")
APP_SECRET = os.environ.get("APP_SECRET")
USER_ID = os.environ.get("USER_ID")
TEMPLATE_ID = os.environ.get("TEMPLATE_ID")
OPENWEATHER_KEY = os.environ.get("OPENWEATHER_KEY", "")
NEXT_MEETING_DATE = os.environ.get("NEXT_MEETING_DATE", "2026-04-04")

# 删除 LOCATION，改用城市名
NAME_1 = os.environ.get("NAME_1", "美孚")
NAME_2 = os.environ.get("NAME_2", "巢鸭")

# 城市名配置（精确地点 + 备用）
CITY_1_PRECISE = "Sham Shui Po,Hong Kong"  # 深水埗
CITY_1_FALLBACK = "Hong Kong"               # 备用

CITY_2_PRECISE = "Nishisugamo,Tokyo"        # 西巢鸭
CITY_2_FALLBACK = "Tokyo"                    # 备用

# ==================== 函数 ====================

def get_access_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    resp = requests.get(url, timeout=10).json()
    return resp.get('access_token')

def get_weather_city(city_name, api_key):
    """用城市名获取天气"""
    if not api_key:
        return "API未配置", "--", "--"
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric&lang=zh_cn"
        data = requests.get(url, timeout=10).json()
        
        if data.get('cod') == 200:
            weather = data['weather'][0]['description']
            temp_max = round(data['main'].get('temp_max', data['main']['temp']))
            temp_min = round(data['main'].get('temp_min', data['main']['temp']))
            return weather, temp_max, temp_min
        return "获取失败", "--", "--"
    except Exception as e:
        print(f"天气API错误: {e}")
        return "服务暂不可用", "--", "--"

def get_weather_with_fallback(precise_city, fallback_city, api_key):
    """先尝试精确地点，失败则用备用"""
    # 尝试精确地点
    w, h, l = get_weather_city(precise_city, api_key)
    if w not in ["获取失败", "服务暂不可用", "API未配置"]:
        return w, h, l, ""  # 成功，无备用标记
    
    # 失败，尝试备用
    w, h, l = get_weather_city(fallback_city, api_key)
    return w, h, l, "(备用)"

def get_days_left():
    try:
        today = datetime.date.today()
        meeting = datetime.datetime.strptime(NEXT_MEETING_DATE, "%Y-%m-%d").date()
        days = (meeting - today).days
        return max(days, 0)
    except:
        return 0

def get_words():
    quotes = [
        "我不在你身边的日子里，请照顾好自己。",
        "但愿人长久，千里共婵娟。",
    ]
    return quotes[datetime.date.today().day % len(quotes)]

def main():
    print("=== 早安推送 ===")
    token = get_access_token()
    if not token:
        print("❌ 获取token失败")
        return
    
    today = datetime.date.today()
    weekday = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][today.weekday()]
    
    # 获取天气（带备用）
    w1, h1, l1, fb1 = get_weather_with_fallback(CITY_1_PRECISE, CITY_1_FALLBACK, OPENWEATHER_KEY)
    w2, h2, l2, fb2 = get_weather_with_fallback(CITY_2_PRECISE, CITY_2_FALLBACK, OPENWEATHER_KEY)
    
    data = {
        "date": {
            "value": f"{today.strftime('%Y年%m月%d日')} {weekday}",
            "color": "#333333"
        },
        "weather": {
            "value": f"{NAME_1}{fb1}: {w1}",
            "color": "#4ECDC4"
        },
        "temperature": {
            "value": f"{h1}°C",
            "color": "#FF6B6B"
        },
        "temperature1": {
            "value": f"{l1}°C",
            "color": "#4ECDC4"
        },
        "weather2": {
            "value": f"{NAME_2}{fb2}: {w2}",
            "color": "#4ECDC4"
        },
        "temperature2": {
            "value": f"{h2}°C",
            "color": "#FF6B6B"
        },
        "temperature3": {
            "value": f"{l2}°C",
            "color": "#4ECDC4"
        },
        "date_left": {
            "value": f"{get_days_left()}天",
            "color": "#FF69B4"
        },
        "words": {
            "value": get_words(),
            "color": "#95E1D3"
        }
    }
    
    print(f"内容: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
    payload = {"touser": USER_ID, "template_id": TEMPLATE_ID, "data": data}
    result = requests.post(url, json=payload, timeout=10).json()
    
    if result.get('errcode') == 0:
        print("✅ 推送成功！")
    else:
        print(f"❌ 失败: {result.get('errmsg')}")

if __name__ == "__main__":
    main()
