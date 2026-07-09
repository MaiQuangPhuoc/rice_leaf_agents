# import logging
 
# from mailbox import BabylMessage
# import sys
# import os

 
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
# # from state import State
# from typing import Union, List
# from langchain_core.messages import BaseMessage

# from src.state import State

# from typing import List, Optional
# # from langchain_openai import ChatOpenAI
# # from langchain_anthropic import ChatAnthropic
# # from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_groq import ChatGroq
# # from langchain.prompts import ChatPromptTemplate
# from langchain_core.prompts import ChatPromptTemplate
# from langchain.tools import BaseTool
# from pydantic import BaseModel
# from src.configs import env_config


# logger = logging.getLogger(__name__)

# class LLMClient:
#     """Client for interacting with various LLM providers."""
    
#     SUPPORTED_PROVIDERS = {
#         # "openai": ChatOpenAI,
#         # "anthropic": ChatAnthropic, 
#         # "google": ChatGoogleGenerativeAI,
#         "groq": ChatGroq
#     }
    
#     def __init__(self, model: str, api_provider: str):
#         """
#         Initialize the LLM client.
        
#         Args:
#             model: Model name to use
#             api_provider: API provider ('openai', 'anthropic', 'google', 'groq')
            
#         Raises:
#             ValueError: If unsupported provider or missing configuration
#         """
#         if api_provider not in self.SUPPORTED_PROVIDERS:
#             raise ValueError(f"Unsupported provider: {api_provider}. Supported: {list(self.SUPPORTED_PROVIDERS.keys())}")
        
#         self._llm = self._initialize_llm(model, api_provider)
#         self.model = model
#         self.api_provider = api_provider

#     def _initialize_llm(self, model: str, api_provider: str):
#         """Initialize the appropriate LLM based on provider."""
#         try:
#             # if api_provider == "openai":
#             #     if not env_config.openai_api_key:
#             #         raise ValueError("OpenAI API key not configured")
#             #     return ChatOpenAI(model=model, openai_api_key=env_config.openai_api_key)
                
#             # elif api_provider == "anthropic":
#             #     if not env_config.anthropic_api_key:
#             #         raise ValueError("Anthropic API key not configured")
#             #     return ChatAnthropic(model=model, anthropic_api_key=env_config.anthropic_api_key)
                
#             # if api_provider == "google":
#             #     if not env_config.google_api_key:
#             #         raise ValueError("Google API key not configured")
#             #     return ChatGoogleGenerativeAI(model=model, google_api_key=env_config.google_api_key)
                
#             if api_provider == "groq":
#                 if not env_config.groq_api_key:
#                     raise ValueError("Groq API key not configured")
#                 return ChatGroq(model=model, groq_api_key=env_config.groq_api_key)
                
#         except Exception as e:
#             logger.error(f"Failed to initialize {api_provider} LLM: {e}")
#             raise

#     def invoke_with_retries(
#         self,
#         prompt: ChatPromptTemplate,
#         max_tokens: int = 1024,
#         temperature: float = 1,
#         llm_tools: List[BaseTool] = None,
#         output_model: Optional[BaseModel] = None,
#         num_retries: int = 1,
#     ):
#         """
#         Invoke the LLM with retry logic.
        
#         Args:
#             prompt: Chat prompt template
#             max_tokens: Maximum tokens to generate
#             temperature: Sampling temperature
#             llm_tools: List of tools to bind to the LLM
#             output_model: Pydantic model for structured output
#             num_retries: Number of retry attempts
            
#         Returns:
#             LLM response
            
#         Raises:
#             Exception: If all retry attempts fail
#         """
#         if llm_tools is None:
#             llm_tools = []
            
#         llm = self._configure_llm(max_tokens, temperature, llm_tools, output_model)
        
#         for attempt in range(num_retries):
#             try:
#                 chain = prompt | llm
#                 response = chain.invoke(input={})
#                 logger.info(f"LLM invocation successful on attempt {attempt + 1}")
#                 return response
                
#             except Exception as e:
#                 logger.error(f"Attempt {attempt + 1} failed: {e}")
                
#                 if attempt == num_retries - 1:
#                     logger.error(f"All {num_retries} attempts failed")
#                     raise
                    
#                 logger.info(f"Retrying... {attempt + 2}/{num_retries}")

#     async def ainvoke_with_retries(
#         self,
#         # prompt: ChatPromptTemplate,
#         prompt: Union[ChatPromptTemplate, List[BaseMessage]],

#         max_tokens: int = 1024,
#         temperature: float = 1,
#         llm_tools: List[BaseTool] = None,
#         output_model: Optional[BaseModel] = None,
#         num_retries: int = 1,
#     ):
#         if llm_tools is None:
#             llm_tools = []

#         llm = self._configure_llm(max_tokens, temperature, llm_tools, output_model)

#         for attempt in range(num_retries):
#             try:
#                 # print("ainvoke is running with ")

#                 if isinstance(prompt, list):  # list[BaseMessage]
#                     print("list[BaseMessage]")

#                     response = await llm.ainvoke(prompt)
#                 else:  # ChatPromptTemplate
#                     print("ChatPromptTemplate")

#                     chain = prompt | llm
#                     response = await chain.ainvoke(input={})

#                 # logger.info(f"LLM_LLM gọi thành công ở lần thử thứ {attempt + 1}")
#                 # logger.debug(f" Đầu ra LLM:\n{response}")
#                 # print(f"✅ LLM phản hồi:\n{response.content if hasattr(response, 'content') else response}")
                
#                 return response

#             except Exception as e:
#                 logger.error(f"❌ Lỗi ở lần thử thứ {attempt + 1}: {e}")

#                 if attempt == num_retries - 1:
#                     logger.error(f"🚫 Tất cả {num_retries} lần gọi đều thất bại")

                 
                

#                     raise

#                 logger.info(f"🔁 Đang thử lại... ({attempt + 2}/{num_retries})")

#     def _configure_llm(self, max_tokens: int, temperature: float, 
#                       llm_tools: List[BaseTool], output_model: Optional[BaseModel]):
#         """Configure the LLM with the specified parameters."""
#         llm = self._llm.bind(max_tokens=max_tokens, temperature=temperature)
        
#         if llm_tools:
#             llm = llm.bind_tools(llm_tools)
            
#         if output_model:
#             llm = llm.with_structured_output(output_model)
            
#         return llm

# # Global LLM client instance
# try:
#     llm_client = LLMClient(
#         model=env_config.model,
#         api_provider=env_config.api_provider
#     )
# except Exception as e:
#     logger.error(f"Failed to initialize global LLM client: {e}")
#     llm_client = None

# from langchain_core.messages import HumanMessage

# try:
#     llm_client = LLMClient(
#         model=env_config.model,
#         api_provider=env_config.api_provider
#     )
#     print("✅ LLM phản hồi:")
#     # Dùng trực tiếp llm bên trong LLMClient để test
#     response = llm_client._llm.invoke([


#         HumanMessage(content="năm 2026 ai là tổng thống mỹ?")
#     ])


#     print(response.content)

# except Exception as e:
#     logger.error(f"❌ Lỗi khởi tạo LLM client hoặc gọi LLM: {e}")


# # from langchain_groq import ChatGroq
# # model=env_config.model
# # groq_api_key=env_config.groq_api_key
# # llm = ChatGroq(model=model, groq_api_key=groq_api_key)
# # print(f"------------------------------\n model name : {model} , api : {groq_api_key}")
# # print(llm.bind_tools([]))  # không lỗi là 



import logging, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from typing import List, Optional, Union
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import BaseTool
from pydantic import BaseModel

from src.configs import env_config

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM client hỗ trợ groq / openai / openrouter, bật/tắt bằng cách
    đổi api_provider trong .env, không cần sửa code."""

    def __init__(self, model: str, api_provider: str = None):
        self.model = model
        self.api_provider = api_provider or env_config.api_provider
        self._llm = self._initialize_llm()

    def _initialize_llm(self):
        provider = self.api_provider

        if provider == "groq":
            from langchain_groq import ChatGroq
            if not env_config.groq_api_key:
                raise ValueError("Thiếu GROQ_API_KEY trong .env")
            return ChatGroq(model=self.model, groq_api_key=env_config.groq_api_key)

        elif provider == "openai":
            from langchain_openai import ChatOpenAI
            if not env_config.openai_api_key:
                raise ValueError("Thiếu OPENAI_API_KEY trong .env")
            return ChatOpenAI(model=self.model, api_key=env_config.openai_api_key)

        elif provider == "openrouter":
            from langchain_openai import ChatOpenAI
            if not env_config.openrouter_api_key:
                raise ValueError("Thiếu OPENROUTER_API_KEY trong .env")
            return ChatOpenAI(
                model=self.model,
                api_key=env_config.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            )

        else:
            raise ValueError(f"api_provider không hỗ trợ: {provider}")

    def _configure_llm(self, max_tokens, temperature, llm_tools, output_model):
        llm = self._llm.bind(max_tokens=max_tokens, temperature=temperature)
        if llm_tools:
            llm = llm.bind_tools(llm_tools)
        if output_model:
            llm = llm.with_structured_output(output_model)
        return llm

    def invoke_with_retries(self, prompt: ChatPromptTemplate, max_tokens=1024,
                             temperature=1, llm_tools: List[BaseTool] = None,
                             output_model: Optional[BaseModel] = None, num_retries=1):
        llm_tools = llm_tools or []
        llm = self._configure_llm(max_tokens, temperature, llm_tools, output_model)
        for attempt in range(num_retries):
            try:
                chain = prompt | llm
                response = chain.invoke(input={})
                logger.info(f"LLM invocation successful on attempt {attempt + 1}")
                return response
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == num_retries - 1:
                    raise
                logger.info(f"Retrying... {attempt + 2}/{num_retries}")

    async def ainvoke_with_retries(self, prompt: Union[ChatPromptTemplate, List[BaseMessage]],
                                    max_tokens=1024, temperature=1,
                                    llm_tools: List[BaseTool] = None,
                                    output_model: Optional[BaseModel] = None, num_retries=1):
        llm_tools = llm_tools or []
        llm = self._configure_llm(max_tokens, temperature, llm_tools, output_model)
        for attempt in range(num_retries):
            try:
                if isinstance(prompt, list):
                    return await llm.ainvoke(prompt)
                chain = prompt | llm
                return await chain.ainvoke(input={})
            except Exception as e:
                logger.error(f"Lỗi ở lần thử thứ {attempt + 1}: {e}")
                if attempt == num_retries - 1:
                    raise
                logger.info(f"Đang thử lại... ({attempt + 2}/{num_retries})")


# Global client — comment dòng dưới nếu không muốn auto-init lúc import
try:
    llm_client = LLMClient(model=env_config.model, api_provider=env_config.api_provider)
except Exception as e:
    logger.error(f"Failed to initialize global LLM client: {e}")
    llm_client = None


# from langchain_core.messages import HumanMessage

# try:
#     llm_client = LLMClient(
#         model=env_config.model,
#         api_provider=env_config.api_provider
#     )
#     print("LLM phản hồi:")
#     # Dùng trực tiếp llm bên trong LLMClient để test
#     response = llm_client._llm.invoke([


#         HumanMessage(content="năm 2026 ai là tổng thống mỹ?")
#     ])


#     print(response.content)

# except Exception as e:
#     logger.error(f" Lỗi khởi tạo LLM client hoặc gọi LLM: {e}")