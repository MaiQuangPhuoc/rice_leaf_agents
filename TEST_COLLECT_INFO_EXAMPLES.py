"""
VÍ DỤ USAGE: collect_info() mới

Trước đây: quá phức tạp, dùng PLANNING.txt, không validate
Bây giờ: Simple, clean, validate, in ra xác nhận
"""

# ============ SCENARIO 1: ĐỦ THÔNG TIN ============
print("=" * 60)
print("SCENARIO 1: User cung cấp đủ thông tin")
print("=" * 60)

query_1 = """
Tôi cần phòng bệnh đạo ôn cho lúa. 
Thể loại lúa tuổi 25 ngày. 
Ở Hà Nội. 
Kéo dài 7 ngày.
"""

"""
Expected Output:
───────────────────────────────────────────────────────────────
📋 THÔNG TIN KỀ HOẠCH ĐÃ THU THẬP:
══════════════════════════════════════════════════════════════════
🔴 Bệnh: Đạo ôn
⏱ Thời gian: 7 ngày
📍 Vị trí: Hà Nội
🌾 Giai đoạn lúa: Tuổi 25 ngày
═══════════════════════════════════════════════════════════════════

✅ Đủ thông tin cần thiết. Bạn xác nhận ổn chưa? (Nếu ổn, tools sẽ tiếp tục)

Result: {
    "disease": "Đạo ôn",
    "duration_days": 7,
    "location": "Hà Nội",
    "rice_stage": "Tuổi 25 ngày",
    "status": "skeleton",
    ...
}
"""

# ============ SCENARIO 2: THIẾU THÔNG TIN ============
print("\n" + "=" * 60)
print("SCENARIO 2: User chưa cung cấp đủ thông tin")
print("=" * 60)

query_2 = """
Bệnh lúa mà mình chưa biết tên là gì.
Cần khoảng 5 ngày để xử lý.
"""

"""
Expected Output:
───────────────────────────────────────────────────────────────
📋 THÔNG TIN KỌ HOẠCH ĐÃ THU THẬP:
══════════════════════════════════════════════════════════════════
🔴 Bệnh: (chưa xác định)
⏱ Thời gian: 5 ngày
📍 Vị trí: (chưa xác định)
🌾 Giai đoạn lúa: (chưa xác định)
═══════════════════════════════════════════════════════════════════

⚠️ THIẾU THÔNG TIN:
  • disease (tên bệnh)
  • location (vị trí)
  • rice_stage (giai đoạn lúa)

Bạn vui lòng cung cấp đầy đủ thông tin trên để tiếp tục.

Result: {
    "disease": null,  ← THIẾU (bắt buộc)
    "duration_days": 5,
    "location": null,  ← THIẾU (nên có)
    "rice_stage": null,  ← THIẾU (nên có)
    ...
}
"""

# ============ SCENARIO 3: CHỈ THIẾU OPTIONAL ============
print("\n" + "=" * 60)
print("SCENARIO 3: Đủ bắt buộc, thiếu optional")
print("=" * 60)

query_3 = """
Cần phòng bệnh Bạc lá (Bacterial leaf scald).
Khoảng 10 ngày.
Ở Cần Thơ.
"""

"""
Expected Output:
───────────────────────────────────────────────────────────────
📋 THÔNG TIN KỌ HOẠCH ĐÃ THU THẬP:
══════════════════════════════════════════════════════════════════
🔴 Bệnh: Bạc lá
⏱ Thời gian: 10 ngày
📍 Vị trí: Cần Thơ
🌾 Giai đoạn lúa: (chưa xác định)
═══════════════════════════════════════════════════════════════════

✅ Đủ thông tin cần thiết. Bạn xác nhận ổn chưa? (Nếu ổn, tools sẽ tiếp tục)

Note: rice_stage chưa có, nhưng không block vì nó chỉ optional (suggestion).

Result: {
    "disease": "Bạc lá",
    "duration_days": 10,
    "location": "Cần Thơ",
    "rice_stage": null,  ← OK (optional)
    ...
}
"""

# ============ VALIDATE LOGIC ============
print("\n" + "=" * 60)
print("VALIDATE LOGIC")
print("=" * 60)

"""
def validate_plan_info(plan_info: PlanInfo) -> Tuple[bool, List[str]]:
    missing = []
    suggestions = []
    
    # BẮTBUỘC
    if not plan_info.disease:
        missing.append("disease (tên bệnh)")
    
    if plan_info.duration_days is None or plan_info.duration_days <= 0:
        missing.append("duration_days (số ngày kế hoạch)")
    
    # SUGGESTION (nên có)
    if not plan_info.location:
        suggestions.append("location (vị trí)")
    
    if not plan_info.rice_stage:
        suggestions.append("rice_stage (giai đoạn lúa)")
    
    is_complete = len(missing) == 0  ← chỉ check BẮTBUỘC
    all_missing = missing + suggestions  ← nhưng return cả hai
    
    return is_complete, all_missing  ← (True/False, [list thiếu])
"""

# ============ FLOW ============
print("\n" + "=" * 60)
print("FLOW HOÀN CHỈNH")
print("=" * 60)

"""
collect_info(query="...", llm_client=client)
    │
    ├─ [Bước 1] Extract thông tin dùng COLLECT_INFO_PROMPT (không PLANNING.txt)
    │   prompt = COLLECT_INFO_PROMPT.format(query=query)
    │   plan_info = llm_struct.invoke(prompt)  ← structured output PlanInfo
    │
    ├─ [Bước 2] Kiểm tra đủ ý chưa
    │   is_complete, missing_fields = validate_plan_info(plan_info)
    │   is_complete = True nếu có disease + duration_days
    │   missing_fields = list(bắtbuộc + suggestion)
    │
    ├─ [Bước 3] Format thông tin đẹp
    │   display = format_plan_info_for_display(plan_info)
    │   📋 THÔNG TIN... 🔴 Bệnh... ⏱ Thời gian... etc.
    │
    └─ [Bước 4] Quyết định response
        if is_complete:
            response = display + "✅ Đủ thông tin..."
        else:
            response = display + "⚠️ THIẾU THÔNG TIN..."
        
        return response, plan_info.model_dump()
"""

print("\n✅ XONG refactor planning_tools.py!")
print("   • Dùng prompt riêng thay vì PLANNING.txt")
print("   • Validate đủ ý (bắtbuộc vs suggestion)")
print("   • In ra đẹp + xác nhận")
print("   • Nếu ok → ready cho create_skeleton_tool")
