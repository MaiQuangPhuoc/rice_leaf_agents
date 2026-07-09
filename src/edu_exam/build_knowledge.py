import re
import json
import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage
from src.state_edu import ExamState
from src.clients.a import DeepSeekClient
from src.edu_exam.curriculum import extract_chapter_keys
from src.edu_exam.curriculum import normalize_chapter_key, CHAPTER_MAP
 
 
PROMPT_PATH = Path(r'D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompt_edu\prompt\build_knowledge.txt')
SECTIONS_PATH = Path(r'D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\src\modules\rag\process_toan_10\curriculum_sections.json')
CURRICULUM_SECTIONS = json.loads(SECTIONS_PATH.read_text(encoding="utf-8"))
 
 
 
ANALYZE_PROMPT_PATH = Path(r'D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompt_edu\prompt\analyze_knowledge.txt')
 
 
 
def _build_queue(profile: dict) -> list:
    """Tạo queue [chương] theo pham_vi_kiem_tra."""
    return extract_chapter_keys(profile)
 
 
def _build_chapter_section_text(ch: str) -> str:
    """Liệt kê tất cả bài + section trong chương, không giải thích."""
    lines = []
    for i, (lesson, sections) in enumerate(CURRICULUM_SECTIONS[ch].items(), 1):
        lines.append(f"Bài {i}: {lesson}")
        for j, sec in enumerate(sections, 1):
            lines.append(f"  {j}. {sec}")
    return "\n".join(lines)
 
 
def _parse_scores_chapter(answer: str, ch: str) -> dict:
    """Parse câu trả lời user → {bài: {section: score}}."""
    numbers = re.findall(r'[0-3]', answer)
    result  = {}
    idx     = 0
    for lesson, sections in CURRICULUM_SECTIONS[ch].items():
        result[lesson] = {}
        for sec in sections:
            result[lesson][sec] = int(numbers[idx]) if idx < len(numbers) else 0
            idx += 1
    return result
 
 
# CHAPTER_MAP = {
#     "mệnh đề và tập hợp": "chương 1",
#     "bất phương trình và hệ bất phương trình bậc nhất hai ẩn": "chương 2",
#     "hàm số bậc hai và đồ thị": "chương 3",
#     "hệ thức lượng trong tam giác": "chương 4",
#     "vecto": "chương 5",
#     "thống kê": "chương 6",
# }
 
def _analyze_chapters(state: dict, llm_client: DeepSeekClient) -> dict:
    """Giai đoạn 2: LLM phân tích từng chương → gộp thành knowledge_profile."""
    profile          = state.get("student_profile", {})
    retrieved_chunks = state.get("retrieved_chunks", [])
    knowledge_scores = state.get("knowledge_scores", {})
    pham_vi          = profile.get("pham_vi_kiem_tra", "")
    ghi_chu          = profile.get("ghi_chu", "không có")
 
    template          = ANALYZE_PROMPT_PATH.read_text(encoding="utf-8")
    knowledge_profile = {}
 
    for ch_key, ch_scores in knowledge_scores.items():
        # Lọc chunks theo chương
        # print("-"*30)
        # print(f"ch_key : {ch_key}")
        # print(f"ch_scores : {ch_scores}")
 
        chunks_ch = [
            c["content"]
            for c in retrieved_chunks
            if CHAPTER_MAP.get(
                c["metadata"].get("chapter_name", "").strip().lower(),
                ""
            ) == ch_key.strip().lower()
        ]
        chunks_text = "\n---\n".join(chunks_ch[:10])
 
        # Format scores
        scores_text = "\n".join([
            f"  {lesson}:\n" + "\n".join([f"    - {sec}: {score}" for sec, score in sections.items()])
            for lesson, sections in ch_scores.items()
        ])
 
        prompt = (template
                  .replace("{chuong}",   ch_key)
                  .replace("{pham_vi}",  str(pham_vi))
                  .replace("{ghi_chu}",  str(ghi_chu))
                  .replace("{scores}",   scores_text)
                  .replace("{chunks}",   chunks_text))
        
        # print("-"*30)
        # print(f"prompt : \n {prompt}")
        # print("-"*30)
 
        response = llm_client._llm.invoke([{"role": "user", "content": prompt}])
        knowledge_profile[ch_key] = response.content
        response_test = response.content
 
        # print("-"*30)
        # print(f"response_test : \n {response_test}")
        # print("-"*30)
 
    return knowledge_profile
 
 
def _build_queue(profile: dict) -> list:
    """Tạo queue [chương] theo pham_vi_kiem_tra."""
    return extract_chapter_keys(profile)
 
 
def _build_chapter_section_text(ch: str) -> str:
    """Liệt kê tất cả bài + section trong chương, không giải thích."""
    lines = []
    for i, (lesson, sections) in enumerate(CURRICULUM_SECTIONS[ch].items(), 1):
        lines.append(f"Bài {i}: {lesson}")
        for j, sec in enumerate(sections, 1):
            lines.append(f"  {j}. {sec}")
    return "\n".join(lines)
 
 
def _parse_scores_chapter(answer: str, ch: str) -> dict:
    """Parse câu trả lời user → {bài: {section: score}}."""
    numbers = re.findall(r'[0-3]', answer)
    result  = {}
    idx     = 0
    for lesson, sections in CURRICULUM_SECTIONS[ch].items():
        result[lesson] = {}
        for sec in sections:
            result[lesson][sec] = int(numbers[idx]) if idx < len(numbers) else 0
            idx += 1
    return result
 
 
def build_knowledge(state: ExamState, llm_client: DeepSeekClient) -> dict:
    print(">>> [Node] build_knowledge")
 
    completed_build_knowlege = state.get("completed_build_knowlege", {})
    
    if completed_build_knowlege:
        print(' ========================== completed_build_knowlege completed ========================== \n'*2)
        return {"current_step":"build_knowledge"}
 
    messages          = state.get("messages", [])
    knowledge_queue   = state.get("knowledge_queue")
    knowledge_pending = state.get("knowledge_pending")
    knowledge_scores  = state.get("knowledge_scores", {})
    knowledge_done    = state.get("knowledge_done", False)
 
    if knowledge_done:
        return {}
 
    # ── Khởi tạo queue lần đầu ───────────────────────────────────────────────
    if knowledge_queue is None:
        profile        = state.get("student_profile", {})
        knowledge_queue = _build_queue(profile)
 
    # ── Có pending → parse score chương vừa hỏi ──────────────────────────────
    if knowledge_pending:
        last_input = next((m.content for m in reversed(messages) if isinstance(m, HumanMessage)), "")
        ch         = knowledge_pending["chuong"]
        knowledge_scores[ch] = _parse_scores_chapter(last_input, ch)
 
    # ── Hết queue → giai đoạn 2: phân tích ─────────────────────────────────
    if not knowledge_queue:
        knowledge_profile = _analyze_chapters(state, llm_client)
        completed_build_knowlege = len(knowledge_profile) > 0 
        return {
            "knowledge_scores":   knowledge_scores,
            "knowledge_profile":  knowledge_profile,
            "knowledge_queue":    [],
            "knowledge_pending":  None,
            "knowledge_done":     True,
            "current_step":       "build_knowledge",
            "completed_build_knowlege": completed_build_knowlege
        }
 
    # ── Lấy chương tiếp theo ─────────────────────────────────────────────────
    ch           = knowledge_queue[0]
    section_text = _build_chapter_section_text(ch)
 
    template   = PROMPT_PATH.read_text(encoding="utf-8")
    prompt     = (template
                  .replace("{chuong}", ch.upper())
                  .replace("{sections}", section_text))
 
    response   = llm_client._llm.invoke([{"role": "system", "content": prompt}])
    ai_message = AIMessage(content=response.content)
 
    return {
        "messages":          [ai_message],
        "knowledge_queue":   knowledge_queue[1:],
        "knowledge_pending": {"chuong": ch},
        "knowledge_scores":  knowledge_scores,
        "knowledge_done":    False,
        "current_step":      "build_knowledge",
    }
 
