import logging
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.graph.state import CompiledStateGraph
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import time
from datetime import datetime
from src.agents.detail_planner import DetailPlanner
from src.agents.profile_collector import ProfileCollector
from src.agents.overview_planner import OverViewPlanner

from src.clients.llm import LLMClient
from state import AgentProfile
from state import State

logger = logging.getLogger(__name__)

llm_client=LLMClient(model="meta-llama/llama-4-scout-17b-16e-instruct",api_provider="groq")

def run_overview_planner(state: State):
    """Check if profile is completed and ready for overview planning"""
    profile_completed = state.get("profile_completed", False)
    if profile_completed:
        return "overview_planner"
    return END

def process_overview_output(state: State):
    
    return 

def build_graph():
    graph = StateGraph(State)
    
    # Initialize agents
    profile_collector = ProfileCollector(llm_client=llm_client)
    overview_planner = OverViewPlanner(llm_client=llm_client)
    detail_planner = DetailPlanner(llm_client=llm_client)

    # Add nodes
    graph.add_node("profile_collector", profile_collector)
    graph.add_node("overview_planner", overview_planner)
    graph.add_node("detail_planner", detail_planner)
    graph.add_node("process_overview_output", process_overview_output)

    # Set up edges
    graph.add_edge(START, "profile_collector")
    
    # Conditional edge from profile collector
    graph.add_conditional_edges(
        "profile_collector",
        run_overview_planner,
        {END: END, "overview_planner": "overview_planner"},
    )
    graph.add_edge("overview_planner", "process_overview_output")
    graph.add_edge("process_overview_output", "detail_planner")
    graph.add_edge("detail_planner", END)



    compiled_graph = graph.compile()
    return compiled_graph

build_graph()


# study_modules=[StudyModule(module_name='Chương 1: Mệnh đề, Tập hợp', lesson_titles=['Mệnh đề', 'Tập hợp', 'Các phép toán tập hợp', 'Các tập hợp số', 'Số gần đúng. Sai số'], objectives=['Nắm vững các khái niệm và phép toán cơ bản để có tư duy chính xác và logic.''], description='Chương này là nền tảng cơ bản của Toán học phổ thông, giới thiệu ngôn ngữ của logic toán học qua mệnh đề và lý thuyết tập hợp', resources=[Resource(type='video', url='youtube.com/playlist?list=menh_de_va_tap_hop_10', title='Video bài giảng Mệnh đề, Tập hợp'), Resource(type='tài liệu', url='tailieutoan.vn/menh_de_va_tap_hop', title='Tài liệu bài giảng Mệnh đề, Tập hợp')], duration_estimate='4 tuần', priority='cao')] total_duration='16 tuần' constraints=Constraints(available_hours_per_day='5 tiếng', deadline='2025-12-12', max_modules_per_week=1) learner_profile=LearnerProfile(level='học lực giỏi', preferred_study_style='học qua video lý thuyết và bài tập', learning_goals='Thi học sinh giỏi toán 10, đạt giải nhất kì thi', plan_scope='Các chủ đề kém và chủ đề quan tâm muốn học')