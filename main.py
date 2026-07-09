
from ast import Dict, Import
import logging
import sys ,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.clients.databases import qdrant 
from src.clients.llm import LLMClient
from state1 import State ,  AgentProfile, StudyPlanOverview
from src.agents.profile_collector import ProfileCollector
from src.agents.overview_planner import OverViewPlanner
from src.agents.detail_planner import DetailPlanner 
from src.agents.review_planner import ReviewPlanner 
from src.agents.mini_test import MiniTestPlanner 
import asyncio
from datetime import datetime
import json
from langgraph.graph import MessagesState, StateGraph
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
import asyncio
from langchain_core.runnables import RunnableConfig
from pydantic_settings import BaseSettings
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.configs import env_config


import asyncio
from typingAny,  Import Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain.schema import HumanMessage, AIMessage


def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Main")

    # Initialize the LLM client
    llm_client = LLMClient()

    # Set up the initial state
    state = State(
        messages=[],
        profile_user=None,
        profile_completed=False,
        ok=""
    )

    # Run the Profile Collector
    logger.info("Starting Profile Collector...")
    profile_collector = ProfileCollector(llm_client)
    profile_agent = profile_collector(state)

    while not state["profile_completed"]:
        user_input = input("You: ")
        state["messages"].append({"role": "user", "content": user_input})

        response = profile_agent.invoke(
            state,
            config=RunnableConfig(configurable={"thread_id": "profile_thread"})
        )

        # Update state with the response
        state.update(response)
        print(f"System: {response['messages'][-1]['content']}")

    logger.info("Profile collection completed.")

    # Run the Overview Planner
    logger.info("Starting Overview Planner...")
    overview_planner = OverviewPlanner(llm_client, qdrant)
    overview_agent = overview_planner(state)

    while True:
        user_input = input("You: ")
        state["messages"].append({"role": "user", "content": user_input})

        response = overview_agent.invoke(
            state,
            config=RunnableConfig(configurable={"thread_id": "overview_thread"})
        )

        # Update state with the response
        state.update(response)
        print(f"System: {response['messages'][-1]['content']}")

        if response.get("end", False):
            logger.info("Overview planning completed.")
            break

if __name__ == "__main__":
    main()
