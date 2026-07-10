from ast import List
import logging
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import re
from langgraph.graph import END, StateGraph
from langchain_core.messages import SystemMessage, HumanMessage
# from langgraph.graph import MessagesState
from src.clients.llm import LLMClient
from state import State ,FeedbackResult, StudyPlanDetail
# from src.clients.databases import qdrant
# from src.state import State, StudyPlanDetail 
from src.tools.tool import   create_daily_tool , review_tools
# from src.agents.overview_planner import OverViewPlanner
# from langchain.schema import AIMessage
# from sentence_transformers import CrossEncoder
# from datetime import datetime
from src.configs import env_config
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver


# daily_tool = create_daily_tool(
#     llm_client=LLMClient(model=env_config.model, api_provider=env_config.api_provider),
#     state=DailyInfo
# )



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


        # finlal prompt
        with open(r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\src.agents.review_planner.call.sp.txt","r", encoding="utf-8") as file:
            self._system_prompt_final = file.read()

        with open(r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\src.agents.review_planner.call.um.txt","r", encoding="utf-8") as file:
            self._user_message_template_final  = file.read()

    def build_prompt_final(self, state: State):

        study_details_result = state.get("study_details_result", {})

        system_message = self._system_prompt_final.format(
            study_details_result=study_details_result
        )


        review_user = state.get("review_user", {})


        # human_message = self._user_message_template_final.format(
        #     review_user=review_user
        # )
        human_message = self._user_message_template_final.replace("{review_user}", str(review_user))



        return [
            SystemMessage(content=system_message),
            HumanMessage(content=human_message)
        ]

    def build(self, state: State):

        conversation_messages = [
            msg.content
            for msg in state["messages"]
            # if msg.type == "human"
            if msg.type in ("human", "ai")
        ]
        feedback_text = "\n".join(conversation_messages)


        # study_details_result = state.get("study_details_result", {})

        # system_message = self._system_prompt.format(
        #     study_details_result=study_details_result
        # )
 

        user_message = self._user_message_template.format(
            review_user=feedback_text
        )

        return [
            SystemMessage(content=self._system_prompt),
            HumanMessage(content=user_message)
        ]



class ReviewPlanner:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.prompt_builder = ReviewPlannerPromptBuilder()
    
    def __call__(self, state: State) -> dict:

        print("============= call__start_review =============\n"*4)
        # return {
        #     "flow": "2"
        # }




        if state is None:
            state = State

        if state.get("review_completed", False):
            # print("✅ review ✅")
            return state
        
        print("============= call__start_review =============\n")

        try:
            def chat(state: State):
                print("=============chat review is runing============")
                llm_with_tools = self.llm_client._llm.bind_tools([review_tool])

                prompt = self.prompt_builder.build(state)  
                # print("\nPrompt base: ", prompt)            
             
                response = llm_with_tools.invoke(prompt)

                return {"messages": [response]}
            
            tools = ToolNode([review_tool])
     
            def create_feedback(state: State):
                print("\n===============create_prompt review is running===================.")
                recent_tool_messages = []
                for message in reversed(state["messages"]):
                    if message.type == "tool":
                        recent_tool_messages.append(message)
                    else:
                        break
                tool_messages = recent_tool_messages[::-1]
                last_tool_msg = tool_messages[-1]
                
                print("last_tool_msg.artifact")
                print(last_tool_msg.artifact)


                if not last_tool_msg.artifact:
                    return{
                        "messsages":"artifact none"
                    }
                


                
                return {
                    "review_user":last_tool_msg.artifact
                }
            
            async def generate(state: State):
                print("\n===============generate reiew is running===================.")

                final_prompt = self.prompt_builder.build_prompt_final(state)
                # print("\nfinal_prompt :", final_prompt)

                response = await self.llm_client.ainvoke_with_retries(
                    prompt=final_prompt, output_model=StudyPlanDetail
                )

                if response:
                    print("\n review response :" , response)

                    return {
                        "review_result":response,
                        "review_completed":True,
                        "flow": "2"
                    }                    
                else:
                    print("review response in none")


            
            def run_gen(state: State):
                if state.get("review_user"):
                    return "generate"
                return END




            graph_builder = StateGraph(State)
            graph_builder.add_node(chat)
            graph_builder.add_node(tools)
            graph_builder.add_node(create_feedback)
            graph_builder.add_node(generate)


            graph_builder.set_entry_point("chat")
            graph_builder.add_conditional_edges(
                "chat",
                tools_condition,
                {END: END, "tools": "tools"},
            )

            graph_builder.add_edge("tools", "create_feedback")

            graph_builder.add_conditional_edges(
                "create_feedback",
                run_gen,
                {END: END, "generate": "generate"},
            )

            graph_builder.add_edge("generate", END)

            graph = graph_builder.compile(checkpointer=MemorySaver())
            return graph        
            
        except Exception as e:
            # logger.error(f"Error executing profile collector: {e}")
            raise RuntimeError(f"Profile collection failed: {e}")
