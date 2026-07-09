from ast import List
import logging
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from langchain.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from src.clients.llm import LLMClient
from state import State
from src.clients.databases import qdrant
from state import State, StudyPlanDetail 
from src.tools.tool import retrieve_tool
from src.agents.overview_planner import OverViewPlanner
from langchain.schema import AIMessage
from sentence_transformers import CrossEncoder
# from google_genai import VertexAI
from datetime import datetime



logger = logging.getLogger(__name__)
 
class DetailPlannerPromptBuilder:
    def __init__(self):
        # System prompt: vai trò của agent (không chứa data)
        with open(
            r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\src.agents.detail_planner.call.sp.txt",
            "r", encoding="utf-8"
        ) as file:
            self._system_prompt = file.read()

        # User prompt: khung chứa dữ liệu học viên + hội thoại
        with open(
            r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\src.agents.detail_planner.call.um.txt",
            "r", encoding="utf-8"
        ) as file:
            self._user_message_template = file.read()
    
    # def build(self, state: State , context : str) -> List:
    def build(self, state: State):

        """Build prompt for DetailPlanAgent using overview_result"""

        print("DETAIL BUILD IS RUNNING...")

        overview_result = state.get("overview_result")
        if overview_result is None:
            print("overview_result is None")
            return []

        study_modules = overview_result.study_modules
        constraints = overview_result.constraints
        learner_profile = overview_result.learner_profile

        if study_modules and constraints and learner_profile:
            print("overview data ok")

        # prompts = []

        up =[]
        for module in study_modules:
            # Format resources list
            resources_str = "\n".join(
                [f"- {res.type}: {res.title} ({res.url})" for res in module.resources]
            )

            # Fill user message template with study plan + context + conversation
            user_message = self._user_message_template.format(
                module_name=module.module_name,
                module_lesson_titles=", ".join(module.lesson_titles),
                module_objectives="\n".join(module.objectives),
                duration_estimate=module.duration_estimate,
                module_resources=resources_str,
                module_priority=module.priority,

                learner_level=learner_profile.level,
                preferred_study_style=learner_profile.preferred_study_style,

                available_hours_per_day=constraints.available_hours_per_day,
                available_days_per_week=", ".join(constraints.available_days_per_week),


            )

            up.append(user_message)
            

        # user_message = self._user_message_template.format(
        #     conversation_context="Mô -đun xử lý để lập kế hoạch chi tiết",
        #     conversation=f"Vui lòng tạo gói chi tiết cho tất cả các mô -đun trong LEARNER’S OVERALL STUDY PLAN"
        # )

        # combined_message = "\n\n".join(up)
        combined_message = "LEARNER’S OVERALL STUDY PLAN\n" + "\n\n---\n\n".join(up[0:])



        combined_message += (
            "\n\n===\n\n"
            "Bạn cần lập kế hoạch chi tiết cho **tất cả các mô-đun ở trên**. "
            "Không được bỏ sót bất kỳ mô-đun nào."
        )
 
        return [
            SystemMessage(content=self._system_prompt),
            HumanMessage(content=combined_message)
        ]



    

class DetailPlanner:
    def __init__(self, llm_client: LLMClient , vector_store):
        self.llm_client = llm_client 
        self.prompt_builder = DetailPlannerPromptBuilder()
        self.retriever = retrieve_tool(vector_store=vector_store ,search_kwargs={"k":4})
        self.overview = OverViewPlanner(llm_client, vector_store)
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    def rerank_documents(self, query, docs, top_k=1):
        # Load cross-encoder model
        # reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        # Prepare query-document pairs
        query_doc_pairs = [(query, doc.page_content) for doc in docs]
        
        # Get relevance scores
        scores = self.reranker.predict(query_doc_pairs)
        
        # Sort by score (descending)
        doc_scores = list(zip(docs, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k reranked documents
        return [doc for doc, score in doc_scores[:top_k]]


    def create_query(self, state: State):
        overview_result = state.get("overview_result")
        if overview_result is None:
            print("overview_result is None")
            return []

        study_modules = overview_result.study_modules
        all_result = []

        for module in study_modules:
            module_name = module.module_name
            for lesson in module.lesson_titles:
                query = f"[{module_name} - {lesson}]"
                # query = f"{lesson}"
                print("query :" , query)
                print("------------------------------------------")

                # retriever
                results = self.retriever.invoke(query)

                doc_re_rank = self.rerank_documents(query,results)
                # print(f"Before rerank: {len(results)}, After: {len(doc_re_rank)}")

                # for re in results:
                #     ress = re.page_content
                #     print("-"*40)
                #     print(ress)

                # print("\ndoc_re_rank :" , doc_re_rank)
                # print("-"*40)


                # Nếu results là Document hoặc list Document thì xử lý
                if isinstance(doc_re_rank, list):
                    # print("list")
                    all_result.extend(doc_re_rank)
                else:
                    # print("type:", type(results))
                    all_result.append(doc_re_rank)
        # Unique theo nội dung text
        seen = set()
        unique_results = []
        for doc in all_result:
            
            
            content = doc.page_content.strip() if hasattr(doc, "page_content") else str(doc)
            
            # print(f"-------------------")
            # print(content[:50])  # in thử 50 ký tự đầu

            if content.lstrip().startswith("nội dung chuẩn chương trình final_version_toan_10"):  # loại bỏ space rồi mới check
                # print(">>> Bỏ doc này vì bắt đầu bằng xxx")
                continue
            if content not in seen:
                seen.add(content)
                unique_results.append(doc)


        # print("unique_results : "  ,unique_results)

        return unique_results
    



    async def __call__(self, state:State):
        """Generate detailed study plan based on overview_result."""
        print("============= call__start__detail =============\n"*4)



        if state.get("detail_completed"):
            # print("✅ detail ✅")
            return state

        state["messages"].clear()
        # return {
        #     "plan_id": "dsf",
        #     "detail_completed": True,
        #     "study_details_result": "total_number_sessions=5 sessions_done=0 detail_plans=[DetailPlan(module_name='Chương 2: Hàm số bậc nhất và bậc hai', total_number_session_in_module=3, total_number_session_done_in_module=0, lessons=[Lesson(lesson_id='T10-ĐS-C2-B3', lesson_plan='Đại số Học kỳ: Kì 1', lesson_dif='4/5 (Vận dụng & Vận dụng cao)', total_number_sessions_in_lesson=3, lesson_title='Bài 3: Hàm số bậc hai', descriptions='Nhận biết, nắm vững các đặc điểm (trục đối xứng, đỉnh, bảng biến thiên) và vẽ đồ thị của hàm số y=ax2+bx+c. Nắm vững cách lập bảng biến thiên, vẽ đồ thị và giải các dạng bài tập liên quan.', objectives=['Nhận biết, nắm vững các đặc điểm (trục đối xứng, đỉnh, bảng biến thiên) của hàm số bậc hai', 'Vẽ được đồ thị của hàm số y=ax2+bx+c', 'Giải các dạng bài tập liên quan đến hàm số bậc hai'], sessions=[Session(session_id='T10-ĐS-C2-B3-B-1', session_number=1, status='Chưa hoàn thành', session_name='Định nghĩa và Đồ thị Hàm số bậc hai cơ bản', daily=DailyStudyItem(hours=8.0, session_date='2025-03-10', duration_minutes=90), core_content='Định nghĩa hàm số bậc hai (y=ax2+bx+c), nhận dạng. Đồ thị hàm số bậc hai: parabol, đỉnh I(-b/2a; -Δ/4a), trục đối xứng x=-b/2a.', objectives=['Nắm được định nghĩa và nhận dạng hàm số bậc hai', 'Hiểu khái niệm parabol, đỉnh và trục đối xứng của đồ thị hàm số bậc hai', 'Xác định được tọa độ đỉnh và phương trình trục đối xứng của parabol'], activities=['Nghe giảng video về định nghĩa và các yếu tố cơ bản của hàm số bậc hai', 'Đọc tài liệu lý thuyết để củng cố kiến thức', 'Thực hành các ví dụ cơ bản về nhận dạng hàm số và xác định đỉnh, trục đối xứng'], assignments=['Bài tập nhận dạng hàm số bậc hai', 'Bài tập xác định tọa độ đỉnh và phương trình trục đối xứng của parabol'], resources=[Resource(type='video', url='https://www.youtube.com/watch?v=R2jQx1hK7yU', title='Video bài giảng Hàm số bậc hai'), Resource(type='tài liệu', url='https://loigiaihay.com/ly-thuyet-ham-so-bac-hai-a109834.html', title='Tài liệu lý thuyết Hàm số bậc hai'), Resource(type='bài tập', url='https://vndoc.com/bai-tap-ham-so-bac-hai-toan-10-179834', title='Bài tập cơ bản Hàm số bậc hai')]), Session(session_id='T10-ĐS-C2-B3-B-2', session_number=2, status='Chưa hoàn thành', session_name='Lập bảng biến thiên và Vẽ đồ thị Hàm số bậc hai', daily=DailyStudyItem(hours=8.0, session_date='2025-03-12', duration_minutes=90), core_content='Lập bảng biến thiên của hàm số bậc hai (chiều biến thiên, giá trị lớn nhất/nhỏ nhất). Các bước vẽ đồ thị hàm số bậc hai dựa trên đỉnh, trục đối xứng và các điểm đặc biệt.', objectives=['Thành thạo lập bảng biến thiên của hàm số bậc hai', 'Vẽ được đồ thị hàm số bậc hai một cách chính xác', 'Hiểu mối liên hệ giữa bảng biến thiên và đồ thị'], activities=['Xem video hướng dẫn chi tiết về cách lập bảng biến thiên và vẽ đồ thị', 'Thực hành vẽ đồ thị các hàm số bậc hai khác nhau trên giấy hoặc phần mềm', 'Làm bài tập vận dụng về lập bảng biến thiên và vẽ đồ thị'], assignments=['Bài tập lập bảng biến thiên và vẽ đồ thị hàm số bậc hai', 'Bài tập xác định các khoảng đồng biến, nghịch biến của hàm số'], resources=[Resource(type='video', url='https://www.youtube.com/watch?v=R2jQx1hK7yU', title='Video hướng dẫn vẽ đồ thị Hàm số bậc hai'), Resource(type='tài liệu', url='https://loigiaihay.com/ly-thuyet-ham-so-bac-hai-a109834.html', title='Tài liệu các bước vẽ đồ thị'), Resource(type='bài tập', url='https://vndoc.com/bai-tap-ham-so-bac-hai-toan-10-179834', title='Bài tập lập bảng biến thiên và vẽ đồ thị')]), Session(session_id='T10-ĐS-C2-B3-B-3', session_number=3, status='Chưa hoàn thành', session_name='Bài tập nâng cao và Ứng dụng Hàm số bậc hai', daily=DailyStudyItem(hours=8.0, session_date='2025-03-14', duration_minutes=90), core_content='Tìm giá trị lớn nhất, nhỏ nhất của hàm số bậc hai trên một khoảng cho trước. Các dạng bài tập tổng hợp và ứng dụng thực tế của hàm số bậc hai.', objectives=['Vận dụng kiến thức để tìm giá trị lớn nhất, nhỏ nhất của hàm số trên một đoạn/khoảng', 'Giải quyết các dạng bài tập tổng hợp về hàm số bậc hai', 'Hiểu được ứng dụng của hàm số bậc hai trong các bài toán thực tế'], activities=['Luyện tập các dạng bài tập vận dụng cao về tìm GTLN, GTNN', 'Thảo luận và giải các bài tập tổng hợp, các bài toán có lời văn liên quan', 'Ôn tập toàn bộ kiến thức về hàm số bậc hai đã học'], assignments=['Bài tập tìm giá trị lớn nhất, nhỏ nhất của hàm số bậc hai', 'Bài tập tổng hợp về hàm số bậc hai (trong SGK và sách nâng cao)'], resources=[Resource(type='video', url='https://www.youtube.com/watch?v=R2jQx1hK7yU', title='Video bài giảng ứng dụng Hàm số bậc hai'), Resource(type='tài liệu', url='https://loigiaihay.com/ly-thuyet-ham-so-bac-hai-a109834.html', title='Tài liệu các dạng bài tập nâng cao'), Resource(type='bài tập', url='https://vndoc.com/bai-tap-ham-so-bac-hai-toan-10-179834', title='Bài tập tìm GTLN, GTNN và tổng hợp')])])]), DetailPlan(module_name='Chương 9: Phương pháp tọa độ trong mặt phẳng', total_number_session_in_module=2, total_number_session_done_in_module=0, lessons=[Lesson(lesson_id='T10-HH-C3-B1', lesson_plan='Hình học Học kỳ: Kì 2', lesson_dif='3/5 (Thông hiểu & Vận dụng)', total_number_sessions_in_lesson=2, lesson_title='Bài 1: Phương trình đường thẳng', descriptions='Hiểu rõ các dạng phương trình đường thẳng (tham số, tổng quát, chính tắc). Giải quyết thành thạo các bài toán về vị trí tương đối, khoảng cách, góc và các yếu tố liên quan đến đường thẳng trong mặt phẳng tọa độ.', objectives=['Nắm vững các loại phương trình đường thẳng (tham số, tổng quát)', 'Biết cách chuyển đổi giữa các dạng phương trình đường thẳng', 'Nắm vững cách tính khoảng cách từ một điểm đến một đường thẳng', 'Nắm vững cách tính góc giữa hai đường thẳng'], sessions=[Session(session_id='T10-HH-C3-B1-B-1', session_number=1, status='Chưa hoàn thành', session_name='Các dạng Phương trình đường thẳng và chuyển đổi', daily=DailyStudyItem(hours=8.0, session_date='2025-03-16', duration_minutes=90), core_content='Vectơ chỉ phương và vectơ pháp tuyến. Phương trình tham số của đường thẳng. Phương trình tổng quát của đường thẳng (Ax+By+C=0). Cách chuyển đổi giữa các dạng phương trình.', objectives=['Phân biệt được vectơ chỉ phương và vectơ pháp tuyến', 'Viết được phương trình tham số của đường thẳng', 'Viết được phương trình tổng quát của đường thẳng', 'Thực hiện chuyển đổi giữa phương trình tham số và tổng quát'], activities=['Nghe giảng video về các loại vectơ và dạng phương trình đường thẳng', 'Đọc tài liệu lý thuyết để hiểu rõ các công thức và quy tắc', 'Thực hành viết phương trình đường thẳng khi biết các yếu tố khác nhau (điểm, vectơ)'], assignments=['Bài tập xác định vectơ chỉ phương, pháp tuyến', 'Bài tập viết phương trình tham số và tổng quát của đường thẳng', 'Bài tập chuyển đổi dạng phương trình đường thẳng'], resources=[Resource(type='video', url='https://www.youtube.com/watch?v=F3tJ8X5rKkM', title='Video bài giảng Phương trình đường thẳng'), Resource(type='tài liệu', url='https://loigiaihay.com/ly-thuyet-phuong-trinh-duong-thang-c46a6252.html', title='Tài liệu các dạng Phương trình đường thẳng'), Resource(type='bài tập', url='https://vndoc.com/bai-tap-trac-nghiem-phuong-trinh-duong-thang-toan-10-187016', title='Bài tập về các dạng Phương trình đường thẳng')]), Session(session_id='T10-HH-C3-B1-B-2', session_number=2, status='Chưa hoàn thành', session_name='Bài toán Khoảng cách và Góc giữa các đường thẳng', daily=DailyStudyItem(hours=8.0, session_date='2025-03-17', duration_minutes=90), core_content='Công thức tính khoảng cách từ một điểm đến một đường thẳng. Công thức tính góc giữa hai đường thẳng. Các bài toán liên quan đến vị trí tương đối của hai đường thẳng.', objectives=['Nắm vững công thức và cách tính khoảng cách từ một điểm đến một đường thẳng', 'Nắm vững công thức và cách tính góc giữa hai đường thẳng', 'Giải quyết các bài toán về vị trí tương đối của hai đường thẳng (song song, cắt nhau, trùng nhau)'], activities=['Xem video hướng dẫn giải các bài toán về khoảng cách và góc', 'Thực hành giải các bài tập tính khoảng cách, tính góc', 'Làm các bài tập trắc nghiệm và tự luận tổng hợp về phương trình đường thẳng'], assignments=['Bài tập tính khoảng cách từ điểm đến đường thẳng', 'Bài tập tính góc giữa hai đường thẳng', 'Bài tập tổng hợp về phương trình đường thẳng và các yếu tố liên quan'], resources=[Resource(type='video', url='https://www.youtube.com/watch?v=F3tJ8X5rKkM', title='Video bài giảng Khoảng cách và Góc'), Resource(type='tài liệu', url='https://loigiaihay.com/ly-thuyet-phuong-trinh-duong-thang-c46a6252.html', title='Tài liệu công thức Khoảng cách và Góc'), Resource(type='bài tập', url='https://vndoc.com/bai-tap-trac-nghiem-phuong-trinh-duong-thang-toan-10-187016', title='Bài tập tính Khoảng cách và Góc')])])])]"
        # }
 

#    ---------------------------------------------------------------------------------------------------------
    

        print("============= call__start__detail =============\n"*4)


        print("call details_agent is runing...")

        docss = self.create_query(state)
        docs  = self.overview.format_docs(docss)
        # print("\========================docs=========================" , docs)
        print('-'*40)
        prompt = self.prompt_builder.build(state)
        # print("\nprompt:" ,prompt)





        # Thêm HumanMessage chứa docs
        new_prompt = prompt + [HumanMessage(content="Nội dung các bài học cụ thể như sau:\n" + docs)]

        # print("\ntype new_prompt:" , type(new_prompt))


        # print("\nnew_prompt: ", new_prompt)
        print('-'*40)

        response = await self.llm_client.ainvoke_with_retries(
            prompt=new_prompt, output_model=StudyPlanDetail
        )

        if response:
            print("\n detail_response :" , response)
        else:
            print("response in none")

        plan_id = datetime.now().strftime("%Y%m%d%H%M%S")

        # plan_id = f"plan_{uuid.uuid4().hex}"
        return{
            "plan_id": plan_id,
            "messages":[AIMessage(content=f"✅ details_agent_done___code:{plan_id}✅")],
            "study_details_result" : response,
            "detail_completed" : True   
        }

