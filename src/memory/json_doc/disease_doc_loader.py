import json
import os

# Map tên bệnh (context_dict["disease"]) → tên file JSON
DISEASE_FILE_MAP = {
    "đạo ôn lá": "dao_on.json",
    "Khô vằn": "kho_van.json"
    # thêm bệnh khác ở đây
}

# JSON_DIR = os.path.join(os.path.dirname(__file__))
JSON_DIR = r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\src\memory\json_doc"


def _normalize_severity(value: str) -> str:
    """trung bình → trung_bình, còn lại giữ nguyên"""
    if value is None:
        return None
    return value.strip().replace(" ", "_")


def load_disease_doc(context_dict: dict) -> dict:
    """
    Nhận context_dict, trả về dict gồm các trường quan trọng từ file JSON bệnh.
    Trả về {} nếu không tìm thấy file.
    """
    disease = (context_dict.get("disease") or "").strip().lower()
    filename = DISEASE_FILE_MAP.get(disease)
    if not filename:
        return {}

    filepath = os.path.join(JSON_DIR, filename)
    if not os.path.exists(filepath):
        return {}

    with open(filepath, "r", encoding="utf-8") as f:
        doc = json.load(f)

    result = {}

    # 1. template_ke_hoach theo disease_severity
    severity_raw = context_dict.get("disease_severity")
    severity_key = _normalize_severity(severity_raw)
    result["template_ke_hoach"] = doc.get("template_ke_hoach", {}).get(severity_key, [])

    # 2. thu_vien_phase — lấy toàn bộ để build prompt
    result["thu_vien_phase"] = doc.get("thu_vien_phase", [])

    # 3. luu_y_theo_giai_doan_lua
    rice_stage = (context_dict.get("rice_stage") or "").strip().lower()
    result["luu_y_rice_stage"] = doc.get("luu_y_theo_giai_doan_lua", {}).get(rice_stage, [])

    # 4. anh_huong_thoi_tiet + hanh_dong_theo_thoi_tiet
    weather = (context_dict.get("weather_description") or "").strip().lower()
    anh_huong = doc.get("anh_huong_thoi_tiet", {})
    hanh_dong_tt = doc.get("hanh_dong_theo_thoi_tiet", {})
    # Tìm key khớp (partial match vì weather có thể là "mưa nhiều, ẩm độ cao")
    result["weather_notes"] = []
    result["weather_actions"] = []
    for key in anh_huong:
        if key in weather:
            result["weather_notes"].append(f"{key}: {anh_huong[key]}")
    for key in hanh_dong_tt:
        if key in weather:
            result["weather_actions"].extend(hanh_dong_tt[key])

    # 5. luu_y_theo_giong_lua
    rice_variety = (context_dict.get("rice_variety") or "").strip()
    result["luu_y_giong_lua"] = doc.get("luu_y_theo_giong_lua", {}).get(rice_variety, [])

    # 6. muc_tieu_dieu_tri
    result["muc_tieu_dieu_tri"] = doc.get("muc_tieu_dieu_tri", [])

    # 7. chi_so_danh_gia
    result["chi_so_danh_gia"] = doc.get("chi_so_danh_gia", [])

    return result