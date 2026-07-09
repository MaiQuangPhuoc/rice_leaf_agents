from langchain_core.tools import tool
from langchain_core.documents import Document
import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

 
from src.configs import env_config

import requests
from tavily import TavilyClient
import re
import unicodedata
import unicodedata

 
_tavily = TavilyClient(api_key=env_config.api_key_tavily)
 



# Thêm sau dòng import, trước @tool
LOCATION_MAP = {
    "quảng nam": "Tam Ky",
    "cần thơ": "Can Tho",
    "an giang": "Long Xuyen",
    "hà nội": "Hanoi",
    "hồ chí minh": "Ho Chi Minh City",
    "đà nẵng": "Da Nang",
    "huế": "Hue",
    "quảng ngãi": "Quang Ngai",
    "bình định": "Quy Nhon",
    "kiên giang": "Rach Gia",
    "đồng tháp": "Cao Lanh",
    "tiền giang": "My Tho",
    "hậu giang": "Vi Thanh",
    "sóc trăng": "Soc Trang",
    "bạc liêu": "Bac Lieu",
    "cà mau": "Ca Mau",
}

# Trong weather_tool, thêm dòng đầu tiên trong try block:



@tool
def weather_tool(location: str, forecast: bool = False) -> str:
    """
    Lấy thông tin thời tiết tại một địa điểm.
    Dùng khi user hỏi về thời tiết, độ ẩm, nhiệt độ ảnh hưởng đến bệnh lúa.

    Args:
        location: Tên địa điểm (ví dụ: "Can Tho", "An Giang")
        forecast: False = thời tiết hiện tại, True = dự báo 5 ngày tới
    """
    try:
        if forecast:
            url = "http://api.openweathermap.org/data/2.5/forecast"
        else:
            url = "http://api.openweathermap.org/data/2.5/weather"


        location_en = LOCATION_MAP.get(location.lower().strip(), location)
        params = {
            "q": f"{location_en},VN",
            "appid": env_config.api_key_weather,
            "units": "metric",
            "lang": "vi"
        }
        res = requests.get(url, params=params, timeout=5)
        data = res.json()

        if res.status_code != 200:
            return f"Không lấy được thời tiết tại {location}."

        if not forecast:
            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            desc = data["weather"][0]["description"]
            warning = ""
            if humidity > 85 and 20 <= temp <= 28:
                warning = "⚠️ Nguy cơ cao bệnh ĐẠO ÔN (ẩm cao, 20-28°C)."
            elif humidity > 85 and temp > 28:
                warning = "⚠️ Nguy cơ cao bệnh KHÔ VẰN, BẠC LÁ."
            return (
                f"Thời tiết hiện tại tại {location}:\n"
                f"- Nhiệt độ: {temp}°C\n"
                f"- Độ ẩm: {humidity}%\n"
                f"- Mô tả: {desc}\n"
                f"{warning}"
            )
        else:
            output = f"Dự báo 5 ngày tới tại {location}:\n"
            seen_dates = []
            for item in data["list"]:
                date = item["dt_txt"][:10]
                if date not in seen_dates:
                    seen_dates.append(date)
                    temp = item["main"]["temp"]
                    humidity = item["main"]["humidity"]
                    desc = item["weather"][0]["description"]
                    warning = ""
                    if humidity > 85 and 20 <= temp <= 28:
                        warning = " ⚠️ Nguy cơ ĐẠO ÔN"
                    elif humidity > 85 and temp > 28:
                        warning = " ⚠️ Nguy cơ KHÔ VẰN/BẠC LÁ"
                    output += f"- {date}: {temp}°C, ẩm {humidity}%, {desc}{warning}\n"
            return output.strip()

    except Exception as e:
        return f"Lỗi khi lấy thời tiết: {e}"



# URL đáng tin cậy (domain ưu tiên)
TRUSTED_DOMAINS = [
    "nongnghiep.vn", "baomoi.com", "vnexpress.net",
    "mard.gov.vn", "cuctrongtrot.gov.vn", "khuyennongvn.gov.vn",
    "bvtvhcm.gov.vn", "vaas.vn", "hoind.vn"
]

# URL rác / video → loại bỏ
BLOCKED_DOMAINS = [
    "youtube.com", "youtu.be", "tiktok.com", "facebook.com",
    "instagram.com", "twitter.com", "x.com", "pinterest.com"
]


def _is_blocked(url: str) -> bool:
    return any(domain in url for domain in BLOCKED_DOMAINS)


def _trust_score(url: str) -> int:
    """Ưu tiên domain đáng tin, trả về 1 nếu trusted, 0 nếu không."""
    return 1 if any(domain in url for domain in TRUSTED_DOMAINS) else 0


def _clean_text(text: str) -> str:
    """Loại bỏ nhiễu, chuẩn hóa text tiếng Việt."""
    # Chuẩn hóa unicode (NFC để tiếng Việt đúng dấu)
    text = unicodedata.normalize("NFC", text)
    # Bỏ HTML tags nếu còn sót
    text = re.sub(r"<[^>]+>", "", text)
    # Bỏ ký tự đặc biệt không cần thiết
    text = re.sub(r"[^\w\s\.\,\!\?\:\;\-\(\)\/\%°]", " ", text, flags=re.UNICODE)
    # Bỏ khoảng trắng thừa
    text = re.sub(r"\s+", " ", text).strip()
    return text


@tool
def web_search_tool(query: str) -> str:
    """
    Tìm kiếm thông tin trên internet.
    Dùng khi cần thông tin mới nhất về thuốc trừ sâu, kỹ thuật canh tác,
    hoặc thông tin không có trong cơ sở dữ liệu nội bộ.

    Args:
        query: Câu truy vấn tìm kiếm
    """
    try:
        results = _tavily.search(query=query, max_results=6, search_depth="basic")
        if not results or not results.get("results"):
            return "Không tìm thấy kết quả."

        # Lọc blocked + sort theo trust score
        filtered = [
            r for r in results["results"]
            if not _is_blocked(r.get("url", ""))
        ]
        filtered.sort(key=lambda r: _trust_score(r.get("url", "")), reverse=True)

        # Lấy top 3 sau lọc
        top = filtered[:3]
        if not top:
            return "Không tìm thấy kết quả phù hợp (đã lọc video/mạng xã hội)."

        output = ""
        for i, r in enumerate(top, 1):
            title = _clean_text(r.get("title", ""))
            content = _clean_text(r.get("content", ""))[:400]
            url = r.get("url", "")
            output += f"[{i}] {title}\nURL: {url}\n{content}\n\n"

        return output.strip()

    except Exception as e:
        return f"Lỗi khi tìm kiếm: {e}"