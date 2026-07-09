import sys ,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.clients.databases import qdrant, qdrant_qa
from src.clients.llm import LLMClient
from state import State   
from src.agents.profile_collector import ProfileCollector
from src.agents.overview_planner import OverViewPlanner
from src.agents.detail_planner import DetailPlanner 
from src.agents.review_planner import ReviewPlanner 
from src.agents.QA_planner import QAPlanner 
from src.agents.QA_program import QAProgram

from src.agents.mini_test import MiniTestPlanner 





import asyncio
from datetime import datetime
import json




from langgraph.graph import MessagesState, StateGraph
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.runnables import RunnableConfig
from pydantic_settings import BaseSettings
from langchain_core.messages import HumanMessage
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.configs import env_config



# --------------------------------------------------------------------------------------------------------------------
def to_dict_safe(obj):
    if obj is None:
        return None
    if hasattr(obj, "dict"):   # Pydantic BaseModel
        return obj.dict()
    if isinstance(obj, (list, tuple)):
        return [to_dict_safe(o) for o in obj]
    if isinstance(obj, dict):
        return {k: to_dict_safe(v) for k, v in obj.items()}
    return obj  # kiểu cơ bản (str, int, float, bool)

def save_plan(state, folder="plans"):
    os.makedirs(folder, exist_ok=True)
    # plan_id = "20250830221757"
    plan_id = state.get("plan_id")
  
    file_path = os.path.join(folder, f"{plan_id}.json")
    # current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    # convert bất kỳ object nào có dict() sang dict
    overview_result = state.get("overview_result")
    review_result = to_dict_safe(state.get("review_result"))

    if hasattr(overview_result, "dict"):
        overview_result = overview_result.dict()
    if hasattr(review_result, "dict"):
        review_result = review_result.dict()

    data = {
        "plan_id": plan_id,        
        "time": current_time,
        "status": "Đang học",
        "overview_result": "overview_result",
        "review_result": review_result
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return file_path
# --------------------------------------------------------------------------------------------------------------------
def run_mini_test(state: State):
    if state.get("review_completed", False):
        # print("✅ review --> mini_test ✅")
        save_file = save_plan(state)
        print(f"kế hoạch đã được lưu vào :  {save_file}")

        return "mini_test_planner"
    else:
        # print("❌ review --> mini_test_planner ❌")
        return END

# --------------------------------------------------------------------------------------------------------------------

def run_review_planner(state: State):
    if state.get("detail_completed", False):
        # print("✅ detail --> review  ✅")
        state["messages"] = []
        state["messages"].clear()
        state["plan_id"] = None
        # state["plan_id"].clear()

        return "review_planner"
    else:
        # print("❌ detail --> review ❌")
        return END
# --------------------------------------------------------------------------------------------------------------------

def run_detail_planner(state: State):
    if state.get("overview_completed", False):
        # print("✅ Overview --> detail ✅")
        return "detail_planner"
    else:
        # print("❌ Overview --> detail ❌")
        return END
# --------------------------------------------------------------------------------------------------------------------

def run_overview_planner(state: State):
    profile_completed = state.get("profile_completed", False)
    if profile_completed:
        # print("✅ profile --> overview ✅")
        return "overview_planner"
    else:
        # print("❌ profile --> overview ❌")
        return END

    
# --------------------------------------------------------------------------------------------------------------------

# def router(state: State):
#     """Router function - phân tích query và cập nhật flow tương ứng"""
#     flow = state.get("flow", "1")
    
#     # Nếu flow = "1", giữ nguyên để chạy profile collector
#     if flow == "1":
#         return {"flow": "1"}
    
#     # Với các flow khác (2.1, 2.2), luôn phân tích lại query mới nhất
#     else:
#         human_messages = [msg for msg in state["messages"] if msg.type == "human"]
#         if human_messages:
#             query = human_messages[-1].content.lower()
#             # Phân tích query để cập nhật flow
#             if any(k in query for k in [ "kế hoạch", "tiến độ", "lộ trình", "id", "mục tiêu học tập", "thời gian", "trong chương", "phút", "cần nắm", "tổng quan học tập" ]):
#                 return {"flow": "2.1"}
#             else:
#                 return {"flow": "2.2"}
        
#         # Fallback nếu không có human messages
#         return {"flow": "2.2"}

# # Hàm helper để xác định node tiếp theo
# def route_to_next(state: State):
#     """Hàm helper để xác định node tiếp theo dựa trên flow và phân tích query"""
#     flow = state.get("flow", "1")
    
#     # Nếu flow = "1", chạy profile collector
#     if flow == "1":
#         return "profile_collector"
    
#     # Với flow "2.1" và "2.2", luôn phân tích lại query mới nhất
#     elif flow in ["2.1", "2.2"]:
#         human_messages = [msg for msg in state["messages"] if msg.type == "human"]
#         if human_messages:
#             query = human_messages[-1].content.lower()
#             # Phân tích query để quyết định đi qa_planner hay qa_program
#             if any(k in query for k in [ "kế hoạch", "tiến độ", "lộ trình", "id", "mục tiêu học tập", "thời gian", "trong chương", "phút", "cần nắm", "tổng quan học tập" ]):
#                 return "qa_planner"
#             else:
#                 return "qa_program"
    
#     # Fallback cho trường hợp khác
#     human_messages = [msg for msg in state["messages"] if msg.type == "human"]
#     if human_messages:
#         query = human_messages[-1].content.lower()
#         if any(k in query for k in ["kế hoạch", "tiến độ", "lộ trình", "module"]):
#             return "qa_planner"
#         else:
#             return "qa_program"
    
#     return "profile_collector"

def router(state: State):
    """Router function - phân tích query và cập nhật flow tương ứng"""
    flow = state.get("flow", "1")
    
    # Nếu flow = "1", giữ nguyên để chạy profile collector
    if flow == "1":
        return {"flow": "1"}
    
    # Với các flow khác (2.1, 2.2), luôn phân tích lại query mới nhất
    else:
        human_messages = [msg for msg in state["messages"] if msg.type == "human"]
        if human_messages:
            query = human_messages[-1].content.lower()
            
            # Nếu có các key đặc biệt => flow = 1
            if any(k in query for k in ["tạo", "muốn tạo", "tạo kế hoạch", "tạo kế hoạch học tập"]):
                return {"flow": "1"}
            
            # Nếu có từ khóa liên quan kế hoạch
            if any(k in query for k in ["kế hoạch", "tiến độ", "lộ trình", "id", 
                                        "mục tiêu học tập", "thời gian", "trong chương", 
                                        "phút", "cần nắm", "tổng quan học tập"]):
                return {"flow": "2.1"}
            else:
                return {"flow": "2.2"}
        
        # Fallback nếu không có human messages
        return {"flow": "2.2"}


def route_to_next(state: State):
    """Hàm helper để xác định node tiếp theo dựa trên flow và phân tích query"""
    flow = state.get("flow", "1")
    
    # Nếu flow = "1", chạy profile collector
    if flow == "1":
        return "profile_collector"
    
    elif flow in ["2.1", "2.2"]:
        human_messages = [msg for msg in state["messages"] if msg.type == "human"]
        if human_messages:
            query = human_messages[-1].content.lower()
            
            # Nếu có các key đặc biệt => quay lại profile_collector
            if any(k in query for k in ["tạo", "muốn tạo", "tạo kế hoạch", "tạo kế hoạch học tập"]):
                return "profile_collector"
            
            if any(k in query for k in ["kế hoạch", "tiến độ", "lộ trình", "id", 
                                        "mục tiêu học tập", "thời gian", "trong chương", 
                                        "phút", "cần nắm", "tổng quan học tập"]):
                return "qa_planner"
            else:
                return "qa_program"
    
    # Fallback cho trường hợp khác
    human_messages = [msg for msg in state["messages"] if msg.type == "human"]
    if human_messages:
        query = human_messages[-1].content.lower()  
        if any(k in query for k in ["tạo", "muốn tạo", "tạo kế hoạch", "tạo kế hoạch học tập"]):
            return "profile_collector"
        elif any(k in query for k in ["kế hoạch", "tiến độ", "lộ trình", "module"]):
            return "qa_planner"
        else:
            return "qa_program"
    
    return "profile_collector"

# Cập nhật cách tạo graph
def create_agent_graph(llm_client):
    profile_collector = ProfileCollector(llm_client)
    overview_planner = OverViewPlanner(llm_client, vector_store=qdrant)
    detail_planner = DetailPlanner(llm_client, vector_store=qdrant)
    review_planner = ReviewPlanner(llm_client)
    qa_planner = QAPlanner(llm_client)
    qa_program = QAProgram(llm_client, vector_store=qdrant_qa)
    mini_test_planner = MiniTestPlanner(llm_client)

    graph = StateGraph(State)
    
    # Thêm các node
    graph.add_node("profile_collector", profile_collector)
    graph.add_node("overview_planner", overview_planner)
    graph.add_node("detail_planner", detail_planner)
    graph.add_node("review_planner", review_planner)
    graph.add_node("qa_planner", qa_planner)
    graph.add_node("qa_program", qa_program)
    graph.add_node("mini_test_planner", mini_test_planner)
    graph.add_node("router", router)

    # Cập nhật conditional edges cho router
    graph.add_conditional_edges(
        "router",
        route_to_next,  # Sử dụng hàm helper thay vì router
        {
            "profile_collector": "profile_collector",
            "qa_planner": "qa_planner", 
            "qa_program": "qa_program",
        }
    )

    graph.add_edge(START, "router")

# -----------------------[   1   ] ------------------------------
    graph.add_conditional_edges(
        "profile_collector",
        run_overview_planner, 
        {END: END, "overview_planner": "overview_planner"}
    )

    graph.add_conditional_edges(
        "overview_planner",
        run_detail_planner,
        {END: END, "detail_planner": "detail_planner"}
    )

    graph.add_conditional_edges(
        "detail_planner",
        run_review_planner,
        {END: END, "review_planner": "review_planner"}
    )

    graph.add_conditional_edges(
        "review_planner",
        run_mini_test,
        {END: END, "mini_test_planner": "mini_test_planner"}
    ) 

# ----------------------- [   2.1   ] ------------------------------
    graph.add_conditional_edges(
        "qa_planner",
        run_mini_test,
        {END: END, "mini_test_planner": "mini_test_planner"}
    ) 

# ----------------------- [   2.2   ] ------------------------------
    graph.add_conditional_edges(
        "qa_program",
        run_mini_test,
        {END: END, "mini_test_planner": "mini_test_planner"}
    ) 
   

    graph.add_edge("mini_test_planner" , END)

    return graph.compile(checkpointer=MemorySaver())

# --------------------------------------------------------------------------------------------------------------------
async def main():
    print("=== Bắt đầu hội thoại với hệ thống ===")
    llm_client = LLMClient(model=env_config.model, api_provider=env_config.api_provider)
    state: State = {
        "messages": [],
        "profile_user": None,
        "profile_completed": False,
        "overview_completed": False,
        "overview_result": None,
        "ok": "",
        "study_details_result":"total_number_sessions=5 sessions_done=0 detail_plans=[DetailPlan(module_name='Chương 2: Hàm số bậc nhất và bậc hai', total_number_session_in_module=3, total_number_session_done_in_module=0, lessons=[Lesson(lesson_id='T10-ĐS-C2-B3', lesson_plan='Đại số Học kỳ: Kì 1', lesson_dif='4/5 (Vận dụng & Vận dụng cao)', total_number_sessions_in_lesson=3, lesson_title='Bài 3: Hàm số bậc hai', descriptions='Nhận biết, nắm vững các đặc điểm (trục đối xứng, đỉnh, bảng biến thiên) và vẽ đồ thị của hàm số y=ax2+bx+c. Nắm vững cách lập bảng biến thiên, vẽ đồ thị và giải các dạng bài tập liên quan.', objectives=['Nhận biết, nắm vững các đặc điểm (trục đối xứng, đỉnh, bảng biến thiên) của hàm số bậc hai', 'Vẽ được đồ thị của hàm số y=ax2+bx+c', 'Giải các dạng bài tập liên quan đến hàm số bậc hai'], sessions=[Session(session_id='T10-ĐS-C2-B3-B-1', session_number=1, status='Chưa hoàn thành', session_name='Định nghĩa và Đồ thị Hàm số bậc hai cơ bản', daily=DailyStudyItem(hours=8.0, session_date='2025-03-10', duration_minutes=90), core_content='Định nghĩa hàm số bậc hai (y=ax2+bx+c), nhận dạng. Đồ thị hàm số bậc hai: parabol, đỉnh I(-b/2a; -Δ/4a), trục đối xứng x=-b/2a.', objectives=['Nắm được định nghĩa và nhận dạng hàm số bậc hai', 'Hiểu khái niệm parabol, đỉnh và trục đối xứng của đồ thị hàm số bậc hai', 'Xác định được tọa độ đỉnh và phương trình trục đối xứng của parabol'], activities=['Nghe giảng video về định nghĩa và các yếu tố cơ bản của hàm số bậc hai', 'Đọc tài liệu lý thuyết để củng cố kiến thức', 'Thực hành các ví dụ cơ bản về nhận dạng hàm số và xác định đỉnh, trục đối xứng'], assignments=['Bài tập nhận dạng hàm số bậc hai', 'Bài tập xác định tọa độ đỉnh và phương trình trục đối xứng của parabol'], resources=[Resource(type='video', url='https://www.youtube.com/watch?v=R2jQx1hK7yU', title='Video bài giảng Hàm số bậc hai'), Resource(type='tài liệu', url='https://loigiaihay.com/ly-thuyet-ham-so-bac-hai-a109834.html', title='Tài liệu lý thuyết Hàm số bậc hai'), Resource(type='bài tập', url='https://vndoc.com/bai-tap-ham-so-bac-hai-toan-10-179834', title='Bài tập cơ bản Hàm số bậc hai')]), Session(session_id='T10-ĐS-C2-B3-B-2', session_number=2, status='Chưa hoàn thành', session_name='Lập bảng biến thiên và Vẽ đồ thị Hàm số bậc hai', daily=DailyStudyItem(hours=8.0, session_date='2025-03-12', duration_minutes=90), core_content='Lập bảng biến thiên của hàm số bậc hai (chiều biến thiên, giá trị lớn nhất/nhỏ nhất). Các bước vẽ đồ thị hàm số bậc hai dựa trên đỉnh, trục đối xứng và các điểm đặc biệt.', objectives=['Thành thạo lập bảng biến thiên của hàm số bậc hai', 'Vẽ được đồ thị hàm số bậc hai một cách chính xác', 'Hiểu mối liên hệ giữa bảng biến thiên và đồ thị'], activities=['Xem video hướng dẫn chi tiết về cách lập bảng biến thiên và vẽ đồ thị', 'Thực hành vẽ đồ thị các hàm số bậc hai khác nhau trên giấy hoặc phần mềm', 'Làm bài tập vận dụng về lập bảng biến thiên và vẽ đồ thị'], assignments=['Bài tập lập bảng biến thiên và vẽ đồ thị hàm số bậc hai', 'Bài tập xác định các khoảng đồng biến, nghịch biến của hàm số'], resources=[Resource(type='video', url='https://www.youtube.com/watch?v=R2jQx1hK7yU', title='Video hướng dẫn vẽ đồ thị Hàm số bậc hai'), Resource(type='tài liệu', url='https://loigiaihay.com/ly-thuyet-ham-so-bac-hai-a109834.html', title='Tài liệu các bước vẽ đồ thị'), Resource(type='bài tập', url='https://vndoc.com/bai-tap-ham-so-bac-hai-toan-10-179834', title='Bài tập lập bảng biến thiên và vẽ đồ thị')]), Session(session_id='T10-ĐS-C2-B3-B-3', session_number=3, status='Chưa hoàn thành', session_name='Bài tập nâng cao và Ứng dụng Hàm số bậc hai', daily=DailyStudyItem(hours=8.0, session_date='2025-03-14', duration_minutes=90), core_content='Tìm giá trị lớn nhất, nhỏ nhất của hàm số bậc hai trên một khoảng cho trước. Các dạng bài tập tổng hợp và ứng dụng thực tế của hàm số bậc hai.', objectives=['Vận dụng kiến thức để tìm giá trị lớn nhất, nhỏ nhất của hàm số trên một đoạn/khoảng', 'Giải quyết các dạng bài tập tổng hợp về hàm số bậc hai', 'Hiểu được ứng dụng của hàm số bậc hai trong các bài toán thực tế'], activities=['Luyện tập các dạng bài tập vận dụng cao về tìm GTLN, GTNN', 'Thảo luận và giải các bài tập tổng hợp, các bài toán có lời văn liên quan', 'Ôn tập toàn bộ kiến thức về hàm số bậc hai đã học'], assignments=['Bài tập tìm giá trị lớn nhất, nhỏ nhất của hàm số bậc hai', 'Bài tập tổng hợp về hàm số bậc hai (trong SGK và sách nâng cao)'], resources=[Resource(type='video', url='https://www.youtube.com/watch?v=R2jQx1hK7yU', title='Video bài giảng ứng dụng Hàm số bậc hai'), Resource(type='tài liệu', url='https://loigiaihay.com/ly-thuyet-ham-so-bac-hai-a109834.html', title='Tài liệu các dạng bài tập nâng cao'), Resource(type='bài tập', url='https://vndoc.com/bai-tap-ham-so-bac-hai-toan-10-179834', title='Bài tập tìm GTLN, GTNN và tổng hợp')])])]), DetailPlan(module_name='Chương 9: Phương pháp tọa độ trong mặt phẳng', total_number_session_in_module=2, total_number_session_done_in_module=0, lessons=[Lesson(lesson_id='T10-HH-C3-B1', lesson_plan='Hình học Học kỳ: Kì 2', lesson_dif='3/5 (Thông hiểu & Vận dụng)', total_number_sessions_in_lesson=2, lesson_title='Bài 1: Phương trình đường thẳng', descriptions='Hiểu rõ các dạng phương trình đường thẳng (tham số, tổng quát, chính tắc). Giải quyết thành thạo các bài toán về vị trí tương đối, khoảng cách, góc và các yếu tố liên quan đến đường thẳng trong mặt phẳng tọa độ.', objectives=['Nắm vững các loại phương trình đường thẳng (tham số, tổng quát)', 'Biết cách chuyển đổi giữa các dạng phương trình đường thẳng', 'Nắm vững cách tính khoảng cách từ một điểm đến một đường thẳng', 'Nắm vững cách tính góc giữa hai đường thẳng'], sessions=[Session(session_id='T10-HH-C3-B1-B-1', session_number=1, status='Chưa hoàn thành', session_name='Các dạng Phương trình đường thẳng và chuyển đổi', daily=DailyStudyItem(hours=8.0, session_date='2025-03-16', duration_minutes=90), core_content='Vectơ chỉ phương và vectơ pháp tuyến. Phương trình tham số của đường thẳng. Phương trình tổng quát của đường thẳng (Ax+By+C=0). Cách chuyển đổi giữa các dạng phương trình.', objectives=['Phân biệt được vectơ chỉ phương và vectơ pháp tuyến', 'Viết được phương trình tham số của đường thẳng', 'Viết được phương trình tổng quát của đường thẳng', 'Thực hiện chuyển đổi giữa phương trình tham số và tổng quát'], activities=['Nghe giảng video về các loại vectơ và dạng phương trình đường thẳng', 'Đọc tài liệu lý thuyết để hiểu rõ các công thức và quy tắc', 'Thực hành viết phương trình đường thẳng khi biết các yếu tố khác nhau (điểm, vectơ)'], assignments=['Bài tập xác định vectơ chỉ phương, pháp tuyến', 'Bài tập viết phương trình tham số và tổng quát của đường thẳng', 'Bài tập chuyển đổi dạng phương trình đường thẳng'], resources=[Resource(type='video', url='https://www.youtube.com/watch?v=F3tJ8X5rKkM', title='Video bài giảng Phương trình đường thẳng'), Resource(type='tài liệu', url='https://loigiaihay.com/ly-thuyet-phuong-trinh-duong-thang-c46a6252.html', title='Tài liệu các dạng Phương trình đường thẳng'), Resource(type='bài tập', url='https://vndoc.com/bai-tap-trac-nghiem-phuong-trinh-duong-thang-toan-10-187016', title='Bài tập về các dạng Phương trình đường thẳng')]), Session(session_id='T10-HH-C3-B1-B-2', session_number=2, status='Chưa hoàn thành', session_name='Bài toán Khoảng cách và Góc giữa các đường thẳng', daily=DailyStudyItem(hours=8.0, session_date='2025-03-17', duration_minutes=90), core_content='Công thức tính khoảng cách từ một điểm đến một đường thẳng. Công thức tính góc giữa hai đường thẳng. Các bài toán liên quan đến vị trí tương đối của hai đường thẳng.', objectives=['Nắm vững công thức và cách tính khoảng cách từ một điểm đến một đường thẳng', 'Nắm vững công thức và cách tính góc giữa hai đường thẳng', 'Giải quyết các bài toán về vị trí tương đối của hai đường thẳng (song song, cắt nhau, trùng nhau)'], activities=['Xem video hướng dẫn giải các bài toán về khoảng cách và góc', 'Thực hành giải các bài tập tính khoảng cách, tính góc', 'Làm các bài tập trắc nghiệm và tự luận tổng hợp về phương trình đường thẳng'], assignments=['Bài tập tính khoảng cách từ điểm đến đường thẳng', 'Bài tập tính góc giữa hai đường thẳng', 'Bài tập tổng hợp về phương trình đường thẳng và các yếu tố liên quan'], resources=[Resource(type='video', url='https://www.youtube.com/watch?v=F3tJ8X5rKkM', title='Video bài giảng Khoảng cách và Góc'), Resource(type='tài liệu', url='https://loigiaihay.com/ly-thuyet-phuong-trinh-duong-thang-c46a6252.html', title='Tài liệu công thức Khoảng cách và Góc'), Resource(type='bài tập', url='https://vndoc.com/bai-tap-trac-nghiem-phuong-trinh-duong-thang-toan-10-187016', title='Bài tập tính Khoảng cách và Góc')])])])]",
        "detail_completed": False,
        "plan_id": "",
        "status": "Đang học",
        "review_user": None,  
        "review_result ": None,
        "review_completed": False,
        "plan_data":None,
        "qa_planner_completed": False, 
        "flow": "2"
    }
    graph = create_agent_graph(llm_client)

    while True:
        print("flow: ", state.get("flow"))
        print("="*30)
        user_input = input("💁‍♂️    User: ")
        if user_input.strip().lower() in ["q", "quit", "exit"]:
            break

        # if user_input.strip() in ["1", "2", "2.1", "2.2"]:
        #     state["flow"] = user_input.strip()

        state["messages"].append(HumanMessage(content=user_input))
        state = await graph.ainvoke(state, config=RunnableConfig(configurable={"thread_id": "demo_thread"}))

        ai_messages = [msg for msg in state["messages"] if msg.type == "ai"]
        if ai_messages:
            print("="*100)
            print(f"⚙️  ⚙️   Agent : {ai_messages[-1].content}")

        print("="*40)
        flow = router(state)
        print("👉: ",flow)
        print("="*40)


        # review_result = state.get("review_result")
        # if review_result:
        #     print("review_result: ", review_result)

        # human_messages = [msg for msg in state["messages"] if msg.type == "human"]
        


        

        # print("\n======================================= messages ======================================="*2)

        # for mess in state.get("messages", []):
        #     print(f"[{mess.type}]===== {mess.content}")
        #     print("----------")

        # print("\n===================================================================================="*2)
        

 



 
        # print("\n======================================= state ======================================="*2)
        # for k,v in state.items():
        #     print(f"{k}: {v}\n----------\n")

if __name__ == "__main__":
    asyncio.run(main())
      




# --------------------------------------------------------------------------------------------------------------------
      #     # print("\nplan_id", state.get("plan_id"))
        #     # print("\noverview_result", state.get("overview_result"))
        #     # print("\nstudy_details_result", state.get("study_details_result"))
        #     saved_file = save_plan(state)
        #     print("đã lưu vào : " , saved_file)


# def save_plan(state, folder="plans"):
#     os.makedirs(folder, exist_ok=True)
#     plan_id = state.get("plan_id")
#     file_path = os.path.join(folder, f"{plan_id}.json")
#     current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

#     # convert bất kỳ object nào có dict() sang dict
#     overview_result = state.get("overview_result")
#     study_details_result = state.get("study_details_result")

#     if hasattr(overview_result, "dict"):
#         overview_result = overview_result.dict()
#     if hasattr(study_details_result, "dict"):
#         study_details_result = study_details_result.dict()

#     data = {
#         "plan_id": plan_id,        
#         "time": current_time,
#         "overview_result": overview_result,
#         "study_details_result": study_details_result
#     }

#     with open(file_path, "w", encoding="utf-8") as f:
#         json.dump(data, f, ensure_ascii=False, indent=2)

#     return file_path

# --------------------------------------------------------------------------------------------------------------------
