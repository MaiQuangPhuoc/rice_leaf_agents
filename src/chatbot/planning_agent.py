import os
import sys
import json
from typing import Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from langchain_core.messages import HumanMessage, AIMessage
# from src.state import State
from src.state import State, Plan, SkeletonPhase
from src.tools.planning_tools import create_skeleton as create_skeleton_tool
from src.memory.json_doc.disease_doc_loader import load_disease_doc
from src.clients.llm import LLMClient
from src.chatbot.fill_detail import fill_detail



COLLECT_INFO_PROMPT_PATH = r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\COLLECT_INFO.txt"
CREATE_SKELETON_PROMPT_PATH = r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\CREATE_SKELETON.txt"
PLANNING_PROMPT_PATH     = r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\PLANNING.txt"

SUMMARY_CONVER_PROMPT_PATH = r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\SUMMARY_CONVER.txt"

def summary_conver(llm_client, query: str, response: str) -> str:
    with open(SUMMARY_CONVER_PROMPT_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    conversation = f"Người dùng: {query}\nBot: {response}"
    prompt = template.replace("{conversation}", conversation)

    result = llm_client._llm.invoke([
        {"role": "system", "content": prompt},
        {"role": "user", "content": "Tóm tắt hội thoại trên."},
    ])

    return result.content.strip()

def collect_info(llm_client, state: State, prompt: str, query: str) -> str:
    response = llm_client._llm.invoke([
        {"role": "system", "content": prompt},
        {"role": "user", "content": query},   # dùng query thực của user
    ])
    # print("=" * 20)
    # print(f"[collect_info] response:\n{response.content}")
    # print("=" * 20)
    return response
    
 
LABEL_MAP = {
    "Mục tiêu":        "disease",
    "Địa điểm":        "location",
    "Số ngày":         "duration_days",
    "Giai đoạn lúa":   "rice_stage",
    "Phạm vi bệnh":    "disease_scale",
    "Thời gian bệnh":  "disease_duration",
    "Mức độ":          "disease_severity",
    "Giống lúa":       "rice_variety",
    "Đang dùng thuốc": "current_medicine",
    "Thời tiết":       "weather_description",
}

def parse_collect_to_context(response_collect: str) -> dict:
    result = {v: None for v in LABEL_MAP.values()}

    for line in response_collect.split("\n"):
        line = line.strip().lstrip("-").strip()
        for label, field in LABEL_MAP.items():
            if line.startswith(label):
                parts = line.split(":", 1)
                value = parts[1].strip() if len(parts) > 1 else ""
                if value.lower() in ("chưa có", "none", "null", ""):
                    result[field] = None
                elif field == "duration_days":
                    try:
                        result[field] = int("".join(filter(str.isdigit, value))) or None
                    except Exception:
                        result[field] = None
                else:
                    result[field] = value
                break

    print(f"[parse_collect] result:\n{json.dumps(result, ensure_ascii=False, indent=2)}")
    return result
def build_skeleton_prompt(base_prompt: str, context_dict: dict, disease_doc: dict) -> str:
    """
    Inject context_dict và disease_doc vào CREATE_SKELETON.txt.
    base_prompt: nội dung file CREATE_SKELETON.txt (chưa replace gì).
    """


    # Build phần tài liệu tham khảo từ disease_doc
    doc_lines = []

    if disease_doc.get("template_ke_hoach"):
        doc_lines.append("### Thứ tự giai đoạn gợi ý theo mức độ bệnh:")
        for phase_name in disease_doc["template_ke_hoach"]:
            doc_lines.append(f"- {phase_name}")

    if disease_doc.get("thu_vien_phase"):
        doc_lines.append("\n### Thư viện giai đoạn tham khảo:")
        for p in disease_doc["thu_vien_phase"]:
            actions = ", ".join(p.get("hanh_dong_chinh", []))
            doc_lines.append(
                f"- {p['ten_phase']}: {p['muc_tieu']}. Hành động: {actions}. Kết quả: {p['ket_qua_mong_doi']}"
            )

    if disease_doc.get("muc_tieu_dieu_tri"):
        doc_lines.append("\n### Mục tiêu điều trị:")
        for m in disease_doc["muc_tieu_dieu_tri"]:
            doc_lines.append(f"- {m}")

    if disease_doc.get("luu_y_rice_stage"):
        doc_lines.append("\n### Lưu ý theo giai đoạn lúa:")
        for note in disease_doc["luu_y_rice_stage"]:
            doc_lines.append(f"- {note}")

    if disease_doc.get("weather_notes"):
        doc_lines.append("\n### Ảnh hưởng thời tiết:")
        for note in disease_doc["weather_notes"]:
            doc_lines.append(f"- {note}")

    if disease_doc.get("weather_actions"):
        doc_lines.append("\n### Hành động theo thời tiết:")
        for action in disease_doc["weather_actions"]:
            doc_lines.append(f"- {action}")

    if disease_doc.get("luu_y_giong_lua"):
        doc_lines.append("\n### Lưu ý theo giống lúa:")
        for note in disease_doc["luu_y_giong_lua"]:
            doc_lines.append(f"- {note}")

    if disease_doc.get("chi_so_danh_gia"):
        doc_lines.append("\n### Chỉ số đánh giá hoàn thành:")
        for chi_so in disease_doc["chi_so_danh_gia"]:
            doc_lines.append(f"- {chi_so}")

    context_doc = "\n".join(doc_lines) if doc_lines else "Chưa có tài liệu tham khảo."

    prompt = (
        base_prompt
        .replace("{plan_context}", json.dumps(context_dict, ensure_ascii=False, indent=2))
        .replace("{context}", context_doc)
    )
    return prompt


REQUIRED_FIELDS = [
    "disease",
    "location",
    "duration_days",
    "rice_stage",
    "disease_scale",
    "disease_duration",
    "disease_severity",
    "rice_variety",
    "current_medicine",
    "weather_description",
]


EMPTY_VALUES = {"none", "null", "", "chưa rõ", "chưa cung cấp", "chưa có"}

def is_collect_complete(context_dict: dict) -> bool:
    for field in REQUIRED_FIELDS:
        value = context_dict.get(field)
        if value is None:
            return False
        if isinstance(value, str) and value.strip().lower() in EMPTY_VALUES:
            return False
    return True

def create_skeleton(llm_client, context_dict: dict, prompt: str) -> list:
    response = llm_client._llm.invoke([
        {"role": "system", "content": prompt},
        {"role": "user", "content": "Sinh skeleton kế hoạch."},
    ])
    raw = response.content.strip().replace("```json", "").replace("```", "").strip()
    skeleton = json.loads(raw)
    print(f"[create_skeleton]:\n{json.dumps(skeleton, ensure_ascii=False, indent=2)}")
    return skeleton


class PlanningAgent:

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def _load_prompt(self, path: str, state: State , query) -> str:
        with open(path, "r", encoding="utf-8") as f:
            template = f.read()

        # history 
        # history_msgs = list(state.get("history", []))[-6:]
        # history_text = "\n".join(
        #     f"{'Người dùng' if m.type == 'human' else 'Bot'}: {m.content}"
        #     for m in history_msgs
        # ) or "Chưa có lịch sử."

        messages = state.get("messages", [])

        history_text = "\n".join(
            f"{'\nNgười dùng: ' if m.type == 'human' else '\nHệ thống: '}: {m.content}"
            for m in messages[:-1][-6:]
        ) or "Chưa có lịch sử."

        user_memory = state.get("user_memory")
        user_memory_text = "Chưa có thông tin."
        if user_memory:
            data = user_memory if isinstance(user_memory, dict) else user_memory.model_dump()
            user_memory_text = "\n".join(
                f"- {k}: {v}" for k, v in data.items()
                if v and k not in ["user_id", "thread_id", "updated_at"]
            ) or "Chưa có thông tin."

        return (
            template
            .replace("{history_text}", history_text)
            .replace("{user_memory}", user_memory_text)
            .replace("{query}", query)
        )



    def __call__(self, state: State) -> dict:
        print("============= PLANNING_Agent =============")

        query_extract = state.get("query_extract")
        if isinstance(query_extract, dict):
            query_extract = query_extract["query_extract"]
        query = query_extract.query_clear

        prompt_collect = self._load_prompt(COLLECT_INFO_PROMPT_PATH , state , query)
        print("="*30)
        # print(f"[prompt_collect]:\n{prompt_collect}")
 

        collect_result = collect_info(
            llm_client=self.llm_client,
            state=state,
            prompt=prompt_collect,
            query=query
        )

        response_collect = collect_result.content

        summary_result  = summary_conver(llm_client = self.llm_client, query= query, response =response_collect) 

        current_history = list(state.get("history", []))
        new_pair = [
            HumanMessage(content=query),
            AIMessage(content=summary_result if summary_result else ""),
        ]
        updated_history = (current_history + new_pair)[-6:]

 
        context_dict = parse_collect_to_context(response_collect)
        print("="*30)
        print(f"context_dict : {context_dict}")

        collect_tools = is_collect_complete(context_dict)
        print("="*30)
        # print(f"collect_tools : {collect_tools}")

        if collect_tools:
            print("============================== đủ trường ===============================\n"*5)
            print("="*30)
            disease_doc = load_disease_doc(context_dict)
            with open(CREATE_SKELETON_PROMPT_PATH, "r", encoding="utf-8") as f:
                skeleton_base = f.read()
            final_skeleton_prompt = build_skeleton_prompt(skeleton_base, context_dict, disease_doc)
            # print(f"[final_skeleton_prompt]:\n{final_skeleton_prompt}")
   


            skeleton = create_skeleton(self.llm_client, context_dict, final_skeleton_prompt)
            # result_skeleton = json.dumps(skeleton, ensure_ascii=False, indent=2)
            # print("="*30)
            # print(f"[result_skeleton] \n {result_skeleton}")
            # return {
            #     "messages": [AIMessage(content=response_collect)],
            #     "history": updated_history
            # }


            user_memory = state.get("user_memory")
            plan = Plan(
                plan_id=str(uuid.uuid4()),
                # user_id=user_memory.user_id if user_memory else "unknown",
                # thread_id=user_memory.thread_id if user_memory else "unknown",
                user_id="user_id",
                thread_id="thread_id",
                disease=context_dict["disease"],
                duration_days=context_dict["duration_days"],
                location=context_dict.get("location"),
                rice_stage=context_dict.get("rice_stage"),
                status="skeleton",
                skeleton=[SkeletonPhase(**p) for p in skeleton],
                steps=[],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
            )
            print("="*30)
            print(" ================================== plan 2 json ================================== ")
            plan2 = json.dumps(plan.model_dump(), ensure_ascii=False, indent=2)
            print(f"plan2 json : \n {plan2}")

            plan_dict = plan.model_dump()
            plan_dict = fill_detail(self.llm_client, context_dict, plan_dict)
            print(" ================================== plan_dict ==================================")
            
            print(f"plan_dict : \n{plan_dict}")

            return {
                "messages":     [AIMessage(content=response_collect)],
                "history":      updated_history,
                "current_plan": plan_dict,
            }

        return {
            "messages": [AIMessage(content=response_collect)],
            "history": updated_history
        }



