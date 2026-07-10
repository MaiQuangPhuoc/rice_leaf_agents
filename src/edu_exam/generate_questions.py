import json, re
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from datetime import datetime
from pathlib import Path
from langchain_core.messages import AIMessage
from src.state_edu import ExamState
# from src.clients.llm import LLMClient
from src.clients.a import DeepSeekClient


from src.edu_exam.curriculum import normalize_chapter_key
# from src.edu_exam.tools.sympy_tool import check_duplicate_options
from src.edu_exam.tools.sympy_tool import verify_giai_thich, check_duplicate_options

PROMPT_PATH = Path(r'D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompt_edu\prompt\generate_questions.txt')
OUTPUT_DIR  = Path(r'D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\src\test_exam')
BATCH_SIZE  = 10


# ── Parse ──────────────────────────────────────────────────────────────────────

def _parse_questions(text: str) -> list:
    # Bóc markdown fence nếu có (```json ... ``` hoặc ``` ... ```)
    text = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text.strip())

    # Tìm JSON list
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if not match:
        raise ValueError("Không tìm thấy JSON list trong response")
    raw = match.group()

    # Escape backslash lạ (không phải escape hợp lệ của JSON)
    raw = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', raw)

    return json.loads(raw)


# ── Lưu JSON ra file ──────────────────────────────────────────────────────────

def _save_exam_json(generated_exam: list) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path  = OUTPUT_DIR / f"exam_{timestamp}.json"

    exam_clean = [
        {
            "chuong":          q.get("chuong", ""),
            "bai":             q.get("bai", ""),
            "dang_bai":        q.get("dang_bai", ""),
            "do_kho":          q.get("do_kho", ""),
            "question":        q.get("question", ""),
            "options":         q.get("options", {}),
            "correct_answer":  q.get("correct_answer", ""),
            "giai_thich":      q.get("giai_thich", ""),
        }
        for q in generated_exam
    ]

    out_path.write_text(
        json.dumps(exam_clean, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f">>> Đã lưu đề thi: {out_path}")
    return out_path


# ── Filter chunks theo chương + section ───────────────────────────────────────

def _get_chunks_for_chapter(retrieved_chunks: list, ch_key: str, dang_bais: set) -> str:
    """Lọc chunks theo chương, ưu tiên section khớp dang_bai."""
    priority = []
    fallback = []

    for c in retrieved_chunks:
        meta     = c.get("metadata", {})
        ck       = normalize_chapter_key(meta.get("chapter_name", ""))
        sec_name = meta.get("section_name", "").lower()

        if ck != ch_key:
            continue

        if any(d in sec_name or sec_name in d for d in dang_bais if d):
            priority.append(c["content"][:400])
        else:
            fallback.append(c["content"][:200])

    combined = priority[:6] + fallback[:3]
    return "\n---\n".join(combined)


# ── Format ─────────────────────────────────────────────────────────────────────

def _format_specs(specs: list) -> str:
    lines = []
    for s in specs:
        lines.append(
            f"id={s['id']} | bai={s['bai']} | dang_bai={s['dang_bai']} | "
            f"do_kho={s['do_kho']} | yeu_cau={s['yeu_cau']} | "
            f"ngu_canh={', '.join(s.get('ngu_canh', []))}"
        )
    return "\n".join(lines)


def _format_memory(exam_memory: list) -> str:
    if not exam_memory:
        return "Chưa có câu nào."
    return "\n".join(
        f"- id={m['id']} | dang_bai={m['dang_bai']} | y_tuong={m['y_tuong']}"
        for m in exam_memory[-20:]
    )


# ── Validation ─────────────────────────────────────────────────────────────────

def _hard_validate(q: dict) -> dict:
    errors = []
    for field in ["id", "question", "options", "correct_answer"]:
        if field not in q:
            errors.append(f"Thiếu field: {field}")

    options = q.get("options", {})
    for key in ["A", "B", "C", "D"]:
        if key not in options:
            errors.append(f"Thiếu đáp án {key}")

    if q.get("correct_answer") not in ["A", "B", "C", "D"]:
        errors.append("correct_answer không hợp lệ")

    dup = check_duplicate_options(options)
    if dup["duplicate_check"] == "fail":
        errors.append(dup["reason"])

    return {"hard_check": "pass" if not errors else "fail", "errors": errors}


# thay bằng
def _sympy_validate(q: dict) -> dict:
    correct_key  = q.get("correct_answer", "")
    correct_text = q.get("options", {}).get(correct_key, "")
    giai_thich   = q.get("giai_thich", "")
    return verify_giai_thich(correct_text, giai_thich)


# ── Node chính ─────────────────────────────────────────────────────────────────

def generate_questions(state: ExamState, llm_client: DeepSeekClient) -> dict:
    print(">>> [Node] generate_questions" * 3)

    if state.get("generate_done", False):
        return {}

    question_specs   = state.get("question_specs", [])
    retrieved_chunks = state.get("retrieved_chunks", [])
    exam_memory      = state.get("exam_memory", [])
    generated_exam   = state.get("generated_exam", [])

    template = PROMPT_PATH.read_text(encoding="utf-8")

    # ── Bước 1: Group specs theo chương ───────────────────────────────────────
    specs_by_chapter = {}
    for s in question_specs:
        ch_key = normalize_chapter_key(s.get("chuong", ""))
        specs_by_chapter.setdefault(ch_key, []).append(s)

    # ── Bước 2: Loop từng chương ──────────────────────────────────────────────
    for ch_key, ch_specs in specs_by_chapter.items():
        print(f"\n[{ch_key}] bắt đầu sinh {len(ch_specs)} câu")

        dang_bais_ch = {s.get("dang_bai", "").lower() for s in ch_specs}
        chunks_ch    = _get_chunks_for_chapter(retrieved_chunks, ch_key, dang_bais_ch)

        # ── Bước 3: Loop batch trong chương ───────────────────────────────────
        for i in range(0, len(ch_specs), BATCH_SIZE):
            batch_specs = ch_specs[i: i + BATCH_SIZE]
            batch_idx   = i // BATCH_SIZE

            dang_bais_batch = {s.get("dang_bai", "").lower() for s in batch_specs}
            chunks_batch    = _get_chunks_for_chapter(retrieved_chunks, ch_key, dang_bais_batch)

            specs_text  = _format_specs(batch_specs)
            memory_text = _format_memory(exam_memory)

            prompt = (template
                      .replace("{question_specs}", specs_text)
                      .replace("{chunks}",         chunks_batch)
                      .replace("{exam_memory}",    memory_text)
                      .replace("{so_cau}",         str(len(batch_specs))))

            questions_batch = []
            for attempt in range(3):
                response = llm_client._llm.invoke([{"role": "user", "content": prompt}])
                try:
                    questions_batch = _parse_questions(response.content)
                    print(f"[{ch_key}] batch {batch_idx}: {len(questions_batch)}/{len(batch_specs)} câu")
                    break
                except Exception as e:
                    print(f"[{ch_key}] batch {batch_idx} attempt {attempt} lỗi: {e}")

            specs_by_id = {s["id"]: s for s in batch_specs}

            for q in questions_batch:
                spec = specs_by_id.get(q.get("id"), {})
                q["validation_type"] = spec.get("validation_type", "llm_review")
                hard  = _hard_validate(q)
                sympy = _sympy_validate(q)
                q["validation"] = {
                    "hard_check":   hard["hard_check"],
                    "errors":       hard["errors"],
                    "sympy_check":  sympy["sympy_check"],
                    "sympy_reason": sympy["reason"],
                }
                generated_exam.append(q)
                exam_memory.append({
                    "id":       q.get("id"),
                    "chuong":   ch_key,
                    "bai":      q.get("bai", ""),
                    "dang_bai": q.get("dang_bai", ""),
                    "y_tuong":  q.get("y_tuong", ""),
                })

        print(f"[{ch_key}] hoàn tất — tổng: {len(generated_exam)} câu")

    # ── Lưu JSON ra file ──────────────────────────────────────────────────────
    exam_json = json.dumps(generated_exam, ensure_ascii=False, indent=2)
    _save_exam_json(generated_exam)
    

    print(f"\n>>> generate_questions hoàn tất: {len(generated_exam)} câu")

    return {
        "messages":      [AIMessage(content=exam_json)],
        "generated_exam": generated_exam,
        "exam_memory":    exam_memory,
        "generate_done":  len(generated_exam) > 0,
        "current_step":   "generate_questions",
    }