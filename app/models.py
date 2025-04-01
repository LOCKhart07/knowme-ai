from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class MessageRole(str, Enum):
    """Enumeration of possible message roles in a chat conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """
    Represents a single message in a chat conversation.

    Attributes:
        role (MessageRole): The role of the message sender (user, assistant, or system)
        content (str): The content of the message
    """

    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")


class ChatHistory(BaseModel):
    """
    Represents a chat conversation history.

    Attributes:
        messages (List[Message]): List of messages in the conversation
    """

    messages: List[Message] = Field(
        default_factory=list, description="List of chat messages"
    )


class QueryRequest(BaseModel):
    """
    Represents a chat query request from the user.

    Attributes:
        query (str): The user's query text
        history (Optional[ChatHistory]): Optional chat history for context
    """

    query: str = Field(..., description="User's query text")
    history: Optional[ChatHistory] = Field(
        default=None, description="Optional chat history"
    )


class PongResponse(BaseModel):
    """
    Response model for the health check endpoint.

    Attributes:
        message (str): Response message, typically "pong"
    """

    message: str = Field(..., description="Health check response message")


class QueryResponse(BaseModel):
    """
    Response model for a chat query.

    Attributes:
        response (str): The AI's response to the query
        history (ChatHistory): Updated chat history including the new interaction
    """

    response: str = Field(..., description="AI's response to the query")
    history: ChatHistory = Field(..., description="Updated chat history")


class StreamingResponse(BaseModel):
    """
    Response model for streaming chat responses.

    Attributes:
        chunk (str): A chunk of the AI's response
        is_final (bool): Whether this is the final chunk
    """

    chunk: str = Field(..., description="A chunk of the AI's response")
    is_final: bool = Field(..., description="Whether this is the final chunk")
