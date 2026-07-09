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


        if state.get("overview_completed", False):
            # print("✅ overview ✅")
            return state
        

        print("============= call__start__overview =============\n"*4)

        # return {
        #     "overview_completed": True,
        #     # "flow":"2",
        #     "overview_result": "study_modules=[StudyModule(module_name='Chương 2: Hàm số bậc nhất và bậc hai', lesson_titles=['Bài 3: Hàm số bậc hai'], objectives=['Nắm vững kiến thức về đồ thị, trục đối xứng, đỉnh và các tính chất của hàm số bậc hai.', 'Khảo sát, vẽ đồ thị và giải các dạng bài tập liên quan đến hàm số bậc hai để khắc phục điểm yếu.'], description='Chương này tập trung vào hàm số bậc hai, giúp học sinh củng cố nền tảng, khắc phục điểm yếu và chuẩn bị cho các dạng bài nâng cao.', resources=[Resource(type='video', url='youtube.com/playlist?list=hm_so_bac_nhat_va_bac_hai_toan _10', title='Video bài giảng Hàm số bậc nhất và bậc hai'), Resource(type='tài liệu', url='tailieutoan.vn/ham_so_bac_nhat_va_bac_hai', title='Tài liệu Hàm số bậc nhất và bậc hai')], duration_estimate='1-2 tuần', priority='cao'), StudyModule(module_name='Chương 9: Phương pháp tọa độ trong mặt phẳng', lesson_titles=['Bài 1: Phương trình đường thẳng'], objectives=['Hiểu rõ các dạng phương trình đường thẳng (tham số, tổng quát, chính tắc).', 'Giải quyết thành thạo các bài toán về vị trí tương đối, khoảng cách, góc và các yếu tố liên quan đến đường thẳng trong mặt phẳng tọa độ.'], description='Chương này đi sâu vào phương trình đường thẳng, một chủ đề trọng tâm trong hình học giải tích, cần thiết cho kỳ thi học sinh giỏi.', resources=[Resource(type='video', url='youtube.com/playlist?list=Phương_pháp_tọa_độ_mặt_phẳng_Toán_10', title='Video bài giảng Phương pháp tọa độ mặt phẳng'), Resource(type='tài liệu', url='tailieutoan.vn/chuyen-de-phuong_phap_toa_do', title='Tài liệu Phương pháp tọa độ mặt phẳng')], duration_estimate='1-2 tuần', priority='cao')] constraints=Constraints(available_hours_per_day='2.5 tiếng', deadline='2025-11-30', max_modules_per_week=1, available_days_per_week=['thứ hai', 'thứ tư', 'thứ sáu', 'chủ nhật']) learner_profile=LearnerProfile(level='học tốt', preferred_study_style='học qua video', learning_goals='Thi học sinh giỏi Toán 10 cấp thành phố năm 2025, đạt giải nhất', plan_name='Kế hoạch ôn thi học sinh giỏi Toán 10', plan_scope='chủ đề quan tâm')"
        # }


#    ---------------------------------------------------------------------------------------------------------
    
        query = "nội dung chuẩn chương trình final_version_toan_10 "

        docs = self.retrieve.invoke(query)

        context_text = self.format_docs(docs)

        state["retrieved_context"] = context_text
        messages = self.prompt_builder.build(state, context=context_text)

        response = await self.llm_client.ainvoke_with_retries(
            prompt=messages,
            output_model=StudyPlanOverview
        )

        if response:
            print("overview response:", response)
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


