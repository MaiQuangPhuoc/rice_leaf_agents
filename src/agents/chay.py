from ast import List
import logging
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import re
from langgraph.graph import END, StateGraph
from langchain_core.messages import SystemMessage, HumanMessage
# from langgraph.graph import MessagesState
from src.clients.llm import LLMClient
from state import State ,FeedbackResult, ReviewFeedback
# from src.clients.databases import qdrant
# from src.state import State, StudyPlanDetail 
from src.tools.tool import review_tools, create_parser_output_tool
# from src.agents.overview_planner import OverViewPlanner
# from langchain.schema import AIMessage
# from sentence_transformers import CrossEncoder
# from datetime import datetime
from src.configs import env_config
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver




review_tool = review_tools(
    llm_client=LLMClient(model=env_config.model, api_provider=env_config.api_provider),
    state=FeedbackResult
)

class ReviewPlannerPromptBuilder:
    def __init__(self):
        # System prompt: vai trò của agent (không chứa data)
        with open(
            r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\src.agents.review_planner.call.sp.collect.txt",
            "r", encoding="utf-8"
        ) as file:
            self._system_prompt = file.read()

        # User prompt: khung chứa dữ liệu học viên + hội thoại
        with open(
            r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\src.agents.review_planner.call.um.collect.txt",
            "r", encoding="utf-8"
        ) as file:
            self._user_message_template = file.read()

    def build(self, state: State):
        study_details_result = state.get("study_details_result", {})

        conversation_messages = [
            msg.content
            for msg in state["messages"]
            if msg.type == "human"
        ]
        feedback_text = "\n".join(conversation_messages)

        # system_message = self._system_prompt.format(
        #     study_details_result=study_details_result
        # )

        user_message = self._user_message_template.format(
            feedback=feedback_text
        )

        return [
            SystemMessage(content=self._system_prompt),
            HumanMessage(content=user_message)
        ]


class ReviewPlanner:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.prompt_builder = ReviewPlannerPromptBuilder()

    async def __call__(self, state: State):
        if state.get("review_completed"):
            return state
        


            print("============= call__start__review =============\n")

        prompt = self.prompt_builder.build(state)
        print(f"Prompt ReviewPlanner:\n{prompt}\n")

        # def chat(): 
        #     llm_with_tools = self.llm_client._llm.bind_tools([review_tool])
        #     response = llm_with_tools.invoke(prompt)
        #     print(f"\n----------\nresponse: {response.content} -- type: {type(response)}")


        #     return {
        #         "messages": response
        #     }
        
        # tools = ToolNode([review_tool])

        # def create_prompt(state : State):
        #     recent_tool_messages = []
        #     for message in reversed(state["messages"]):
        #         if message.type == "tool":
        #             recent_tool_messages.append(message)
        #         else:
        #             break
        #     tool_messages = recent_tool_messages[::-1]
        #     last_tool_msg = tool_messages[-1]

        #     if not last_tool_msg.artifact:
        #         return{
        #             "messsages":"artifact none"
        #         }
            
        #     print(f"Last tool message.artifact : {last_tool_msg.artifact}")

            
            
        #     return {
        #         "feedbacks":last_tool_msg.artifact
        #     }
        
        # graph_builder = StateGraph(State)
        # graph_builder.add_node(chat)
        # graph_builder.add_node(tools)
        # graph_builder.add_node(create_prompt)

        # graph_builder.set_entry_point("chat")
        # graph_builder.add_conditional_edges(
        #     "chat",
        #     tools_condition,
        #     {END: END, "tools": "tools"},
        # )
        # graph_builder.add_edge("tools", "create_prompt")
        # graph_builder.add_edge("create_prompt", END)

        # graph = graph_builder.compile(checkpointer=MemorySaver())
        # return graph        




