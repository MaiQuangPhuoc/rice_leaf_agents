import sys ,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.clients.databases import qdrant 
from src.clients.llm import LLMClient
from State import State   
from src.agents.profile_collector import ProfileCollector
from src.agents.overview_planner import OverViewPlanner
from src.agents.detail_planner import DetailPlanner 
from src.agents.review_planner import ReviewPlanner 
from src.agents.mini_test import MiniTestPlanner 


import asyncio
from datetime import datetime
import json




from langgraph.graph import MessagesState, StateGraph
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
import asyncio
from langchain_core.runnables import RunnableConfig
from pydantic_settings import BaseSettings
from langchain_core.messages import HumanMessage
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.configs import env_config



# --------------------------------------------------------------------------------------------------------------------
def run_overview_planner(state: State):
    profile_completed = state.get("profile_completed", False)
    if profile_completed:
        print("✅ profile --> overview ✅")
        return "overview_planner"
    else:
        print("❌ profile --> overview ❌")
        # return "profile_collector"
        return END


# --------------------------------------------------------------------------------------------------------------------
def create_agent_graph(llm_client):
    profile_collector = ProfileCollector(llm_client)
    overview_planner = OverViewPlanner(llm_client,vector_store = qdrant)

    graph = StateGraph(State)
    graph.add_node("profile_collector", profile_collector)
    graph.add_node("overview_planner", overview_planner)

    graph.add_edge(START, "profile_collector")

    graph.add_conditional_edges(
        "profile_collector",
        run_overview_planner
    )

    graph.add_edge("overview_planner" , END)

    return graph.compile(checkpointer=MemorySaver())
# --------------------------------------------------------------------------------------------------------------------
# async def main():
#     print("=== Bắt đầu hội thoại với hệ thống ===")
#     llm_client = LLMClient(model=env_config.model, api_provider=env_config.api_provider)
#     state: State = {
#         "messages": [],
#         "profile_user": None,
#         "profile_completed": False
#     }
#     graph = create_agent_graph(llm_client)

#     while True:
#         user_input = input("🗣️   User: ")
#         if user_input.strip().lower() in ["q", "quit", "exit"]:
#             break

#         state["messages"].append(HumanMessage(content=user_input))
#         state = await graph.ainvoke(state, config=RunnableConfig(configurable={"thread_id": "demo_thread"}))

#         ai_messages = [msg for msg in state["messages"] if msg.type == "ai"]
#         if ai_messages:
#             print(f"⚙️   Agent: {ai_messages[-1].content}")

#         # for message in state["messages"]:
#         #     print(f"{message.type}: {message.content}")

# ----------------------------------------------------------------------
async def main():
    print("=== Bắt đầu hội thoại với hệ thống ===")
    llm_client = LLMClient(model=env_config.model, api_provider=env_config.api_provider)
    state: State = {
        "messages": [],
        "profile_user": [],
        "profile_completed": False
    }
    graph = create_agent_graph(llm_client)

    while True:
        user_input = input("🗣️   User: ")
        if user_input.strip().lower() in ["q", "quit", "exit"]:
            break

        # Thêm tin nhắn mới vào state['messages']
        state["messages"].append(HumanMessage(content=user_input))

        # Giả sử mỗi input là một ý (input) và thêm vào state['profile_user']
        state["profile_user"].append(user_input)

        # Chỉ gọi graph.ainvoke khi đủ 10 ý
        if len(state["profile_user"]) >= 10:
            state = await graph.ainvoke(state, config=RunnableConfig(configurable={"thread_id": "demo_thread"}))

            ai_messages = [msg for msg in state["messages"] if msg.type == "ai"]
            if ai_messages:
                print(f"⚙️   Agent: {ai_messages[-1].content}")

            # Đặt lại trạng thái nếu cần
            state["profile_completed"] = True
            break  # Thoát vòng lặp sau khi hoàn thành

        else:
            print(f"❌ Chưa đủ 10 ý, hiện tại có {len(state['profile_user'])} ý.")

if __name__ == "__main__":
    asyncio.run(main())
      
