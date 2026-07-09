from ast import List
import logging
import sys
import os

from pydantic_core import ValidationError
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.agents.profile_collector import ProfileCollector
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from src.agents.profile_collector import ProfileCollector
# from src.tools.tool import create_retrieve_tool
from state import State, AgentProfile , StudyPlanOverview
# from src.clients.databases import qdrant
from src.clients.llm import LLMClient
from langchain_core.runnables import RunnableConfig
from src.tools.tool import retrieve_tool
from langchain_core.documents import Document
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.clients.databases import qdrant
from src.modules.rag.retrievers import VectorStoreRetriever
from src.configs import env_config
from langchain_core.messages import AIMessage


class OverviewPlannerPromptBuilder:
    def __init__(self):
        with open(
            r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\src.agents.overview_planner.call.sp.txt",
            "r", encoding="utf-8"
        ) as file:
            self._prompt_template = file.read()

        with open(
            r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\src.agents.overview_planner.call.um.txt",
            "r", encoding="utf-8"
        ) as file:
            self._user_message_template = file.read()

    def build(self, state: State, context: str) -> List:
        print("overview_build_prompt:")

        profile: AgentProfile = state.get("profile_user")
        if profile is None:
            raise ValueError("Thiếu dữ liệu hồ sơ học tập (profile_user) trong state.")

        # Gộp các biến cần format
        variables = {
            "learning_goal": profile.learning_goal,
            "expected_result": profile.expected_result,
            "deadline": profile.deadline,
            "available_time": profile.available_time,
            "current_ability": profile.current_ability,
            "learning_obstacles": profile.learning_obstacles,
            "learning_preference": profile.learning_preference,
            "specific_topics_interest": profile.specific_topics_interest,
            "notes": profile.notes or "",
            "context": context,
            "plan_scope": profile.plan_scope
        }
        # Tạo prompt template
        user_message = self._user_message_template.format(**variables)

        return [
            SystemMessage(content=self._prompt_template),
            HumanMessage(content=user_message)
        ]


class OverViewPlanner:
    def __init__(self, llm_client: LLMClient, vector_store):
        self.llm_client = llm_client
        self.prompt_builder = OverviewPlannerPromptBuilder()
        self.retrieve = retrieve_tool(vector_store=vector_store, search_kwargs={"k": 1})

    async def __call__(self, state: State) -> StudyPlanOverview:
        print("\n[OverviewPlanner] __call__ is running")

       

        # Tạo truy vấn tìm kiếm chương trình học
        query = "nội dung chuẩn chương trình final_version_toan_10 "
        # query = "Khái quát nội dung chương trình version2_toan_10"



        docs = self.retrieve.invoke(query)

        

        # print("context:" , docs)

        
        context_text = self.format_docs(docs)

        # print("context đã format  :"  , context_text)

        # Gán context vào state để lưu (nếu cần dùng lại sau)
        state["retrieved_context"] = context_text

        # Tạo prompt với context rõ ràng
        messages = self.prompt_builder.build(state, context=context_text)


        # print("prompt format:" )
        # for msg in messages:
        #     print(f"{msg.type.upper()}:\n{msg.content}\n")


        # Gửi prompt đến LLM
        response = await self.llm_client.ainvoke_with_retries(
            prompt=messages,
            output_model=StudyPlanOverview
        )
        print('-'*40)
        print("response: " , response)
        print('-'*40)

        # if response:
        #     state["overview_result"] = response
        #     state["overview_completed"] = True
        #     state["messages"] = [AIMessage(content="✅ profile_agent_done ✅")]
        # else:
        #     state["overview_completed"] = False
        
        # return state

        if response:
            state["overview_result"] = response
            state["overview_completed"] = True
            return {
                **state,
                "messages": [AIMessage(content="✅ overview_agent_done ✅")],
            }
        else:
            state["overview_completed"] = False
            return state


    
    def format_docs(self, docs: list[Document]) -> str:
        """Chuyển đổi các Document thành đoạn văn bản mô tả chương trình học."""
        result = []
        for i, doc in enumerate(docs, 1):
            chapter = doc.metadata.get("chapter", "Chưa rõ chương")
            lesson = doc.metadata.get("lesson", "Chưa rõ bài")
            desc = doc.page_content.strip()
            result.append(
                # f"===== document {i} =====\n"
                # f"*** Chương: {chapter}\n"
                # f"*** Bài: {lesson}\n"
                f"*** Mô tả: {desc}\n"
                # f"{chapter} - {lesson}\n-----------------------------\n"
            )
        return "\n\n".join(result)



# logger = logging.getLogger(__name__)

# class OverviewPlannerPromptBuilder:
#     def __init__(self):
#         with open(r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\src.agents.overview_planner.call.sp.txt", "r", encoding="utf-8") as file:
#             self._prompt_template = file.read()

#         with open(r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\\src.agents.overview_planner.call.um.txt", "r", encoding="utf-8") as file:
#             self._user_message_template = file.read()


#     def build(self, state: State):
#         print("overview_build_prompt:")

#         profile: AgentProfile = state.get("profile_user")
#         if profile is None:
#             raise ValueError("Thiếu dữ liệu hồ sơ học tập (profile_user) trong state.")

#         context_text = state.get("retrieved_context", "")
#         if not context_text:
#             print("No context:")
#         else:
#             print("Có context:")

#         # Tạo nội dung prompt từ profile
#         variables = {
#             "learning_goal": profile.learning_goal,
#             "expected_result": profile.expected_result,
#             "deadline": profile.deadline,
#             "available_time": profile.available_time,
#             "current_ability": profile.current_ability, 
#             "learning_obstacles": profile.learning_obstacles,
#             "learning_preference": profile.learning_preference,
#             "specific_topics_interest": profile.specific_topics_interest,
#             "notes": profile.notes or "",
#             "context": context_text
#         }

#         for key, value in variables.items():
#             print(f"-----\n{key} = {value}")

#         user_message = self._user_message_template.format(**variables)

#         messages = [
#             {"role": "system", "content": self._prompt_template},
#             {"role": "user", "content": user_message},
#         ]

#         return ChatPromptTemplate.from_messages(messages)
    
# class OverViewPlanner:
#     def __init__(self, llm_client: LLMClient, vector_store : VectorStoreRetriever):
#         self.llm_client = llm_client
#         self.prompt_builder = OverviewPlannerPromptBuilder()
#         self.retrieve = retrieve_tool(vector_store=vector_store, search_kwargs={"k": 1})

#     async def __call__(self, state: State):

#         print("overview_planner: __call__ is running \n")
        
#         # profile_user: AgentProfile = state.get("profile_user")
#         # if profile_user is None:
#         #     raise ValueError("Thiếu dữ liệu hồ sơ học tập (profile_user) trong state.")
        
#         # query_parts = [
#         #     "chương trình toán 10",
#         #     profile_user.specific_topics_interest,
#         #     profile_user.current_ability or "",
#         #     profile_user.learning_obstacles or ""
#         # ]
#         # query = " ".join([part for part in query_parts if part.strip()])

#         query = "Chương trình toán 10"
#         docs = self.retrieve.invoke(query)
#         curriculum_text = self.format_docs(docs)
#         state["retrieved_context"] = curriculum_text
#         prompt = self.prompt_builder.build(state)

#         print("Prompt before formatting:", prompt)


#         # prompt1 = prompt.format()

#         # print("\nPrompt đã render:\n", prompt1)


#         response = await self.llm_client.ainvoke_with_retries(
#             prompt=prompt,
#             output_model=StudyPlanOverview
#         )
  
#         print("-", * 40)
#         print("Response từ LLM:", response)

#         return response


#     def format_docs(self, docs):
#         """Biến list Document thành text đẹp."""
#         result = []
#         for i, doc in enumerate(docs, 1):
#             chapter = doc.metadata.get("chapter", "No chapter")
#             lesson = doc.metadata.get("lesson", "No leson")
#             desc = doc.page_content.strip()
#             result.append(
#                 f"=====document {i}=====\n***chapter: {chapter}\n***lesson : {lesson}\n***Mô tả: {desc}\n"
#             )
#         return "\n\n".join(result)


# class OverViewPlanner:
#     def __init__(self, llm_client: LLMClient):
#         self.llm_client = llm_client 
#         self.prompt_builder = OverviewPlannerPromptBuilder()
    
#     def __call__(self, state : State):

#         # for key, value in state.items():
#         #     print(f"\n-----\n{key} = {value}")

#         print("-" * 50 )
#         print("overview_planner: __call__\n")

#         my_retriever = VectorStoreRetriever(
#             vector_store=qdrant,
#             search_kwargs={"k": 3}
#         )

#         # base_retriever = my_retriever.as_retriever()

#         # profile_user  : AgentProfile = state.get("profile_user")

#         # query = profile_user.specific_topics_interest
#         # print(f"Query for retrieval: {query}")

#         # docs = base_retriever.invoke(query)

#         # for i, doc in enumerate(docs, 1):
#         #     print(f"\n----- Documents {i} -----")
#         #     print(doc.page_content)
#         #     print("-" * 40)

#         profile_user : AgentProfile = state.get("profile_user")
#         if profile_user is None:
#             raise ValueError("Thiếu dữ liệu hồ sơ học tập (profile_user) trong state.")
#         query = profile_user.specific_topics_interest

#         docs = retrieve_tool(vector_store=qdrant,search_kwargs={"k":3}).invoke(query)

#         for i, doc in enumerate(docs, 1):
#             print(f"\n----- Documents {i} -----")
#             print(doc.page_content)
#             print("-" * 40)


#         prompt = self.prompt_builder.build(state)
#         print("Prompt đã render:\n", prompt.format())

#         return prompt
    

# class OverViewPlanner:
#     def __init__(self, llm_client: LLMClient):
#         self.llm_client = llm_client 
#         self.prompt_builder = OverviewPlannerPromptBuilder()
    
#     async def __call__(self, state):
#         # retrieve = create_retrieve_tool(
#         #     vector_db=qdrant,
#         #     retrieve_count=3,
#         # )
#         print(self.prompt_builder.build(state))
#         response = await self.llm_client.ainvoke_with_retries(
#             prompt=self.prompt_builder.build(state),
#             output_model=StudyPlanOverview
#         )

#         return response
