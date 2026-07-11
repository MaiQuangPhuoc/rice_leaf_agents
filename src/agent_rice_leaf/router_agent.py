import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.state import State

# from langchain.schema import AIMessage
 
from langgraph.graph import END
from src.state import State , QueryExtract
from src.clients.llm import LLMClient
from langchain_core.messages import HumanMessage , AIMessage, SystemMessage


ROUTER_PROMPT_PATH = r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\ROUTER_PROMPT.txt"
QUERY_TRANSFORM_PROMPT_PATH = r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\QUERY_TRANSFORM_PROMPT.txt"

with open(ROUTER_PROMPT_PATH, "r", encoding="utf-8") as f:
    ROUTER_PROMPT = f.read()

DISEASE_MAPPING = {
    "DỮ LIỆU BỆNH HỌC: BỆNH ĐẠO ÔN LÁ": "LEAF BLAST",
    "BỆNH ĐỐM LÁ HẸP / GẠCH NÂU": "NARROW BROWN LEAF SPOT",
    "BỆNH ĐỐM NÂU": "BROWN SPOT",
    "BỆNH KHÔ VẰN": "SHEATH BLIGHT",
    "BỆNH BẠC LÁ": "BACTERIAL LEAF BLIGHT - BLB",
    "BỆNH BỎNG LÁ": "RICE LEAF YELLOWING",
    "LÁ LÚA KHỎE MẠNH": "HEALTHY RICE LEAF"
}

DISEASE_MAPPING_TEXT = "\n".join(f"- {vn}: {en}" for vn, en in DISEASE_MAPPING.items())

with open(QUERY_TRANSFORM_PROMPT_PATH, "r", encoding="utf-8") as f:
    _query_transform_template = f.read()

QUERY_TRANSFORM_PROMPT = _query_transform_template.replace(
    "{disease_mapping}", DISEASE_MAPPING_TEXT
)

class RouterAgent:

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def __call__(self, state: State) -> dict:
        print("======================================= Router_Agent =======================================")

        def query_transform(state: State) -> dict:
            messages = state.get("messages", [])
            user_message = [msg.content for msg in messages if msg.type == "human"][-1]

            history_text = "\n".join(
                f"{'Người dùng' if m.type == 'human' else 'Bot'}: {m.content}"
                for m in messages[:-1][-6:]
            )

            prompt = QUERY_TRANSFORM_PROMPT
            if history_text:
                prompt += f"\nLịch sử:\n{history_text}\n"
            prompt += f"\nCâu hỏi hiện tại: \"{user_message}\""

            response = self.llm_client._llm.invoke(prompt)
            raw = response.content.strip()

            result = {"query_clear": user_message, "disease": None, "scientific_name": None, "topic": None, "keywords": []}
            for line in raw.split("\n"):
                line = line.strip()
                if line.startswith("query_clear:"):
                    result["query_clear"] = line.split("query_clear:")[1].strip()
                elif line.startswith("disease:"):
                    val = line.split("disease:")[1].strip()
                    result["disease"] = [d.strip() for d in val.split(",")] if val else None
                elif line.startswith("scientific_name:"):
                    val = line.split("scientific_name:")[1].strip()
                    result["scientific_name"] = val if val else None
                elif line.startswith("topic:"):
                    result["topic"] = line.split("topic:")[1].strip()
                elif line.startswith("keywords:"):
                    kw = line.split("keywords:")[1].strip()
                    result["keywords"] = [k.strip() for k in kw.split(",") if k.strip()]

            valid_scientific = set(DISEASE_MAPPING.values())
            if result["scientific_name"] not in valid_scientific:
                result["scientific_name"] = None

            query_extract = QueryExtract(**result)
            return {"query_extract": query_extract}

        # Bước 1: làm rõ query + trích xuất
        transform_result = query_transform(state)
        state = {**state, **transform_result}

        query_clear = state["query_extract"].query_clear

        messages = state.get("messages", [])
        history_text = "\n".join(
            f"{'Người dùng' if m.type == 'human' else 'Bot'}: {m.content}"
            for m in messages[:-1][-6:]
        )

        prompt = ROUTER_PROMPT
        if history_text:
            prompt += f"\nLịch sử hội thoại:\n{history_text}\n"
        prompt += f"\nCâu hỏi hiện tại: \"{query_clear}\""

        response = self.llm_client._llm.invoke(prompt)
        llm_output = response.content.strip()

        print(f"[Router] LLM output:\n{llm_output}")

        route = None
        reason = ""
        for line in llm_output.split("\n"):
            line = line.strip()
            if line.startswith("route:"):
                try:
                    route = int(line.split("route:")[1].strip())
                except ValueError:
                    route = None
            elif line.startswith("reason:"):
                reason = line.split("reason:")[1].strip()

        print(f"[Router] route={route}, reason={reason}")

        if route == 1:
            return {"route": 1, "state_router": True, "query_extract": transform_result}
        elif route == 2:
            return {"route": 2, "state_router": True, "query_extract": transform_result}
        else:
            return {"route": 0, "state_router": False, "query_extract": transform_result}
