# import sys,os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
# # from src.state import State
# from langgraph.graph import StateGraph, END
# from src.state_edu import ExamState
# from src.edu_exam.collect_info import collect_info
# # from nodes.retrieve_docs import retrieve_docs
# # from nodes.build_knowledge import build_knowledge
# # from nodes.build_matrix import build_matrixs
# # from nodes.build_specs import build_specs
# # from nodes.generate_questions import generate_questions
# # from nodes.evaluate_exam import evaluate_exam
# # from nodes.run_exam import run_exam


# def should_continue_collect(state: ExamState) -> str:
#     if state.get("profile_complete"):
#         return "end"
#     return "collect_info"
 
 
# def build_graph():
#     g = StateGraph(ExamState)
 
#     g.add_node("collect_info", collect_info)
 
#     g.set_entry_point("collect_info")
 
#     g.add_conditional_edges(
#         "collect_info",
#         should_continue_collect,
#         {
#             "collect_info": "collect_info",
#             "end": END,
#         }
#     )
 
#     return g.compile()
 
 
# exam_graph = build_graph()