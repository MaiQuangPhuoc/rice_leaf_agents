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
from src.configs import env_config
from prompts.prompt import prompt_summary
from src.clients.databases import qdrant_memory
from src.modules.rag.tools_rag import RAGTools
from src.tools.tools_web_search import tools_web_search





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
        self.retriever = retrieve_tool(vector_store=vector_store ,search_kwargs={"k":10})
        # self.extract_lllm_response_tool = extract_summary(llm_client=self.llm_client)
        # self.retriever_tools_rag = retrieve_tool(vector_store=vector_store ,search_kwargs={"k":3})

        self.reranker = VietnameseReranker()
        # self.tools_rag = RAGTools(llm_client=llm_client, vector_store=qdrant_memory).get_tools()




    def __call__(self, state: State) -> dict:
        print("============= RAG_Agent =============\n")

        # Lấy messages từ state
        messages: list[BaseMessage] = state.get("messages_query_transform", [])

        # print(">>> Lịch sử hội thoại trong state:")
        # for m in messages:
        #     print(type(m), ":", m.content)

        # Lấy message user cuối cùng
        last_user_message = ""
        for m in reversed(messages):
            if isinstance(m, HumanMessage):
                last_user_message = m.content
                break

        # print("\n>>> Last user message:", last_user_message, type(last_user_message))

        # Giả lập context từ Vector DB
        # context = "ABC"
        # print("\n>>> Context from Vector DB:", context, type(context))

        # Build prompt đầy đủ
        prompt = self.prompt_builder.build(state)
        prompt_format = prompt.format()
        # print("\n>>> PROMPT FORMAT:",prompt_format, type(prompt_format))
 




        results = self.retriever.invoke(last_user_message)
        if results: 
            print("\n =================================== Retrieved Results ===================================")
        # for doc in results:
        #     print(f"\n- {doc.page_content[:200]}")

            print("số lượng tài liệu truy xuất được:", len(results))

        
        docs_text = [doc.page_content for doc in results]


        print("\n =================================== Re-ranked Results ===================================")        
  
        reranked_results = self.reranker.rerank(last_user_message, docs_text, top_k=4)


        high_quality = [ (doc, score) for doc, score in reranked_results if score >= 0.7]

        final_results = high_quality[:2]
        final_context = "\n".join([d for d, score in final_results])
        if final_results:
            print("\n======================= re_rank ===================================")

            print("số lượng tài liệu re_rank:", len(final_results))
        else:
            print("\nkhông có tài liệu re_rank"*3)


 
        # api_key = env_config.api_key_tavily

        if not final_context:
            print("================ web_search ======================")
            docs = tools_web_search(query=last_user_message, api_key=env_config.api_key_tavily, k=10)
            docs_text = [d.page_content for d in docs]

            reranked_results = self.reranker.rerank(last_user_message, docs_text, top_k=2)
            # final_context = "\n".join([d for d in reranked_results])
            final_context = "\n".join([doc for doc, score in reranked_results])


            print(final_context)

            # for doc, score in reranked_results:
            #     print(f"\n\n\n- {doc} \n=== (Score: {score})")  

            # print("===="*30)

        # for doc, score in reranked_results:
        #     print(f"\n- {doc} === (Score: {score})")    

        # print("-"*20)
        # for doc, score in final_results:
        #     print(f"\n- {doc} === (Score: {score})")    
        
 

        
        # print("\n =================================== final_prompt ===================================")
        # final_prompt = (
        #     f"{prompt_format}\n\n"
        #     f"{final_context}\n\nHãy trả lời câu hỏi như sau:\n"
        #     f"Câu hỏi: {last_user_message}\n\n"
        # )



        # # print(final_prompt)
        
        # llm_response = self.llm_client._llm.invoke(final_prompt)
        # llm_response_content = llm_response.content   
        # # print("\n LLM Response:", llm_response_content)

        # if llm_response_content:
        #     print("\ncó llm_response_content")


 

        # query = "Bệnh đạo ôn là gì?"
        
        # context = "Bệnh đạo ôn là một bệnh nguy hiểm trên cây lúa, do nấm Pyricularia oryzae gây ra, tấn công mọi bộ phận như lá, thân, cổ bông, gié và hạt, có thể gây thiệt hại nặng nề cho năng suất. Bệnh thường xuất hiện trong điều kiện thời tiết thuận lợi như ẩm ướt, mưa phùn, nhiệt độ mát mẻ và có sự chênh lệch nhiệt độ ngày đêm cao. Biểu hiện của bệnh Trên lá: Ban đầu xuất hiện vết nhỏ màu xám nhạt, sau đó lớn dần thành hình thoi với tâm màu xám tro và viền màu nâu hoặc đen. Trong trường hợp nặng, các vết bệnh liên kết lại thành mảng lớn gây cháy lá.Trên thân: Vết bệnh có màu nâu, làm thân bị bóp teo lại, cắt đứt mạch dẫn dinh dưỡng, khiến lúa trổ bị lép trắng.Trên cổ bông và gié: Vết bệnh xuất hiện ở cổ bông, gây thối cổ và làm bông chết sớm.Trên hạt: Bệnh có thể gây đốm nâu trên vỏ trấu và làm hạt bị đen, lép. Điều kiện thuận lợi cho bệnh phát triển Thời tiết ẩm ướt kéo dài, có sương mù, mưa phùn.Nhiệt độ dao động trong khoảng \(22-28\degree C\).Độ ẩm không khí trên \(90\%\).Bón thừa đạm hoặc thiếu kali"

        


        # Tạo object tools_rag trước




        print("========== memory rag ==============")
        retrieve = retrieve_tool(vector_store=qdrant_memory ,search_kwargs={"k":5})
        result_memory = retrieve.invoke(last_user_message)
        if result_memory:
            print("\n======================= Retrieved Results from Memory =======================")


        # docs_text_memory = [doc.page_content for doc in result_memory]


        # result_memory_re_rank = self.reranker.rerank(last_user_message,docs_text_memory, top_k=2)
        # if result_memory_re_rank:
        #     print("\n======================= Re-ranked Results from Memory =======================")

        # re-rank memory 
        # print(" =================================== Re-ranked Results from Memory ===================================")
        # for doc, score in result_memory_re_rank:
        #     print(f"\n--> {doc} === (Score: {score})")    

        # print("-"*200)

        results_memory = "\n".join([doc.page_content for doc in result_memory])
        print("số lượng retrive_rag_tools:", len(results_memory))   


        # print("\n======================= n query gần nhất =======================")
        prev_3 = [m.content.strip() for m in messages if isinstance(m, HumanMessage)][-4:]
        query = prev_3[-1]
        conversation = prev_3[:-1]
        if not conversation:
            print("\n======================= conversation =======================")


        # print("Câu hỏi:", query)
        # print("last_user_message:", last_user_message)


        # print("2 tin trước:", conversation)


        print("\n =================================== final_prompt ===================================")
        final_prompt = (
            f"{prompt_format}\n\n# Các cuộc trò chuyện gần đây như sau:\n"
            f"{results_memory}\n\nVài câu hỏi gần đây nhất của người dùng là:\n"
            f"{conversation}\n\nNgữ cảnh dữ liệu hỗ trợ trả lời gồm:\n"
            f"{final_context}\n\nHãy dựa vào các dữ liệu trên và trả lời câu hỏi sau:\n"
            f"Câu hỏi: {query}\n\n"
        )

        # print(final_prompt)
        # đối với bệnh đạo ôn trên lá lúa, cây cần bổ sung nhóm chất dinh dưỡng nào để hạn chế tái nhiễm? 

        llm_response = self.llm_client._llm.invoke(final_prompt)
        llm_response_content = llm_response.content
        if llm_response_content:
            # print("\ncó llm_response_content")
            print("\n======================= LLM Response =======================")

        # tóm tắt response 
        # extract_lllm_response_tool =  extract_summary(llm_response_content)
        # if extract_lllm_response_tool:
        #     print("\n======================= summary_llm_response_content =======================")



        #     summary_llm_response_content_tt = (
        #         f"Câu hỏi: {last_user_message}\n"
        #         f"Trả lời: {extract_lllm_response_tool}\n"
        #     )



            # summary_llm_response_content = "\n".join([last_user_message, extract_lllm_response_tool])

            # print("======== summary_llm_response_content ========")
            # print(summary_llm_response_content)
            # # print("có extract_lllm_response_tool")
            # return {"history": [summary_llm_response_content]}

        # print("\n======================= LLM Response =======================")

        # print("\n", llm_response_content)

        # print("\n======================= extract_lllm_response_tool =======================")   
        # print("\n", extract_lllm_response_tool)



        # print("\n======================= summary =======================")

        prompt_summary = self.prompt_builder.build_summary_prompt(last_user_message,llm_response_content)
        # print("prompt_summary", prompt_summary)
        summary_llm_response = self.llm_client._llm.invoke(prompt_summary)
        summary_llm_response_content = summary_llm_response.content

        # print("\nsummary_llm_response", summary_llm_response_content)
        if summary_llm_response_content:
            print("\n======================= summary =======================")

            # print("có summary_llm_response_content")


        print("\n======================= RAG_ tools =======================")

        tools = RAGTools(vector_store=qdrant_memory, max_nodes=10)
        tools.add_node(
            text=summary_llm_response_content,
            metadata={"source": "summary"}
        )



        results_memory = tools.retrieve_top_k(query=last_user_message, k=3)

        # for doc in results_memory:
        #     print(f"\n---> {doc.page_content}")




        # for text, score, metadata in results_memory:
        #     print(f"\n--> {text} \n(Score: {score})") 



        # xóa tất cả
        if last_user_message.strip().lower() == "q":
            tools.delete_all_nodes()

        last_3_human_messages = []
        for m in reversed(messages):
            if isinstance(m, HumanMessage):
                last_3_human_messages.append(m.content.strip())
                if len(last_3_human_messages) >= 3:
                    break

        # Đảo ngược lại để đúng thứ tự thời gian (cũ → mới)
        last_3_human_messages = last_3_human_messages[::-1]

        # In ra để debug (tùy chọn)
        print("========== Last 3 Human Messages ========== ")
        for i, msg in enumerate(last_3_human_messages, 1):
            print(f"   {i}. {msg}")

        # Lấy 2 tin nhắn Human trước tin nhắn cuối cùng



 







        # Trả về message mẫu
        return {
            "messages": [AIMessage(content=llm_response_content)],
            "history": ["summary_llm_response_content_tt"]
        }
    



