import json
import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from pathlib import Path
from typing import Type, Union
from langchain.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
from src.clients.llm import LLMClient
from src.state1 import State, AgentProfile 
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langchain.schema import HumanMessage , AIMessage, SystemMessage
from langgraph.graph import END
from langgraph.prebuilt import ToolNode, tools_condition
logger = logging.getLogger(__name__)
from langgraph.graph import MessagesState, StateGraph
from src.tools.tool import create_parser_output_tool
from src.configs import env_config


collect_profile = create_parser_output_tool(
    llm_client=LLMClient(model=env_config.model, api_provider=env_config.api_provider),
    state=AgentProfile
)
class ProfileCollectorPromptBuilder:
    """Builds prompts for the profile collector agent."""
    
    def __init__(self):
        with open(r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\router_sp.txt", "r",encoding="utf-8") as file:
            self._prompt_template = file.read()

        with open(r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\router_up.txt", "r", encoding="utf-8") as file:
            self._user_message_template = file.read()
    def build(self, state : State) :

        # print("-----build--profile--prompt-----")
        user_message =""
        # user_message = self._user_message_template
       
        messages = [
            {"role": "system", "content": self._prompt_template},
            {"role": "user", "content": user_message},
        ]

        return ChatPromptTemplate.from_messages(messages)
    
class ProfileCollector:
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client 
        self.prompt_builder = ProfileCollectorPromptBuilder()

    def __call__(self, state: State) -> dict:

        print("============= call__start_profile =============\n"*4)
        # return state
        # return{
        #     "profile_completed": True
        # }


        if state is None:
            state = State

        if state.get("profile_completed", False):
            # print("✅ profile ✅")
            return state
        
        # print("============= call__start__profile =============\n"*4)

        try:
            systemPrompt = self.prompt_builder.build(state)  
            # print("profie is runing...")

            def chat(state: State):
                print("=============chat is runing============")
                llm_with_tools = self.llm_client._llm.bind_tools([collect_profile])

                conversation_messages = [
                    message.content
                    for message in state["messages"]
                    if message.type in ("human")

                    # if message.type in ("human", "system")
                    or (message.type == "ai" and not message.tool_calls)
                ]

                prompt = ([SystemMessage(content=systemPrompt.format())] if systemPrompt else []) + conversation_messages
                response = llm_with_tools.invoke(prompt)
                print("\response:", response)


                return {"messages": [response]}
            
            tools = ToolNode([collect_profile])
     
            def generate(state: State):
                print("\n===============generate is running===================.")
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
                    "profile_user":last_tool_msg.artifact,
                    "profile_completed":True,
                    "messages":[AIMessage(content="✅ profile_agent_done ✅")],
                    "ok":"male"
                }




            graph_builder = StateGraph(State)
            graph_builder.add_node(chat)
            graph_builder.add_node(tools)
            graph_builder.add_node(generate)

            graph_builder.set_entry_point("chat")
            graph_builder.add_conditional_edges(
                "chat",
                tools_condition,
                {END: END, "tools": "tools"},
            )
            graph_builder.add_edge("tools", "generate")
            graph_builder.add_edge("generate", END)

            graph = graph_builder.compile(checkpointer=MemorySaver())
            return graph        
            
        except Exception as e:
            logger.error(f"Error executing profile collector: {e}")
            raise RuntimeError(f"Profile collection failed: {e}")



if __name__ == "__main__":
    llm_client = LLMClient(model=env_config.model, api_provider=env_config.api_provider)
    # Khởi tạo state ban đầu
    state: State = {
        "messages": [],
        "profile_user": None,
        "profile_completed": False,
        "ok":""
    }

    agent = ProfileCollector(llm_client)
    profile_agent = agent(State)


    print("=== Bắt đầu hội thoại với hệ thống ===")
    while True:
        user_input = input("Bạn: ")
        state["messages"].append(HumanMessage(content=user_input))  # Thêm tin nhắn người dùng vào state
        
        if user_input.strip().lower() in ["exit", "quit", "q"]:
            break

        response = profile_agent.invoke(
            state,
            config=RunnableConfig(configurable={"thread_id": "test_thread"})
        )

        # Cập nhật state với phản hồi từ AI
        ai_reply = response["messages"][-1].content if isinstance(response, dict) else response
        state["messages"].append(AIMessage(content=ai_reply))  # Thêm tin nhắn AI vào state

        # Cập nhật các trường khác từ phản hồi
        if isinstance(response, dict):
            for key in ["profile_user", "profile_completed", "ok"]:
                if key in response:
                    state[key] = response[key]

        print(f"Hệ thống: {ai_reply}")

        # # In toàn bộ state
        # for k, v in state.items():
        #     print(f"{k}: {v}\n")

