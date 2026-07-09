import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.state import State

logger = logging.getLogger(__name__)
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage







class RagAgent:

    def __init__(self, llm_client: State):
        self.llm_client = llm_client
        # self.tools = [retrieve_tool, ask_clarification_tool]
       

    def _build_system_prompt(self, state: State) -> str:
        

        return 'build'
    
    def __call__(self, state: State) -> dict:
        print("============= RAG_Agent (ReAct) =============")

      

        return {
            "messages": [AIMessage(content="RAG")]
        }