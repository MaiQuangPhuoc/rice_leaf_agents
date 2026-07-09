from pydantic import BaseModel, Field, field_validator
from typing import Annotated, List, Literal, Optional
from typing_extensions import TypedDict
from datetime import date
from langgraph.graph import StateGraph, MessagesState, START, END , add_messages
from langchain_core.messages import (
    AnyMessage)
from langchain_core.documents import Document

# class LearningPreference(BaseModel):
#     """Represents learning preferences and methods preferred by the learner."""
    
#     method: Optional[List[str]] = Field(
#         default_factory=list,
#         description="Phương pháp học ưa thích, ví dụ: 'Video', 'Lý thuyết trước'"
#     )
#     focus: Optional[List[str]] = Field(
#         default_factory=list,                                                                                                                                      
#         description="Ưu tiên học nội dung gì"
#     )

# Bạn là một trợ lý AI học tập thông minh.
# Nhiệm vụ: thu thập thông tin lịch trình đời sống thường ngày của người học để xây dựng hồ sơ cá nhân.

# -----------------------------------------
class QAItem(BaseModel):
    query : str = Field(..., description="nội dung câu hỏi liên quan đến kế hoạch, ví dụ: Chương X có các dạng bài nào , tài nguyên video bài X có chính xác không?")
    answer: str = Field(..., description="Câu trả lời của câu hỏi, ví dụ: tìm nghiệm 2 ẩn , video đó rất đúng")

class QAResponse(BaseModel):
    # module_name: Optional[str] =  Field(None,description="Chương/bài mà câu hỏi hướng đến, ví dụ: chương 1 mệnh đề tập hợp")
    answers: List[QAItem] = Field(..., description="Danh sách các phản hồi, câu trả lời, ví dụ: Chương 2 học 5 buổi , kiến thức rất quan trọng, ...")


class QAItem_pro(BaseModel):
    answer: str = Field(..., description="Câu trả lời của câu hỏi, ví dụ: mệnh đề là câu khẳng định.... , các dạng bài tập của mệnh đề là mệnh đề kéo the, mệnh đề chứa biến , ....")

class QA_response_pro(BaseModel):
    answers: List[QAItem_pro] = Field(..., description="Danh sách các phản hồi, câu trả lời")
 
# -----------------------------------------

class get_id_plan(BaseModel):
    """Represents a single day's study plan within a module."""
    id: int = Field(..., description="id của kế hoạch cần trích xuất là số , ví dụ : 20251212142134")

# -----------------------------------------

class DailyInfo(BaseModel):
    time_get_up: str = Field(..., description="Thời gian học viên thức dậy, ví dụ: 6h30 sáng")
    breakfast: str = Field(..., description="Bữa sáng của học viên, ví dụ: bánh mì, phở, không ăn")
    study_time: str = Field(..., description="Thời gian học trong ngày, ví dụ: 8h-11h sáng, 14h-16h chiều")
    exercise: str = Field(..., description="Hoạt động thể dục/thể thao, ví dụ: chạy bộ, đá bóng, không tập")


# class FeedbackResult(BaseModel):
#     time: str = Field(default="", description="Phản hồi liên quan đến thời gian học, ví dụ: 'tăng thời lượng chương 3 lên 2 giờ/buổi', giảm thời gia học 1 tiết còn 50 phút")
#     resource: str = Field(default="", description="Phản hồi liên quan đến tài nguyên học tập, ví dụ: 'thêm video minh họa cho bài 2', thêm tài liệu , ...")
#     content: str = Field(default="", description="Phản hồi liên quan đến nội dung hoặc chủ đề, ví dụ: 'bỏ phần luyện tập bài 1 chương 2' , bài hàm số bậc hai cần thêm các dạng bài tập, ...")
#     difficulty: str = Field(default="", description="Phản hồi liên quan đến độ khó, ví dụ: 'giảm độ khó của bài tập chương 5', tăng độ khó bài tập của bài X lên,...")
#     schedule: str = Field(default="", description="Phản hồi liên quan đến lịch học, ví dụ: 'dời buổi học ngày 12/03 sang 14/03' , không phân bổ các bài buổi học vào giờ đêm, ...")

class FeedbackResult(BaseModel):
    valid_inputs: List[str] = Field(default_factory=list, description="Danh sách phản hồi hợp lệ, các phản hồi không hợp lệ thì bỏ đi...")

# class FeedbackResult(BaseModel):
#     feedback_1: str = Field(..., description="phản hồi từ người học")
#     feedback_2: str = Field(..., description="phản hồi từ người học")
#     feedback_3: str = Field(..., description="phản hồi từ người học")
#     feedback_4: str = Field(..., description="phản hồi từ người học")




class AgentProfile(BaseModel):
  
    learning_goal: str = Field(default="", description="Mục tiêu học tập, ví dụ: 'Ôn thi THPT'")
    expected_result: str = Field(default="", description="Kết quả mong muốn")
    deadline: Optional[str] = Field(default="", description="Hạn chót cần đạt mục tiêu (ví dụ: '2025-07-31')")
    available_time: Optional[str] = Field(default="", description="Thời gian có thể học , VD: 10 tiếng/tuần , 60 phút/ngày")
    current_ability: Optional[str] = Field(default="", description="học lực hiện tại , VD: khá , giỏi , nắm căn bản")
    learning_obstacles: str = Field(default="", description="Khó khăn hiện tại")
    learning_preference: Optional[str] = Field(default="", description="Phong cách học tập, VD: Lý thuyết  và bài tập, học qua ví dụ")
    specific_topics_interest: str = Field(default="", description="Chủ đề muốn tập trung học")
    notes: Optional[str] = Field(default="", description="Ghi chú thêm")
    plan_scope: str = Field(..., description="Phạm vi kế hoạch học (ví dụ: 'toàn bộ chương trình', 'học kỳ 1', 'học kỳ 2')")
    
    # finished: bool = Field(default=False, description="Trạng thái đã hoàn thành hồ sơ")urn False


# class DailyStudyItem(BaseModel):
#     """Represents a single day's study plan within a module."""
    
#     day: int = Field(..., description="Day number within the module (starting from 1)", ge=1)
#     hours: float = Field(..., description="Study hours for the day", gt=0, le=24)
#     notes: Optional[str] = Field(None, description="Optional note or focus area for the day")

# class StudyModule(BaseModel):
#     """Represents a complete study module with objectives, resources, and schedule."""
    
#     # id: str = Field(..., description="Unique identifier for the module", min_length=1)
#     module_name: str = Field(..., description="Tên chương học")
#     lesson_titles: List[str] = Field(..., description="Danh sách tên các bài học trong chương")
#     # description: str = Field(..., description="Mô tả ngắn về nội dung chính của chương")

#     # title: str = Field(..., description="Name of the study module", min_length=1)
#     objectives: List[str] = Field(..., description="List of learning objectives for this module", min_items=1)
#     description: Optional[str] = Field(None, description="Brief description of what this module covers")
#     prerequisites: Optional[List[str]] = Field(None, description="Required knowledge before starting this module")
#     duration_estimate: str = Field(..., description="Estimated duration for completing the module (e.g., '4 days')")
#     priority: str = Field("medium", description="Priority level of the module", )
#     # resources: Optional[List[Resource]] = Field(None, description="Suggested learning resources")
#     # daily_study_schedule: Optional[List[DailyStudyItem]] = Field(None, description="Suggested daily study schedule for this module")



# class Constraints(BaseModel):
#     """Represents scheduling and time constraints for the study plan."""
    
#     available_hours_per_day: float = Field(..., description="Maximum number of study hours available per day", gt=0, le=24)
#     deadline: date = Field(..., description="Deadline to complete the entire study plan")
#     max_modules_per_week: Optional[int] = Field(None, description="Maximum number of modules allowed per week (if any)", ge=1)

# class LearnerProfile(BaseModel):
#     """Represents the learner's current level and preferences."""
    
#     level: str = Field(..., description="Current learning level of the student")
#     preferred_study_style: Optional[str] = Field(None, description="Preferred study style (e.g., learning by doing, watching videos)")
#     learning_goals: List[str] = Field(..., description="List of high-level learning goals", min_items=1)

# class StudyPlanOverview(BaseModel):
#     """Complete study plan overview containing all modules, constraints, and learner information."""
    
#     modules: List[StudyModule] = Field(..., description="List of study modules with objectives, priority, resources, and daily time suggestions", min_items=1)
#     total_duration: str = Field(..., description="Overall study plan duration, e.g., '3 weeks', '15 days'")
#     constraints: Constraints = Field(..., description="Study time and scheduling constraints")
#     learner_profile: LearnerProfile = Field(..., description="Student's current level and goals")



# -----------------------------------------------------------------------------
class Resource(BaseModel):
    """Represents a learning resource with type and access information."""
    
    type: str = Field(..., description="loại tài nguyên được cung cấp với các giá trị như : video ,tài liệu")
    # type: Literal["video", "document"] = Field(..., description="Loại tài nguyên: video, document")
    url : str = Field(...,description="đường dẫn , liên kết đến tài nguyên , VD: link video/tài liệu Hàm số bậc hai ,thống kê")
    title: str = Field(..., description="tên/mô tả nội dung của tài nguyên được cung cấp ,VD: Video bài giảng Hàm số , Tài liệu thống kê")

    # resources: List[Resource]  = Field(..., description="Danh sách tài nguyên của chương ")

class StudyModule(BaseModel):
    """Đại diện cho một chương học trong kế hoạch học tập."""
    
    module_name: str = Field(..., description="Tên chương học, VD: CHương 1: mệnh đề , chương 2 : lượng giác")
    lesson_titles: List[str] = Field(..., description="Danh sách các bài học trong chương , VD: bài 1 tập hợp , bài 2 : hàm số , bài 3 : vector")
    objectives: List[str] = Field(..., description="Các mục tiêu học tập cần đạt được trong chương, VD: nắm được vector và cách tính độ dài 1 vector...")
    description: str = Field(..., description="Mô tả ngắn gọn về nội dung chính của chương , VD: giới thiệu cho học sinh về cách tính vecto ,  đưa hàm số bậc 2 về bậc 1..")
    resources: List[Resource]  = Field(..., description="Danh sách tài nguyên của chương , VD: đường dẫn đến tài liệu, video")
    duration_estimate: str = Field(..., description="Thời gian ước tính để hoàn thành chương, ví dụ: 3 tuần, 5 tuần")
    priority: str = Field(..., description="Mức độ ưu tiên của chương (thấp , vừa ,  cao )")

class Constraints(BaseModel):
    """Các ràng buộc về thời gian và lịch học."""
    
    available_hours_per_day: str = Field(..., description="Số giờ học tối đa mỗi ngày VD 2 tiếng ")
    deadline: str = Field(..., description="Hạn chót để hoàn thành toàn bộ kế hoạch học tập")
    max_modules_per_week: int = Field(..., description="Số chương tối đa có thể học mỗi tuần")
    available_days_per_week : List[str] = Field(..., description="Danh sách các ngày có thể học tron tuần , VD: thứ 23,5,7 , chỉ học học thứ 3 và thứ 6 , ngày ngẫu nhiên hoặc các ngày linh động...")

class LearnerProfile(BaseModel):
    """Thông tin người học và phạm vi kế hoạch."""
    
    level: str = Field(..., description="Trình độ hiện tại của người học")
    preferred_study_style: str = Field(..., description="Phong cách học ưa thích (ví dụ: học qua video, thực hành)")
    learning_goals: str = Field(..., description="Các mục tiêu học tập tổng quát")
    plan_name: str = Field(..., description="tên kế hoạch , ví dụ: Kế hoạch thi học sinh giỏi toán 10, Học tốt toán 10")
    plan_scope: str = Field(..., description="Phạm vi kế hoạch học (ví dụ: toàn bộ chương trình, học kỳ 1, chủ đề quan tâm , chủ đề muốn học)")

 
class StudyPlanOverview(BaseModel):
   
    study_modules: List[StudyModule] = Field(..., description="Danh sách các chương học trong kế hoạch")
    constraints: Constraints = Field(..., description="Các giới hạn và ràng buộc thời gian học tập")
    learner_profile: LearnerProfile = Field(..., description="Thông tin người học và mục tiêu")



 
# class StudyModule(BaseModel):
#     module_name: str = Field(..., description="Tên chương học")
#     lesson_titles: List[str] = Field(..., description="Danh sách tên các bài học trong chương")
#     description: str = Field(..., description="Mô tả ngắn về nội dung chính của chương")
#     estimated_duration_days: int = Field(..., description="Số ngày ước lượng để hoàn thành chương")

# class StudyPlanOverview(BaseModel):
   
#     study_modules: List[StudyModule] = Field(..., description="Danh sách các chương học trong kế hoạch")
#     total_duration: str = Field(..., description="Tổng thời gian dự kiến để hoàn thành kế hoạch (ví dụ: '3 tuần', '15 ngày')")
#     constraints: Constraints = Field(..., description="Các giới hạn và ràng buộc thời gian học tập")
#     learner_profile: LearnerProfile = Field(..., description="Thông tin người học và mục tiêu")

    # goal_summary: str = Field(..., description="Tóm tắt mục tiêu học tập của người học")
    # strategy: str = Field(..., description="Chiến lược học tập tổng thể được đề xuất")
    # total_estimated_days: int = Field(..., description="Tổng số ngày ước lượng để hoàn thành toàn bộ kế hoạch")
    # available_days: int = Field(..., description="Tổng số ngày người học có thể dành cho việc học")
    # intensity_suggestion: str = Field(..., description="Gợi ý cường độ học tập (ví dụ: số ngày/tuần)")




# ========================================== details===========================================

# from typing import List
# from pydantic import BaseModel, Field
# class Resource(BaseModel):
#     """Represents a learning resource with type and access information."""
    
#     type: str = Field(..., description="loại tài nguyên được cung cấp với các giá trị như : video ,tài liệu")
#     # type: Literal["video", "document"] = Field(..., description="Loại tài nguyên: video, document")
#     url : str = Field(...,description="đường dẫn , liên kết đến tài nguyên , VD: link video/tài liệu Hàm số bậc hai ,thống kê")
#     title: str = Field(..., description="tên/mô tả nội dung của tài nguyên được cung cấp ,VD: Video bài giảng Hàm số , Tài liệu thống kê")

class DailyStudyItem(BaseModel):
    """Represents a single day's study plan within a module."""
    
    # day: int = Field(..., description="Day number within the module (starting from 1)", ge=1)
    hours: float = Field(..., description="Thời gian bắt đầu học , VD: 7:00 , 8:30")
    # # notes: Optional[str] = Field(None, description="Optional note or focus area for the day")
    # session_date: str = Field(..., description="Ngày học, định dạng YYYY-MM-DD , VD: 2025-03-12")
    # duration_minutes: int = Field(..., description="Thời lượng buổi học , VD : 60 phút , 2 giờ")

 
# buoi hoc 
class Session(BaseModel):
    session_id: str = Field(..., description="đinh danh của buổi học trong bài học hay id buổi học , VD:T10-ĐS-C3-B1-B1 , T10-HH-C1-B3_B5 ")
    session_number: int = Field(..., description="Số thứ tự buổi học , VD: 1 , 2,3 ")
    status: str = Field(default="Chưa hoàn thành", description="Trạng thái buổi đã hoàn thành hay chưa, mặc định là chưa hoàn thành")
    session_name: str = Field(..., description="Tên khái quát buổi học , VD: Làm quen với mệnh đề, Vận dụng các dạng toán trong mệnh đề, Ôn tập mệnh đề, ...")
    daily : DailyStudyItem = Field(..., description="Yếu tố ngày giờ liên quan đến buổi học")
    core_content: str = Field(..., description="Trọng tâm kiến thức của buổi học , VD: Phương trình đường thẳng , cách viết phương trình, ...")
    objectives : List[str] = Field(..., description="Danh sách mục tiêu cần nắm trong buổi học , VD: nắm cách tính khoảng cách đến đường thẳng , Vận dụng vẽ phương trình đường thẳng ...")
    activities: List[str] = Field(..., description="Danh sách hoạt động trong buổi học , VD: kết hợp ôn tập và học lý thuyết , thực hành các dạng toán hình chuyển động ...")
    assignments: List[str] = Field(..., description="Danh sách các dạng bài tập , VD: đường thẳng trong mặt phẳng , tính khoảng cách ,...")
    resources: List[Resource] = Field(default_factory=list, description="Danh sách tài nguyên, video , tài liệu và bài tập ")

# bài hoc
class Lesson(BaseModel):
    # chapter_title : str = Field(..., description="Tên chương học")
    lesson_id: str = Field(..., description="đinh danh của bài học hay id bài học , VD:T10-ĐS-C3-B1 , T10-HH-C1-B3 ")
    lesson_plan: str = Field(..., description="mô tả phạm vi bài học , VD:Đại số Học kỳ: Kì 1 , Hình học học kỳ:2")
    lesson_dif: str = Field(..., description="độ khó bài học , VD:2/5 (Nhận biết & Thông hiểu)")
    total_number_sessions_in_lesson: int = Field(..., description="tổng số buổi học của bài học , VD: 1 , 2,3 ")
    lesson_title: str = Field(..., description="Tên bài học , VD: Phương trình đường elip")
    descriptions: str = Field(..., description="Giới thiệu ngắn gọn nội dung bài học , VD: cách biểu diễn đường thẳng , qua đó tính góc và khoảng cách đến đường thẳng khác, ...")
    objectives: List[str] = Field(..., description="Danh sách mục tiêu cần nắm được của bài học, VD: vẽ đường thẳng , dịch chuyển đường thẳng , vector đường thẳng, ...")
    sessions: List[Session] = Field(..., description="Các buổi học chi tiết cho bài học này")


class DetailPlan(BaseModel):
    module_name: str = Field(..., description="Tên chương học ,VD: Chương 9: Phương pháp tọa độ trong mặt phẳng")
    total_number_session_in_module: int = Field(..., description="tổng số buổi học của 1 chương/module, tổng số buổi của các bài trong 1 chương/module , VD: 5 , 10 , 12  ")
    total_number_session_done_in_module: int = Field(default=0, description="Số buổi đã hoàn thành của chương/module đó , mặc định = 0")
    lessons: List[Lesson] = Field(..., description="Danh sách các bài học thuộc chương")
    # number_sessions: str = Field(..., description="Số lượng buổi học của 1 bài học , VD: 5 buổi , 2 buổi ...")
     
class StudyPlanDetail(BaseModel):
    total_number_sessions : int = Field(..., description="Tổng số buổi học của  toàn bộ kế hoạch,VD:7,13,34,..")
    sessions_done: int = Field(default=0, description="Số buổi đã hoàn thành, mặc định = 0")
    detail_plans: List[DetailPlan] = Field(..., description="Danh sách các chương học với kế hoạch chi tiết"
    )


class State(TypedDict):  
    messages: Annotated[list[AnyMessage], add_messages]
    profile_user :  Optional[AgentProfile]
    profile_completed: bool
    ok: str
    overview_completed: bool
    overview_result: Optional[StudyPlanOverview]
    study_details_result : Optional[StudyPlanDetail] 
    detail_completed: bool 
    plan_id: str
    status:str
    review_user : Optional[DailyInfo]
    review_result : str
    review_completed: bool
    plan_data: str
    qa_planner_completed: bool
    flow: str

    # context: Optional[str]  # Context for overview planning
    # learning_goal: str   
    # expected_result: str  
    # deadline: str 
    # available_time: str
    # current_ability: str
    # learning_obstacles: str  # Changed from str to List[str]
    # learning_preference: str
    # specific_topics_interest: str # Changed from str to List[str]
    # notes: str


class ReviewInput(BaseModel):
    satisfied: bool = Field(...,description="Người học có hài lòng với kế hoạch học tập chi tiết hay không , VD True = hài lòng, False = không hài lòng.")
    reason: Optional[str] = Field(None,description="Lý do không hài lòng với kế hoạch (chỉ bắt buộc nếu satisfied=False).")


 