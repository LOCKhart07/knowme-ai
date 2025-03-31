from pydantic import BaseModel
from typing import List, Optional


class Message(BaseModel):
    role: str
    content: str


class ChatHistory(BaseModel):
    messages: List[Message]


class QueryRequest(BaseModel):
    query: str
    history: Optional[ChatHistory] = None


class PongResponse(BaseModel):
    message: str


class QueryResponse(BaseModel):
    response: str
    history: ChatHistory
