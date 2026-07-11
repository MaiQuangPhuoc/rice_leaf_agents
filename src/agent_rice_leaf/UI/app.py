from flask import Flask, request, jsonify
import requests
import base64

app = Flask(__name__)

RUNPY_URL = "http://127.0.0.1:8000/from_image"   # endpoint run.py sẽ tạo

@app.post("/upload")
def upload():
    img = request.files["image"].read()
    b64 = base64.b64encode(img).decode()

    # Gửi ảnh sang run.py
    resp = requests.post(RUNPY_URL, json={"image": b64})
    reply = resp.json().get("reply")

    return jsonify({"reply": reply})

@app.post("/chat")
def chat():
    text = request.json.get("text")
    resp = requests.post("http://127.0.0.1:8000/from_text", json={"text": text})
    return jsonify(resp.json())

if __name__ == "__main__":
    app.run(port=5000)
