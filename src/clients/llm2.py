import logging
 
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
)
from langchain_core.messages import HumanMessage

from typing import List, Optional, Union

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI

from src.configs2 import env_config

logger = logging.getLogger(__name__)


class LLMClient:

    def __init__(self, model: str):
        self.model = model
        self.model = model

        self._llm = self._initialize_llm()

    def _initialize_llm(self):

        return ChatOpenAI(
            model=self.model,
            api_key=env_config.openai_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    def _configure_llm(
        self,
        max_tokens: int,
        temperature: float,
        llm_tools: List[BaseTool],
        output_model=None,
    ):

        llm = self._llm.bind(
            max_tokens=max_tokens,
            temperature=temperature,
        )

        if llm_tools:
            llm = llm.bind_tools(llm_tools)

        if output_model:
            llm = llm.with_structured_output(output_model)

        return llm

    def invoke_with_retries(
        self,
        prompt: ChatPromptTemplate,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        llm_tools: List[BaseTool] = None,
        output_model=None,
        num_retries: int = 3,
    ):

        if llm_tools is None:
            llm_tools = []

        llm = self._configure_llm(
            max_tokens=max_tokens,
            temperature=temperature,
            llm_tools=llm_tools,
            output_model=output_model,
        )

        for attempt in range(num_retries):

            try:
                chain = prompt | llm
                return chain.invoke({})

            except Exception as e:

                logger.error(
                    f"Attempt {attempt + 1} failed: {e}"
                )

                if attempt == num_retries - 1:
                    raise

    async def ainvoke_with_retries(
        self,
        prompt: Union[
            ChatPromptTemplate,
            List[BaseMessage]
        ],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        llm_tools: List[BaseTool] = None,
        output_model=None,
        num_retries: int = 3,
    ):

        if llm_tools is None:
            llm_tools = []

        llm = self._configure_llm(
            max_tokens=max_tokens,
            temperature=temperature,
            llm_tools=llm_tools,
            output_model=output_model,
        )

        for attempt in range(num_retries):

            try:

                if isinstance(prompt, list):
                    return await llm.ainvoke(prompt)

                chain = prompt | llm
                return await chain.ainvoke({})

            except Exception as e:

                logger.error(
                    f"Attempt {attempt + 1} failed: {e}"
                )

                if attempt == num_retries - 1:
                    raise


llm_client = LLMClient(
    model=env_config.model
)



response = llm_client._llm.invoke(
    [
        HumanMessage(
            content="Năm 2026 ai là tổng thống Mỹ?"
        )
    ]
)

print(response.content)