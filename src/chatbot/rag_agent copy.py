import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.state import State

# print('oks')
from langgraph.prebuilt import create_react_agent
from src.tools.rag_tools import retrieve_tool, ask_clarification_tool , weather_tool, web_search_tool
# from typing import Type, Union
from langchain.prompts import ChatPromptTemplate
# from langgraph.checkpoint.memory import MemorySaver
# from langchain_core.runnables import RunnableConfig
# from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
from src.clients.llm import LLMClient
# from state import State
# from src.modules.rag.reranker import VietnameseReranker
from langchain_core.messages import BaseMessage
# from langchain_core.tools import tool
# from langgraph.prebuilt import ToolNode
from langchain.schema import HumanMessage , AIMessage, SystemMessage
# from langgraph.graph import END
# from langgraph.prebuilt import ToolNode, tools_condition
logger = logging.getLogger(__name__)
# from langgraph.graph import MessagesState, StateGraph
# from src.tools.tool import retrieve_tool  
# from src.tools.tools import extract_summary
# from src.configs import env_config
# from prompts.prompt import prompt_summary
# from src.clients.databases import qdrant_memory
# from src.modules.rag.tools_rag import RAGTools
# from src.tools.tools_web_search import tools_web_search

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

# from src.clients.embedding import embeddings_qa
# from src.configs import env_config
# from src.modules.rag.retrievers2 import VectorStoreRetriever


REACT_SYSTEM_PROMPT = """Bạn là chuyên gia tư vấn bệnh hại lá lúa.

NGUYÊN TẮC:
- Chỉ dùng thông tin từ retrieve_tool, không bịa đặt
- Nếu triệu chứng quá chung chung → dùng ask_clarification_tool hỏi lại
- Chỉ khẳng định tên bệnh khi có ≥2 triệu chứng đặc trưng từ tài liệu
- Không đủ dữ liệu → nói rõ "chưa đủ dữ liệu để khẳng định"

LỊCH SỬ HỘI THOẠI:
{history}

THÔNG TIN NGƯỜI DÙNG:
{user_memory}
"""



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
        # Fallback: tóm tắt = 200 ký tự đầu thay vì 100
        # return response.strip(), response.strip()[:200]
    # logger.warning("[RAG] LLM không trả về ---TÓM TẮT--- đúng format")
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