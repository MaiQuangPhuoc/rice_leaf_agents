import re

# ── Mapping chương ────────────────────────────────────────────────────────────

CHAPTER = {
    "chương 1": "MỆNH ĐỀ VÀ TẬP HỢP",
    "chương 2": "BẤT PHƯƠNG TRÌNH VÀ HỆ BẤT PHƯƠNG TRÌNH BẬC NHẤT HAI ẨN",
    "chương 3": "HÀM SỐ BẬC HAI VÀ ĐỒ THỊ",
    "chương 4": "HỆ THỨC LƯỢNG TRONG TAM GIÁC",
    "chương 5": "VECTƠ",
    "chương 6": "THỐNG KÊ",
}

LESSON = {
    "chương 1": ["Mệnh đề", "Tập hợp", "Các phép toán trên tập hợp"],
    "chương 2": ["Bất phương trình bậc nhất hai ẩn", "Hệ bất phương trình bậc nhất hai ẩn"],
    "chương 3": ["Hàm số và đồ thị", "Hàm số bậc hai"],
    "chương 4": [
        "Giá trị lượng giác của một góc từ 0° đến 180°",
        "Định lí cosin và định lí sin",
        "Giải tam giác và ứng dụng thực tế",
    ],
    "chương 5": [
        "Khái niệm vectơ",
        "Tổng và hiệu của hai vectơ",
        "Tích của một số với một vectơ",
        "Tích vô hướng của hai vectơ",
    ],
    "chương 6": [
        "Số gần đúng và sai số",
        "Mô tả và biểu diễn dữ liệu trên các bảng và biểu đồ",
        "Các số đặc trưng đo xu thế trung tâm của mẫu số liệu",
        "Các số đặc trưng đo mức độ phân tán của mẫu số liệu",
    ],
}

# ── Hàm extract số chương từ profile ─────────────────────────────────────────

def extract_chapter_keys(profile: dict) -> list[str]:
    """
    Lấy danh sách key chương từ profile.
    Ưu tiên pham_vi_kiem_tra, fallback ho_so_kien_thuc.
    Trả về: ["chương 1", "chương 2", ...]
    """
    raw = profile.get("pham_vi_kiem_tra") or profile.get("phạm_vi_kiểm_tra", "")

    # Fallback: lấy từ ho_so_kien_thuc
    if not raw:
        ho_so = profile.get("ho_so_kien_thuc") or profile.get("hồ_sơ_kiến_thức", [])
        raw = ", ".join([item.get("chu_de", "") for item in ho_so])

    # Extract số từ string: "Chương 1, 2, 3" → ["1", "2", "3"]
    numbers = re.findall(r'\d+', str(raw))
    return [f"chương {n}" for n in numbers if f"chương {n}" in CHAPTER]


# ── Hàm map ra chương và bài ─────────────────────────────────────────────────

def map_scope(profile: dict) -> dict:
    """
    Từ profile → map ra scope_chapters và scope_lessons.
    Trả về dict lưu vào state.
    """
    keys = extract_chapter_keys(profile)

    scope_chapters = {k: CHAPTER[k] for k in keys}
    scope_lessons  = {k: LESSON[k]  for k in keys}

    print("------------------- mapping curriculum --------------")
    print(f"scope_chapter : \n{scope_chapters} \n----------------------\nscope lesson : \n{scope_lessons}\n----------------------\n")

    return {
        "scope_chapters": scope_chapters,
        "scope_lessons":  scope_lessons,
    }


CHAPTER_MAP = {
    "mệnh đề và tập hợp": "chương 1",
    "bất phương trình và hệ bất phương trình bậc nhất hai ẩn": "chương 2",
    "hàm số bậc hai và đồ thị": "chương 3",
    "hệ thức lượng trong tam giác": "chương 4",
    "vecto": "chương 5",
    "thống kê": "chương 6",
}

ROMAN = {"I":1,"II":2,"III":3,"IV":4,"V":5,"VI":6}

def normalize_chapter_key(text: str) -> str:
    """Chuẩn hóa bất kỳ chuỗi chương nào về dạng 'chương N'."""
    text = text.strip().lower()

    # Tìm số La Mã: "chương III", "Chương IV - ..."
    m = re.search(r'ch[ươ]+ng\s+([ivxlc]+)', text, re.IGNORECASE)
    if m:
        roman = m.group(1).upper()
        if roman in ROMAN:
            return f"chương {ROMAN[roman]}"

    # Tìm số thường: "chương 3", "chương 3 - ..."
    m = re.search(r'ch[ươ]+ng\s+(\d+)', text)
    if m:
        return f"chương {m.group(1)}"

    # Match tên chương
    for name, key in CHAPTER_MAP.items():
        if name in text:
            return key

    return text  # fallback giữ nguyên