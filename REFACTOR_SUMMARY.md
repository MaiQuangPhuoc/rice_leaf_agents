# 🔧 TÓM TẮT REFACTOR planning_tools.py

## ❌ VẤN ĐỀ CŨ
- `collect_info()` dùng PLANNING.txt → **rất nhiễu**
- Không kiểm tra đủ ý chưa
- Không in ra thông tin để người dùng xác nhận

## ✅ GÌ ĐÃ ĐƯỢC SỬA

### 1. **Prompt Riêng (Thay vì PLANNING.txt)**
```python
COLLECT_INFO_PROMPT = """Bạn là người hỗ trợ lập kế hoạch phòng bệnh lúa...
- disease: tên bệnh (bắt buộc)
- duration_days: số ngày (bắt buộc)
- location: vị trí (tùy chọn)
- rice_stage: giai đoạn lúa (tùy chọn)
"""
```
✨ **Lợi ích**: Clear, structured, không nhiễu từ PLANNING.txt

---

### 2. **Hàm Kiểm Tra Đủ Ý: `validate_plan_info()`**
```python
def validate_plan_info(plan_info: PlanInfo) -> Tuple[bool, List[str]]:
    """
    Kiểm tra PlanInfo có đủ thông tin chưa.
    Trả về: (is_complete, missing_fields)
    """
```

**Logic:**
- ✅ **Bắt buộc**: `disease` + `duration_days`
- 💡 **Nên có**: `location` + `rice_stage` (nhưng null được, chỉ suggestion)
- Trả về: `True` nếu đủ bắt buộc, danh sách cái thiếu

---

### 3. **Hàm Format Đẹp: `format_plan_info_for_display()`**
```python
def format_plan_info_for_display(plan_info: PlanInfo) -> str:
    """In ra thông tin kế hoạch với emoji và định dạng dễ đọc."""
```

**Output ví dụ:**
```
📋 THÔNG TIN KỀ HOẠCH ĐÃ THU THẬP:
══════════════════════════════════════════════════
🔴 Bệnh: Đạo ôn
⏱ Thời gian: 7 ngày
📍 Vị trí: Hà Nội
🌾 Giai đoạn lúa: Tuổi 25 ngày
══════════════════════════════════════════════════
```

---

### 4. **Quy Trình `collect_info()` Mới**

**Trước:**
```
user_query → extract → return info (chưa validate, không hỏi xác nhận)
```

**Sau:**
```
user_query 
  ↓
dùng COLLECT_INFO_PROMPT extract (không PLANNING.txt)
  ↓
validate_plan_info() kiểm tra đủ ý
  ↓
format_plan_info_for_display() in ra đẹp
  ↓
├─ Nếu ✅ đủ → "✅ Đủ thông tin, bạn xác nhận ổn chưa?"
└─ Nếu ❌ chưa → "⚠️ THIẾU: • location\n • rice_stage\nVui lòng cung cấp..."
  ↓
return (response, plan_info.model_dump())
```

---

## 📊 SO SÁNH

| Tiêu chí | Cũ | Mới |
|---|---|---|
| **Source** | PLANNING.txt (nhiễu) | COLLECT_INFO_PROMPT (clean) |
| **Validate** | ❌ | ✅ có `validate_plan_info()` |
| **Feedback** | ❌ | ✅ in ra + hỏi xác nhận |
| **Optional fields** | ❌ clear | ✅ distinguish required vs optional |
| **UX** | Mặc định accept | Người dùng phải confirm |

---

## 🎯 CÁC TRƯỜNG THÔNG TIN

### Bắt Buộc (must-have)
- ✅ `disease` - tên bệnh
- ✅ `duration_days` - số ngày kế hoạch

### Tùy Chọn (should-have, nhưng nên có)
- 💡 `location` - vị trí (tỉnh/huyện)
- 💡 `rice_stage` - giai đoạn lúa

✨ **Logic**: Nếu thiếu tùy chọn → chỉ warning, không block. Nếu thiếu bắt buộc → block, hỏi lại.

---

## 🚀 CẠP NHẬT

**File thay đổi:**
- `src/tools/planning_tools.py`

**Hàm mới:**
- `validate_plan_info()` - check đủ ý
- `format_plan_info_for_display()` - format output

**Hàm sửa:**
- `collect_info()` - dùng prompt riêng, validate, in ra

**Constant mới:**
- `COLLECT_INFO_PROMPT` - prompt riêng để extract

---

## ✨ RESULT

✅ **Collect Phase:**
1. Dùng prompt riêng (không PLANNING.txt)
2. Auto validate đủ ý chưa
3. In ra để người dùng xem
4. Nếu ok → xong tools, tiếp tục bước tiếp theo
5. Nếu chưa → guide user cần cung cấp gì

🎯 **Final UX:**
```
User: "Phòng đạo ôn cho lúa tuổi 25 ngày ở Hà Nội trong 7 ngày"
      ↓
Tool: Hiển thị thông tin + xác nhận
      ↓
User: "OK" hoặc cung cấp thêm thông tin thiếu
      ↓
Tiếp tục create_skeleton_tool
```
