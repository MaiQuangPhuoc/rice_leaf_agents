import sys ,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.clients.databases import qdrant 
from src.clients.llm import LLMClient
from State import AgentProfile , State   
from src.agents.profile_collector import ProfileCollector
from src.agents.overview_planner import OverViewPlanner
from src.agents.detail_planner import DetailPlanner
import asyncio
from datetime import datetime


from flask import Flask, request, jsonify
from flask_cors import CORS
import json

from langgraph.graph import MessagesState, StateGraph
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
import asyncio
from langchain_core.runnables import RunnableConfig
from pydantic_settings import BaseSettings
from langchain_core.messages import HumanMessage
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.configs import env_config

# --------------------------------------------------------------------------------------------------------------------
def run_detail_planner(state: State):
    if state.get("overview_completed", False):
        print("✅ Overview ✅")
        return "detail_planner"
    else:
        print("❌ Overview ❌")
        return END


def run_overview_planner(state: State):
    profile_completed = state.get("profile_completed", False)
    if profile_completed:
        print("✅ profile ✅")
        return "overview_planner"
    else:
        print("❌ profile ❌")
    return END

# ===== Tạo graph =====
def create_agent_graph(llm_client):
    profile_collector = ProfileCollector(llm_client)
    overview_planner = OverViewPlanner(llm_client,vector_store = qdrant)
    detail_planner = DetailPlanner(llm_client,vector_store = qdrant)

    graph = StateGraph(State)
    graph.add_node("profile_collector", profile_collector)
    graph.add_node("overview_planner", overview_planner)
    graph.add_node("detail_planner", detail_planner)


    graph.add_edge(START, "profile_collector")

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

    # graph.add_edge("overview_planner" , END)


    # graph.add_edge("overview_planner","detail_planner")
    graph.add_edge("detail_planner" , END)

    return graph.compile(checkpointer=MemorySaver())


app = Flask(__name__)
CORS(app)

# ---- Khởi tạo graph 1 lần khi start server ----
llm_client = LLMClient(model=env_config.model, api_provider=env_config.api_provider)
graph = create_agent_graph(llm_client)

# state toàn cục (bạn có thể lưu theo session_id nếu nhiều user)
# state: State = {
#     "messages": [],
#     "profile_user": None,
#     "profile_completed": False,
#     "overview_completed": False,
#     "overview_result": None,
#     "ok": "",
#     "study_details_result": None,
#     "detail_completed": False,
#     "plan_id": None
# }


# @app.route("/chat", methods=["POST"])
# def chat():
#     data = request.get_json()
#     user_message = data.get("text", "")

#     async def process_message():
#         global state
#         # Thêm tin nhắn user

#         if user_message.strip().lower() in ["q", "quit", "exit"]:
#             return jsonify({"reply": "🔚 Cuộc hội thoại đã kết thúc."})

#         state["messages"].append(HumanMessage(content=user_message))

#         # Chạy graph (như demo.py)
#         state = await graph.ainvoke(state, config=RunnableConfig(configurable={"thread_id": "demo_thread"}))

#         # Lấy response cuối của agent
#         ai_messages = [msg for msg in state["messages"] if msg.type == "ai"]
#         # print("agent: ", ai_messages[-1].content)
#         reply = ai_messages[-1].content if ai_messages else "Không có phản hồi"
#         return reply

#     # Vì Flask không chạy async trực tiếp, dùng asyncio.run
#     reply = asyncio.run(process_message())
#     return jsonify({"reply": reply})



# ----------------------------------------------------------------


state: State = {
    "messages": [],
    "profile_user": None,
    "profile_completed": False,
    "overview_completed": False,
    "overview_result": None,
    "ok": "",
    "study_details_result": None,
    "detail_completed": False,
    "plan_id": None,
    "status":None
}
# ----------------------------------------------------------------

def save_plan(state, folder="plans"):
    os.makedirs(folder, exist_ok=True)
    plan_id = state.get("plan_id")
    file_path = os.path.join(folder, f"{plan_id}.json")
    # current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    # convert bất kỳ object nào có dict() sang dict
    overview_result = state.get("overview_result")
    study_details_result = state.get("study_details_result")

    if hasattr(overview_result, "dict"):
        overview_result = overview_result.dict()
    if hasattr(study_details_result, "dict"):
        study_details_result = study_details_result.dict()

    data = {
        "plan_id": plan_id,        
        "time": current_time,
        "status": "Đang học",
        "overview_result": overview_result,
        "study_details_result": study_details_result
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return file_path
# ----------------------------------------------------------------

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("text", "")

    async def process_message():
        global state

        # if user_message.strip().lower() in ["q", "quit", "exit"]:
        #     return jsonify({"reply": "🔚 Cuộc hội thoại đã kết thúc."})

        state["messages"].append(HumanMessage(content=user_message))

        # Chạy graph
        state = await graph.ainvoke(state, config=RunnableConfig(configurable={"thread_id": "demo_thread"}))

        # Lấy response cuối của agent
        ai_messages = [msg for msg in state["messages"] if msg.type == "ai"]
        reply = ai_messages[-1].content if ai_messages else "Không có phản hồi"

        # Lưu kế hoạch ra file JSON
        if state.get("detail_completed"):
            saved_file = save_plan(state)
            print(f"kế hoạch đã được lưu vào :  {saved_file}")

        return reply

    reply = asyncio.run(process_message())
    return jsonify({"reply": reply})

# ----------------------------------------------------------------

@app.route("/get_all_plans",methods=["GET"])
def get_all_plans():

    # print("get_all_plan_is_running...")
    plans_folder = "plans"
    plan_files = os.listdir(plans_folder)
    all_plans = []

    # print("plans: ", plan_files)

    for file_name in plan_files:
        if file_name.endswith(".json"):
            with open(os.path.join(plans_folder, file_name), "r", encoding="utf-8") as f:
                plan_data = json.load(f)
                # chỉ lấy một số trường cần hiển thị, không lấy detail quá dài
                all_plans.append({
                    "plan_id": plan_data.get("plan_id"),
                    "plan_name": plan_data.get("overview_result", {}).get("learner_profile", {}).get("plan_name"),
                    "time": plan_data.get("time"),
                    "status": plan_data.get("status"),
                    "total_number_sessions":plan_data.get("study_details_result", {}).get("total_number_sessions"),
                    "sessions_done":plan_data.get("study_details_result", {}).get("sessions_done"),

                })
                print("all_plans: ", all_plans)


    return jsonify(all_plans)

# ----------------------------------------------------------------

@app.route("/overview/<plan_id>")
def get_overview(plan_id):
    # print(f"📩 Overview Nhận request với id: {plan_id}")   # log khi nhận
    file_path = f"plans/{plan_id}.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if data:
            print("data ok")
        else:
            print("data none")
    return jsonify(data)

# ----------------------------------------------------------------

@app.route("/lesson/<plan_id>/<lesson_id>")
def get_lesson(plan_id, lesson_id):
    # print(f"📩 Nhận request với plan_id={plan_id}, lesson_id={lesson_id}")

    file_path = f"plans/{plan_id}.json"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        detail_plans = data.get("study_details_result", {}).get("detail_plans", [])

        for plan in detail_plans:
            lessons = plan.get("lessons", [])
            for lesson in lessons:
                if lesson.get("lesson_id") == lesson_id:
                    print("✅ lesson found" , lesson)
                    return jsonify(lesson)

        print("⚠️ lesson not found")
        return jsonify({"error": "Lesson not found"}), 404

    except FileNotFoundError:
        print("❌ Plan file not found")
        return jsonify({"error": "Plan not found"}), 404
    except Exception as e:
        print("💥 Error:", e)
        return jsonify({"error": str(e)}), 500

# ----------------------------------------------------------------
@app.route("/lesson/<plan_id>/<lesson_id>/session/status", methods=["PATCH"])
def update_session_status(plan_id, lesson_id):
    body = request.get_json(silent=True) or {}
    session_id = body.get("session_id")
    new_status = body.get("status")
    if not session_id or not new_status:
        return jsonify({"error": "Thiếu session_id hoặc status"}), 400
    if new_status not in ("Đã hoàn thành", "Chưa hoàn thành"):
        return jsonify({"error": "status phải là 'Đã hoàn thành' hoặc 'Chưa hoàn thành'"}), 400

    file_path = f"plans/{plan_id}.json"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return jsonify({"error": "Plan not found"}), 404

    sdr = data.get("study_details_result", {})
    detail_plans = sdr.get("detail_plans", [])
    sessions_done = sdr.get("sessions_done", 0)

    # tìm module & lesson & session
    module_ref = None
    lesson_ref = None
    session_ref = None
    for mod in detail_plans:
        for les in mod.get("lessons", []):
            if les.get("lesson_id") == lesson_id:
                for sess in les.get("sessions", []):
                    if sess.get("session_id") == session_id:
                        module_ref = mod
                        lesson_ref = les
                        session_ref = sess
                        break
            if session_ref: break
        if session_ref: break

    if not session_ref:
        return jsonify({"error": "Session not found"}), 404

    old_status = session_ref.get("status", "Chưa hoàn thành")
    if old_status == new_status:
        # không thay đổi gì
        return jsonify({
            "ok": True,
            "no_change": True,
            "status": new_status,
            "module_done": module_ref.get("total_number_session_done_in_module", 0),
            "sessions_done": sessions_done
        })

    # tính delta
    delta = 1 if (old_status == "Chưa hoàn thành" and new_status == "Đã hoàn thành") else -1

    # cập nhật status
    session_ref["status"] = new_status

    # cập nhật 2 bộ đếm
    mod_total = int(module_ref.get("total_number_session_done_in_module", 0)) + delta
    mod_total = max(0, min(mod_total, int(module_ref.get("total_number_session_in_module", mod_total))))
    module_ref["total_number_session_done_in_module"] = mod_total

    sessions_done = int(sessions_done) + delta
    sessions_done = max(0, min(sessions_done, int(sdr.get("total_number_sessions", sessions_done))))
    sdr["sessions_done"] = sessions_done

    # ghi file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return jsonify({
        "ok": True,
        "status": new_status,
        "delta": delta,
        "module_done": mod_total,
        "sessions_done": sessions_done
    })

# ----------------------------------------------------------------------------------
@app.route("/debug", methods=["POST"])
def debug_route():
    body = request.get_json(silent=True) or {}

    plan_id = body.get("plan_id")
    lesson_id = body.get("lesson_id")
    session_id = body.get("session_id")

    print(f"📩 Nhận request \nplan_id: {plan_id}\nlesson_id: {lesson_id}\nsession_id: {session_id}")

    file_path = f"plans/{plan_id}.json"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        detail_plans = data.get("study_details_result", {}).get("detail_plans", [])

        # Lọc đúng lesson trước
        for plan in detail_plans:
            for lesson in plan.get("lessons", []):
                if lesson.get("lesson_id") == lesson_id:
                    # Tìm session trong lesson
                    for session in lesson.get("sessions", []):
                        if session.get("session_id") == session_id:
                            print("✅ session found:", session)
                            return jsonify(session)

        print("⚠️ session not found")
        return jsonify({"error": "Session not found"}), 404

    except FileNotFoundError:
        print("❌ Plan file not found")
        return jsonify({"error": "Plan not found"}), 404
    except Exception as e:
        print("💥 Error:", e)
        return jsonify({"error": str(e)}), 500

# --------------------------------------------------------
@app.delete("/delete_plan/<plan_id>")
def delete_plan(plan_id):
    print("plan_id: " ,plan_id)
    file_path = f"plans/{plan_id}.json"

    try:
        if os.path.exists(file_path):
            os.remove(file_path)   # Xóa file
            print(f"🗑️ Đã xóa kế hoạch {plan_id}")
            return jsonify({"ok": True, "message": f"Plan {plan_id} deleted"})
        else:
            print(f"⚠️ Không tìm thấy {file_path}")
            return jsonify({"ok": False, "error": "Plan not found"}), 404
    except Exception as e:
        print("💥 Error:", e)
        return jsonify({"ok": False, "error": str(e)}), 500


# ---------------------------------------------------------
@app.patch("/update_plan")
def update_plan():
    body = request.get_json(silent=True) or {}
    plan_id = body.get("plan_id")
    plan_name = body.get("plan_name")
    status = body.get("status")

    file_path = f"plans/{plan_id}.json"
    # with open(file_path, "r", encoding="utf-8") as f:
    #     data = json.load(f)

 
    # return jsonify({"ok": True, "msg": "Nhận thành công"})

    try:
        # Mở file và đọc dữ liệu
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Cập nhật giá trị mới nếu có
        if plan_name is not None:
            # data["overview_result"]["learner_profile"]["plan_name"]
            data.setdefault("overview_result", {}).setdefault("learner_profile", {})["plan_name"] = plan_name

        if status is not None:
            data["status"] = status

        # Ghi lại file JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return jsonify({"ok": True, "msg": "Cập nhật thành công", "data": data})

    except Exception as e:
        return jsonify({"ok": False, "msg": f"Lỗi khi cập nhật: {str(e)}"}), 500



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)