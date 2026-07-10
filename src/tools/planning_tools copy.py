import sys
import os
from datetime import datetime
from typing import List, Optional, Literal, Tuple

from pydantic import BaseModel, Field
from langchain_core.tools import tool

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.state import Plan, PlanStep
import json
from src.memory.plan_store import PlanStore
from langchain.schema import HumanMessage


# ====== PROMPT RIÊNG ĐỂ EXTRACT THÔNG TIN (thay vì PLANNING.txt) ======
COLLECT_INFO_PROMPT = """Bạn là người hỗ trợ lập kế hoạch phòng bệnh lúa cho nông dân.

Dựa vào yêu cầu sau, hãy trích xuất các thông tin quan trọng theo schema:
- disease: tên bệnh cần phòng trị (bắt buộc)
- duration_days: số ngày dự kiến thực hiện kế hoạch (bắt buộc)
- location: vị trị (tỉnh, huyện) nếu có (tùy chọn nhưng nên có)
- rice_stage: giai đoạn lúa hiện tại (tùy chọn nhưng nên có)

YÊU CẦU: {query}

Trích xuất và trả về JSON theo schema PlanInfo:
{{
  "disease": "...",
  "duration_days": X,
  "location": "... hoặc null",
  "rice_stage": "... hoặc null"
}}

Chỉ trả về JSON, không giải thích thêm.""" 



class PlanInfo(BaseModel):
    plan_id: Optional[str] = Field(None, description="UUID định danh kế hoạch")
    user_id: Optional[str] = Field(None, description="ID người dùng tạo kế hoạch")
    thread_id: Optional[str] = Field(None, description="ID luồng hội thoại")
    disease: str = Field(..., description="Bệnh cần phòng trị hoặc mục tiêu kế hoạch")
    duration_days: int = Field(..., description="Thời gian kế hoạch tính bằng ngày")
    location: Optional[str] = Field(None, description="Vị trí áp dụng kế hoạch")
    rice_stage: Optional[str] = Field(None, description="Giai đoạn lúa đang xử lý")
    status: Literal["skeleton", "detail", "review", "done"] = Field(
        "skeleton", description="Trạng thái hiện tại của kế hoạch"
    )
    skeleton: List[str] = Field(
        default_factory=list,
        description="Sườn kế hoạch tổng quát, ví dụ ['Tuần 1: ...', 'Tuần 2: ...']",
    )
    steps: List[PlanStep] = Field(
        default_factory=list,
        description="Chi tiết từng bước của kế hoạch theo schema PlanStep",
    )
    created_at: Optional[str] = Field(None, description="Thời gian tạo kế hoạch")
    updated_at: Optional[str] = Field(None, description="Thời gian cập nhật gần nhất của kế hoạch")

    class Config:
        arbitrary_types_allowed = True

from pydantic import BaseModel, Field
from typing import Optional


COLLECT_INFO_PROMPT = """
# VAI TRÒ
Bạn là trợ lý thu thập thông tin để lập kế hoạch chăm sóc và phục hồi lúa.
Giọng nói: thân thiện, gần gũi như người trong làng, kiên nhẫn, không vội vàng.

# NHIỆM VỤ
Đọc toàn bộ hội thoại bên dưới và trích xuất thông tin vào đúng các trường schema.
- Chỉ điền những gì user ĐÃ NÓI RÕ RÀNG trong hội thoại.
- Không suy luận, không bịa đặt, không đoán mò.
- Thông tin chưa có → để null.

# CÁC TRƯỜNG CẦN THU THẬP

## BẮT BUỘC (phải có mới tạo được kế hoạch):
- disease        : Mục tiêu kế hoạch — bệnh gì HOẶC việc gì cần làm
                   Ví dụ: "đạo ôn", "khô vằn", "bạc lá", "cải tạo đất",
                           "bổ sung dinh dưỡng", "phục hồi sau ngập úng"
- location       : Địa điểm ruộng lúa (tỉnh/huyện)
- duration_days  : Số ngày muốn lên kế hoạch (số nguyên)

## KHUYẾN KHÍCH (càng đầy đủ kế hoạch càng sát thực tế):
- disease_scale     : Phạm vi bị ảnh hưởng
                      Ví dụ: "vài khóm", "vài luống", "nửa ruộng", "cả ruộng"
- disease_duration  : Tình trạng xuất hiện bao lâu rồi
                      Ví dụ: "mới phát hiện hôm nay", "3 ngày", "1 tuần"
- disease_severity  : Mức độ hoặc mô tả cụ thể
                      Ví dụ: "nhẹ", "nặng", "lá vàng từ chóp xuống", "bẹ lá thối đen"
- rice_stage        : Giai đoạn lúa hiện tại
                      Ví dụ: "mạ", "đẻ nhánh", "đứng cái", "làm đòng",
                              "trổ bông", "ngậm sữa", "chín"
- rice_variety      : Giống lúa đang trồng
                      Ví dụ: "OM5451", "IR50404", "Đài Thơm 8", "ST25"
- current_medicine  : Đang dùng thuốc/biện pháp gì (nếu có)
                      Ví dụ: "Tricyclazole", "đã bón vôi", "chưa dùng gì"
- weather_description: Mô tả thời tiết theo cảm nhận của user
                      Ví dụ: "mưa nhiều", "nắng nóng", "sáng có sương mù"

# LỊCH SỬ HỘI THOẠI
{history}

# YÊU CẦU OUTPUT
Trả về JSON hợp lệ theo đúng schema PlanContext.
Chỉ trả về JSON, không giải thích thêm.
"""

COLLECT_INFO_QUESTION_PROMPT = """
# VAI TRÒ
Bạn là trợ lý lập kế hoạch chăm sóc lúa — thân thiện, gần gũi, kiên nhẫn.

# NHIỆM VỤ
Dựa vào thông tin đã có và thông tin còn thiếu bên dưới,
hỏi người dùng để thu thập thêm thông tin.

# QUY TẮC HỎI
- Mỗi lượt chỉ hỏi TỐI ĐA 2 câu — không hỏi dồn.
- Hỏi phần BẮT BUỘC còn thiếu trước.
- Sau khi đủ bắt buộc, khuyến khích hỏi thêm phần còn lại (nhẹ nhàng, không ép).
- Dùng ngôn ngữ đơn giản, tránh thuật ngữ kỹ thuật.
- Xưng "tôi", gọi user là "bác" hoặc "anh/chị".

# THÔNG TIN ĐÃ CÓ
{collected}

# THÔNG TIN BẮT BUỘC CÒN THIẾU
{missing_required}

# THÔNG TIN KHUYẾN KHÍCH CÒN THIẾU
{missing_optional}

Hãy viết câu hỏi tiếp theo cho người dùng.
"""

class PlanContext(BaseModel):
    """
    Thông tin thô thu thập từ user trước khi tạo kế hoạch.
    Dùng để điền dần qua nhiều lượt hội thoại.
    """

    # ── BẮT BUỘC ──────────────────────────────────────────────
    disease: Optional[str] = Field(
        None,
        description=(
            "Mục tiêu chính của kế hoạch. "
            "Có thể là tên bệnh ('đạo ôn', 'khô vằn', 'bạc lá'), "
            "hoặc mục tiêu khác ('cải tạo đất', 'bổ sung dinh dưỡng', 'phục hồi sau ngập')."
        )
    )

    location: Optional[str] = Field(
        None,
        description="Địa điểm ruộng lúa, ví dụ: 'Quảng Nam', 'Cần Thơ', 'An Giang'."
    )

    duration_days: Optional[int] = Field(
        None,
        description="Số ngày muốn lên kế hoạch, ví dụ: 7, 14, 21."
    )

    # ── TÌNH TRẠNG BỆNH / VẤN ĐỀ ─────────────────────────────
    disease_scale: Optional[str] = Field(
        None,
        description=(
            "Phạm vi không gian bị ảnh hưởng: "
            "'nhỏ (vài khóm)', 'trung bình (vài luống)', 'lớn (cả ruộng)'."
        )
    )

    disease_duration: Optional[str] = Field(
        None,
        description="Bị bao lâu rồi, ví dụ: 'mới phát hiện hôm nay', '3 ngày', '1 tuần'."
    )

    disease_severity: Optional[str] = Field(
        None,
        description=(
            "Mức độ nặng nhẹ hoặc mô tả cụ thể tình trạng hiện tại: "
            "'nhẹ', 'trung bình', 'nặng', "
            "hoặc mô tả: 'lá vàng từ chóp xuống', 'bẹ lá thối'."
        )
    )

    # ── LÚA ───────────────────────────────────────────────────
    rice_stage: Optional[str] = Field(
        None,
        description=(
            "Giai đoạn sinh trưởng hiện tại của lúa: "
            "'mạ', 'đẻ nhánh', 'đứng cái', 'làm đòng', 'trổ bông', 'ngậm sữa', 'chín'."
        )
    )

    rice_variety: Optional[str] = Field(
        None,
        description="Giống lúa đang trồng, ví dụ: 'OM5451', 'IR50404', 'Đài Thơm 8', 'ST25'."
    )

    # ── THUỐC ĐANG DÙNG ───────────────────────────────────────
    current_medicine: Optional[str] = Field(
        None,
        description=(
            "Thuốc hoặc biện pháp user đang áp dụng (nếu có), "
            "ví dụ: 'Tricyclazole', 'Validamycin', 'chưa dùng gì', 'đã bón vôi'."
        )
    )

    # ── THỜI TIẾT (chủ quan từ user) ──────────────────────────
    weather_description: Optional[str] = Field(
        None,
        description=(
            "Mô tả thời tiết theo cảm nhận của user, "
            "ví dụ: 'mưa nhiều', 'nắng nóng', 'sáng có sương mù', 'hanh khô'. "
            "Không phải dữ liệu từ API thời tiết."
        )
    )

def check_required(ctx: PlanContext) -> list[str]:
    missing = []
    if not ctx.disease:       missing.append("disease")
    if not ctx.location:      missing.append("location")
    if not ctx.duration_days: missing.append("duration_days")
    return missing  # [] = đủ rồi, có phần tử = còn thiếu



# ====== HÀM KIỂM TRA ĐỦ THÔNG TIN ======
def validate_plan_info(plan_info: PlanInfo) -> Tuple[bool, List[str]]:
    """
    Kiểm tra xem PlanInfo có đủ thông tin chưa.
    
    Trả về: (is_complete, missing_fields)
    - is_complete: True nếu đủ thông tin cần thiết
    - missing_fields: list các trường thiếu hoặc cần cố gắng bổ sung
    """
    missing = []
    
    # Bắt buộc
    if not plan_info.disease or plan_info.disease.strip() == "":
        missing.append("disease (tên bệnh)")
    
    if plan_info.duration_days is None or plan_info.duration_days <= 0:
        missing.append("duration_days (số ngày kế hoạch)")
    
    # Nên có nhưng không bắt buộc
    suggestions = []
    if not plan_info.location or plan_info.location.strip() == "":
        suggestions.append("location (vị trí)")
    
    if not plan_info.rice_stage or plan_info.rice_stage.strip() == "":
        suggestions.append("rice_stage (giai đoạn lúa)")
    
    is_complete = len(missing) == 0
    all_missing = missing + suggestions
    
    return is_complete, all_missing


def format_plan_info_for_display(plan_info: PlanInfo) -> str:
    """In ra thông tin kế hoạch theo định dạng đẹp cho người dùng xem."""
    lines = [
        "📋 THÔNG TIN KỀ HOẠCH ĐÃ THU THẬP:",
        "═" * 50,
    ]
    
    # Bắt buộc
    lines.append(f"🔴 Bệnh: {plan_info.disease}")
    lines.append(f"⏱ Thời gian: {plan_info.duration_days} ngày")
    
    # Tùy chọn
    if plan_info.location:
        lines.append(f"📍 Vị trí: {plan_info.location}")
    else:
        lines.append(f"📍 Vị trí: (chưa xác định)")
    
    if plan_info.rice_stage:
        lines.append(f"🌾 Giai đoạn lúa: {plan_info.rice_stage}")
    else:
        lines.append(f"🌾 Giai đoạn lúa: (chưa xác định)")
    
    lines.append("═" * 50)
    
    return "\n".join(lines)





def build_plan_from_info(
    plan_info: PlanInfo,
    default_user_id: str = "unknown",
    default_thread_id: str = "default",
) -> Plan:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return Plan(
        plan_id=plan_info.plan_id or f"plan-{int(datetime.now().timestamp())}",
        user_id=plan_info.user_id or default_user_id,
        thread_id=plan_info.thread_id or default_thread_id,
        disease=plan_info.disease,
        duration_days=plan_info.duration_days,
        location=plan_info.location,
        rice_stage=plan_info.rice_stage,
        status=plan_info.status,
        skeleton=plan_info.skeleton,
        steps=plan_info.steps,
        created_at=plan_info.created_at or now,
        updated_at=plan_info.updated_at or now,
    )


@tool(response_format="content_and_artifact")
def collect_info(query: str, llm_client=None):
    """
    Thu thập thông tin kế hoạch từ yêu cầu người dùng.
    
    Quy trình:
    1. Dùng prompt riêng (không PLANNING.txt) để extract thông tin
    2. Kiểm tra đủ ý chưa (validate_plan_info)
    3. In ra thông tin để người dùng xem
    4. Nếu đủ → xong tools, nếu chưa → hỏi lại những gì thiếu
    """
    if llm_client is None or not hasattr(llm_client, "_llm"):
        return "Thiếu LLM client để trích xuất thông tin kế hoạch.", None

    # Bước 1: Dùng prompt riêng với structured output
    prompt = COLLECT_INFO_PROMPT.format(query=query)
    
    try:
        llm_struct = llm_client._llm.with_structured_output(PlanInfo)
        result = llm_struct.invoke(prompt)
        
        if result is None:
            return "Không thể trích xuất thông tin kế hoạch từ yêu cầu.", None
        
        plan_info = result if isinstance(result, PlanInfo) else PlanInfo(**result)
    except Exception as e:
        return f"Lỗi khi trích xuất thông tin: {e}", None

    # Bước 2: Kiểm tra đủ ý chưa
    is_complete, missing_fields = validate_plan_info(plan_info)

    # Bước 3: In ra thông tin để người dùng xem
    display = format_plan_info_for_display(plan_info)
    
    if is_complete:
        # Đủ thông tin → xong collect_info, sẵn sàng cho bước tiếp theo
        response = display + "\n\n✅ Đủ thông tin cần thiết. Bạn xác nhận ổn chưa? (Nếu ổn, tools sẽ tiếp tục)"
    else:
        # Chưa đủ → in ra cái thiếu và hỏi lại
        missing_str = "\n".join([f"  • {field}" for field in missing_fields])
        response = (
            display + 
            "\n\n⚠️ THIẾU THÔNG TIN:\n" + missing_str + 
            "\n\nBạn vui lòng cung cấp đầy đủ thông tin trên để tiếp tục."
        )

    print(f"\n{response}\n")
    
    return response, plan_info.model_dump()


def plan_info_to_plan(plan_info: PlanInfo, user_id: str, thread_id: str) -> Plan:
    """Chuyển thông tin kế hoạch đã trích xuất sang đối tượng Plan đầy đủ."""
    plan_info.user_id = plan_info.user_id or user_id
    plan_info.thread_id = plan_info.thread_id or thread_id
    return build_plan_from_info(plan_info)


def load_plan_templates(template_path: str = None) -> dict:
    """Đọc mẫu kế hoạch, trả về dict theo template_level."""
    template_path = template_path or r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\plan_templates.txt"
    if not os.path.exists(template_path):
        return {}

    with open(template_path, "r", encoding="utf-8") as f:
        raw = f.read()

    parts = [part.strip() for part in raw.split("-------------------------") if part.strip()]
    templates = {}

    for part in parts:
        start = part.find("{")
        end = part.rfind("}")
        if start == -1 or end == -1:
            continue
        try:
            t = json.loads(part[start:end + 1])
            level = t.get("template_level")
            if level:
                templates[level] = t
        except Exception:
            continue

    return templates





def synthesize_skeleton_from_retrieval(
    plan_info: PlanInfo,
    retriever=None,
    llm_client=None,
) -> List[str]:
    """Tạo sườn kế hoạch từ nội dung truy vấn nếu không tìm được mẫu phù hợp."""
    prompt = (
        f"Tạo sườn kế hoạch phòng bệnh cho {plan_info.disease} trong "
        f"{plan_info.duration_days} ngày. "
        f"Giai đoạn nên phù hợp với vị trí {plan_info.location or 'chưa xác định'} "
        f"và giai đoạn lúa {plan_info.rice_stage or 'chưa xác định'}."
    )

    retrieved = None
    if retriever is not None:
        try:
            retrieved = retriever(prompt)
        except Exception:
            retrieved = None

    if llm_client is not None and retrieved:
        try:
            llm = llm_client._llm
            llm_output = llm.invoke(
                prompt + "\n\nThông tin tham chiếu:\n" + str(retrieved)
            )
            # text = llm_output if isinstance(llm_output, str) else str(llm_output)
            # dòng 166 - sửa
            text = llm_output.content if hasattr(llm_output, "content") else str(llm_output)
            
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            skeleton = [line for line in lines if line.lower().startswith("giai đoạn")]
            if skeleton:
                return skeleton
        except Exception:
            pass

    phases = min(4, max(2, plan_info.duration_days // 4))
    skeleton = [f"Giai đoạn {i}: Thiết lập và thực hiện bước {i}" for i in range(1, phases + 1)]
    return skeleton


@tool(response_format="content_and_artifact")
def create_skeleton_tool(query: str, llm_client=None, retriever=None, template_path: str = None, template_level: str = "simple"):
    """Tạo sườn kế hoạch từ mẫu. template_level: simple / medium / complex."""
    plan_info = None
    try:
        payload = json.loads(query)
        plan_info = PlanInfo(**payload)
    except Exception:
        if llm_client is not None and hasattr(llm_client, "_llm"):
            llm_struct = llm_client._llm.with_structured_output(PlanInfo)
            result = llm_struct.invoke(query)
            if result is not None:
                plan_info = result if isinstance(result, PlanInfo) else PlanInfo(**result)

    if plan_info is None:
        return "Không thể xác định thông tin kế hoạch từ input.", None

    templates = load_plan_templates(template_path)
    matched = templates.get(template_level) or templates.get("simple")

    if matched:
        skeleton = matched.get("skeleton", [])
        plan_info.skeleton = skeleton
        plan_info.status = "skeleton"
        return (
            f"Đã tạo sườn kế hoạch theo mẫu '{template_level}'.",
            {"plan_info": plan_info.model_dump(), "template_used": matched.get("plan_id")},
        )

    skeleton = synthesize_skeleton_from_retrieval(plan_info, retriever=retriever, llm_client=llm_client)
    plan_info.skeleton = skeleton
    plan_info.status = "skeleton"
    return (
        "Không tìm thấy mẫu, đã tạo sườn từ truy vấn.",
        {"plan_info": plan_info.model_dump(), "template_used": None},
    )


@tool(response_format="content_and_artifact")
def fill_detail_tool(query: str, llm_client=None, retriever=None):
    """Điền chi tiết từng bước vào sườn kế hoạch đã có, chia theo từng giai đoạn."""
    try:
        payload = json.loads(query)
        plan_info = PlanInfo(**payload)
    except Exception:
        return "Input phải là JSON chứa PlanInfo (có skeleton).", None

    if not plan_info.skeleton:
        return "Chưa có sườn kế hoạch. Hãy chạy create_skeleton_tool trước.", None

    if llm_client is None or not hasattr(llm_client, "_llm"):
        return "Thiếu LLM client.", None

    # Lấy context từ retriever
    context = ""
    if retriever is not None:
        try:
            docs = retriever(f"phòng trị {plan_info.disease} {plan_info.rice_stage or ''}")
            context = "\n".join([d.page_content for d in docs]) if docs else ""
        except Exception:
            context = ""

    # Chia ngày theo số giai đoạn trong skeleton
    n_phases = len(plan_info.skeleton)
    days_per_phase = plan_info.duration_days // n_phases
    remainder = plan_info.duration_days % n_phases

    all_steps = []
    current_day = 1

    for i, phase in enumerate(plan_info.skeleton):
        # Giai đoạn cuối nhận phần dư ngày
        phase_days = days_per_phase + (remainder if i == n_phases - 1 else 0)
        start_day = current_day
        end_day = current_day + phase_days - 1

        prompt = f"""Bạn là chuyên gia bệnh lúa. Điền chi tiết kế hoạch cho giai đoạn sau.

Thông tin kế hoạch:
- Bệnh: {plan_info.disease}
- Vị trí: {plan_info.location or 'chưa xác định'}
- Giai đoạn lúa: {plan_info.rice_stage or 'chưa xác định'}

Giai đoạn hiện tại: {phase}
Điền chi tiết từ ngày {start_day} đến ngày {end_day}.

Tài liệu tham chiếu:
{context or 'Không có'}

Trả về JSON list, mỗi bước theo schema:
{{"day": int, "action": str, "medicine": str, "dosage": str, "condition": str, "note": str}}

Đơn vị liều lượng: muỗng canh, nắp chai, bình 16 lít — không dùng ml hay g/L.
Chỉ trả về JSON list, không giải thích thêm."""

        try:
            result = llm_client._llm.invoke([HumanMessage(content=prompt)])
            text = result.content if hasattr(result, "content") else str(result)
            text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            steps = json.loads(text)
            all_steps.extend([PlanStep(**s) for s in steps])
        except Exception as e:
            return f"Lỗi khi điền giai đoạn {i+1}: {e}", None

        current_day = end_day + 1

    plan_info.steps = all_steps
    plan_info.status = "detail"
    return "Đã điền chi tiết kế hoạch theo từng giai đoạn.", plan_info.model_dump()


@tool(response_format="content_and_artifact")
def edit_plan_tool(query: str, llm_client=None):
    """Chỉnh sửa plan theo yêu cầu user. query là JSON: {plan_info: ..., request: str}"""
    try:
        payload = json.loads(query)
        plan_info = PlanInfo(**payload["plan_info"])
        request = payload["request"]
    except Exception:
        return "Input phải là JSON: {plan_info: ..., request: str}.", None

    if llm_client is None or not hasattr(llm_client, "_llm"):
        return "Thiếu LLM client.", None

    prompt = f"""Chỉnh sửa kế hoạch sau theo yêu cầu của người dùng.

Kế hoạch hiện tại:
{json.dumps(plan_info.model_dump(), ensure_ascii=False, indent=2)}

Yêu cầu chỉnh sửa: {request}

Trả về JSON đầy đủ của plan sau khi chỉnh sửa (cùng schema PlanInfo).
Chỉ trả về JSON, không giải thích."""

    try:
        from langchain_core.messages import HumanMessage
        result = llm_client._llm.invoke([HumanMessage(content=prompt)])
        text = result.content if hasattr(result, "content") else str(result)
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        updated = json.loads(text)
        updated_plan = PlanInfo(**updated)
        updated_plan.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return "Đã chỉnh sửa kế hoạch.", updated_plan.model_dump()
    except Exception as e:
        return f"Lỗi khi chỉnh sửa: {e}", None


@tool(response_format="content_and_artifact")
def save_plan_tool(query: str, db_path: str = None):
    """Lưu plan vào SQLite. query là JSON của PlanInfo đã hoàn chỉnh."""
    if db_path is None:
        return "Thiếu db_path.", None

    try:
        payload = json.loads(query)
        plan_info = PlanInfo(**payload)
    except Exception:
        return "Input phải là JSON PlanInfo.", None

    plan = build_plan_from_info(plan_info)
    store = PlanStore(db_path=db_path)

    existing = store.read(plan.plan_id)
    if existing:
        store.update(plan.plan_id, plan.model_dump())
        return f"Đã cập nhật plan '{plan.plan_id}'.", plan.model_dump()
    else:
        store.create(plan.model_dump())
        return f"Đã lưu plan mới '{plan.plan_id}'.", plan.model_dump()

def make_planning_tools(llm_client, retriever, db_path: str):
    """Factory: tạo planning tools với dependencies đã inject."""
    
    def _create_skeleton(query: str, template_level: str = "simple") -> tuple:
        """Tạo sườn kế hoạch từ mẫu theo mức độ simple/medium/complex."""
        return create_skeleton_tool.func(
            query=query,
            llm_client=llm_client,
            retriever=retriever,
            template_level=template_level,
        )

    def _fill_detail(query: str) -> tuple:
        """Wrapper for fill_detail_tool with injected llm_client and retriever."""
        return fill_detail_tool.func(
            query=query,
            llm_client=llm_client,
            retriever=retriever,
        )

    def _collect_info(query: str) -> tuple:
        """Wrapper for collect_info with injected llm_client."""
        return collect_info.func(
            query=query,
            llm_client=llm_client,
        )

    def _edit_plan(query: str) -> tuple:
        """Wrapper for edit_plan_tool with injected llm_client."""
        return edit_plan_tool.func(
            query=query,
            llm_client=llm_client,
        )

    def _save_plan(query: str) -> tuple:
        """Wrapper for save_plan_tool with injected db_path."""
        return save_plan_tool.func(
            query=query,
            db_path=db_path,
        )

    from langchain_core.tools import tool as _tool

    create_skeleton = _tool(response_format="content_and_artifact")(_create_skeleton)
    create_skeleton.name = "create_skeleton_tool"
    create_skeleton.description = create_skeleton_tool.description

    fill_detail = _tool(response_format="content_and_artifact")(_fill_detail)
    fill_detail.name = "fill_detail_tool"
    fill_detail.description = fill_detail_tool.description

    edit_plan = _tool(response_format="content_and_artifact")(_edit_plan)
    edit_plan.name = "edit_plan_tool"
    edit_plan.description = edit_plan_tool.description

    save_plan = _tool(response_format="content_and_artifact")(_save_plan)
    save_plan.name = "save_plan_tool"
    save_plan.description = save_plan_tool.description

    collect = _tool(response_format="content_and_artifact")(_collect_info)
    collect.name = "collect_info"
    collect.description = collect_info.description

    return [collect, create_skeleton, fill_detail, edit_plan, save_plan]