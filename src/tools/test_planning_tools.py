import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.clients.llm import LLMClient
from src.configs import env_config
from src.tools.planning_tools import (
    PlanContext,
    collect_info,
    check_required,
    ask_user,
)

llm_client = LLMClient(model=env_config.model, api_provider=env_config.api_provider)

# ── Test 1: Đủ thông tin bắt buộc ──────────────────────────────
history_1 = """
Người dùng: tôi muốn lập kế hoạch phòng bệnh đạo ôn 14 ngày cho ruộng ở Quảng Nam
"""

print("=" * 50)
print("TEST 1 — Đủ thông tin bắt buộc")
ctx1 = collect_info(history_1, llm_client)
print(ctx1.model_dump())
missing1 = check_required(ctx1)
print("Thiếu:", missing1)

# ── Test 2: Thiếu thông tin bắt buộc ───────────────────────────
history_2 = """
Người dùng: lúa nhà tôi bị khô vằn rồi, giờ phải làm sao
"""

print("=" * 50)
print("TEST 2 — Thiếu thông tin bắt buộc")
ctx2 = collect_info(history_2, llm_client)
print(ctx2.model_dump())
missing2 = check_required(ctx2)
print("Thiếu:", missing2)
question = ask_user(ctx2, llm_client)
print("Câu hỏi tiếp theo:\n", question)

# ── Test 3: Nhiều lượt hội thoại ────────────────────────────────
history_3 = """
Người dùng: lúa bị bạc lá, ruộng ở Cần Thơ
Bot: Bác muốn lập kế hoạch bao nhiêu ngày ạ?
Người dùng: 10 ngày thôi, lúa đang làm đòng, bị nặng lắm cả ruộng
"""

print("=" * 50)
print("TEST 3 — Nhiều lượt hội thoại")
ctx3 = collect_info(history_3, llm_client)
print(ctx3.model_dump())
missing3 = check_required(ctx3)
print("Thiếu:", missing3)