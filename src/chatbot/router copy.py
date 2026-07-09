import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.state import State

print('oks')

# from pathlib import Path
# from typing import Type, Union
from langchain.prompts import ChatPromptTemplate
# from langgraph.checkpoint.memory import MemorySaver
# from langchain_core.runnables import RunnableConfig
# from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
from src.clients.llm import LLMClient
# from state import State
from src.modules.rag.reranker import VietnameseReranker
from langchain_core.messages import BaseMessage
# from langchain_core.tools import tool
# from langgraph.prebuilt import ToolNode
from langchain.schema import HumanMessage , AIMessage, SystemMessage
# from langgraph.graph import END
# from langgraph.prebuilt import ToolNode, tools_condition
logger = logging.getLogger(__name__)
# from langgraph.graph import MessagesState, StateGraph
from src.tools.tool import retrieve_tool  
from src.tools.tools import extract_summary
# from src.configs import env_config
from prompts.prompt import prompt_summary
from src.clients.databases import qdrant_memory
from src.modules.rag.tools_rag import RAGTools



class MainRouterPromptBuilder:
    """Builds prompts for the profile collector agent."""
    
    def __init__(self):
        with open(r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\prompts\RAG.txt", "r",encoding="utf-8") as file:
            self._prompt_template = file.read()
 
    def build(self, state : State) :
        messages = [
            {"role": "system", "content": self._prompt_template}
        ]
        return ChatPromptTemplate.from_messages(messages)
    
    def build_summary_prompt(self, query, context_RAG):
        return prompt_summary.format(query=query, context_RAG=context_RAG)    
    

class MainAgent:
    
    def __init__(self, llm_client: LLMClient,vector_store):
        self.llm_client = llm_client 
        self.prompt_builder = MainRouterPromptBuilder()
        self.retriever = retrieve_tool(vector_store=vector_store ,search_kwargs={"k":7})
        # self.extract_lllm_response_tool = extract_summary(llm_client=self.llm_client)
        # self.retriever_tools_rag = retrieve_tool(vector_store=vector_store ,search_kwargs={"k":3})

        self.reranker = VietnameseReranker()
        self.tools_rag = RAGTools(llm_client=llm_client, vector_store=qdrant_memory).get_tools()




    def __call__(self, state: State) -> dict:
        print("============= RAG_Agent =============\n")



        print("\n======================= node Retrieve + Re_rank =======================")
        messages: list[BaseMessage] = state.get("messages", [])

        last_user_message = ""
        for m in reversed(messages):
            if isinstance(m, HumanMessage):
                last_user_message = m.content
                break

        results = self.retriever.invoke(last_user_message)
        print("\n === Retrieved Results =====")

        print("số lượng tài liệu truy xuất được:", len(results))
        docs_text = [doc.page_content for doc in results]


        print("\n ====== Re-ranked Results =====")        
        reranked_results = self.reranker.rerank(last_user_message, docs_text, top_k=3)
        high_quality = [ (doc, score) for doc, score in reranked_results if score >= 0.6]
        final_results = high_quality[:2]

        print("số lượng tài liệu re_rank:", len(final_results))
        context_RAG = "\n".join([d for d, score in final_results])


  


        print("\n======================= node Memory =======================")

        # Retrieve từ memory RAG
        retrieve = retrieve_tool(vector_store=qdrant_memory ,search_kwargs={"k":5})
        result_memory = retrieve.invoke(last_user_message)
        memory_context= [doc.page_content for doc in result_memory]

        # re_rank từ memory RAG
        re_rank_memory = self.reranker.rerank(last_user_message, memory_context, top_k=3)
        re_rank_score = [ (doc, score) for doc, score in re_rank_memory if score >= 0.7]
        re_rank_results = re_rank_score[:2]

        print("\n số lượng Memory re_rank:", len(re_rank_results))

        # re_rank_results_memory = "\n".join([doc.page_content for doc in re_rank_results])
        re_rank_results_memory = "\n".join([doc for doc, score in re_rank_results])



        # Lấy 3 tin nhắn Human trước tin nhắn cuối cùng
        prev_3 = [m.content.strip() for m in messages if isinstance(m, HumanMessage)][-4:-1]






        print("\n======================= Node QA =======================")

        # Build prompt đầy đủ
        prompt = self.prompt_builder.build(state)
        prompt_format = prompt.format()

        # Build final prompt
        final_prompt = (
            f"{prompt_format}\n\n# Các cuộc trò chuyện gần đây như sau:\n"
            f"{re_rank_results_memory}\n\nVài câu hỏi gần đây nhất của người dùng là:\n"
            f"{prev_3}\n\nNgữ cảnh dữ liệu hỗ trợ trả lời gồm:\n"
            f"{context_RAG}\n\nHãy dựa vào các dữ liệu trên và trả lời câu hỏi sau:\n"
            f"Câu hỏi: {last_user_message}\n\n"
        )

        # response từ LLM
        llm_response = self.llm_client._llm.invoke(final_prompt)
        llm_response_content = llm_response.content








        print("\n======================= node history  =======================")
        extract_lllm_response_tool = extract_summary(llm_response_content)
        if extract_lllm_response_tool:
            summary_llm_response_content = (
                f"Câu hỏi: {last_user_message}\n"
                f"Trả lời: {extract_lllm_response_tool}\n"
            )
 
            # print(summary_llm_response_content)
            return {"history": [summary_llm_response_content]}
        




        print("\n======================= Node summary =======================")

        # Tóm tắt và lưu vào memory RAG
        prompt_summary = self.prompt_builder.build_summary_prompt(last_user_message,llm_response_content)
        summary_llm_response = self.llm_client._llm.invoke(prompt_summary)
        summary_llm_response_content = summary_llm_response.content

        # Lưu vào memory RAG
        tools = RAGTools(vector_store=qdrant_memory, max_nodes=10)
        tools.add_node(
            text=summary_llm_response_content,
            metadata={"source": "summary"}
        )

        # if last_user_message.strip().lower() == "q":
        #     tools.delete_all_nodes()
 

        return {
            # "messages": [AIMessage(content="" + llm_response_content)], 
            "messages": [AIMessage(content=f"{llm_response_content}")]

        }
    



