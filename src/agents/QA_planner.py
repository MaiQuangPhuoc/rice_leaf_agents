import json
import logging
from multiprocessing import get_context
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# from pathlib import Path
# from typing import Type, Union
from langchain.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
# from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
# from pydantic import BaseModel
from src.clients.llm import LLMClient
from state import State, get_id_plan , QAResponse
from langchain_core.tools import tool
# from langgraph.prebuilt import ToolNode
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import END
from langgraph.prebuilt import ToolNode, tools_condition
logger = logging.getLogger(__name__)
from langgraph.graph import MessagesState, StateGraph
from src.tools.tool import get_id_tools
from src.configs import env_config
  

# collect_tool = create_parser_output_tool(
#     llm_client=LLMClient(model=env_config.model, api_provider=env_config.api_provider),
#     state=MiniTestState
# )


tool_get_id = get_id_tools(
    llm_client=LLMClient(model=env_config.model, api_provider=env_config.api_provider),
    state=get_id_plan
)


class QAPromptBuilder:
    """Agent responsible for collecting and managing user learning mini_test."""

    def __init__(self):
        with open(r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\src.agents.qa_planner.call.sp.get_id.txt","r", encoding="utf-8") as file:
            self._prompt_template = file.read()

        with open(r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\src.agents.qa_planner.call.um.get_id.txt","r", encoding="utf-8") as file:
            self._user_message_template = file.read()

        # prompt_final
        with open(r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\src.agents.qa_planner.call.sp.txt","r", encoding="utf-8") as file:
            self._prompt_template_final = file.read()

        with open(r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\src.agents.qa_planner.call.um.txt","r", encoding="utf-8") as file:
            self._user_message_template_final = file.read()

    def build_final(self, state: State):
        # conversation_messages = [
        #     msg.content
        #     for msg in state["messages"]
        #     # if msg.type in ("human", "ai")
        #     if msg.type in "human"

        # ]
        # text = "\n".join(conversation_messages)

        human_messages = [msg.content for msg in state["messages"] if msg.type == "human"]

        # Lấy list chỉ chứa message cuối cùng
        conversation_messages = [human_messages[-1]] if human_messages else []

        text = "\n".join(conversation_messages)


        plan_data = state.get("plan_data")
        # if plan_data:
        #     print("plan_data OK ")

        user_message = self._user_message_template_final.format(
            qa_user=text,
            plan_data = plan_data
        )


        system_message = self._prompt_template_final

        return [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ]
    

    def build(self, state: State):
        conversation_messages = [
            msg.content
            for msg in state["messages"]
            if msg.type in ("human", "ai")
        ]
        text = "\n".join(conversation_messages)

 
        user_message = self._user_message_template.format(
            qa_user=text
            # plan_data=plan_data   
        )

        system_message = self._prompt_template

        return [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ]

class QAPlanner:

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client 
        self.prompt_builder = QAPromptBuilder()

    def __call__(self, state: State):

        print("============= call__start_QA_plan =============\n"*5)
        # return state

        try:

            def chat(state: State):
                print("=============chat is runing============")
                llm_with_tools = self.llm_client._llm.bind_tools([tool_get_id])

                prompt = self.prompt_builder.build(state)  
                # print("\nPrompt QA: ", prompt)            
             
                response = llm_with_tools.invoke(prompt)

                # print("\nresponse: ", response)

                return {"messages": [response]}
            
            tools = ToolNode([tool_get_id])
     
            def gen_id(state: State):
                print("\n=============== gen ID is running===================.")
                recent_tool_messages = []
                for message in reversed(state["messages"]):
                    if message.type == "tool":
                        recent_tool_messages.append(message)
                    else:
                        break
                tool_messages = recent_tool_messages[::-1]
                last_tool_msg = tool_messages[-1]
                
                if not last_tool_msg.artifact:
                    return{
                        "messsages":"artifact none"
                    }
                
                return {
                    "plan_id":last_tool_msg.artifact
                }

            def get_plan(state: State):
                print("\n===============get_plan review is running===================.")

                # plan_id_raw = state.get("plan_id")
                plan_id_raw: get_id_plan = state.get("plan_id")
                # id = plan_id_raw.id
                plan_id = plan_id_raw.id
                # print("plan_id:", plan_id)
                # print("id:", id)

                if not plan_id:
                    return {"qa_planner_completed": False}

                file_path = os.path.join("plans", f"{plan_id}.json")
                
                if not os.path.exists(file_path):
                    print(f"⚠️ Không tìm thấy file {file_path}")
                    return {
                        "plan_data": None,
                        "messages": [AIMessage(content="id kế hoạch không tồn tại, nhập lại")]
                    }

                with open(file_path, "r", encoding="utf-8") as f:
                    plan_data = json.load(f)

                return {
                    "plan_data": plan_data, 
                    "messages": [AIMessage(content=f"kế hoạch {plan_id} đã sẵn sàng")]

                }
            

            async def chat_QA(state:State):
                print("\n=============== chat_QA review is running ===================.")
      
                
                prompt = self.prompt_builder.build_final(state)
                # print("prompt_chat_QA: ", prompt)
                res = await self.llm_client.ainvoke_with_retries(
                    prompt=prompt, output_model=QAResponse
                )
                # response = res.answers.answer

                # Nếu chỉ cần câu trả lời đầu tiên
                response = res.answers[0].answer

                # Nếu muốn nối tất cả câu trả lời
                response = "\n".join([item.answer for item in res.answers])


                if response:
                    print("\n chat_QA_response :" , response)
                else:
                    print("chat_QA_response in none")
                        
                # response = self.llm_client._llm.invoke(prompt)
                return {
                    "messages": [AIMessage(content=f"{response}")]
                }
            
                    # "messages": [AIMessage(content=f"kế hoạch [response] đã sẵn sàng")]

                # return {
                #     "qa_planner_completed": True 
                # }
                
            def entry_router(state: State):
                """Router node - phải return dict"""
                # Không return string, chỉ pass state through
                return state  # hoặc return {"messages": state.get("messages", [])}

            def route_condition(state: State):
                """Conditional function để routing"""
                # Nếu đã có kế hoạch và id thì vào thẳng chat_QA
                if state.get("plan_id") and state.get("plan_data"):
                    return "chat_QA"
                return "chat"  # chưa có thì đi flow chuẩn

            # Graph setup
            graph_builder = StateGraph(State)

            # Add router node
            graph_builder.add_node("entry_router", entry_router)
            graph_builder.add_node("chat", chat)
            graph_builder.add_node("tools", tools)
            graph_builder.add_node("gen_id", gen_id)
            graph_builder.add_node("get_plan", get_plan)
            graph_builder.add_node("chat_QA", chat_QA)

            # Entry point
            graph_builder.set_entry_point("entry_router")

            # ✅ Sử dụng route_condition cho conditional edges
            graph_builder.add_conditional_edges(
                "entry_router",
                route_condition,  # function riêng cho routing logic
                {"chat": "chat", "chat_QA": "chat_QA"}
            )

            # Các edges khác giữ nguyên
            graph_builder.add_conditional_edges(
                "chat",
                tools_condition,
                {END: END, "tools": "tools"},
            )

            graph_builder.add_edge("tools", "gen_id")

            graph_builder.add_conditional_edges(
                "gen_id",
                lambda state: "get_plan" if state.get("plan_id") else END,
                {END: END, "get_plan": "get_plan"},
            )

            graph_builder.add_conditional_edges(
                "get_plan",
                lambda state: "chat_QA" if state.get("plan_data") else END,
                {END: END, "chat_QA": "chat_QA"},
            )

            graph_builder.add_edge("chat_QA", END)
          

                


            
            # def run_gen(state: State):
            #     if state.get("plan_id"):
            #         return "get_plan"
            #     return END
            

            # def run_chat_QA(state: State):
            #     if state.get("plan_data"):
            #         return "chat_QA"
            #     return END




            # graph_builder = StateGraph(State)
            # graph_builder.add_node(chat)
            # graph_builder.add_node(tools)
            # graph_builder.add_node(gen_id)
            # graph_builder.add_node(get_plan)
            # graph_builder.add_node(chat_QA)



            # graph_builder.set_entry_point("chat")
            # graph_builder.add_conditional_edges(
            #     "chat",
            #     tools_condition,
            #     {END: END, "tools": "tools"},
            # )

            # graph_builder.add_edge("tools", "gen_id")

            # graph_builder.add_conditional_edges(
            #     "gen_id",
            #     run_gen,
            #     {END: END, "get_plan": "get_plan"},
            # )

            # graph_builder.add_conditional_edges(
            #     "get_plan",
            #     run_chat_QA,
            #     {END: END, "chat_QA": "chat_QA"},
            # )

            # graph_builder.add_edge("chat_QA", END)


            graph = graph_builder.compile(checkpointer=MemorySaver())
            return graph  
        except Exception as e:
            raise RuntimeError(f"QA failed: {e}")

# class QAPlanner:

#     def __init__(self, llm_client: LLMClient):
#         self.llm_client = llm_client
#         self.prompt_builder = QAPromptBuilder()

#     def __call__(self, state: State):

#         print("============= call__start_QA =============")

#         def get_plan_flow(state: State):
#             # Nếu đã có plan_id + plan_data thì bỏ qua
#             if state.get("plan_id") and state.get("plan_data"):
#                 print("➡️ Bỏ qua get_plan_flow vì đã có plan_id + plan_data")
#                 return state

#             print("=== get_plan_flow running ===")
#             llm_with_tools = self.llm_client._llm.bind_tools([tool_get_id])

#             # 1. chat để trích xuất ID
#             prompt = self.prompt_builder.build(state)
#             response = llm_with_tools.invoke(prompt)

#             print("response: ", response)
#             state["messages"].append(response)

#             # 2. lấy artifact (plan_id)
#             last_tool_msg = next((m for m in reversed(state["messages"]) if m.type == "tool"), None)
#             if not last_tool_msg or not last_tool_msg.artifact:
#                 return {"messages": [AIMessage(content="❌ Không trích xuất được ID kế hoạch.")]}

#             plan_id = last_tool_msg.artifact.id
#             print("plan_id:", plan_id)

#             # 3. check file tồn tại
#             file_path = os.path.join("plans", f"{plan_id}.json")
#             if not os.path.exists(file_path):
#                 return {
#                     "messages": [AIMessage(content=f"❌ Không tìm thấy kế hoạch với id {plan_id}")]
#                 }

#             # 4. load plan
#             with open(file_path, "r", encoding="utf-8") as f:
#                 plan_data = json.load(f)

#             return {
#                 "plan_id": plan_id,
#                 "plan_data": plan_data,
#                 "messages": [AIMessage(content=f"✅ Kế hoạch {plan_id} đã sẵn sàng")]
#             }

#         def chat_QA(state: State):
#             print("=== chat_QA running ===")

#             if not state.get("plan_data"):
#                 return {"messages": [AIMessage(content="⚠️ Chưa có kế hoạch nào để hỏi đáp.")]}

#             prompt = self.prompt_builder.build_final(state)
#             response = self.llm_client._llm.invoke(prompt)

#             return {"messages": [response]}

#         def run_chat_QA(state: State):
#             if state.get("plan_id") and state.get("plan_data"):
#                 return "chat_QA"
#             return END

#         # --- GRAPH ---
#         graph_builder = StateGraph(State)
#         graph_builder.add_node(get_plan_flow)
#         graph_builder.add_node(chat_QA)

#         graph_builder.set_entry_point("get_plan_flow")

#         # Sau khi get_plan_flow xong, chỉ khi có đủ plan_id + plan_data mới chạy QA
#         graph_builder.add_conditional_edges(
#             "get_plan_flow",
#             run_chat_QA,
#             {END: END, "chat_QA": "chat_QA"},
#         )

#         graph_builder.add_edge("chat_QA", END)

#         graph = graph_builder.compile(checkpointer=MemorySaver())
#         return graph