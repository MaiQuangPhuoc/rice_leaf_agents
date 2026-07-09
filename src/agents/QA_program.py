import json
import logging
from multiprocessing import get_context
import sys
import os
from typing import List
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# from pathlib import Path
# from typing import Type, Union
from langchain.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
# from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
# from pydantic import BaseModel
from src.clients.llm import LLMClient
from state import State, QA_response_pro
from langchain_core.tools import tool
# from langgraph.prebuilt import ToolNode
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import END
from langgraph.prebuilt import ToolNode, tools_condition
logger = logging.getLogger(__name__)
from langgraph.graph import MessagesState, StateGraph
from src.tools.tool import get_id_tools, retrieve_tool_score
from src.tools.tools_web_search import tools_web_search

from src.configs import env_config
# from src.clients.databases import qdrant_qa

from sentence_transformers import CrossEncoder


# collect_tool = create_parser_output_tool(
#     llm_client=LLMClient(model=env_config.model, api_provider=env_config.api_provider),
#     state=MiniTestState
# )


# tool_get_id = get_id_tools(
#     llm_client=LLMClient(model=env_config.model, api_provider=env_config.api_provider),
#     state=get_id_plan
# )


class QAProgramPromptBuilder:
    """Agent responsible for collecting and managing user learning mini_test."""

    def __init__(self):
        with open(r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\src.agents.qa_program.call.sp.txt","r", encoding="utf-8") as file:
            self._prompt_template = file.read()

        with open(r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\src.agents.qa_program.call.um.txt","r", encoding="utf-8") as file:
            self._user_message_template = file.read()


    def build(self, state: State,doc_retrieval , doc_web_search):
        conversation_messages = [
            msg.content
            for msg in state["messages"]
            if msg.type in ("human","ai")
        ]
        last_3_messages = conversation_messages[-3:]

        # Nối lại thành 1 chuỗi
        his = "\n".join(last_3_messages)
        
        human_messages = [msg for msg in state["messages"] if msg.type == "human"]

        if human_messages:
            text = human_messages[-1].content  # chỉ lấy tin nhắn cuối
        else:
            text = ""

 


        system_message = self._prompt_template.format(
            doc_retrieval=doc_retrieval,
            doc_web_search=doc_web_search
        )

        user_message = self._user_message_template.format(
            his = his,
            query=text
        )

        return [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ]

# ----------------------------------------------------------

class QAProgram:
    def __init__(self, llm_client : LLMClient, vector_store):
        self.llm_client = llm_client
        self.prompt_builder = QAProgramPromptBuilder()
        self.retriever = retrieve_tool_score(vector_store=vector_store,  search_kwargs={"k": 10})
        # self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2') 
        self.reranker = CrossEncoder('Alibaba-NLP/gte-multilingual-reranker-base',trust_remote_code=True)

    def retriever_def(self, query, top_k: int = 6):
        docs = self.retriever.invoke(query) 
        
        sorted_docs = sorted(docs, key=lambda x: x[1], reverse=True)

        # Lấy top_k
        top_docs = [doc for doc, score in sorted_docs[:top_k]]

        return top_docs    
    
    def rerank_documents(self, query , docs , top_k):
        if not docs:
            print("not documents")
            return []
        
        query_doc_pairs =  [(query, doc.page_content) for doc in docs]

        scores = self.reranker.predict(query_doc_pairs)

        # Ghép lại (doc, score) rồi sort giảm dần
        doc_scores = list(zip(docs, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)

        # In ra kết quả re-rank
        # print(f"\n================================================ Kết quả re-rank ================================================")
        # print(" 2️⃣ "*40)
        # # 1️⃣2️⃣3️⃣4️⃣
        # for doc, score in doc_scores:
        #     print(f"👉 Score: {score:.4f}")
        #     print("🔗",doc.metadata["url"], "...\n")   
        #     # print("📑",doc.page_content, "...\n")
        #     print("-"*20)

        # Trả về top-k doc
        return [doc for doc, score in doc_scores[:top_k]]
    

    async def __call__(self, state: State):
        print("============= call__start_QA_PROGRAM_MATH_10 =============\n"*5)
        # return state



        humnan_messsage = [mes for mes in state["messages"] if mes.type =="human"]
        query = humnan_messsage[-1].content




        result_web_search = tools_web_search(query , env_config.api_key_tavily, max_results=5)

        # -------------------------------------------------------------
        # print("\n=== Kết quả Web Search ===")
        # print(" 1️⃣ "*20)
        # for i, item in enumerate(result_web_search, 1):
        #     print(f"👉 [{i}] Score: {item.metadata['score']:.4f}")
        #     print(f"🔗 URL: {item.metadata['url']}")
        #     print(f"📑 Nội dung: {item.page_content}...\n")  # lấy 300 ký tự đầu
        #     print("=" * 40)
        # -------------------------------------------------------------

        web_search_reranked_docs_with_tavily = self.rerank_documents(query, result_web_search, top_k=2)
      
      
        # -------------------------------------------------------------
        # print("\n=========================== Kết quả reranked_docs TAVILY được chọn ===========================")
        # print(" 1️⃣ "*20)
        # for d in web_search_reranked_docs_with_tavily:
        #     print("📑",d.page_content, "...\n")
        #     print("🔗",d.metadata["url"], "...\n------------\n")
        # -------------------------------------------------------------

        # RETRIEVAL
        docs = self.retriever_def(query)

        # if not docs:
        #     print("Không tìm thấy context nào qua retriever")
        #     return state

        retrival_reranked_docs_with_retrieval = self.rerank_documents(query, docs, top_k=3)

        # -------------------------------------------------------------
        # print("\n=========================== Kết quả reranked_docs RETRIEVAL được chọn ===========================")
        # print(" 2️⃣ "*20)
        # for d in retrival_reranked_docs_with_retrieval:
        #     print("📑",d.page_content, "...\n")
        # -------------------------------------------------------------

        # Ghép nội dung của các doc từ retrieval
        retrieval_context = "\n\n".join([doc.page_content for doc in retrival_reranked_docs_with_retrieval])
        # retrieval_context = "11111111111111111111111111111"

        # Ghép nội dung của các doc từ web search
        web_search_context = "\n\n".join([doc.page_content for doc in web_search_reranked_docs_with_tavily])
        # web_search_context = "22222222222222222222222222222222"


        # Gọi build prompt
        prompt = self.prompt_builder.build(state, retrieval_context, web_search_context)
        # print("prompt:", prompt)
        print("="*30)
        print("prompt:", prompt)
        print("="*30)

 

        res = await self.llm_client.ainvoke_with_retries(
            prompt=prompt, output_model=QA_response_pro
        )

        response = res.answers[0].answer

        # print("_"*30)
        # print("res: ", res)
        # print("="*30)

        
        return {
            "messages": [AIMessage(content=f"{response}")]
        }
    


