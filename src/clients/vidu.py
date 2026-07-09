# import json
# import logging
# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# from pathlib import Path
# from typing import Type, Union
# from langchain.prompts import ChatPromptTemplate
# from langgraph.checkpoint.memory import MemorySaver
# from langchain_core.runnables import RunnableConfig
# from langgraph.prebuilt import create_react_agent
# from pydantic import BaseModel
# from src.clients.llm import LLMClient
# from src.state import AgentProfile , State 
# from langchain_core.tools import tool
# from langgraph.prebuilt import ToolNode
# from langchain.schema import HumanMessage , AIMessage, SystemMessage
# from langgraph.graph import END
# from langgraph.prebuilt import ToolNode, tools_condition
# logger = logging.getLogger(__name__)
# from langgraph.graph import MessagesState, StateGraph
# from src.tools.tool import create_parser_output_tool
# from src.configs import env_config

# # collect_profile = create_parser_output_tool(
# #     llm_client=LLMClient(model="meta-llama/llama-4-scout-17b-16e-instruct",api_provider="groq"),
# #     state=AgentProfile
# # )

# collect_profile = create_parser_output_tool(
#     llm_client=LLMClient(model=env_config.model,api_provider=env_config.api_provider),
#     state=AgentProfile
# )

# class ProfileCollectorPromptBuilder:
#     """Builds prompts for the profile collector agent."""
    
#     def __init__(self):
#         with open(r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\src.agents.profile_collector.call.sp.txt", "r",encoding="utf-8") as file:
#             self._prompt_template = file.read()

#         with open(r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\prompts\src.agents.profile_collector.call.um.txt", "r", encoding="utf-8") as file:
#             self._user_message_template = file.read()
#     def build(self, state : State) :
#         user_message =""
       
#         messages = [
#             {"role": "system", "content": self._prompt_template},
#             {"role": "user", "content": user_message},
#         ]

#         return ChatPromptTemplate.from_messages(messages)

# class ProfileCollector:
#     """Agent responsible for collecting and managing user learning profiles."""
    
#     def __init__(self, llm_client: LLMClient):
#         """
#         Initialize the profile collector.
        
#         Args:
#             llm_client: LLM client for generating responses
#         """
#         self.llm_client = llm_client 
#         self.prompt_builder = ProfileCollectorPromptBuilder()

#     def __call__(self, state: State) -> dict:
#         """
#         Execute the profile collection process.
        
#         Args:
#             state: Current agent profile state, defaults to new AgentProfile
#             thread_id: Unique identifier for the conversation thread
            
#         Returns:
#             Response from the profile agent
            
#         Raises:
#             ValueError: If invalid parameters provided
#             RuntimeError: If agent execution fails
#         """
#         if state is None:
#             state = State

#         try:
#             systemPrompt = self.prompt_builder.build(state)
#             # print("===== SYSTEM PROMPT =====")
#             # print(systemPrompt.format())
#             # print("=========================")
                    
#             def chat(state: State):
#                 """Generate tool call for retrieval or respond."""
                
#                 llm_with_tools = self.llm_client._llm.bind_tools([collect_profile])
#                 conversation_messages = [
#                     message
#                     for message in state["messages"]
#                     if message.type in ("human", "system")
#                     or (message.type == "ai" and not message.tool_calls)
#                 ]
#                 prompt = ([SystemMessage(content=systemPrompt.format(**state))] if systemPrompt else []) + conversation_messages
#                 # print('prompt',prompt)
#                 # print('``````````````````````````````````````````````````````')
#                 response = llm_with_tools.invoke(prompt)
#                 # print('state---',state)
#                 # print('``````````````````````````````````````````````````````')
#                 # print('state _ messages---',state['messages'])

                

#                 # print('response - ',response)

#                 return {"messages": [response]}
            
#             tools = ToolNode([collect_profile])

#             def generate(state: State):
#                 """Parser the output"""

#                 for msg in state["messages"]:
#                     # if isinstance(msg, HumanMessage):
#                     #     print("Người dùng:", msg.content)
#                     #     print('type:' , msg.type)

#                     print('msg.content--', msg.content)
#                     print('msg.type--', msg.type)
#                     print('------------------- ' )
#                 print('------------------------\n' )

                        

#                 recent_tool_messages = []
#                 for message in reversed(state["messages"]):
#                     if message.type == "tool":
#                         recent_tool_messages.append(message)
#                     else:
#                         break
#                 # print('-------------------------recent_tool_messages------------------\n', recent_tool_messages)

 
                

#                 tool_messages = recent_tool_messages[::-1]

#                 # if not tool_messages:
#                 #     print("Không có message type tool")
#                 #     return "Chưa có kết quả từ tool"

#                 last_tool_msg = tool_messages[-1]  
#                 # print('last_tool_msg--', last_tool_msg)

#                 # print('gen=====================',state)
#                 print('last_tool_msg' , last_tool_msg)
#                 print('\n------------------------\n' )
#                 print('last_tool_msg.artifact--' , last_tool_msg.artifact)

#                 # if last_tool_msg.artifact :
#                 #     return {"profile_user": last_tool_msg.artifact, "messages": "hoàn thành việc thu thập hồ sơ học tập."} 
#                 # else:
#                 #     return "lỗi ?? chưa hoàn thành thu thập abc"


#                 return {"profile_user": last_tool_msg.artifact, "messages": "hoàn thành việc thu thập hồ sơ học tập."} 

#             graph_builder = StateGraph(MessagesState)
#             graph_builder.add_node(chat)
#             graph_builder.add_node(tools)
#             graph_builder.add_node(generate)

#             graph_builder.set_entry_point("chat")
#             graph_builder.add_conditional_edges(
#                 "chat",
#                 tools_condition,
#                 {END: END, "tools": "tools"},
#             )
#             graph_builder.add_edge("tools", "generate")
#             graph_builder.add_edge("generate", END)

#             graph = graph_builder.compile(checkpointer=MemorySaver())
            
#             return graph
            
#         except Exception as e:
#             logger.error(f"Error executing profile collector: {e}")
#             raise RuntimeError(f"Profile collection failed: {e}")

# # if __name__ == "__main__":
# #     llm_client = LLMClient(
# #         model="gpt-4o-mini",
# #         api_provider="openai",
# #     )

# #     agent = ProfileCollector(llm_client)
# #     profile_agent = agent(State)

# #     print("=== Bắt đầu hội thoại với hệ thống ===")
# #     user_input = input("Bạn: ")

# #     while True:
# #         response = profile_agent.invoke(
# #             {"messages": user_input},
# #             config=RunnableConfig(configurable={"thread_id": "test_thread"})
# #         )

# #         ai_reply = response["messages"][-1].content if isinstance(response, dict) else response
# #         print(f"Hệ thống: {ai_reply}")

# #         user_input = input("Bạn: ")
# #         if user_input.strip().lower() in ["exit", "quit", "q"]:
# #             break


# Bạn là một AI hỗ trợ tạo kế hoạch học tập cá nhân hóa. 
# Nhiệm vụ của bạn là thu thập **hồ sơ học tập** của người học để lên kế hoạch phù hợp. Với mỗi phần thông tin, nếu người học đã cung cấp thì trích xuất ra, nếu chưa có hoặc chưa rõ thì bạn hãy hỏi thêm.
# Lưu ý : bạn chỉ có nhiệm vụ thu thập và trích xuất , khong có nhiệm vụ khác nếu yêu cầu không liên quan thì không quan tâm 

# Thông tin cần thu thập gồm:
# 1. **Mục tiêu học tập**: Người học muốn đạt được gì? (VD: Nắm chắc kiến thức cơ bản, luyện thi học kỳ, Học để cải thiện điểm, Thi học sinh giỏi, Học theo chương trình...)
# 2. **Thời gian học mỗi ngày/tuần**: Người học có thể học bao nhiêu thời gian mỗi ngày hoặc mỗi tuần?
# 3. **Năng lực hiện tại**: Trình độ hiện tại như thế nào? (VD: Trung bình, Khá, Giỏi; điểm số gần đây; chủ đề đã biết/chưa biết)
# 4. **Nhu cầu học tập**: Người học muốn học theo cách nào? (VD: Lý thuyết cơ bản trước, Ưu tiên luyện bài tập, Học theo đề thi, Ôn tập chuyên đề yếu ,khác...)
# 5. **Thời hạn/Thời điểm cần hoàn thành**: Khi nào cần đạt mục tiêu? (VD: Trong 1 tháng tới, Trước ngày thi THPT...)
# 6. **Khó khăn hoặc trở ngại hiện tại** (nếu có): VD: Mất gốc, Không có thời gian, Không biết bắt đầu từ đâu...
# 7. **Phong cách/ sở thích học tập** : Người học thích học theo sơ thích gì: video , tài liệu , học theo chủ đề yêu thích....

# Luôn hỏi từng mục một rõ ràng,theo thứ tự, ngắn gọn, dễ hiểu. Nếu người học trả lời thiếu,chưa trả lời ,lang mang, hãy gợi ý chi tiết hoặc nhắc lại để họ bổ sung.
# Nếu cần biết thêm thôn tin gì của người dùng thì in ra mục, hỏi để họ nhập thông tin vào ( vidu như :bạn chưa nhập xxx hãy nhập xxx nhé)

# Hãy bắt đầu bằng câu chào thân thiện, sau đó từng bước thu thập thông tin theo từng phần một ở trên.xong 1 đến 2 , xong 2 đến 3 ...
# Call tool `collect_profile` để trích xuất hồ sơ học tập từ các tin nhắn khi đã thu thập đủ trong hội thoại và đưa vào bản tóm tắt thông tin người dùng sau cùng 
# lưu ý : Trả lời bằng tiếng việt.

# ### Input:
# CONVERSATION CONTEXT:
# <The conversation context between a human and an agent>

# CONVERSATION:
# <A conversation between a human and an agent>


