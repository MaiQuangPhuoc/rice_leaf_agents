import logging
import sys
import os
import json 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.state import State, extract_schema, query_transform_schema
import re
# print('oks')

# from pathlib import Path
# from typing import Type, Union
from langchain.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
# from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
from src.clients.llm import LLMClient
# from state import State
from langgraph.prebuilt import ToolNode, tools_condition

# from langchain_core.tools import tool
# from langgraph.prebuilt import ToolNode
from langchain.schema import HumanMessage , AIMessage, SystemMessage
from langgraph.graph import END
logger = logging.getLogger(__name__)
from langgraph.graph import MessagesState, StateGraph
from src.tools.tools import reprocessing_input, extract_tool, router_rule_based, artifact_to_plain_text,tools_query_transform
from src.configs import env_config
from langchain_core.messages import BaseMessage
from prompts.prompt import QUERY_TRANSFORM_PROMPT


tool_extract = extract_tool(
    llm_client=LLMClient(model=env_config.model, api_provider=env_config.api_provider),
    state=extract_schema
)


tool_query_transform = tools_query_transform(
    llm_client=LLMClient(model=env_config.model, api_provider=env_config.api_provider)
)

class RouterPromptBuilder:
    """Builds prompts for the profile collector agent."""
    
    def __init__(self):
        with open(r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\extract_prompt.txt", "r",encoding="utf-8") as file:
            self._extract_prompt = file.read()

        with open(r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\router_prompt.txt", "r", encoding="utf-8") as file:
            self.router_prompt = file.read()       

    def build_extract(self, state : State) :
        messages = [
            {"role": "system", "content": self._extract_prompt}
        ]
        return ChatPromptTemplate.from_messages(messages)
    
    def build_router(self, state : State) :
        messages = [
            {"role": "system", "content": self.router_prompt}
        ]
        return ChatPromptTemplate.from_messages(messages)
    
    # def build_query_transform_prompt(self, conversation_text, query):
    #     return QUERY_TRANSFORM_PROMPT.format(conversation_text=conversation_text ,query=query) 
    
class RouterAgent:
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client 
        self.prompt_builder = RouterPromptBuilder()
        self.reprocess_tool = reprocessing_input
        self.router_rule_base = router_rule_based
        self.artifact_to_plain_text = artifact_to_plain_text


    def __call__(self, state: State) -> dict:

        print(" ======================================= Router_Agent =======================================\n")

        try:

            THRESHOLD = 0.7

            def query_transform(state: State):
                print("\n=============== query_transform ===================."*2)
                user_message =  [msg.content for msg in state["messages"] if msg.type == "human"][-1]


                # history: list[BaseMessage] = state.get("history", [])
                # history_content = [msg.content for msg in history]

                # user_prompt = (
                #     f"Các cuộc trò chuyện gần đây\n\n{history_content}\n\n"
                #     f"Câu hỏi hiện tại : {user_message}\n"
                # )

                history: list[BaseMessage] = state.get("history", [])
                recent_history = history[-5:]

                history_content = [msg.content for msg in recent_history]

                formatted_history = "\n\n".join(block.strip() for block in history_content)


                user_prompt = (
                    f"Các cuộc trò chuyện gần đây:\n\n"
                    f"{formatted_history}\n\n"
                    f"Câu hỏi hiện tại: {user_message}"
                )

                print("user_prompt: ", user_prompt)  




                # messages: list[BaseMessage] = state.get("messages", [])
                # prev_human_messages = [m.content.strip() for m in messages if isinstance(m, HumanMessage)][-6:]

                # if not prev_human_messages:
                #     state["new_query"] = ""
                #     state["clarity_score"] = 0.0
                #     return state

                # query = prev_human_messages[-1]
                # conversation = prev_human_messages[:-1]
                # conversation_text = "\n".join(conversation) if conversation else "Không có."



                # if not conversation_text:
                #     return state

                # user_prompt = (
                #     f"Các câu hỏi gần nhất:\n{conversation_text}\n\n"
                #     f"vấn đề cần phân giải:\n{query}"
                # )

                system_message = QUERY_TRANSFORM_PROMPT

                # print("=== user_prompt ===")
                # print(user_prompt)
                # print("===   ===")

                prompt_format =  "\n".join([system_message, user_prompt])

                # prompt_format = self.prompt_builder.build_query_transform_prompt(
                #     QUERY_TRANSFORM_PROMPT,
                #     user_prompt
                # )

                # print("=== prompt_format ===")
                # print(prompt_format)

                response = self.llm_client._llm.invoke(prompt_format)
                # response_content = response.content
                # print("response_content : ", response_content)
                # print("=== query_transform response ===")   


                # llm_with_tools = self.llm_client._llm.bind_tools([tool_query_transform])

                # response = llm_with_tools.invoke(prompt_format)
                # artifact = response.artifact

                # print("response",response)
                # artifact  = response.artifact
                # print("=== query_transform artifact ===")
                # print(artifact) 

                # Parse JSON
                # print("=== Parsing JSON response ===")
                # data = json.loads(response.content)
                
             
                # new_query = data.get("new_query", "")
                # score = data.get("score", 0.0)
                # need = data.get("need_clarification", True)

               


                # # Logic trả kết quả cuối
                # if not need and score > 0.7:
                #     final_output = new_query
                # elif score < 0.7:
                #     final_output = "bạn nói rõ hơn được không?"
                # else:
                #     final_output = "Tôi chỉ hỗ trợ các vấn đề về vấn đề liên quan đến lúa"



                # # print("new_query:", new_query)
                # print("score:", score)
                # print("Chuyển chủ đề không  :", need)
                # print("new input :", final_output)

 
                return {
                    "query_transform": response.content.strip()
                }

            



            def chat_prompt(state: State) :            
                print("\n =============== Extract query =============== "*2)

                prompt_extract = self.prompt_builder.build_extract(state)
         
                # user_message =  [msg.content for msg in state["messages_query_transform"] if msg.type == "human"][-1]
                # print("user_message:", user_message)
                # up_0 = self.reprocess_tool(user_message)
                # up = up_0["clean_text"]    

                
                new_input = state["query_transform"]
                print("new_input : ",new_input)
                sp_e = prompt_extract.format()

                prompt = sp_e + new_input

                llm_with_tools = self.llm_client._llm.bind_tools([tool_extract])
                response = llm_with_tools.invoke(prompt)

                # print("\n=============== chat_prompt response ===================.")
                # print(response)

                return {"messages": [response]}
        

            tools = ToolNode([tool_extract])
            
            def create_extract(state: State):
                # print("\n=============== create_extract ===================.")
                recent_tool_messages = []
                for message in reversed(state["messages"]):
                    if message.type == "tool":
                        recent_tool_messages.append(message)
                    else:
                        break
                tool_messages = recent_tool_messages[::-1]
                last_tool_msg = tool_messages[-1]
                    
                # print("create_extract last_tool_msg.artifact")
                # print(last_tool_msg.artifact)

                return {
                    "extract":last_tool_msg.artifact
                }
            
            def router(state: State):
                print("\n =============== Router =============== "*2)
                # pronpt
                prompt_router = self.prompt_builder.build_router(state)
                sp_r = prompt_router.format()
                
                # extract
                artifact_extract = state.get("extract", {})
                artifact_text = artifact_to_plain_text(artifact_extract)


                prompt = sp_r + "\n" + artifact_text
                # print("prompt_router:", prompt)

                llm_response_router = self.llm_client._llm.invoke(prompt)

                llm_router = llm_response_router.content
                # print("llm_router : \n", llm_router)

                # Giả sử llm_router có dạng:
                # route: 1
                # reason: Người dùng hỏi về nguyên nhân bệnh đạo ôn trên lúa.

                # Tách 2 biến route và reason
                llm_route = None
                llm_reason = None

                for line in llm_router.split('\n'):
                    line = line.strip()
                    if line.startswith("route:"):
                        llm_route = line.split("route:")[1].strip()
                    elif line.startswith("reason:"):
                        llm_reason = line.split("reason:")[1].strip()

                reason = "Vấn đề bạn nói chưa phù hợp với lĩnh vực của tôi" + str(llm_reason or "")

                # Gọi hàm rule-based
                router_rule_based_result = self.router_rule_base(artifact_extract)
                print(f"rule base : {router_rule_based_result}")
                print(f"LLM : {llm_route}\n")

                try:
                    llm_route_int = int(llm_route)
                    router_rule_based_int = int(router_rule_based_result)
                except Exception:
                    # Nếu không parse được số, trả về False
                    return {"state_router": False, "messages": [AIMessage(content=reason)]}

                if llm_route_int == router_rule_based_int and llm_route_int in [0,1,2,3]:
                    return {"state_router": True, "route": llm_route_int}
                else:
                    return {"state_router": False, "messages": [AIMessage(content=reason)]}

                # llm_router = llm_response_router.content 
                # print("llm_router : \n",llm_router)

                # reason = "Vấn đề bạn nói chưa phù hợp với lĩnh vực của tôi vì " + str(reason_llm or "")
                 

                # # router_rule_base
                # router_rule_based = self.router_rule_base(artifact_extract)
                # print(f"rule base : {router_rule_based}")
                # print(f"LLM : {route_llm}")
     
                # if int(route_llm) == int(router_rule_based) == 1:
                #     return {"state_router": True, "route": 1}
                # elif int(route_llm) == int(router_rule_based) == 2:
                #     return {"state_router": True, "route": 2}
                # elif int(route_llm) == int(router_rule_based) == 3:
                #     return {"state_router": True, "route": 3}
                # else:
                #     return {"state_router": False,"messages": [AIMessage(content=reason)]}
 
            def run_router(state: State) -> bool:
                if state.get("extract") is None:
                    return END
                return "router"


            graph_builder = StateGraph(State)
            graph_builder.add_node(query_transform)
            graph_builder.add_node(chat_prompt)
            graph_builder.add_node(tools)
            graph_builder.add_node(create_extract)
            graph_builder.add_node(router)


            graph_builder.set_entry_point("query_transform")
            graph_builder.add_edge("query_transform", "chat_prompt")

            # graph_builder.add_conditional_edges(
            #     "query_transform",
            #     tools_condition,
            #     {END: END, "chat_prompt": "chat_prompt"},
            # )
            graph_builder.add_edge("chat_prompt", "tools")

            graph_builder.add_edge("tools", "create_extract")

            graph_builder.add_conditional_edges(
                "create_extract",
                run_router,
                {END: END, "router": "router"},
            )

            graph_builder.add_edge("router", END)

            graph = graph_builder.compile(checkpointer=MemorySaver())
            return graph 

        except Exception as e:
            raise RuntimeError(f"Profile collection failed: {e}")



