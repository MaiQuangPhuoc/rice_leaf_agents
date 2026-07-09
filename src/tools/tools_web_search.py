
import os
import logging
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.documents import Document
from src.modules.rag.reranker import VietnameseReranker
from src.configs import env_config
api_key = env_config.api_key_tavily


def tools_web_search(query: str, api_key: str, k: int = 5, score_threshold: float = 0.5):
    """
    Web search tool dùng TavilySearchResults (API mới nhất của LangChain 2025).
    Trả về list[Document].
    """

    os.environ["TAVILY_API_KEY"] = api_key

    tool = TavilySearchResults(max_results=k)

    response = tool.invoke(query)

    results = []
    for item in response:
        score = item.get("score", 0)
        if score >= score_threshold:
            results.append(
                Document(
                    page_content=item.get("content", ""),
                    metadata={
                        "url": item.get("url", ""),
                        "score": score
                    }
                )
            )
    return results

 