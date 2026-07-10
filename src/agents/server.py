# from flask import Flask, request, jsonify
# from flask_cors import CORS

# # pip install flask flask_cors

# app = Flask(__name__)
# CORS(app)  # cho phép gọi từ frontend (JS chạy ở file:// hoặc 127.0.0.1)

# @app.route("/chat", methods=["POST"])
# def chat():
#     data = request.get_json()
#     user_message = data.get("text", "")

#     user_input = input("🗣️   User: ")

#     return jsonify({"reply": f" đã nhận :{user_message} \nphản hồi: {user_input}"})

# if __name__ == "__main__":
#     app.run(host="127.0.0.1", port=5000, debug=True)


import json
from datetime import datetime

# Lấy thời gian hiện tại theo định dạng YYYY-MM-DD-HH-MM-SS
current_time = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")

# Dữ liệu mẫu
data = {
    "plan_id": "plan_001",
    "overview": "Đây là kế hoạch tổng quan.",
    "detail": "Đây là chi tiết từng bước trong kế hoạch.",
    "time": current_time  # thêm trường thời gian
}

# Đường dẫn file lưu
file_path = r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\plans\study_plan.json"

# Ghi dữ liệu vào file JSON
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"Dữ liệu đã được lưu vào {file_path} lúc {current_time}")
