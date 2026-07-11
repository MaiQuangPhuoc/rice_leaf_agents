import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.tools.rag_tools import weather_tool, web_search_tool

print("=" * 40)
print("TEST 1: weather_tool")
print("=" * 40)
result = weather_tool.invoke({"location": "Quảng Nam"})
print(result)


print("TEST 1.5: weather_tool forecast")
result = weather_tool.invoke({"location": "Can Tho", "forecast": True})
print(result)


print("\n" + "=" * 40)
print("TEST 2: web_search_tool")
print("=" * 40)
result = web_search_tool.invoke({"query": "các giai đoạn phát triển bệnh bạc lá lúa lá gì "})
print(result)
