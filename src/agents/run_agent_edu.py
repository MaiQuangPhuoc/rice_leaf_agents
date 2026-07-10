import sys ,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.clients.databases import qdrant, qdrant_qa
from src.clients.llm import LLMClient
from state import State   
from src.agents.profile_collector import ProfileCollector
from src.agents.overview_planner import OverViewPlanner
from src.agents.detail_planner import DetailPlanner 
from src.agents.review_planner import ReviewPlanner 
from src.agents.QA_planner import QAPlanner 
from src.agents.QA_program import QAProgram

from src.agents.mini_test import MiniTestPlanner 





import asyncio
from datetime import datetime
import json




from langgraph.graph import MessagesState, StateGraph
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.runnables import RunnableConfig
from pydantic_settings import BaseSettings
from langchain_core.messages import HumanMessage
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.configs import env_config



# --------------------------------------------------------------------------------------------------------------------
def to_dict_safe(obj):
    if obj is None:
        return None
    if hasattr(obj, "dict"):   # Pydantic BaseModel
        return obj.dict()
    if isinstance(obj, (list, tuple)):
        return [to_dict_safe(o) for o in obj]
    if isinstance(obj, dict):
        return {k: to_dict_safe(v) for k, v in obj.items()}
    return obj  # kiểu cơ bản (str, int, float, bool)

def save_plan(state, folder="plans"):
    os.makedirs(folder, exist_ok=True)
    # plan_id = "20250830221757"
    plan_id = state.get("plan_id")
  
    file_path = os.path.join(folder, f"{plan_id}.json")
    # current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    # convert bất kỳ object nào có dict() sang dict
    overview_result = state.get("overview_result")
    review_result = to_dict_safe(state.get("review_result"))

    if hasattr(overview_result, "dict"):
        overview_result = overview_result.dict()
    if hasattr(review_result, "dict"):
        review_result = review_result.dict()

    data = {
        "plan_id": plan_id,        
        "time": current_time,
        "status": "Đang học",
        "overview_result": "overview_result",
        "review_result": review_result
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return file_path
# --------------------------------------------------------------------------------------------------------------------
def run_mini_test(state: State):
    if state.get("review_completed", False):
        # print("✅ review --> mini_test ✅")
        save_file = save_plan(state)
        print(f"kế hoạch đã được lưu vào :  {save_file}")

        return "mini_test_planner"
    else:
        # print("❌ review --> mini_test_planner ❌")
        return END

# --------------------------------------------------------------------------------------------------------------------

def run_review_planner(state: State):
    if state.get("detail_completed", False):
        # print("✅ detail --> review  ✅")
        state["messages"] = []
        state["messages"].clear()
        state["plan_id"] = None
        # state["plan_id"].clear()

        return "review_planner"
    else:
        # print("❌ detail --> review ❌")
        return END
# --------------------------------------------------------------------------------------------------------------------

def run_detail_planner(state: State):
    if state.get("overview_completed", False):
        # print("✅ Overview --> detail ✅")
        return "detail_planner"
    else:
        # print("❌ Overview --> detail ❌")
        return END
# --------------------------------------------------------------------------------------------------------------------

def run_overview_planner(state: State):
    profile_completed = state.get("profile_completed", False)
    if profile_completed:
        # print("✅ profile --> overview ✅")
        return "overview_planner"
    else:
        # print("❌ profile --> overview ❌")
        return END


def router(state: State):
    """Router function - phân tích query và cập nhật flow tương ứng"""
    flow = state.get("flow", "1")
    
    # Nếu flow = "1", giữ nguyên để chạy profile collector
    if flow == "1":
        return {"flow": "1"}
    
    # Với các flow khác (2.1, 2.2), luôn phân tích lại query mới nhất
    else:
        human_messages = [msg for msg in state["messages"] if msg.type == "human"]
        if human_messages:
            query = human_messages[-1].content.lower()
            
            # Nếu có các key đặc biệt => flow = 1
            if any(k in query for k in ["tạo", "muốn tạo", "tạo kế hoạch", "tạo kế hoạch học tập"]):
                return {"flow": "1"}
            
            # Nếu có từ khóa liên quan kế hoạch
            if any(k in query for k in ["kế hoạch", "tiến độ", "lộ trình", "id", 
                                        "mục tiêu học tập", "thời gian", "trong chương", 
                                        "phút", "cần nắm", "tổng quan học tập"]):
                return {"flow": "2.1"}
            else:
                return {"flow": "2.2"}
        
        # Fallback nếu không có human messages
        return {"flow": "2.2"}


def route_to_next(state: State):
    """Hàm helper để xác định node tiếp theo dựa trên flow và phân tích query"""
    flow = state.get("flow", "1")
    
    # Nếu flow = "1", chạy profile collector
    if flow == "1":
        return "profile_collector"
    
    elif flow in ["2.1", "2.2"]:
        human_messages = [msg for msg in state["messages"] if msg.type == "human"]
        if human_messages:
            query = human_messages[-1].content.lower()
            
            # Nếu có các key đặc biệt => quay lại profile_collector
            if any(k in query for k in ["tạo", "muốn tạo", "tạo kế hoạch", "tạo kế hoạch học tập"]):
                return "profile_collector"
            
            if any(k in query for k in ["kế hoạch", "tiến độ", "lộ trình", "id", 
                                        "mục tiêu học tập", "thời gian", "trong chương", 
                                        "phút", "cần nắm", "tổng quan học tập"]):
                return "qa_planner"
            else:
                return "qa_program"
    
    # Fallback cho trường hợp khác
    human_messages = [msg for msg in state["messages"] if msg.type == "human"]
    if human_messages:
        query = human_messages[-1].content.lower()  
        if any(k in query for k in ["tạo", "muốn tạo", "tạo kế hoạch", "tạo kế hoạch học tập"]):
            return "profile_collector"
        elif any(k in query for k in ["kế hoạch", "tiến độ", "lộ trình", "module"]):
            return "qa_planner"
        else:
            return "qa_program"
    
    return "profile_collector"

# Cập nhật cách tạo graph
def create_agent_graph(llm_client):
    profile_collector = ProfileCollector(llm_client)
    overview_planner = OverViewPlanner(llm_client, vector_store=qdrant)
    detail_planner = DetailPlanner(llm_client, vector_store=qdrant)
    review_planner = ReviewPlanner(llm_client)
    qa_planner = QAPlanner(llm_client)
    qa_program = QAProgram(llm_client, vector_store=qdrant_qa)
    mini_test_planner = MiniTestPlanner(llm_client)

    graph = StateGraph(State)
    
    # Thêm các node
    graph.add_node("profile_collector", profile_collector)
    graph.add_node("overview_planner", overview_planner)
    graph.add_node("detail_planner", detail_planner)
    graph.add_node("review_planner", review_planner)
    graph.add_node("qa_planner", qa_planner)
    graph.add_node("qa_program", qa_program)
    graph.add_node("mini_test_planner", mini_test_planner)
    graph.add_node("router", router)

    # Cập nhật conditional edges cho router
    graph.add_conditional_edges(
        "router",
        route_to_next,  # Sử dụng hàm helper thay vì router
        {
            "profile_collector": "profile_collector",
            "qa_planner": "qa_planner", 
            "qa_program": "qa_program",
        }
    )

    graph.add_edge(START, "router")

# -----------------------[   1   ] ------------------------------
    graph.add_conditional_edges(
        "profile_collector",
        run_overview_planner, 
        {END: END, "overview_planner": "overview_planner"}
    )

    graph.add_conditional_edges(
        "overview_planner",
        run_detail_planner,
        {END: END, "detail_planner": "detail_planner"}
    )

    graph.add_conditional_edges(
        "detail_planner",
        run_review_planner,
        {END: END, "review_planner": "review_planner"}
    )

    graph.add_conditional_edges(
        "review_planner",
        run_mini_test,
        {END: END, "mini_test_planner": "mini_test_planner"}
    ) 

# ----------------------- [   2.1   ] ------------------------------
    graph.add_conditional_edges(
        "qa_planner",
        run_mini_test,
        {END: END, "mini_test_planner": "mini_test_planner"}
    ) 

# ----------------------- [   2.2   ] ------------------------------
    graph.add_conditional_edges(
        "qa_program",
        run_mini_test,
        {END: END, "mini_test_planner": "mini_test_planner"}
    ) 
   

    graph.add_edge("mini_test_planner" , END)

    return graph.compile(checkpointer=MemorySaver())

# --------------------------------------------------------------------------------------------------------------------
async def main():
    print("=== Bắt đầu hội thoại với hệ thống ===")
    llm_client = LLMClient(model=env_config.model, api_provider=env_config.api_provider)
    state: State = {
        "messages": [],
        "profile_user": None,
        "profile_completed": False,
        "overview_completed": False,
        "overview_result": None,
        "ok": "",
        "study_details_result": None,
        "detail_completed": False,
        "plan_id": "",
        "status": "Đang học",
        "review_user": None,  
        "review_result ": None,
        "review_completed": False,
        "plan_data":None,
        "qa_planner_completed": False, 
        "flow": None
    }
    graph = create_agent_graph(llm_client)

    while True:
        print("flow: ", state.get("flow"))
        print("="*30)
        user_input = input("💁‍♂️    User: ")
        if user_input.strip().lower() in ["q", "quit", "exit"]:
            break

        # if user_input.strip() in ["1", "2", "2.1", "2.2"]:
        #     state["flow"] = user_input.strip()

        state["messages"].append(HumanMessage(content=user_input))
        state = await graph.ainvoke(state, config=RunnableConfig(configurable={"thread_id": "demo_thread"}))

        ai_messages = [msg for msg in state["messages"] if msg.type == "ai"]
        if ai_messages:
            print("="*100)
            print(f"⚙️  ⚙️   Agent : {ai_messages[-1].content}")

        print("="*40)
        flow = router(state)
        print("👉: ",flow)
        print("="*40)


if __name__ == "__main__":
    asyncio.run(main())
      


