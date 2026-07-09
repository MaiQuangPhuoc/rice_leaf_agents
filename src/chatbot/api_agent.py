
import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.state import State

 

from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel
from src.clients.llm import LLMClient
from langchain.schema import HumanMessage , AIMessage, SystemMessage
logger = logging.getLogger(__name__)

from src.configs import env_config



class APIPromptBuilder:
    """Builds prompts for the profile collector agent."""
    
    def __init__(self):
        with open(r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\router_sp.txt", "r",encoding="utf-8") as file:
            self._prompt_template = file.read()
 
    def build(self, state : State) :
        messages = [
            {"role": "system", "content": self._prompt_template}
        ]
        return ChatPromptTemplate.from_messages(messages)
     
    
class apiAgent:
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client 
        self.prompt_builder = APIPromptBuilder()

    def __call__(self, state: State) -> dict:

        print("============= API_Agent =============\n"*3)
 
        return{
            "messages": [AIMessage(content="API_Agent")]
        }
    



