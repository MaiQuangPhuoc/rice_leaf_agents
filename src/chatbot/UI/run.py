from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import sys , os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..","..")))
from src.chatbot.cv import CV
from src.chatbot.engine import ChatbotEngine

from flask import request, jsonify
import os

chatbot = ChatbotEngine()









app = Flask(__name__)
CORS(app)   # Cho phép frontend gọi API từ domain khác

def clean_filename(text):
    # Giả sử filename hợp lệ có đuôi .jpg hoặc .png
    # Tách lấy phần cuối sau dấu ':', nếu có
    if ':' in text:
        text = text.split(':')[-1].strip()
    # Bỏ khoảng trắng 2 đầu
    text = text.strip()
    # Chỉ giữ filename có đuôi hợp lệ, còn nếu không đúng trả về None hoặc ""
    if text.lower().endswith(('.jpg', '.png')):
        return text
    return None


def format_result(result, top_k=None):
    predicted_class = result["predicted_class"]
    predicted_score = result["predicted_score"]

    lines = []
    lines.append(
        f"Dự đoán bệnh : {predicted_class} ({predicted_score * 100:.1f}%)"
    )
    lines.append("-" * 30)

    # sort score giảm dần
    sorted_scores = sorted(
        result["all_scores"].items(),
        key=lambda x: x[1],
        reverse=True
    )

    if top_k is not None:
        sorted_scores = sorted_scores[:top_k]

    for cls, score in sorted_scores:
        lines.append(f"{cls} : {score * 100:.1f}%")

    return "\n".join(lines)



# @app.route("/chat", methods=["POST"])
# def chat():
#     data = request.get_json()
#     user_text_raw = data.get("text", "").strip()
#     filename = clean_filename(user_text_raw)

#     if filename is not None:
#         full_path = os.path.join(r"D:\VKU\Nam_4\ky_I\computer_vision\dataset\test", filename)
#         try:
#             prediction = CV(full_path)
#             bot_reply = format_result(prediction)

#             # prediction = CV(full_path)
#             # bot_reply = f"Dự đoán bệnh lá lúa: {prediction}"
#         except Exception as e:
#             bot_reply = f"Lỗi khi dự đoán: {str(e)}"
#     else:
#         # Nếu không phải tên file ảnh hợp lệ thì trả lời bình thường
#         bot_reply = f"user_input: {user_text_raw}"

#     return jsonify({"reply": bot_reply})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_text_raw = data.get("text", "").strip()

    filename = clean_filename(user_text_raw)

    # 1️⃣ Nếu là ảnh → CV
    if filename is not None:
        full_path = os.path.join(
            r"D:\VKU\Nam_4\ky_I\computer_vision\dataset\test",
            filename
        )
        try:
            prediction = CV(full_path)
            bot_reply = format_result(prediction)
        except Exception as e:
            bot_reply = f"Lỗi khi dự đoán ảnh: {str(e)}"

    # 2️⃣ Nếu là câu hỏi → chatbot
    else:
        bot_reply = chatbot.chat(user_text_raw)

    return jsonify({"reply": bot_reply})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)



# file:///D:/VKU/Nam_4/ky_I/computer_vision/EDUAGENT/src/chatbot/UI/index.html?
# file:///D:/VKU/Nam_4/ky_I/computer_vision/slide/Deep_Learning_Rice_Disease_Classification.pdf.pdf