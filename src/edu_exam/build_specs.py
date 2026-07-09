import json, re
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from pathlib import Path
from src.state_edu import ExamState
# from src.clients.llm import LLMClient
from src.clients.a import DeepSeekClient

from src.edu_exam.curriculum import normalize_chapter_key
from langchain_core.messages import AIMessage

PROMPT_PATH = Path(r'D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompt_edu\prompt\build_specs.txt')

VALIDATION_MAP = {
    "đạo hàm":        "sympy_derivative",
    "khảo sát":       "sympy_calculus",
    "giải phương trình": "sympy_solve",
    "bất phương trình":  "sympy_solve",
    "rút gọn":        "sympy_simplify",
    "xác suất":       "python_math",
    "thống kê":       "python_math",
    "lượng giác":     "sympy_trig",
}

def _get_validation_type(dang_bai: str) -> str:
    dang_bai_lower = dang_bai.lower()
    for keyword, vtype in VALIDATION_MAP.items():
        if keyword in dang_bai_lower:
            return vtype
    return "llm_review"   # ← fallback an toàn

def _parse_specs(text: str) -> list:
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if not match:
        raise ValueError("Không tìm thấy JSON list")
    raw = match.group()
    raw = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', raw)
    return json.loads(raw)


def _format_matrix_chuong(bai_hoc: list) -> str:
    lines = []
    for bai in bai_hoc:
        dk   = bai.get("do_kho", {})
        dang = bai.get("dang_bai", [])
        if dang and isinstance(dang[0], str):
            dang_str = ", ".join(dang)
        else:
            dang_str = ", ".join(d.get("ten", "") for d in dang)
        lines.append(
            f"Bài: {bai['ten']} | {bai['so_cau']} câu | "
            f"dễ={dk.get('de',0)} trung_bình={dk.get('trung_binh',0)} khó={dk.get('kho',0)} | "
            f"Dạng bài: {dang_str}"
        )
    return "\n".join(lines)


def _format_scores_chuong(scores: dict) -> str:
    lines = []
    for lesson, sections in scores.items():
        lines.append(f"{lesson}:")
        for sec, score in sections.items():
            label = ["Không quan tâm", "Ít", "Bình thường", "Cao"][score]
            lines.append(f"  - {sec}: {score} ({label})")
    return "\n".join(lines)


def _get_chunks_chuong(retrieved_chunks: list, ch_key: str) -> str:
    chunks = [
        c["content"][:300]
        for c in retrieved_chunks
        if normalize_chapter_key(c["metadata"].get("chapter_name", "")) == ch_key
    ]
    return "\n---\n".join(chunks[:5])


def _build_batch(
    template: str,
    ch_raw: str,
    bai_hoc: list,
    scores_ch: dict,
    profile_ch: str,
    chunks_ch: str,
    batch_size: int,
    b_de: int,
    b_tb: int,
    b_kho: int,
) -> str:
    return (template
            .replace("{chuong}",                  ch_raw)
            .replace("{ma_tran_chuong}",           _format_matrix_chuong(bai_hoc))
            .replace("{knowledge_scores_chuong}",  _format_scores_chuong(scores_ch))
            .replace("{knowledge_profile_chuong}", str(profile_ch)[:800])
            .replace("{chunks_chuong}",            chunks_ch)
            .replace("{so_cau}",                   str(batch_size))
            .replace("{so_de}",                    str(b_de))
            .replace("{so_trung_binh}",            str(b_tb))
            .replace("{so_kho}",                   str(b_kho)))


def build_specs(state: ExamState, llm_client: DeepSeekClient) -> dict:
    print(">>> [Node] build_specs" * 3)

    if state.get("specs_done", False):
        print("sườn done\n" * 3)
        return {}

    exam_matrix       = state.get("exam_matrix", {})
    knowledge_scores  = state.get("knowledge_scores", {})
    knowledge_profile = state.get("knowledge_profile", {})
    retrieved_chunks  = state.get("retrieved_chunks", [])

    template   = PROMPT_PATH.read_text(encoding="utf-8")
    all_specs  = []
    id_counter = 1

    for ch_data in exam_matrix.get("chuong", []):
        ch_raw  = ch_data.get("ten", "")
        ch_key  = normalize_chapter_key(ch_raw)
        bai_hoc = ch_data.get("bai_hoc", [])

        so_cau = sum(b.get("so_cau", 0) for b in bai_hoc)
        so_de  = sum(b.get("do_kho", {}).get("de", 0) for b in bai_hoc)
        so_tb  = sum(b.get("do_kho", {}).get("trung_binh", 0) for b in bai_hoc)
        so_kho = sum(b.get("do_kho", {}).get("kho", 0) for b in bai_hoc)

        scores_ch  = knowledge_scores.get(ch_key, {})
        profile_ch = knowledge_profile.get(ch_key, "")
        chunks_ch  = _get_chunks_chuong(retrieved_chunks, ch_key)

        specs_ch  = []
        remaining = so_cau
        batch_idx = 0

        # tỉ lệ độ khó để chia đều cho từng batch
        while remaining > 0:
            batch_size = min(10, remaining)
            ratio      = batch_size / so_cau if so_cau > 0 else 0
            b_de       = round(so_de  * ratio)
            b_tb       = round(so_tb  * ratio)
            b_kho      = batch_size - b_de - b_tb  # phần còn lại tránh lệch do làm tròn

            prompt = _build_batch(
                template, ch_raw, bai_hoc,
                scores_ch, profile_ch, chunks_ch,
                batch_size, b_de, b_tb, b_kho,
            )
            print("-"*30)
            # print(f"prompt : \n{prompt}")

            success = False
            for attempt in range(3):
                response = llm_client._llm.invoke([{"role": "user", "content": prompt}])
                try:
                    batch_specs = _parse_specs(response.content)
                    for s in batch_specs:
                        s["id"] = id_counter
                        id_counter += 1
                        s["validation_type"] = _get_validation_type(s.get("dang_bai", ""))
                    specs_ch.extend(batch_specs)
                    remaining -= len(batch_specs)
                    print(f"[{ch_key}] batch {batch_idx}: {len(batch_specs)}/{batch_size} specs, còn {remaining}")
                    success = True
                    break
                except Exception as e:
                    print(f"[{ch_key}] batch {batch_idx} attempt {attempt} lỗi: {e}")

            if not success:
                print(f"[{ch_key}] batch {batch_idx} thất bại sau 3 lần, bỏ qua")
                break

            batch_idx += 1

        print(f"[{ch_key}] tổng: {len(specs_ch)}/{so_cau} specs")
        all_specs.extend(specs_ch)

    specs_json = json.dumps(all_specs, ensure_ascii=False, indent=2)
    print(f">>> build_specs hoàn tất: {len(all_specs)} specs")

    return {
        "messages":       [AIMessage(content=specs_json)],
        "question_specs": all_specs,
        "specs_done":     len(all_specs) > 0,
        "current_step":   "build_specs",
    }