# from pydantic import BaseModel, Field, field_validator
# from typing import Annotated, List, Literal, Optional
# from typing_extensions import TypedDict
# # # from datetime import date
# from langgraph.graph import StateGraph, MessagesState, START, END , add_messages
# from langchain_core.messages import (AnyMessage)

# class QueryExtract(BaseModel):
#     query_clear: str                   
#     disease: Optional[list[str]] = None  
#     scientific_name: Optional[str] = None
#     topic: Optional[str] = None
#     keywords: list[str] = []


# class State(TypedDict):
#     messages: Annotated[list[AnyMessage], add_messages]  # messages của user
#     state_router: bool   # có được đi qua router hay không
#     state_rag: bool      # true → đến rag_agent
#     state_api: bool      # true → đến api_agent
#     state_other: bool    # true → đến other_agent
#     route: Optional[int] # 1: rag_agent, 2: api_agent, 3: other_agent
#     history: Annotated[list[AnyMessage], add_messages]
#     query_extract: Optional[QueryExtract]
#     last_message: Optional[AnyMessage]
