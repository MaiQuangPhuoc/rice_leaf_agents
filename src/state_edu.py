from typing import Annotated, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


# ── Schema bước 1: Hồ sơ học sinh ───────────────────────────────────────────

class KienThuc(BaseModel):
    chu_de: str
    diem: Optional[float] = None
    muc_do: Optional[str] = None  # "Cơ bản" | "Khá" | "Giỏi"


class StudentProfile(BaseModel):
    # Bắt buộc
    mon_hoc: str = Field(..., description="Môn học, ví dụ: Toán")
    khoi_lop: int = Field(..., description="Khối lớp, ví dụ: 10")
    pham_vi_kiem_tra: list[str] = Field(..., description="Chương hoặc bài cần kiểm tra")

    # Khuyến khích
    muc_dich: Optional[str] = None          # "Ôn tập" | "Luyện thi" | "Kiểm tra nhanh"
    loai_de: Optional[str] = None           # "Trắc nghiệm" | "Tự luận" | "Kết hợp"
    so_cau_hoi: Optional[int] = None
    thoi_gian_lam_bai: Optional[int] = None # phút

    # Cá nhân hóa
    muc_tieu_diem: Optional[float] = None   # 5 → 10
    ho_so_kien_thuc: Optional[list[KienThuc]] = None
    ghi_chu: Optional[str] = None


# ── ExamState: chạy xuyên suốt toàn bộ pipeline ─────────────────────────────

class ExamState(TypedDict):
    # Bước 1
    messages: Annotated[list, add_messages]
    student_profile: Optional[dict]          # StudentProfile.model_dump()
    profile_complete: bool                   # True khi đủ 3 trường bắt buộc

    # Bước 2
    retrieved_chunks: list[dict]
    scope_chapters: dict
    scope_lessons: dict
    retrieve_complete: bool
 

    # Bước 3
    knowledge_profile: dict
    knowledge_queue: Optional[list]    # [(chương, bài)] còn cần hỏi
    knowledge_pending: Optional[dict]  # {chương, bài, sections} đang hỏi
    knowledge_scores: dict             # {chương: {bài: {section: score}}}
    knowledge_done: bool
    completed_build_knowlege : bool
    
    # Bước 4
    exam_matrix: dict
    gop_y_matrix: str
    matrix_done: bool

    # Bước 5
    question_specs: list[dict]
    specs_done: bool
 

    # Bước 6
    generated_exam: list[dict]
    exam_memory: list[dict]
    generate_done:  bool

    # Bước 7
    exam_review: dict
    final_exam: list[dict]
    evaluate_done: bool

    # Meta
    current_step: str
    error: Optional[str]
