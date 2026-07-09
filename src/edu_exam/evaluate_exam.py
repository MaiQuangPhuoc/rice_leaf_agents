import json, re
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from pathlib import Path
from langchain_core.messages import AIMessage
from src.state_edu import ExamState
# from src.clients.llm import LLMClient
from src.clients.a import DeepSeekClient

from src.edu_exam.curriculum import normalize_chapter_key
from src.edu_exam.tools.sympy_tool import verify_giai_thich

PROMPT_PATH = Path(r'D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompt_edu\prompt\verify_answer.txt')

SYMPY_TYPES = {
    "sympy_derivative",
    "sympy_calculus",
    "sympy_solve",
    "sympy_simplify",
    "sympy_trig",
    "python_math",
}


# ── Parse ──────────────────────────────────────────────────────────────────────

def _parse_review_batch(text: str) -> list:
    text = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text.strip())
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if not match:
        raise ValueError("Không tìm thấy JSON list")
    raw = match.group()
    raw = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', raw)
    return json.loads(raw)


# ── Lấy chunks liên quan cho cả batch (luồng llm_review) ──────────────────────

def _get_chunks_for_batch(retrieved_chunks: list, batch: list) -> str:
    ch_keys   = {normalize_chapter_key(q.get("chuong", "")) for q in batch}
    dang_bais = {q.get("dang_bai", "").lower() for q in batch}

    matched = []
    for c in retrieved_chunks:
        meta     = c.get("metadata", {})
        ck       = normalize_chapter_key(meta.get("chapter_name", ""))
        sec_name = meta.get("section_name", "").lower()

        if ck not in ch_keys:
            continue
        if any(d in sec_name or sec_name in d for d in dang_bais if d):
            matched.insert(0, c["content"][:400])
        else:
            matched.append(c["content"][:200])

    return "\n---\n".join(matched[:8])


def _format_questions_batch(batch: list) -> str:
    lines = []
    for q in batch:
        options_text = "; ".join(f"{k}={v}" for k, v in q.get("options", {}).items())
        lines.append(
            f"id={q.get('id')} | question={q.get('question')} | "
            f"options=[{options_text}] | correct_answer={q.get('correct_answer')} | "
            f"giai_thich={q.get('giai_thich')}"
        )
    return "\n".join(lines)


# ── Luồng 1: SymPy verify (đã tính sẵn ở bước 6, tính lại để chắc chắn) ───────

def _verify_by_sympy(q: dict) -> dict:
    correct_key  = q.get("correct_answer", "")
    correct_text = q.get("options", {}).get(correct_key, "")
    giai_thich   = q.get("giai_thich", "")

    result = verify_giai_thich(correct_text, giai_thich)

    if result["sympy_check"] == "skip":
        return {
            "verify_method": "llm_fallback",
            "status":        "pending_llm",
            "reason":        result["reason"],
        }

    return {
        "verify_method": "sympy",
        "status":        "pass" if result["sympy_check"] == "pass" else "fail",
        "reason":        result["reason"],
    }


# ── Luồng 2: LLM review theo batch, bám tài liệu ───────────────────────────────

def _verify_batch_by_llm(batch: list, retrieved_chunks: list, llm_client: DeepSeekClient, template: str) -> list:
    chunks_text    = _get_chunks_for_batch(retrieved_chunks, batch)
    questions_text = _format_questions_batch(batch)

    prompt = (template
              .replace("{questions_batch}", questions_text)
              .replace("{chunks}",          chunks_text))

    results_by_id = {}
    for attempt in range(2):
        response = llm_client._llm.invoke([{"role": "user", "content": prompt}])
        try:
            parsed = _parse_review_batch(response.content)
            for r in parsed:
                results_by_id[r.get("id")] = {
                    "verify_method": "llm_review",
                    "status":        r.get("status", "fail"),
                    "reason":        r.get("reason", ""),
                }
            break
        except Exception as e:
            print(f"[llm_review batch] attempt {attempt} lỗi: {e}")

    # Đảm bảo mọi câu trong batch đều có kết quả, kể cả khi LLM bỏ sót
    results = []
    for q in batch:
        qid = q.get("id")
        if qid in results_by_id:
            results.append(results_by_id[qid])
        else:
            results.append({
                "verify_method": "llm_review",
                "status":        "error",
                "reason":        "LLM không trả về kết quả cho câu này",
            })
    return results


# ── Node chính ─────────────────────────────────────────────────────────────────

def evaluate_exam(state: ExamState, llm_client: DeepSeekClient) -> dict:
    print(">>> [Node] evaluate_exam" * 3)

    if state.get("evaluate_done", False):
        return {}

    generated_exam   = state.get("generated_exam", [])
    retrieved_chunks = state.get("retrieved_chunks", [])

    template = PROMPT_PATH.read_text(encoding="utf-8")

    pass_count = 0
    fail_count = 0

    sympy_questions = [q for q in generated_exam if q.get("validation_type", "llm_review") in SYMPY_TYPES]
    llm_questions    = [q for q in generated_exam if q.get("validation_type", "llm_review") not in SYMPY_TYPES]

    # ── Luồng SymPy: verify từng câu, tính rất nhanh không cần batch ──────────
    for q in sympy_questions:
        result = _verify_by_sympy(q)
        if result["status"] == "pending_llm":
            llm_questions.append(q)  # không tính được -> đẩy sang luồng LLM
            continue
        q["answer_review"] = result
        if result["status"] == "pass":
            pass_count += 1
        else:
            fail_count += 1
            print(f"[FAIL] id={q.get('id')} | method=sympy | reason={result['reason']}")

    # ── Luồng LLM review: gom theo chương, batch 10 câu/lần ───────────────────
    llm_by_chapter = {}
    for q in llm_questions:
        ch_key = normalize_chapter_key(q.get("chuong", ""))
        llm_by_chapter.setdefault(ch_key, []).append(q)

    for ch_key, ch_questions in llm_by_chapter.items():
        for i in range(0, len(ch_questions), 10):
            batch   = ch_questions[i:i + 10]
            results = _verify_batch_by_llm(batch, retrieved_chunks, llm_client, template)

            for q, result in zip(batch, results):
                q["answer_review"] = result
                if result["status"] == "pass":
                    pass_count += 1
                else:
                    fail_count += 1
                    print(f"[FAIL] id={q.get('id')} | method={result['verify_method']} | reason={result['reason']}")

    print(f">>> evaluate_exam hoàn tất: {pass_count} pass, {fail_count} fail / {len(generated_exam)} câu")

    summary = f"✅ Đánh giá đáp án hoàn tất: {pass_count}/{len(generated_exam)} câu đúng, {fail_count} câu cần xem lại."

    return {
        "messages":       [AIMessage(content=summary)],
        "generated_exam": generated_exam,
        "evaluate_done":  True,
        "current_step":   "evaluate_exam",
    }
