import os
import sys
import json
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent

from src.state import State
from src.clients.llm import LLMClient
from src.tools.rag_tools import retrieve_tool, weather_tool, web_search_tool
from src.tools.planning_tools import (
    collect_info,
    create_skeleton_tool,
    fill_detail_tool,
    edit_plan_tool,
    save_plan_tool,
    make_planning_tools,
)
from src.configs import env_config

# logger = logging.getLogger(__name__)

PROMPT_PATH = r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\PLANNING.txt"


class PlanningAgent:

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

        # Inject dependencies vào planning tools
        planning_tools = make_planning_tools(
            llm_client=llm_client,
            retriever=lambda q: retrieve_tool.invoke({"query": q}),
            db_path=r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\src\clients\chat_memory.db",
        )

        self.tools = [
            retrieve_tool,
            weather_tool,
            web_search_tool,
            *planning_tools,
        ]

    def _load_prompt(self, state: State) -> str:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            template = f.read()

        # History
        history = list(state.get("history", []))[-6:]
        history_text = "\n".join(
            f"{'Người dùng' if m.type == 'human' else 'Bot'}: {m.content}"
            for m in history
        ) or "Chưa có lịch sử."

        # print(f"history  : {history_text}")

        # User memory
        user_memory = state.get("user_memory")
        user_memory_text = ""
        if user_memory:
            data = user_memory if isinstance(user_memory, dict) else user_memory.model_dump()
            user_memory_text = "\n".join(
                f"- {k}: {v}" for k, v in data.items()
                if v and k not in ["user_id", "thread_id", "updated_at"]
            )


        # print(" ============== user_memory_text ==============")
        # print(f"\nuser_memory_text  : {user_memory_text}")
        

        # Current plan
        current_plan = state.get("current_plan")
        current_plan_text = "Chưa có kế hoạch." 
        if current_plan:
            plan_data = current_plan if isinstance(current_plan, dict) else current_plan.model_dump()
            current_plan_text = json.dumps(plan_data, ensure_ascii=False, indent=2)

        return template.format(
            history=history_text,
            user_memory=user_memory_text or "Chưa có thông tin.",
            current_plan=current_plan_text,
        )

    def split_response(self, response: str) -> tuple[str, str]:
        if "---TÓM TẮT---" in response:
            parts = response.split("---TÓM TẮT---", 1)
            return parts[0].strip(), parts[1].strip()
        # logger.warning("[PlanningAgent] Thiếu ---TÓM TẮT---")
        return response.strip(), ""

    def __call__(self, state: State) -> dict:
        print("============= PLANNING_Agent (ReAct) =============")

        # Lấy query từ messages
        messages = state.get("messages", [])
        last_human = next(
            (m for m in reversed(messages) if m.type == "human"), None
        )
        if last_human is None:
            return {"messages": [AIMessage(content="Không tìm thấy câu hỏi.")]}

        query = last_human.content
        system_prompt = self._load_prompt(state)

        # print(f"system prompt : :{system_prompt}")

        # Tạo ReAct agent
        agent = create_react_agent(
            model=self.llm_client._llm,
            tools=self.tools,
            prompt=system_prompt,
        )

        result = agent.invoke({"messages": [HumanMessage(content=query)]})

        # Debug messages
        print("=== PLANNING AGENT MESSAGES ===")
        for msg in result["messages"]:
            print(f"\n[{msg.type}] {str(msg.content)}")
            if hasattr(msg, "tool") and msg.tool:
                print("  tool:", getattr(msg.tool, "name", msg.tool))
            if hasattr(msg, "name") and msg.name:
                print("  name:", msg.name)
            if hasattr(msg, "artifact") and msg.artifact:
                print("  artifact:", msg.artifact)
            if hasattr(msg, "tool_input") and msg.tool_input:
                print("  tool_input:", msg.tool_input)

        ai_response = result["messages"][-1].content
        display_text, summary_text = self.split_response(ai_response)

        # print(f"\n ============================ RESPONSE PARTS ============================ ")
        # print(f"display_text: {display_text}")
        # print("-"*30)
        # print(f"summary_text: {summary_text}")

        # Cập nhật history
        current_history = list(state.get("history", []))
        new_pair = [
            HumanMessage(content=query),
            AIMessage(content=summary_text if summary_text else ""),
        ]
        updated_history = (current_history + new_pair)[-6:]

        # Cập nhật current_plan nếu agent đã tạo/sửa plan
        updated_plan = state.get("current_plan")
        for msg in result["messages"]:
            if hasattr(msg, "artifact") and msg.artifact:
                artifact = msg.artifact
                if isinstance(artifact, dict) and "plan_info" in artifact:
                    updated_plan = artifact["plan_info"]

        return {
            "messages": [AIMessage(content=display_text)],
            "history": updated_history,
            "current_plan": updated_plan,
        }
