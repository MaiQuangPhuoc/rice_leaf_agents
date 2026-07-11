import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.clients.llm import LLMClient
from src.state import State
import datetime
from src.chatbot.rag_agent import RagAgent
from src.chatbot.router_agent import RouterAgent
from src.chatbot.planning_agent import PlanningAgent
from src.memory.memory_extractor import MemoryExtractor
from src.memory.memory_store import MemoryStore

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver


from src.configs import env_config

# Sau bao nhiêu cặp hội thoại thì extract memory
EXTRACT_EVERY_N_TURNS = 3


def create_agent_graph(llm_client, checkpointer):
    router_agent = RouterAgent(llm_client)
    rag_agent = RagAgent(llm_client)
    planning_agent = PlanningAgent(llm_client)

    graph = StateGraph(State)

    graph.add_node("router_agent", router_agent)
    graph.add_node("rag_agent", rag_agent)
    graph.add_node("planning_agent", planning_agent)

    graph.set_entry_point("router_agent")

    graph.add_conditional_edges(
        "router_agent",
        lambda state: (
            "rag_agent" if state.get("route") == 1
            else "planning_agent" if state.get("route") == 2
            else END
        ),
        {END: END, "rag_agent": "rag_agent", "planning_agent": "planning_agent"}
    )

    graph.add_conditional_edges("rag_agent", lambda state: END, {END: END})
    graph.add_conditional_edges("planning_agent", lambda state: END, {END: END})

    return graph.compile(checkpointer=checkpointer)


def main():
    llm_client = LLMClient(model=env_config.model, api_provider=env_config.api_provider)

    # Khởi tạo memory components
    memory_extractor = MemoryExtractor(llm_client)
    memory_store = MemoryStore(
        url=env_config.qdrant_url,
        api_key=env_config.qdrant_api_key,
    )

    # Định danh người dùng
    user_id = input("👤 Nhập tên / mã người dùng của bạn: ").strip()
    if not user_id:
        user_id = "default_user"
    thread_id = f"session_{user_id}"
    print(f"📌 Session ID: {thread_id}\n")

    with SqliteSaver.from_conn_string(
        r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\src\clients\chat_memory.db"
    ) as checkpointer:
        graph = create_agent_graph(llm_client, checkpointer)

        # ── Bước 1: Load memory từ Qdrant (nếu có từ session trước) ──
        existing_memory = memory_store.load(thread_id)
        if existing_memory:
            print(f"🧠 Đã tải memory từ session trước: {existing_memory}\n")
        else:
            print("🧠 Chưa có memory, bắt đầu phiên mới.\n")

        # ── Bước 2: Khởi tạo State ──
        state: State = {
            "messages": [],
            "state_router": False,
            "state_rag": False,
            "state_api": False,
            "state_other": False,
            "route": None,
            "history": [],
            "query_extract": None,
            "last_message": None,
            "user_memory": existing_memory,
            "current_plan": None,
            "plan_mode": None,
        }

        config = RunnableConfig(configurable={"thread_id": thread_id})
        turn_count = 0

        while True:
            user_input = input("\n👤 Bạn: ").strip()
            if user_input.lower() == "q":
                break

            state["messages"].append(HumanMessage(content=user_input))
            state = graph.invoke(state, config=config)

            # state["messages"] = [HumanMessage(content=user_input)]  # chỉ giữ turn hiện tại
            # state = graph.invoke(state, config=config)

            # state["messages"] = [HumanMessage(content=user_input)]  # chỉ giữ message hiện tại
            # state = graph.invoke(state, config=config)
            turn_count += 1

            if state.get("query_extract"):
                print(f"🔍 query_extract: {state['query_extract']}")

            ai_messages = [msg for msg in state["messages"] if msg.type == "ai"]
            if ai_messages:
                print('-' * 30)
                print(f"🤖 Agent: {ai_messages[-1].content}")

            # ── Bước 3: Extract memory sau mỗi N cặp hội thoại ──
            if turn_count % EXTRACT_EVERY_N_TURNS == 0:
                print(f"\n💾 Đang extract memory (sau {turn_count} turns)...")
                history = state.get("history", [])
                new_memory = memory_extractor.extract(
                    history=history,
                    user_id=user_id,
                    thread_id=thread_id,
                    existing_memory=existing_memory,
                )
                memory_store.save(new_memory)
                existing_memory = new_memory
                state["user_memory"] = new_memory
                print(f"💾 Memory đã lưu: {new_memory}\n")


if __name__ == "__main__":
    main()

