import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.state_edu import ExamState, StudentProfile
# from src.tools.tools_edu.tools_exam import parse_student_profile
from src.clients.a import DeepSeekClient
from src.configs import env_config
import json, re
 
from pathlib import Path
# Load prompt từ file

# Load prompt từ file
PROMPT_PATH = Path(r'D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompt_edu\prompt\collect_info.txt')
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")
 

 
FIELD_PATTERNS = {
    "mon_hoc": r"mon_hoc:\s*(.+)",
    "khoi_lop": r"khoi_lop:\s*(\d+)",
    "pham_vi_kiem_tra": r"pham_vi_kiem_tra:\s*(.+)",
    "muc_dich": r"muc_dich:\s*(.+)",
    "loai_de": r"loai_de:\s*(.+)",
    "so_cau_hoi": r"so_cau_hoi:\s*(\d+)",
    "thoi_gian_lam_bai": r"thoi_gian_lam_bai:\s*(\d+)",
    "muc_tieu_diem": r"muc_tieu_diem:\s*([\d.]+)",
    "ghi_chu": r"ghi_chu:\s*(.+)",
}
 


def _extract_profile(text: str, existing: dict) -> dict:
    profile = dict(existing)

    for field, pattern in FIELD_PATTERNS.items():
        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            continue

        value = match.group(1).strip()

        if field in (
            "khoi_lop",
            "so_cau_hoi",
            "thoi_gian_lam_bai",
        ):
            profile[field] = int(value)

        elif field == "muc_tieu_diem":
            profile[field] = float(value)

        else:
            profile[field] = value

    # -------------------------
    # Parse ho_so_kien_thuc
    # -------------------------

    hs_match = re.search(
        r"ho_so_kien_thuc\s*:(.*?)(?:ghi_chu\s*:|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if hs_match:
        hs_text = hs_match.group(1)

        knowledge = []

        for line in hs_text.splitlines():

            line = line.strip()

            if not line:
                continue

            line = re.sub(r"^[+\-*]\s*", "", line)

            # Chương 3: 8 điểm (Khá)
            m = re.match(
                r"(.+?)\s*:\s*([\d.]+)\s*điểm(?:\s*\((.+?)\))?$",
                line,
                re.IGNORECASE,
            )

            if m:
                item = {
                    "chu_de": m.group(1).strip(),
                    "diem": float(m.group(2)),
                }

                if m.group(3):
                    item["muc_do"] = m.group(3).strip()

                knowledge.append(item)
                continue

            # Chương 1: Khá
            m = re.match(
                r"(.+?)\s*:\s*(Cơ bản|Khá|Giỏi)$",
                line,
                re.IGNORECASE,
            )

            if m:
                knowledge.append(
                    {
                        "chu_de": m.group(1).strip(),
                        "muc_do": m.group(2).strip(),
                    }
                )

        if knowledge:
            profile["ho_so_kien_thuc"] = knowledge

    return profile
 
 
def _is_complete(profile: dict) -> bool:
    required = [
        "mon_hoc",
        "khoi_lop",
        "pham_vi_kiem_tra",
        "muc_dich",
        "loai_de",
        "so_cau_hoi",
        "thoi_gian_lam_bai",
        "muc_tieu_diem",
        "ho_so_kien_thuc",
        "ghi_chu",
    ]

    return all(
        k in profile and profile[k] is not None
        for k in required
    )
 
 
def collect_info(state: ExamState, llm_client: DeepSeekClient) -> dict:
    messages = state.get("messages", [])
    student_profile = state.get("student_profile", {})
    profile_complete = state.get("profile_complete", False)
 
    if profile_complete:
        return {}
 
    # Build history
    history = []
    for m in messages:
        if isinstance(m, HumanMessage):
            history.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            history.append({"role": "assistant", "content": m.content})
 
    # Sinh phản hồi chatbot
    # response = llm_client._llm.invoke([
    #     {"role": "system", "content": SYSTEM_PROMPT},
    #     *history,
    # ])
    response = llm_client._llm.invoke([
        {
            "role": "system",
            "content": SYSTEM_PROMPT + "\n\nHãy trả về đúng MẪU HỢP LỆ."
        },
        *history,
    ])
    ai_message = AIMessage(content=response.content)
 
    new_profile = student_profile
    complete = False
 
    try:
        new_profile = _extract_profile(ai_message.content, student_profile)
        complete = _is_complete(new_profile)
    except Exception:
        pass
 
    return {
        "messages": [ai_message],
        "student_profile": new_profile,
        "profile_complete": complete,
        "current_step": "collect_info",
    }