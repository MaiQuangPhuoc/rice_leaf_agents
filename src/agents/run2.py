import sys ,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.clients.llm import LLMClient
from state import AgentProfile , State   
from src.agents.profile_collector import ProfileCollector
from src.agents.overview_planner import OverViewPlanner
from langgraph.graph import MessagesState, StateGraph
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from src.clients.databases import qdrant 


from langchain_core.runnables import RunnableConfig
from pydantic_settings import BaseSettings
from langchain_core.messages import HumanMessage
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.configs import env_config

# --------------------------------------------------------------------------------------------------------------------

def run_overview_planner(state: State):
    profile_completed = state.get("profile_completed", False)
    if profile_completed:
        print("✅ hồ sơ hoàn tất ✅")
        return "overview_planner"
    else:
        print("❌ Hồ sơ chưa hoàn tất ❌.")
    return END

# ===== Tạo graph =====
def create_agent_graph(llm_client):
    profile_collector = ProfileCollector(llm_client)
    overview_planner = OverViewPlanner(llm_client,vector_store = qdrant)

    graph = StateGraph(State)
    graph.add_node("profile_collector", profile_collector)
    graph.add_node("overview_planner", overview_planner)

    graph.add_edge(START, "profile_collector")

    graph.add_conditional_edges(
        "profile_collector",
        run_overview_planner, 
        {END: END, "overview_planner": "overview_planner"}
    )

    graph.add_edge("overview_planner", END)

    return graph.compile(checkpointer=MemorySaver())

# ===== Main =====
if __name__ == "__main__":
    print("=== Bắt đầu hội thoại với hệ thống ===")

    llm_client = LLMClient(model=env_config.model, api_provider=env_config.api_provider)

    # graph = create_agent_graph(llm_client)

    # State ban đầu
    state: State = {
        "messages": [],
        "profile_user": None,
        "profile_completed": False
    }
    
    graph = create_agent_graph(llm_client)

    while not state.get("profile_completed", False):

  

        user_input = input("🗣️   User: ")
        if user_input.strip().lower() in ["q", "quit", "exit"]:
            break

        state["messages"].append(HumanMessage(content=user_input))

        # Chạy toàn bộ graph
        state = graph.invoke(state, config=RunnableConfig(configurable={"thread_id": "demo_thread"}))

        ai_messages = [msg for msg in state["messages"] if msg.type == "ai"]
        if ai_messages:
            print(f"⚙️   Agent: {ai_messages[-1].content}")

        # print("\n--- STATE HIỆN TẠI ---")
        # for k, v in state.items():
        #     if k != "messages":
        #         print(f"-----\n{k} = {v}")

    print("\n--- profile-completed ---")
    if state.get("profile_completed", False):
        print("✅✅✅✅✅✅✅")
    else:
        print("❌❌❌❌❌❌❌")


# -----------------------------------------------------------------------------------------------------------------------------------
# def run_overview_planner(state: State):
#     """Check if profile is completed and ready for overview planning"""
#     profile_completed = state.get("profile_completed", False)
#     if profile_completed:
#         return "overview_planner"
#     return END

# def create_agent_graph(llm_client):
#     # llm_client = LLMClient(model=env_config.model, api_provider=env_config.api_provider)

#     # Tạo 2 agent
#     profile_collector = ProfileCollector(llm_client)
#     overview_planner = OverViewPlanner(llm_client)

#     # Xây dựng graph
#     graph = StateGraph(State)
#     graph.add_node("profile_collector", profile_collector)
#     graph.add_node("overview_planner", overview_planner)

#     graph.add_edge(START, "profile_collector")



#     graph.add_conditional_edges(
#         "profile_collector",
#         run_overview_planner, 
#         {END: END,"overview_planner": "overview_planner"}
#     )

#     graph.add_edge("overview_planner", END)

#     graph = graph.compile()
#     return graph

# def main():

#     llm_client = LLMClient(model=env_config.model, api_provider=env_config.api_provider)

#     graph = create_agent_graph(llm_client)

#     # Khởi tạo trạng thái ban đầu
#     state = {
#         "messages": [],
#         "profile_user": None,
#         "profile_completed": False
#     }

#     while not state.get("profile_completed", False):

#         user_input = input("-----\n👤Bạn: ")
#         if user_input.lower() == "exit":
#             break

#         state["messages"].append(HumanMessage(content=user_input))

#         state = graph.invoke(state, config=RunnableConfig(configurable={"thread_id": "run_thread"}))

#         ai_messages = [msg for msg in state["messages"] if msg.type == "ai"]
#         if ai_messages:
#             print(f"-----\n🤖 Agent: {ai_messages[-1].content}")


#     for key, value in state.items():
#         if key != "messages":  
#             print(f"-----\n{key}: {value}")


# if __name__ == "__main__":
#     print("=== Bắt đầu hội thoại với hệ thống ===")

#     main()
     