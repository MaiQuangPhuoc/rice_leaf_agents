import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.state_edu import ExamState, StudentProfile
# from src.tools.tools_edu.tools_exam import parse_student_profile
# from src.clients.llm import LLMClient
from src.clients.a import DeepSeekClient

from src.configs import env_config
import json, re
from src.edu_exam.curriculum import map_scope 


 
def _filter_by_scope(docs: list, scope: list[str]) -> list:
    """
    Filter chunk theo thứ tự: chapter_name → lesson_name → section_name.
    Giữ chunk nếu scope match bất kỳ level nào.
    """

    print(' ========================== _filter_by_scope ========================== ')
    result = []
    for doc in docs:
        meta = doc.metadata
        chapter = meta.get("chapter_name", "").lower()
        lesson  = meta.get("lesson_name", "").lower()
        section = meta.get("section_name", "").lower()
 
        for s in scope:
            if s in chapter or s in lesson or s in section:
                result.append(doc)
                break

    for i, re in enumerate(result, 1):
        print(f"[result {i}]")
        print(re.page_content[:100])
        print("\n" + "-" * 50 + "\n")
    return result
 
 
# def _llm_filter(docs: list, profile: dict, llm_client: LLMClient) -> list:
#     """
#     LLM đọc danh sách chủ đề và chọn chunk liên quan đến yêu cầu học sinh.
#     Trả về list index chunk được giữ lại.
#     """
#     print(' ========================== LLM filter ========================== ')

#     topic_list = "\n".join([
#         f"{i}. [{doc.metadata.get('chapter_name')}] "
#         f"{doc.metadata.get('lesson_name')} - "
#         f"{doc.metadata.get('section_name')}"
#         for i, doc in enumerate(docs)
#     ])
 
#     prompt = f"""Học sinh cần ôn tập:
# - Môn: {profile.get('mon_hoc')}
# - Phạm vi: {profile.get('pham_vi_kiem_tra')}
# - Mục tiêu điểm: {profile.get('muc_tieu_diem_so')}
# - Ghi chú: {profile.get('ghi_chu', 'không có')}
 
# Danh sách chủ đề tìm được:
# {topic_list}
 
# Chọn các index LIÊN QUAN đến yêu cầu trên.
# Trả về chỉ list số, ví dụ: 0,1,3,5
# Không giải thích."""
 
#     response = llm_client._llm.invoke([{"role": "user", "content": prompt}])
#     raw = response.content.strip()
 
#     try:
#         indices = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
#         return [docs[i] for i in indices if i < len(docs)]
#     except Exception:
#         return docs  # fallback giữ tất cả
 
 
def retrieve_docs(state: ExamState, llm_client: DeepSeekClient, retriever, top_k: int = 10) -> dict:
    print(">>> [Node] retrieve_docs")
    print(' ========================== retriver ========================== ')

    completed = state.get("retrieve_complete", {})
    if completed:
        print(' ========================== retriver docs completed ========================== \n'*2)

        return { "current_step":     "retrieve_docs"}


 
    profile = state.get("student_profile", {})
 

    scope_data = map_scope(profile)
    scope_chapters = scope_data["scope_chapters"]  # {"chương 1": "MỆNH ĐỀ VÀ TẬP HỢP", ...}
    scope_lessons  = scope_data["scope_lessons"]   # {"chương 1": ["Mệnh đề", ...], ...}
 
    if not scope_chapters:
        print(">>> retrieve_docs: không map được phạm vi kiểm tra")
        return {"retrieved_chunks": [], "current_step": "retrieve_docs"}
 
    # Sinh query theo từng chương và bài
    queries = []
    for ch_key, ch_name in scope_chapters.items():
        queries.append(f"kiến thức nội dung {ch_name}")
        for lesson in scope_lessons.get(ch_key, []):
            queries.append(f"kiến thức nội dung {ch_name} bài {lesson}")

    # for q in queries:
    #     print(f"query : {q}\n-----\n")
 
    # Hybrid search, dedup
    seen = set()
    docs = []
    for q in queries:
        for doc in retriever.hybrid_search(q):
            key = doc.page_content[:50]
            if key not in seen:
                seen.add(key)
                docs.append(doc)
                # print('-'*30)
                # print(f" len doc : {len(docs)}")
                # print('-'*30)


    # for i, doc in enumerate(docs, 1):
        # print(f"[DOC {i}]")
        # print(doc.page_content[:100])
        # print("\n" + "-" * 50 + "\n")
 
    # Filter cứng theo chapter_name và lesson_name
    chapter_names = [v.lower() for v in scope_chapters.values()]
    lesson_names  = [l.lower() for lessons in scope_lessons.values() for l in lessons]
    docs = _filter_by_scope(docs, chapter_names + lesson_names)
 
    # # LLM filter
    # if docs:
    #     docs = _llm_filter(docs, profile, llm_client)

    #     for i, doc in enumerate(docs, 1):
    #         print(f"[_llm_filter {i}]")
    #         print(doc.page_content[:100])
    #         print("\n" + "-" * 50 + "\n")
 
    # Rerank
    if docs:
        rerank_query = " ".join(queries)
        print(' ========================== re-rank ========================== ')
        # print(f"rerank_query : {rerank_query}")
        
        docs = retriever.rerank(rerank_query, docs, top_k=top_k)
        
        # for i, doc in enumerate(docs, 1):
        #     print(f"[rerank {i}]")
        #     print(doc.page_content[:100])
        #     print("\n" + "-" * 50 + "\n")
 
    chunks = [
        {"content": doc.page_content, "metadata": doc.metadata}
        for doc in docs
    ]
 
    print(f">>> retrieve_docs: {len(chunks)} chunks sau rerank")
    retrieve_complete = len(chunks) > 0
    print(f"retrieve_complete")
 
    return {
        "retrieved_chunks": chunks,
        "scope_chapters":   scope_chapters,
        "scope_lessons":    scope_lessons,
        "current_step":     "retrieve_docs",
        "retrieve_complete": retrieve_complete
    }