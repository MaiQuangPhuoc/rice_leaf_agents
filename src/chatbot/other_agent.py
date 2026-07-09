import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.state import State

print('oks')

from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel
from src.clients.llm import LLMClient

from langchain.schema import HumanMessage , AIMessage, SystemMessage
logger = logging.getLogger(__name__)


class OtherRouterPromptBuilder:
    """Builds prompts for the profile collector agent."""
    
    def __init__(self):
        with open(r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\router_sp.txt", "r",encoding="utf-8") as file:
            self._prompt_template = file.read()

        with open(r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\router_up.txt", "r", encoding="utf-8") as file:
            self._user_message_template = file.read()

    def build(self, state : State) :
        # user_message =""
        # user_message = self._user_message_template
       
        messages = [
            {"role": "system", "content": self._prompt_template},
            {"role": "user", "content": self._user_message_template},
        ]

        return ChatPromptTemplate.from_messages(messages)
    
class OtherAgent:
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client 
        self.prompt_builder = OtherRouterPromptBuilder()

    def __call__(self, state: State) -> dict:

        print("============= Other_Agent =============\n"*3)
        # print(self.prompt_builder.build(state))
        return{
            "messages": [AIMessage(content="Other_Agent")],
            "state_main": True
            # "state_main": False
        }
    



