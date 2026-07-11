# import logging
# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
# # from src.state import State

 

# # from pathlib import Path
# # from typing import Type, Union
# # from langchain.prompts import ChatPromptTemplate
# # from langgraph.checkpoint.memory import MemorySaver
# # from langchain_core.runnables import RunnableConfig
# # from langgraph.prebuilt import create_react_agent
# # from pydantic import BaseModel
# # from src.clients.llm import LLMClient
# # from state import State

# # from langchain_core.tools import tool
# # from langgraph.prebuilt import ToolNode
# # from langchain.schema import HumanMessage , AIMessage, SystemMessage
# # from langgraph.graph import END
# # from langgraph.prebuilt import ToolNode, tools_condition
# logger = logging.getLogger(__name__)
# # from langgraph.graph import MessagesState, StateGraph
# # from src.tools.tool import create_parser_output_tool
# from src.configs import env_config
# from src.tools.tools_web_search import tools_web_search
# from src.modules.rag.reranker import VietnameseReranker




# # query ="nên dùng phân bón và thuốc trị bệnh đạo ôn và đốm nâu trên lá lúa"

 
# # api_key = env_config.api_key_tavily

# # print("===="*30)

# # docs = tools_web_search(query=query, api_key=api_key, k=10)
# # for i, d in enumerate(docs, 1):
# #     print(f"\nKết quả {i}:")
# #     # print("URL:", d.metadata.get("url", ""))
# #     print("Score:", d.metadata.get("score", 0))
# #     print("Nội dung:", d.page_content, "...")
# #     print("===="*30)

# # docs_text = [d.page_content for d in docs]

# # print("================ re_rank ======================")
# # re_rank = VietnameseReranker()
# # reranked_results = re_rank.rerank(query, docs_text, top_k=2)

# # for doc, score in reranked_results:
# #     print(f"\n\n\n- {doc} \n=== (Score: {score})")  

# # class APiPromptBuilder:
# #     """Builds prompts for the profile collector agent."""
    
# #     def __init__(self):
# #         with open(r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\router_sp.txt", "r",encoding="utf-8") as file:
# #             self._prompt_template = file.read()

# #         with open(r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\router_up.txt", "r", encoding="utf-8") as file:
# #             self._user_message_template = file.read()

# #     def build(self, state : State) :
# #         # user_message =""
# #         # user_message = self._user_message_template
       
# #         messages = [
# #             {"role": "system", "content": self._prompt_template},
# #             {"role": "user", "content": self._user_message_template},
# #         ]

# #         return ChatPromptTemplate.from_messages(messages)
    
# # class apiAgent:
    
# #     def __init__(self, llm_client: LLMClient):
# #         self.llm_client = llm_client 
# #         self.prompt_builder = APiPromptBuilder()

# #     def __call__(self, state: State) -> dict:

# #         print("============= API_Agent =============\n"*3)
# #         # print(self.prompt_builder.build(state))
# #         return{
# #             "messages": [AIMessage(content="22222222222222222222222222")],
# #             "state_api": True
# #             # "state_api": False

# #         }
    

import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.state import State

 

# from pathlib import Path
# from typing import Type, Union
from langchain.prompts import ChatPromptTemplate
# from langgraph.checkpoint.memory import MemorySaver
# from langchain_core.runnables import RunnableConfig
# from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
from src.clients.llm import LLMClient
# from state import State

# from langchain_core.tools import tool
# from langgraph.prebuilt import ToolNode
from langchain.schema import HumanMessage , AIMessage, SystemMessage
# from langgraph.graph import END
# from langgraph.prebuilt import ToolNode, tools_condition
logger = logging.getLogger(__name__)
# from langgraph.graph import MessagesState, StateGraph
# from src.tools.tool import create_parser_output_tool

from src.configs import env_config
from src.tools.tools_web_search import tools_web_search
from src.modules.rag.reranker import VietnameseReranker



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
            "messages": [AIMessage(content="API")]

        }
    



