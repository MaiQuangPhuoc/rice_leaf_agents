import json, re
import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from pathlib import Path
from langchain_core.messages import AIMessage, HumanMessage
from src.state_edu import ExamState
# from src.clients.llm2 import LLMClient
from src.clients.a import DeepSeekClient

from src.edu_exam.curriculum import normalize_chapter_key

PROMPT_PATH = Path(r'D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompt_edu\prompt\build_matrix.txt')

# Tỉ lệ độ khó theo mục tiêu điểm
DIFFICULTY_RATIO = {
    5:  {"de": 0.70, "trung_binh": 0.25, "kho": 0.05},
    6:  {"de": 0.50, "trung_binh": 0.35, "kho": 0.15},
    7:  {"de": 0.50, "trung_binh": 0.35, "kho": 0.15},
    8:  {"de": 0.35, "trung_binh": 0.40, "kho": 0.25},
    9:  {"de": 0.20, "trung_binh": 0.30, "kho": 0.50},
    10: {"de": 0.20, "trung_binh": 0.30, "kho": 0.50},
}


# ── Tính phân bổ số câu per chương bằng code ──────────────────────────────────

def _calc_chapter_distribution(knowledge_scores: dict, so_cau: int, muc_tieu_diem: int) -> dict:
    """
    Tính số câu + de/trung_binh/kho per chương dựa vào trọng số knowledge_scores.
    Trả về: {ch_key: {so_cau, de, trung_binh, kho}}
    """
    # Tổng score per chương
    ch_scores = {}
    for ch_key, lessons in knowledge_scores.items():
        total = sum(
            score
            for sections in lessons.values()
            for score in sections.values()
        )
        ch_scores[ch_key] = total

    tong_score = sum(ch_scores.values()) or 1  # tránh chia 0

    # Tỉ lệ độ khó
    diem = min(max(muc_tieu_diem, 5), 10)
    ratio = DIFFICULTY_RATIO.get(diem, DIFFICULTY_RATIO[7])

    # Phân bổ số câu per chương theo tỉ lệ trọng số
    result     = {}
    assigned   = 0
    ch_keys    = list(ch_scores.keys())

    for i, ch_key in enumerate(ch_keys):
        if i == len(ch_keys) - 1:
            # Chương cuối: lấy phần còn lại để đảm bảo tổng đúng
            n = so_cau - assigned
        else:
            n = round(so_cau * ch_scores[ch_key] / tong_score)

        de  = round(n * ratio["de"])
        tb  = round(n * ratio["trung_binh"])
        kho = n - de - tb  # phần còn lại tránh lệch do làm tròn

        result[ch_key] = {"so_cau": n, "de": de, "trung_binh": tb, "kho": kho}
        assigned += n

    return result


# ── Format input per chương ────────────────────────────────────────────────────

def _format_scores_ch(scores_ch: dict) -> str:
    lines = []
    for lesson, sections in scores_ch.items():
        lines.append(f"{lesson}:")
        for sec, score in sections.items():
            label = ["Không quan tâm", "Ít", "Bình thường", "Cao"][score]
            lines.append(f"  - {sec}: {score} ({label})")
    return "\n".join(lines)


# ── Parse ──────────────────────────────────────────────────────────────────────

def _parse_matrix_ch(text: str) -> dict:
    text = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text.strip())
    text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)
    start = text.find('{')
    if start == -1:
        raise ValueError("Không tìm thấy JSON")
    decoder = json.JSONDecoder()
    obj, _  = decoder.raw_decode(text[start:])
    return obj


def _validate_ch(ch_data: dict, so_cau: int) -> bool:
    total = sum(b.get("so_cau", 0) for b in ch_data.get("bai_hoc", []))
    return total == so_cau


# ── Node chính ─────────────────────────────────────────────────────────────────

def build_matrix(state: ExamState, llm_client: DeepSeekClient) -> dict:
    print(">>> [Node] build_matrix" * 3)

    if state.get("matrix_done", False):
        print("matrix done")
        return {"current_step": "build_matrix"}

    messages          = state.get("messages", [])
    profile           = state.get("student_profile", {})
    knowledge_scores  = state.get("knowledge_scores", {})
    knowledge_profile = state.get("knowledge_profile", {})
    gop_y             = state.get("gop_y_matrix", "")
    exam_matrix       = state.get("exam_matrix", {})

    # Nếu đã có matrix → đang chờ góp ý từ user
    if exam_matrix and not gop_y:
        last_input = next((m.content for m in reversed(messages) if isinstance(m, HumanMessage)), "")
        if last_input.strip().lower() in ["ok", "xong", "đồng ý", "không", ""]:
            return {"matrix_done": True, "current_step": "build_matrix"}
        gop_y = last_input

    so_cau       = profile.get("so_cau_hoi", 20)
    muc_tieu     = profile.get("muc_tieu_diem", 7)
    ghi_chu      = str(profile.get("ghi_chu", ""))

    # Tính phân bổ số câu + độ khó per chương bằng code
    ch_dist = _calc_chapter_distribution(knowledge_scores, so_cau, muc_tieu)

    template   = PROMPT_PATH.read_text(encoding="utf-8")
    all_chuong = []

    for ch_key, dist in ch_dist.items():
        ch_raw     = ch_key
        scores_ch  = knowledge_scores.get(ch_key, {})
        profile_ch = str(knowledge_profile.get(ch_key, ""))[:800]

        prompt = (template
                  .replace("{chuong}",        ch_raw)
                  .replace("{so_cau}",         str(dist["so_cau"]))
                  .replace("{so_de}",          str(dist["de"]))
                  .replace("{so_trung_binh}",  str(dist["trung_binh"]))
                  .replace("{so_kho}",         str(dist["kho"]))
                  .replace("{muc_tieu_diem}",  str(muc_tieu))
                  .replace("{ghi_chu}",        ghi_chu)
                  .replace("{knowledge_scores_ch}", _format_scores_ch(scores_ch))
                  .replace("{knowledge_profile_ch}", profile_ch)
                  .replace("{gop_y}",          gop_y or "không có"))

        ch_data = {}
        for attempt in range(3):
            response = llm_client._llm.invoke([{"role": "user", "content": prompt}])
            try:
                ch_data = _parse_matrix_ch(response.content)
                total   = sum(b.get("so_cau", 0) for b in ch_data.get("bai_hoc", []))
                print(f"[{ch_key}] attempt {attempt}: {total}/{dist['so_cau']} câu")
                if _validate_ch(ch_data, dist["so_cau"]):
                    break
            except Exception as e:
                print(f"[{ch_key}] attempt {attempt} lỗi: {e}")

        all_chuong.append({
            "ten":     ch_raw,
            "so_cau":  dist["so_cau"],
            "bai_hoc": ch_data.get("bai_hoc", []),
        })

    matrix = {
        "tong_so_cau": so_cau,
        "tong_do_kho": {
            "de":         sum(d["de"]         for d in ch_dist.values()),
            "trung_binh": sum(d["trung_binh"] for d in ch_dist.values()),
            "kho":        sum(d["kho"]         for d in ch_dist.values()),
        },
        "chuong": all_chuong,
    }

    print(f">>> build_matrix: tổng {sum(b['so_cau'] for c in all_chuong for b in c['bai_hoc'])} câu")

    ai_message = AIMessage(content=
        f"Ma trận đề đã được xây dựng:\n```json\n"
        f"{json.dumps(matrix, ensure_ascii=False, indent=2)}\n```\n"
        f"Bạn có góp ý gì không? (gõ 'ok' để tiếp tục)"
    )

    return {
        "messages":     [ai_message],
        "exam_matrix":  matrix,
        "gop_y_matrix": "",
        "matrix_done":  False,
        "current_step": "build_matrix",
    }