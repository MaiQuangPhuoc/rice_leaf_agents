from langchain_core.tools import tool 
# from tavily import TavilyClient
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
# from src.configs import env_config
# from langchain_community.tools. 
# from langchain_core.documents import Document
from src.state import extract_schema, query_transform_schema


# tools.py
import re
from typing import Any, Dict

from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
 

def extract_tool(llm_client, state :extract_schema):
    """Create tool for parsing output.""" 
    @tool(response_format="content_and_artifact")
    def extract_output(query: str):
        """Tool để trích xuất đầu vào của người dùng thành định dạng có cấu trúc."""
        llm_output = llm_client._llm.with_structured_output(state)
        
        response = llm_output.invoke(query)
        
        return "Đang trích xuất ..." if response else "Không thể trích xuất yêu cầu", response
    
    return extract_output

def extract_tool_key(llm_client, state: extract_schema):
    """Create tool for parsing output."""
    
    llm_output = llm_client._llm.with_structured_output(state)
    
    @tool
    def extract_output(query: str) -> dict:
        """Tool để trích xuất các từ khoá quan trọng từ nội dung thông tin bệnh lá lúa"""
        response = llm_output.invoke(query)
        
        if response is None:
            return {}
        
        return response.dict() if hasattr(response, "dict") else response
    
    return extract_output

def reprocessing_input(raw_input: Any) -> Dict:
    """
    Tiền xử lý input dưới dạng TEXT.
    Trả về:
        {
            "clean_text": str hoặc None,
            "is_valid": bool,
            "reason": str (nếu invalid)
        }
    """

    # 1. validate input
    if raw_input is None:
        return {
            "clean_text": None,
            "is_valid": False,
            "reason": "Input None"
        }

    if not isinstance(raw_input, str):
        return {
            "clean_text": None,
            "is_valid": False,
            "reason": "Không phải text"
        }

    text = raw_input.strip()

    # 2. xóa markdown, html
    text = re.sub(r"<.*?>", " ", text)
    text = re.sub(r"`{1,3}.*?`{1,3}", " ", text)

    # 3. lowercase
    text = text.lower()

    # 4. loại ký tự rác
    text = re.sub(
        r"[^a-zA-Z0-9áàảãạăằắẳẵặâầấẩẫậđéèẻẽẹêềếểễệíìỉĩịóòỏõọôồốổỗộơờớởỡợ"
        r"úùủũụưừứửữựýỳỷỹỵ\s]",
        " ",
        text,
    )

    # 5. gom space
    text = re.sub(r"\s{2,}", " ", text).strip()

    # 6. kiểm tra text rỗng hoặc vô nghĩa
    if text == "":
        return {
            "clean_text": None,
            "is_valid": False,
            "reason": "Text rỗng sau khi xử lý"
        }

    if len(text) < 2:
        return {
            "clean_text": text,
            "is_valid": False,
            "reason": "Text quá ngắn"
        }

    # 7. trả về kết quả  
    return {
        "clean_text": text,
        "is_valid": True,
        "reason": ""
    }

# input = "BỆNH ĐẠO ON /có cac TRIỆU chung gi?"
# result = reprocessing_input(input)
# print(result)   

# def router_rule_based(intent: str, keywords: list[str], clean_text: str) -> int:
    """
    Rule-based router cho chatbot bệnh lá lúa.
    Trả về:
        1 → chuyển tiếp sang DiseaseAgent
        0 → không chuyển tiếp
    """

    # ====== 1. Intent cần chuyển tiếp ======
    INTENT_REDIRECT = [
        # nhóm chẩn đoán bệnh
        "hỏi bệnh", "mô tả triệu chứng", "chẩn đoán bệnh",
        "nhận diện bệnh", "xác định bệnh",

        # nhóm xử lý bệnh
        "hỏi thuốc", "hỏi cách trị", "hỏi xử lý", "hỏi phun thuốc",
        "xin hướng dẫn điều trị", "kế hoạch xử lý",

        # nhóm nông nghiệp chung
        "trồng trọt", "cải tạo đất", "bón phân", "kỹ thuật chăm sóc",
        "quản lý dinh dưỡng", "tư vấn nông nghiệp", "tư vấn lúa",

        # sâu bệnh
        "kiểm soát sâu bệnh", "hỏi về sâu", "hỏi về nấm", "hỏi dịch hại",

        # khi input là ảnh
        "mô tả ảnh", "phân tích hình ảnh",
    ]

    # ====== 2. Từ khóa bệnh – triệu chứng – sâu bệnh ======

    COMMON_SYMPTOMS = [
        "đốm", "vàng", "bạc", "cháy", "héo", "rụng",
        "thối", "khô", "mụn", "xỉn", "xám", "sọc",
        "nâu", "đen", "co lại", "khảm", "biến màu", "loang",
    ]

    SPECIFIC_DISEASES = [
        "đạo ôn", "khô vằn", "cháy bìa lá", "cháy lá", "bạc lá",
        "thối thân", "vàng lá chín sớm", "lem lép hạt",
        "đốm nâu", "lùn xoắn lá", "lùn sọc đen", "thối rễ",
        "đốm trắng",
    ]

    PESTS_PATHOGENS = [
        "rầy", "rầy nâu", "bọ xít", "sâu cuốn lá", "sâu đục thân",
        "nấm", "vi khuẩn", "virus", "bọ trĩ", "ốc bươu vàng",
    ]

    AGRI_CONTEXT = [
        "phun thuốc", "thuốc trừ", "phân bón", "bón phân",
        "tưới", "quản lý nước", "gieo sạ", "giống lúa", "mật độ",
    ]

    disease_keywords = list(set(
        COMMON_SYMPTOMS + SPECIFIC_DISEASES + PESTS_PATHOGENS + AGRI_CONTEXT
    ))

    text = clean_text.lower().strip()

    # ====== Rule 1: intent hợp lệ → chuyển tiếp ======
    if intent in INTENT_REDIRECT:
        return 1

    # ====== Rule 2: xuất hiện từ khóa triệu chứng hoặc bệnh → chuyển tiếp ======
    for kw in disease_keywords:
        if kw in text:
            return 1

    # ====== Rule 3: nếu schema đã trích xuất được keywords → chuyển tiếp ======
    if keywords and len(keywords) > 0:
        for kw in keywords:
            if kw.lower() in disease_keywords:
                return 1

    # ====== Rule 4: không hợp lệ → không chuyển tiếp ======
    return 0

 
def extract_summary(text):
    start_key = "tóm lại"
    end_key = "bạn"

    text_lower = text.lower()

    # tìm vị trí bắt đầu
    start_idx = text_lower.find(start_key)
    if start_idx == -1:
        return None

    # tìm vị trí kết thúc (trước chữ "bạn")
    end_idx = text_lower.find(end_key, start_idx)
    if end_idx == -1:
        # nếu không có chữ "bạn" phía sau, lấy đến hết
        return text[start_idx:].strip()

    return text[start_idx:end_idx].strip()

# def extract_summary(text):
#     key = "tóm lại"
#     idx = text.lower().find(key)
#     if idx == -1:
#         return None
#     return text[idx:].strip()

def tools_query_transform(llm_client):
    @tool(response_format="content_and_artifact")
    def query_transform_tool(query: str):
        """Phân tích, disambiguate và viết lại câu hỏi dựa trên lịch sử hội thoại."""

        llm_struct = llm_client._llm.with_structured_output(query_transform_schema)

        result = llm_struct.invoke(query)

        return {
            "message": "Transformed query successfully",
            "artifact": result
        }

    return query_transform_tool



# def router_rule_based(extracted):

  
#     intent = (extracted.intent if hasattr(extracted, "intent") else extracted.get("intent", "")).lower()
#     keywords = (extracted.keywords if hasattr(extracted, "keywords") else extracted.get("keywords", []))
#     clean_text = (extracted.clean_text if hasattr(extracted, "clean_text") else extracted.get("clean_text", "")).strip()

#     if isinstance(keywords, str):
#         keywords = keywords.lower().split()
#     else:
#         keywords = [kw.lower() for kw in keywords]

#     # Rule 0: loại bỏ

#     if intent in ["ngoài phạm vi", "không xác định", "không chắc"]:
#         return 0
#     if len(clean_text) == 0:
#         return 0

#     # Rule 1: chuyển tiếp RAG - bệnh, triệu chứng, thuốc, sâu bệnh, phân bón, gieo sạ,...
#     rag_intents = [
#         "hỏi bệnh", "mô tả triệu chứng", "hỏi thuốc", "tư vấn thuốc", 
#         "hỏi sâu bệnh", "tư vấn phân bón", "hỏi gieo sạ", "tư vấn canh tác"
#     ]
#     rag_keywords = [
#         "bệnh", "triệu chứng", "thuốc", "sâu", "bệnh lá", "phân bón", 
#         "gieo sạ", "phun thuốc", "virus", "nấm", "cây lúa"
#     ]

#     # Rule 2: tool agent - kế hoạch, tính toán, lịch phun, dự báo, quy trình,...
#     tool_intents = [
#         "kế hoạch cải tạo đất", "lịch phun thuốc", "tính toán", "check list",
#         "quy trình", "dự báo", "tư vấn kỹ thuật", "lập kế hoạch"
#     ]
#     tool_keywords = [
#         "tính toán", "kế hoạch", "lịch", "dự báo", "checklist", "quy trình", "liều lượng"
#     ]

#     # Rule 3: câu hỏi ngoài lề, hỗ trợ, kiến thức chung, giá cả, mùa vụ, thời tiết,...
#     other_keywords = [
#         "giá", "mùa vụ", "thời tiết", "hỗ trợ", "mua bán", "hỏi chung", "thông tin chung", "tin tức",
#         "đất", "nước", "giống", "quy trình chung", "kỹ thuật trồng"
#     ]

#     # Ưu tiên intent
#     if intent in rag_intents:
#         return 1
#     if intent in tool_intents:
#         return 2

#     # Kiểm tra keywords
#     if any(kw in rag_keywords for kw in keywords):
#         return 1
#     if any(kw in tool_keywords for kw in keywords):
#         return 2
#     if any(kw in other_keywords for kw in keywords):
#         return 3

#     # Nếu intent chứa từ hỏi hoặc tư vấn thì cho qua 1
#     if any(w in intent for w in ["hỏi", "mô tả", "tư vấn"]):
#         return 1

#     # Mặc định
#     return 0
def router_rule_based(extracted):
    intent = (extracted.intent if hasattr(extracted, "intent") else extracted.get("intent", "")).lower().strip()
    subject = (extracted.subject if hasattr(extracted, "subject") else extracted.get("subject", "")).lower().strip()
    keywords = (extracted.keywords if hasattr(extracted, "keywords") else extracted.get("keywords", []))
    clean_text = (extracted.clean_text if hasattr(extracted, "clean_text") else extracted.get("clean_text", "")).lower().strip()
    confidence = (extracted.confidence if hasattr(extracted, "confidence") else extracted.get("confidence", 0))

    if isinstance(keywords, str):
        keywords = keywords.lower().split()
    else:
        keywords = [kw.lower() for kw in keywords]

    # Rule 0: KHÔNG CHUYỂN TIẾP
    # - Intent nằm trong nhóm không rõ, ngoài phạm vi hoặc không chắc chắn
    # - Clean_text rỗng
    # - Confidence quá thấp (ví dụ < 0.5)
    # - Nội dung có ngôn từ tiêu cực, spam, không liên quan (đánh dấu bằng từ khóa hoặc intent)
    invalid_intents = ["ngoài phạm vi", "không xác định", "không chắc", ""]
    invalid_keywords = ["spam", "đùa", "tán gẫu", "bán lúa", "xàm", "chửi", "ngôn từ quá khích"]

    if intent in invalid_intents:
        return 0
    if confidence < 0.5:
        return 0
    if len(clean_text) == 0:
        return 0
    if any(kw in keywords for kw in invalid_keywords):
        return 0

    # Rule 1: CHUYỂN TIẾP TRỌNG TÂM BỆNH LÁ LÚA
    # Các câu hỏi trực tiếp liên quan đến bệnh lá lúa, nguyên nhân, triệu chứng, cách xử lý, thuốc, sâu bệnh, giống,…
    route1_intents = [
        "hỏi bệnh", "mô tả triệu chứng", "hỏi thuốc", "tư vấn thuốc",
        "hỏi sâu bệnh", "tư vấn phân bón", "hỏi gieo sạ", "tư vấn canh tác",
        "hỏi giống", "tư vấn bệnh"
    ]
    route1_keywords = [
        "bệnh", "triệu chứng", "thuốc", "sâu", "bệnh lá", "phân bón", "gieo sạ",
        "phun thuốc", "virus", "nấm", "cây lúa", "đạo ôn", "đốm nâu", "bạc lá",
        "khô vằn", "cháy lá", "giống lúa", "cách xử lý", "biện pháp"
    ]

    # Rule 2: CHUYỂN TIẾP NGOÀI TRỌNG TÂM NHƯ VI KHUẨN, NẤM, THỜI TIẾT,...
    route2_intents = [
        "kế hoạch cải tạo đất", "lịch phun thuốc", "tính toán", "check list",
        "quy trình", "dự báo", "tư vấn kỹ thuật", "lập kế hoạch",
        "hỏi thời tiết", "hỏi vi khuẩn", "hỏi nấm", "hỏi virus"
    ]
    route2_keywords = [
        "tính toán", "kế hoạch", "lịch", "dự báo", "checklist", "quy trình",
        "vi khuẩn", "virus", "nấm", "thời tiết", "đất đai"
    ]

    # Ưu tiên kiểm tra intent trước
    if intent in route1_intents:
        return 1
    if intent in route2_intents:
        return 2

    # Kiểm tra keywords nếu intent không rõ ràng
    if any(kw in route1_keywords for kw in keywords):
        return 1
    if any(kw in route2_keywords for kw in keywords):
        return 2

    # Nếu intent có chứa từ khóa hỏi, mô tả, tư vấn thì ưu tiên route 1
    if any(w in intent for w in ["hỏi", "mô tả", "tư vấn"]):
        return 1

    # Mặc định không chuyển tiếp
    return 0



# def artifact_to_plain_text(artifact):
#     d = artifact.dict()

#     # xử lý list keywords thành chuỗi
#     keywords = ", ".join(d["keywords"])

#     # tạo text sạch
#     text = (
#         f"intent: {d['intent']}\n"
#         f"keywords: {keywords}\n"
#         f"clean_text: {d['clean_text']}"
#     )

#     return text
def artifact_to_plain_text(artifact):
    d = artifact.dict()

    keywords = ", ".join(d.get("keywords", []))

    text = (
        f"intent: {d.get('intent')}\n"
        f"subject: {d.get('subject')}\n"
        f"keywords: {keywords}\n"
        f"clean_text: {d.get('clean_text')}\n"
        f"confidence: {d.get('confidence')}"
    )

    return text

# data = {
#     "input_type": "text",
#     "intent": "nấu ăn",
#     "keywords": ["chiên trúng", "chống mặt", "nấu canh"],
#     "clean_text": "toi cần công thức nấu ăn cho món chiên trứng và canh chua cá lóc"
# }
# print(router_rule_based(data))
