from pydantic import BaseModel, Field, field_validator
from typing import Annotated, List, Literal, Optional
from typing_extensions import TypedDict
# # from datetime import date
from langgraph.graph import StateGraph, MessagesState, START, END , add_messages
from langchain_core.messages import (AnyMessage)

# from schema import PersonalProfile
# print("ok")

# class query_transform_schema(BaseModel):
#     possible_meanings: List[dict] = Field(..., description="Danh sách các cách hiểu có thể của câu hỏi cùng với điểm phù hợp tương ứng.")
#     chosen_meaning: str = Field(..., description="Cách hiểu được chọn là phù hợp nhất dựa trên đánh giá.")
#     new_query: str = Field(..., description="Câu hỏi đã được viết lại sao cho rõ ràng và cụ thể hơn.")
#     score: float = Field(..., description="Điểm đánh giá mức độ chắc chắn của câu hỏi đã được viết lại (từ 0 đến 1).")
#     need_clarification: bool = Field(..., description="Chỉ ra liệu có cần yêu cầu người dùng làm rõ câu hỏi hay không.")

# class MeaningOption(BaseModel):
#     meaning: str = Field(..., description="Cách hiểu cụ thể của câu hỏi")
#     fit_score: float = Field(..., ge=0.0, le=1.0, description="Độ phù hợp của cách hiểu này (0.0 – 1.0)")

class query_transform_schema(BaseModel):
    possible_meanings: List[dict] = Field(
        ..., 
        description="Danh sách các cách hiểu có thể, kèm điểm phù hợp"
    )
    chosen_meaning: str = Field(..., description="Cách hiểu được chọn là tốt nhất")
    new_query: str = Field(..., description="Câu hỏi đã được viết lại rõ ràng, đầy đủ")
    score: float = Field(..., ge=0.0, le=1.0, description="Độ tự tin tổng thể của việc viết lại (0.0 – 1.0)")
    need_clarification: bool = Field(..., description="Có cần hỏi lại người dùng không")

# class extract_schema(BaseModel):
#     input_type: str = Field(..., description="type của input, vd: text, image, unvailed")
#     intent: str = Field(..., description="ý định hướng đến của người dùng, vd: hỏi bệnh, hỏi thuốc, kế hoạchcải tạo đất")
#     keywords: List[str] = Field(..., description="danh sách các từ khóa chính liên quan đến yêu cầu của người dùng")
#     clean_text: str = Field(..., description="nội dung đã được làm sạch, tách từ, chuẩn hóa")

class extract_schema(BaseModel):
    intent: str = Field(
        ...,
        description="ý định chính của người dùng, dùng để routing (vd: hỏi bệnh, hỏi thuốc, mô tả triệu chứng, xác nhận thông tin, phản biện, ngoài phạm vi)"
    )
    subject: Optional[str] = Field(
        None,
        description="chủ thể chính nếu có (vd: bệnh bạc lá, bệnh đạo ôn, lá lúa, sâu hại)"
    )
    keywords: List[str] = Field(
        ...,
        description="các từ khóa quan trọng xuất hiện trực tiếp trong câu (đã chuẩn hóa)"
    )
    clean_text: str = Field(
        ...,
        description="câu đã được chuẩn hóa, sửa lỗi chính tả, viết thường, không ký tự rác"
    )
    confidence: float = Field(
        ...,
        description="độ chắc chắn của intent (0–1)"
    )

class extract_schema_key_word_chunking(BaseModel):
    keywords: List[str] = Field(
         ...,
        description="Danh sách các từ khóa trích xuất từ nội dung, ví dụ : 'hạch nấm', 'sợi nấm', 'nệm xâm nhiễm', 'enzyme phân giải', 'lây lan dọc', 'lây lan ngang', 'tán lá'"
    )

class State1(TypedDict):  
    messages: Annotated[list[AnyMessage], add_messages]
    messages_router: Annotated[list[AnyMessage], add_messages]
    state_router: bool
    state_main: bool
    state_api: bool
    state_other: bool
    route: Optional[int]    
    extract : Optional[extract_schema]
    history: Annotated[list, add_messages]
    query_transform: str


class SkeletonPhase(BaseModel):
    phase: str = Field(description="Tên giai đoạn. Ví dụ: Giai đoạn 1: Khảo sát ban đầu,Giai đoạn 2: Quá trình cải tạo đất hay quy trình phòng bệnh đạo ôn..")
    duration_days: int = Field(description="Số ngày của giai đoạn này, ví dụ :4 ngày , 6 ngày , 1 tuần ....")
    main_content: str = Field(description="Nội dung chính cần thực hiện, ví dụ : Thu thập thống kế ruộng vườn , Cai tạo đất tới xốp hay phun thuốc phòng bệnh")
    expected_result: str = Field(description="Kết quả kỳ vọng sau giai đoạn, ví dụ : thống kê thông tin, cải tạo đất , diệt bệnh tận gốc...")




class PlanStep(BaseModel):
    day: int                        # ngày thứ mấy
    action: str                     # việc cần làm
    medicine: Optional[str]         # thuốc dùng
    dosage: Optional[str]           # liều lượng
    condition: Optional[str]        # điều kiện thực hiện
    note: Optional[str]             # ghi chú
    phase: Optional[str] = None   # thuộc giai đoạn nào, vd: "Giai đoạn 1"

class PlanContext(BaseModel):
    disease:             Optional[str] = Field(default=None, description="Mục tiêu chính: tên bệnh hoặc công việc. Ví dụ: đạo ôn, khô vằn, cải tạo đất.")
    location:            Optional[str] = Field(default=None, description="Địa điểm ruộng. Ví dụ: Quảng Nam, Cần Thơ.")
    duration_days:       Optional[int] = Field(default=None, description="Số ngày kế hoạch. Ví dụ: 7, 14, 21.")
    disease_scale:       Optional[str] = Field(default=None, description="Phạm vi bị ảnh hưởng. Ví dụ: vài khóm, cả ruộng.")
    disease_duration:    Optional[str] = Field(default=None, description="Thời gian xuất hiện. Ví dụ: hôm nay, 3 ngày.")
    disease_severity:    Optional[str] = Field(default=None, description="Mức độ. Ví dụ: nhẹ, trung bình, nặng.")
    rice_stage:          Optional[str] = Field(default=None, description="Giai đoạn lúa. Ví dụ: đẻ nhánh, làm đòng, trổ bông.")
    rice_variety:        Optional[str] = Field(default=None, description="Giống lúa. Ví dụ: OM5451, ST25.")
    current_medicine:    Optional[str] = Field(default=None, description="Thuốc đang dùng. Ví dụ: Tricyclazole, chưa xử lý.")
    weather_description: Optional[str] = Field(default=None, description="Thời tiết theo mô tả người dùng. Ví dụ: mưa nhiều, nắng nóng.")



class Plan(BaseModel):
    plan_id: str                    # uuid
    user_id: str
    thread_id: str
    disease: str                    # bệnh cần phòng trị
    duration_days: int              # tổng số ngày
    location: Optional[str]        
    rice_stage: Optional[str]      
    status: Literal["skeleton", "detail", "review", "done"]
    skeleton: list[SkeletonPhase]             # sườn kế hoạch ["Tuần 1: ...", "Tuần 2: ..."]
    steps: list[PlanStep]           # chi tiết từng bước
    created_at: str
    updated_at: str

class UserMemory(BaseModel):
    user_id: str
    thread_id: str
    location: Optional[str] = None          # vị trí ruộng
    rice_stage: Optional[str] = None        # giai đoạn lúa
    current_disease: Optional[str] = None   # bệnh đang xử lý
    disease_history: list[str] = []         # tất cả bệnh đã đề cập
    last_topic: Optional[str] = None        # chủ đề cuối cùng
    disease_progress: Optional[str] = None  # tiến độ xử lý bệnh
    updated_at: Optional[str] = None    


class QueryExtract(BaseModel):
    query_clear: str                   
    disease: Optional[list[str]] = None  
    scientific_name: Optional[str] = None
    topic: Optional[str] = None
    keywords: list[str] = []


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]  # messages của user
    state_router: bool   # có được đi qua router hay không
    state_rag: bool      # true → đến rag_agent
    state_api: bool      # true → đến api_agent
    state_other: bool    # true → đến other_agent
    route: Optional[int] # 1: rag_agent, 2: api_agent, 3: other_agent
    history: Annotated[list[AnyMessage], add_messages]
    query_extract: Optional[QueryExtract]
    last_message: Optional[AnyMessage]
    user_memory: Optional[UserMemory] 
    current_plan: Optional[Plan]     
    plan_mode: Optional[str] 
 


