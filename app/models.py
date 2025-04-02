from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime, UTC
import uuid


class MessageRole(str, Enum):
    """Enumeration of possible message roles in a chat conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """
    Represents a single message in a chat conversation.

    Attributes:
        message_id (uuid.UUID): Unique identifier for the message
        role (MessageRole): The role of the message sender (user, assistant, or system)
        content (str): The content of the message
        timestamp (datetime): The timestamp when the message was sent
    """

    message_id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4, description="Unique identifier for the message"
    )
    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the message was sent",
    )


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
        message_id (Optional[uuid.UUID]): Optional message ID for the user's query
    """

    query: str = Field(..., description="User's query text")
    history: Optional[ChatHistory] = Field(
        default=None, description="Optional chat history"
    )
    message_id: Optional[uuid.UUID] = Field(
        default=None, description="Optional message ID for the user's query"
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
        message_id (uuid.UUID): The ID of the assistant's response message
        request_id (Optional[uuid.UUID]): The ID of the user's request message
    """

    response: str = Field(..., description="AI's response to the query")
    history: ChatHistory = Field(..., description="Updated chat history")
    message_id: uuid.UUID = Field(
        ..., description="ID of the assistant's response message"
    )
    request_id: Optional[uuid.UUID] = Field(
        default=None, description="ID of the user's request message"
    )


class StreamingResponse(BaseModel):
    """
    Response model for streaming chat responses.

    Attributes:
        message (Message): The message containing the chunk of the AI's response
        is_final (bool): Whether this is the final chunk
        request_id (Optional[uuid.UUID]): The ID of the user's request message
    """

    message: Message = Field(
        ..., description="The message containing the chunk of the AI's response"
    )
    is_final: bool = Field(..., description="Whether this is the final chunk")
    request_id: Optional[uuid.UUID] = Field(
        default=None, description="ID of the user's request message"
    )
