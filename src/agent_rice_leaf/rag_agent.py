import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.state import State

from langgraph.prebuilt import create_react_agent
from src.tools.rag_tools import retrieve_tool, ask_clarification_tool , weather_tool, web_search_tool
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel
from src.clients.llm import LLMClient
from langchain_core.messages import BaseMessage
from langchain.schema import HumanMessage , AIMessage, SystemMessage
logger = logging.getLogger(__name__)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

class RagAgent:

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        # self.tools = [retrieve_tool, ask_clarification_tool]
        self.tools = [retrieve_tool, ask_clarification_tool, weather_tool, web_search_tool]

    def _build_system_prompt(self, state: State) -> str:
        # Đọc RAG.txt
        with open(r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\RAG2.txt", "r", encoding="utf-8") as f:
            template = f.read()

        history = list(state.get("history", []))[-6:]
        history_text = "\n".join(
            f"{'Người dùng' if m.type == 'human' else 'Bot'}: {m.content}"
            for m in history
        )

        user_memory = state.get("user_memory")
        user_memory_text = ""
        if user_memory:
            user_memory_text = "\n".join(
                f"- {k}: {v}" for k, v in user_memory.items()
                if v and k not in ["user_id", "thread_id", "updated_at"]
            )

        return template.format(
            history=history_text or "Chưa có lịch sử.",
            user_memory=user_memory_text or "Chưa có thông tin.",
        )
    
    def split_response(self, response: str) -> tuple[str, str]:
        if "---TÓM TẮT---" in response:
            parts = response.split("---TÓM TẮT---", 1)
            return parts[0].strip(), parts[1].strip()
 
        return response.strip(), ""

    def __call__(self, state: State) -> dict:
        print("============= RAG_Agent (ReAct) =============")

        query_extract = state.get("query_extract")
        if isinstance(query_extract, dict):
            query_extract = query_extract["query_extract"]
        query_clear = query_extract.query_clear

        system_prompt = self._build_system_prompt(state)
        print("=== SYSTEM PROMPT ===")
        print(system_prompt)
        print("=== END SYSTEM PROMPT ===")

        # Tạo ReAct agent
        agent = create_react_agent(
            model=self.llm_client._llm,
            tools=self.tools,
            prompt=system_prompt,
        )

        result = agent.invoke({"messages": [HumanMessage(content=query_clear)]})

        print("=========sult[messages]")
        for msg in result["messages"]:
            print(f"[{msg.type}] {msg.content[:100]}")

        # Lấy message cuối cùng của agent
        ai_response = result["messages"][-1].content

        # Tách display và summary (giữ nguyên logic cũ)
        display_text, summary_text = self.split_response(ai_response)
        print("=== RESPONSE PARTS ===")
        print("display_text:", display_text)
        print("summary_text:", summary_text)
        print("=== END RESPONSE PARTS ===")

        # Cập nhật history
        current_history = list(state.get("history", []))
        new_pair = [
            HumanMessage(content=query_clear),
            # AIMessage(content=summary_text if summary_text else display_text[:100])
            AIMessage(content=summary_text if summary_text else "")
        ]
        updated_history = (current_history + new_pair)[-6:]

        return {
            "messages": [AIMessage(content=display_text)],
            "history": updated_history
        }