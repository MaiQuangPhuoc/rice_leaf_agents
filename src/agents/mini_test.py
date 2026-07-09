import json
import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# from pathlib import Path
# from typing import Type, Union
from langchain.prompts import ChatPromptTemplate
# from langgraph.checkpoint.memory import MemorySaver
# from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
# from pydantic import BaseModel
from src.clients.llm import LLMClient
from state import State
from langchain_core.tools import tool
# from langgraph.prebuilt import ToolNode
# from langchain.schema import HumanMessage , AIMessage, SystemMessage
from langgraph.graph import END
# from langgraph.prebuilt import ToolNode, tools_condition
logger = logging.getLogger(__name__)
# from langgraph.graph import MessagesState, StateGraph
# from src.tools.tool import create_parser_output_tool
# from src.configs import env_config
  

# collect_tool = create_parser_output_tool(
#     llm_client=LLMClient(model=env_config.model, api_provider=env_config.api_provider),
#     state=MiniTestState
# )

class MiniTestPromptBuilder:
    """Agent responsible for collecting and managing user learning mini_test."""

    def __init__(self):
        with open(r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\mini_test_sp.txt", "r",encoding="utf-8") as file:
            self._prompt_template = file.read()

        with open(r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\mini_test_up.txt", "r", encoding="utf-8") as file:
            self._user_message_template = file.read()

    def build(self, state : State) :
        user_message = ""

        messages = [
            {"role":"system", "content":self._prompt_template},
            {"role":"user", "content":user_message}
        ]
       
        return ChatPromptTemplate.from_messages(messages)

class MiniTestPlanner:

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client 
        self.prompt_builder = MiniTestPromptBuilder()

    def __call__(self, state: State):

        print( "=================== start__mini_test ===================\n"*4)
        return state

        # if state is None:
        #     print('state none')

        # try:
        #     prompt_template = self.prompt_builder.build(state)
                    
        #     def chat(state: MiniTestState):
        #         llm = self.llm_client._llm.bind_tools([collect_tool])
        #         messages = [
        #             message for message in state["messages"]
        #             if message.type in ("human", "system") or (message.type == "ai" and not message.tool_calls)
        #         ]
        #         prompt = [SystemMessage(content=prompt_template.format(**state))] + messages
        #         response = llm.invoke(prompt)
                
        #         # print('-' * 40)
        #         # print(response)
        #         # print('-' * 40)

        #         return {"messages": [response]}
            
        #     tools = ToolNode([collect_tool])

        #     def generate(state: MiniTestState):
        #         # print("state_messages :" , state['messages'])
        #         # print('-' * 30)
        #         recent_tool_messages = []
        #         for message in reversed(state["messages"]):
        #             if message.type == "tool":
        #                 recent_tool_messages.append(message)
        #                 print('recent_tool_message:' , recent_tool_messages)
        #             else:
        #                 break
        #         tool_messages = recent_tool_messages[::-1]
        #         print('tool_message :' , tool_messages)

        #         last_tool_msg = tool_messages[-1]  

        #         print('last_tool_msg.artifact' , last_tool_msg.artifact)

        #         return {"minitest_user": last_tool_msg.artifact, "messages": "hoàn thành việc thu thập mini_test."}

        #     builder = StateGraph(MiniTestState)
        #     builder.add_node(chat)
        #     builder.add_node(generate)

        #     builder.set_entry_point("chat")
        #     builder.add_conditional_edges("chat", tools_condition, {END: END, "tools": "generate"})
        #     builder.add_edge("generate", END)

        #     return builder.compile(checkpointer=MemorySaver())
            
        # except Exception as e:
        #     logger.error(f"Error executing profile collector: {e}")
        #     raise RuntimeError(f"Profile collection failed: {e}")
