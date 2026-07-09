from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from src.clients.llm import LLMClient
from src.chatbot.RAG import MainAgent
from src.chatbot.router import RouterAgent
from src.chatbot.api import apiAgent
from src.chatbot.other import OtherAgent
from src.clients.databases import qdrant
from src.state import State
from src.configs import env_config

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver


class ChatbotEngine:
    def __init__(self):
        self.llm_client = LLMClient(
            model=env_config.model,
            api_provider=env_config.api_provider
        )

        self.state: State = {
            "messages": [],
            "messages_router": [],
            "state_router": False,
            "state_main": False,
            "state_api": False,
            "state_other": False,
            "route": None,
            "extract": None,
            "history": [],
            "query_transform": None
        }

        self.graph = self._create_graph()

    def _create_graph(self):
        router_agent = RouterAgent(self.llm_client)
        main_agent = MainAgent(self.llm_client, vector_store=qdrant)
        api_agent = apiAgent(self.llm_client)
        other_agent = OtherAgent(self.llm_client)

        graph = StateGraph(State)

        graph.add_node("router_agent", router_agent)
        graph.add_node("main_agent", main_agent)
        graph.add_node("api_agent", api_agent)
        graph.add_node("other_agent", other_agent)

        graph.set_entry_point("router_agent")

        graph.add_conditional_edges(
            "router_agent",
            lambda state: (
                "main_agent" if state.get("route") == 1
                else "api_agent" if state.get("route") == 2
                else "other_agent" if state.get("route") == 3
                else END
            ),
            {
                "main_agent": "main_agent",
                "api_agent": "api_agent",
                "other_agent": "other_agent",
                END: END
            }
        )

        graph.add_conditional_edges("main_agent", lambda _: END, {END: END})
        graph.add_conditional_edges("api_agent", lambda _: END, {END: END})
        graph.add_conditional_edges("other_agent", lambda _: END, {END: END})

        return graph.compile(checkpointer=MemorySaver())

    def chat(self, user_text: str) -> str:
        self.state["messages"].append(
            HumanMessage(content=user_text)
        )

        self.state = self.graph.invoke(
            self.state,
            config=RunnableConfig(
                configurable={"thread_id": "web_chat"}
            )
        )

        ai_messages = [
            msg for msg in self.state["messages"]
            if msg.type == "ai"
        ]

        if ai_messages:
            return ai_messages[-1].content

        return "Xin lỗi, tôi chưa có phản hồi."
