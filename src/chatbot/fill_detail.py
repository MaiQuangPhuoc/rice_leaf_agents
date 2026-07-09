import os
import sys
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import datetime
from src.modules.rag.retrievers2 import VectorStoreRetriever
from src.clients.embedding import embeddings_qa
from src.configs import env_config

_retriever = VectorStoreRetriever(
    url=env_config.qdrant_url,
    api_key=env_config.qdrant_api_key,
    embeddings=embeddings_qa,
    collection_name="documents",
    top_k=15,
)

DISEASE_MAP = {
    "đạo ôn": "DỮ LIỆU BỆNH HỌC: BỆNH ĐẠO ÔN LÁ",
    "đốm nâu": "BỆNH ĐỐM NÂU",
}


PHASE_KEYWORDS = {
    "khảo sát":      "triệu chứng nhận diện vết bệnh đạo ôn đánh giá mức độ",
    "xử lý":         "thuốc tricyclazole liều lượng phun phòng trị đạo ôn",
    "kiểm soát":     "ngăn lây lan bào tử đạo ôn quản lý nước đạm",
    "theo dõi":      "đánh giá hiệu quả thuốc phục hồi lá lúa sau phun",
    "ổn định":       "phục hồi sinh trưởng bón phân kali lúa đẻ nhánh sau bệnh",
}

def _get_phase_keyword(phase_name: str) -> str:
    phase_lower = phase_name.lower()
    for key, kw in PHASE_KEYWORDS.items():
        if key in phase_lower:
            return kw
    return ""

def build_queries(context_dict: dict, plan: dict) -> list[dict]:
    disease    = context_dict.get("disease", "")
    rice_stage = context_dict.get("rice_stage", "")
    severity   = context_dict.get("disease_severity", "")
    weather    = context_dict.get("weather_description", "")

    queries = []
    for phase in plan.get("skeleton", []):
        phase_name   = phase.get("phase", "")
        phase_kw     = _get_phase_keyword(phase_name)
        query = (
            f"{disease} {rice_stage} {severity} {weather} {phase_kw}"
        ).strip()
        queries.append({"phase": phase_name, "query": query})

    print(f"[build_queries]:\n{json.dumps(queries, ensure_ascii=False, indent=2)}")
    return queries


PLAN_SAVE_DIR = r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\src\memory\plan"

def save_plan(plan: dict) -> str:
    os.makedirs(PLAN_SAVE_DIR, exist_ok=True)
    filename = datetime.datetime.now().strftime("%H-%M-%S") + ".json"
    filepath = os.path.join(PLAN_SAVE_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print(f"[save_plan]: {filepath}")
    return filepath


# lấy tên bệnh ( ví dụ: đạo ôn lá, bệnh đạo ôn , lá lúa mắc đạo ôn ---> đạo ôn)
DISEASE_KEYWORDS = ["đạo ôn", "đốm nâu", "bạc lá"]

def extract_disease_key(disease_raw: str) -> str | None:
    disease_raw = disease_raw.strip().lower()
    for keyword in DISEASE_KEYWORDS:
        if keyword in disease_raw:
            return keyword
    return None

def retrieve_for_plan(context_dict: dict, plan: dict) -> str:
    disease_raw     = (context_dict.get("disease") or "").strip().lower()
    disease_key = extract_disease_key(disease_raw)

    metadata_filter = DISEASE_MAP.get(disease_key)

    queries  = build_queries(context_dict, plan)
    seen     = set()
    all_docs = []

    for item in queries:
        docs = _retriever.search_and_filter_rerank(
            query=item["query"],
            disease=[metadata_filter] if metadata_filter else None,
            min_results=1,
            filter_top_k=10,
            rerank_top_k=3,
        )
        for doc in docs:
            # filter theo metadata["disease"]
            if metadata_filter and doc.metadata.get("disease") != metadata_filter:
                continue
            doc_id = doc.page_content[:80]
            if doc_id not in seen:
                seen.add(doc_id)
                all_docs.append((item["phase"], doc))

    if not all_docs:
        return "Không tìm thấy tài liệu liên quan."

    lines = []
    for phase, doc in all_docs:
        lines.append(
            f"[Phase: {phase}] "
            f"Topic: {doc.metadata.get('topic', 'N/A')}\n"
            f"{doc.page_content}"
        )

    return "\n\n".join(lines)


FILL_DETAIL_PROMPT_PATH = r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\FILL_DETAIL.txt"

def build_fill_prompt(context_dict: dict, plan: dict, context_rag: str) -> str:
    with open(FILL_DETAIL_PROMPT_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    return (
        template
        .replace("{plan_context}", json.dumps(context_dict, ensure_ascii=False, indent=2))
        .replace("{skeleton}", json.dumps(plan.get("skeleton", []), ensure_ascii=False, indent=2))
        .replace("{context_rag}", context_rag)
    )


def fill_detail(llm_client, context_dict: dict, plan: dict) -> list:
    context_rag  = retrieve_for_plan(context_dict, plan)
    final_prompt = build_fill_prompt(context_dict, plan, context_rag)

    print(f"[fill_detail prompt]:\n{final_prompt}")

    response = llm_client._llm.invoke([
        {"role": "system", "content": final_prompt},
        {"role": "user",   "content": "Sinh kế hoạch chi tiết từng ngày."},
    ])

    raw      = response.content.strip().replace("```json", "").replace("```", "").strip()
    steps    = json.loads(raw)
    print(f"[fill_detail steps]:\n{json.dumps(steps, ensure_ascii=False, indent=2)}")

    plan["steps"]  = steps
    plan["status"] = "detail"
    save_plan(plan)
    return plan



