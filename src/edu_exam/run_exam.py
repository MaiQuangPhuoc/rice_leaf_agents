import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
# from graph import exam_graph
from langgraph.graph import StateGraph, END
# from src.clients.llm import LLMClient
from src.clients.a import DeepSeekClient

from src.configs import env_config
# from state_edu import ExamState
from src.state_edu import ExamState
from langchain_core.runnables import RunnableConfig
from src.clients.embedding import embeddings_qa
from src.edu_exam.collect_info import collect_info
from src.edu_exam.build_knowledge import build_knowledge as _build_knowledge
from src.edu_exam.build_matrix import build_matrix as _build_matrix
from src.edu_exam.build_specs import build_specs as _build_specs
from src.edu_exam.generate_questions import generate_questions as _generate_questions
from src.edu_exam.evaluate_exam import evaluate_exam as _evaluate_exam
from src.edu_exam.retrieve_docs import retrieve_docs as _retrieve_docs
 
from src.modules.rag.process_toan_10.retrievers2 import VectorStoreRetriever

from functools import partial
load_dotenv()
 
llm_client = DeepSeekClient()
 
# def retrieve_docs(state: ExamState) -> dict:
#     print(">>> [Node] retrieve_docs")
#     return {"current_step": "retrieve_docs"}
 
# def build_knowledge(state: ExamState, llm_client: LLMClient) -> dict:
#     print(">>> [Node] build_knowledge")
#     return {"current_step": "build_knowledge"}
 
 
# def build_matrix(state: ExamState) -> dict:
#     print(">>> [Node] build_matrix")
#     return {"current_step": "build_matrix"}
 
# def build_specs(state: ExamState) -> dict:
#     print(">>> [Node] build_specs")
#     return {"current_step": "build_specs"}
 
def generate_questions(state: ExamState) -> dict:
    print(">>> [Node] generate_questions")
    return {"current_step": "generate_questions"}
 
def evaluate_exam(state: ExamState) -> dict:
    print(">>> [Node] evaluate_exam")
    return {"current_step": "evaluate_exam", "exam_review": {"status": "pass"}}
 
 
def create_graph(llm_client: DeepSeekClient,retriever):
    g = StateGraph(ExamState)
 
    g.add_node("collect_info",       partial(collect_info, llm_client=llm_client))
    g.add_node("retrieve_docs",      partial(_retrieve_docs, llm_client=llm_client, retriever=retriever, top_k=5))
    g.add_node("build_knowledge",    partial(_build_knowledge, llm_client=llm_client))
    g.add_node("build_matrix",       partial(_build_matrix, llm_client=llm_client))
    g.add_node("build_specs",        partial(_build_specs, llm_client=llm_client))
    g.add_node("generate_questions", partial(_generate_questions, llm_client=llm_client))
    g.add_node("evaluate_exam",      partial(_evaluate_exam, llm_client=llm_client))
 
    g.set_entry_point("collect_info")
 
    g.add_conditional_edges(
        "collect_info",
        lambda state: "retrieve_docs" if state.get("profile_complete") else END,
        {"retrieve_docs": "retrieve_docs", END: END}
    )
 
    g.add_conditional_edges(
        "retrieve_docs",
        lambda state: (
            "build_knowledge"
            if state.get("retrieve_complete")
            else END
        ),
        {
            "build_knowledge": "build_knowledge",
            END: END,
        }
    )
 
    g.add_conditional_edges(
        "build_knowledge",
        lambda state: "build_matrix" if state.get("knowledge_done") else END,
        {"build_matrix": "build_matrix", END: END}
    )    

    g.add_conditional_edges(
        "build_matrix",
        lambda state: "build_specs" if state.get("matrix_done") else END,
        {"build_specs": "build_specs", END: END}
    )

    g.add_conditional_edges(
        "build_specs",
        lambda state: "generate_questions" if state.get("specs_done") else END,
        {"generate_questions": "generate_questions", END: END}
    )
    
    # g.add_edge("build_specs",        "generate_questions")
    g.add_edge("generate_questions", "evaluate_exam")
    g.add_edge("evaluate_exam",      END)
 
    return g.compile()
 
 
def run():
    print("=" * 50)
    print("🎓 Hệ thống tạo đề kiểm tra thông minh")
    print("=" * 50)
    print("Gõ 'quit' để thoát\n")
 
    # llm_client = LLMClient(model=env_config.model, api_provider=env_config.api_provider)
    llm_client = DeepSeekClient()

 
    retriever = VectorStoreRetriever(
        url=env_config.qdrant_url,
        api_key=env_config.qdrant_api_key,
        embeddings=embeddings_qa,
        collection_name="doc_toan_10_1",
        top_k=10,
    )
 
    graph = create_graph(llm_client, retriever)
 
    state = {
        "messages": [],
        "student_profile": {},
        "profile_complete": False,
        "detected_chapters": [],
        "retrieved_chunks": [],
        "retrieve_complete": False,
        "scope_chapters": {},
        "scope_lessons": {},
        "section_selected": False,
        "scored_chunks": [],
        "_pending_sections": [],
        "knowledge_profile": {},
        "knowledge_queue":   None,
        "knowledge_pending": None,
        "knowledge_scores":  {},
        "knowledge_done":    False,
        "completed_build_knowlege" : False,
        "exam_matrix": {},
        "question_specs": [],
        "specs_done": False,
        "generated_exam": [],
        "exam_memory": [],
        "generate_done":  False,
        "exam_review": {},
        "final_exam": [],
        "evaluate_done": False,
        "current_step": "",
        "error": None,
    }
 
    
    while True:
        user_input = input("Học sinh: ").strip()
        if user_input.lower() == "quit":
            break
        if not user_input:
            continue

        # bỏ # ở đầu mỗi dòng
        user_input = "\n".join(
            line.lstrip("#").strip()
            for line in user_input.splitlines()
        )
 
        state["messages"].append(HumanMessage(content=user_input))
 
        # # Chỉ invoke đúng bước cần thiết
        # if not state.get("profile_complete"):
        #     state = graph.invoke(state)
        # elif not state.get("knowledge_done"):
        #     state = graph.invoke(state)
        # else:
        #     break
        # thay bằng


        if not state.get("profile_complete"):
            state = graph.invoke(state)
        elif not state.get("knowledge_done"):
            state = graph.invoke(state)
        elif not state.get("matrix_done"):
            state = graph.invoke(state)
        elif not state.get("specs_done"):
            state = graph.invoke(state)
        elif not state.get("generate_done"):
            state = graph.invoke(state)
        elif not state.get("evaluate_done"):
            state = graph.invoke(state)
        else:
            break

        
        # In phản hồi AI mới nhất
        ai_messages = [m for m in state["messages"] if hasattr(m, "type") and m.type == "ai"]
        if ai_messages:
            print("-"*70)
            print(f"Trợ lý: {ai_messages[-1].content}\n")
            print("-"*70)
 
 
        # in tóm tắt knowledge chỉ 1 lần khi vừa xong
        # if state.get("knowledge_done") and not state.get("matrix_done"):
        #     scores = state.get("knowledge_scores", {})
        #     print("\n📋 TÓM TẮT MỨC ĐỘ QUAN TÂM:")
        #     for ch, lessons in scores.items():
        #         print(f"\n  {ch.upper()}:")
        #         for lesson, sections in lessons.items():
        #             print(f"    Bài: {lesson}")
        #             for sec, score in sections.items():
        #                 label = ["Không", "Ít", "Bình thường", "Cao"][score]
        #                 print(f"      - {sec}: {score} ({label})")
        #     print("\n✅ Hoàn tất bước 3. Bắt đầu xây dựng ma trận đề...\n")
 
        if state.get("knowledge_done"):
            print(f"knowledge_done ====> TRUE")
        if state.get("specs_done"):
            print(f"specs_done     ====> TRUE")
        if state.get("generate_done"):
            print(f"generate_done  ====> TRUE")
        if state.get("evaluate_done"):
            print(f"evaluate_done  ====> TRUE")
 
 
    return state
 
 
if __name__ == "__main__":
    run()
 
# tôi cần tạo đề thi toán 10 , 20 câu trắc nghiệm trong 100 phút với mục tiêu 9 điểm để ôn thi cuối kì ,phạm vi 3 chương đầu tiên phần đại số ,chương 1 khá , chương 2 giỏi chương 3 8 điểm ,lưu ý  chú ý các chương 1 ,3
# 1,0,2,0,2,1,0,2,0,3
# 2,0,3,0,0,3
# 1,2,1,2,3,1,3