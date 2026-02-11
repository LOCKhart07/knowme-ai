from typing import Optional, Tuple, List, AsyncGenerator
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
import logging
import traceback
from dataclasses import dataclass
import os
import uuid
import time
from .api_key_balancer import APIKeyBalancer

from ..prompts import BasePrompts
from ..models import ChatHistory, Message, MessageRole
from .info_service import InfoService
from .redis_service import RedisService

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Cache keys
CACHE_KEYS = {
    "resume_text": "resume:text",
    "full_name": "resume:full_name",
    "summary": "resume:summary",
    "skills": "resume:skills",
    "languages": "resume:languages",
    "experience": "resume:experience",
    "projects": "resume:projects",
    "education": "resume:education",
    "certifications": "resume:certifications",
    "contact_details": "resume:contact_details",
}

# Cache expiration time in seconds (1 hour)
CACHE_EXPIRE = 3600


@dataclass
class ResumeDetails:
    """Data class to hold all resume-related information."""

    full_name: Optional[str] = None
    summary: Optional[str] = None
    skills: Optional[str] = None
    languages: Optional[str] = None
    experience: Optional[str] = None
    projects: Optional[str] = None
    education: Optional[str] = None
    certifications: Optional[str] = None
    contact_details: Optional[str] = None
    resume_text: Optional[str] = None


class LLMService:
    """
    Service for handling LLM-based chat interactions.

    This service manages the interaction with the language model, including
    resume information retrieval and chat history management.
    """

    def __init__(self, model_name: str = None, temperature: float = 0.7):
        """
        Initialize the LLM service.

        Args:
            model_name (str, optional): Name of the LLM model to use. If not provided,
                                      will use GEMINI_MODEL environment variable or default to "gemini-2.0-flash-lite"
            temperature (float): Temperature parameter for the LLM
        """
        self.model_name = model_name or os.getenv("MODEL_NAME", "gemini-2.0-flash-lite")
        self.temperature = temperature
        self.info_service = InfoService()
        self.redis_service = RedisService()
        self.api_key_balancer = APIKeyBalancer(self.redis_service)
        self.details = ResumeDetails()
        self._setup_prompt_template()
        self._setup_llm()

    def _setup_llm(self) -> None:
        """Set up the LLM with the current API key."""
        api_key = self.api_key_balancer.get_next_key()
        if not api_key:
            raise ValueError("No available API keys found")

        print("Using API key:", api_key)
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=api_key,
            temperature=self.temperature,
        )

    async def _retry_with_new_key(self, func, *args, **kwargs):
        """Retry a function with a new API key if the current one fails."""
        max_retries = len(self.api_key_balancer.api_keys) * 2  # Allow two full cycles
        retry_delay = 1  # Start with 1 second delay

        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_message = str(e)
                logger.error(
                    f"API call failed (attempt {attempt + 1}/{max_retries}): {error_message}"
                )

                # Mark current key as failed
                current_key = self.llm.google_api_key
                self.api_key_balancer.mark_key_failed(current_key, error_message)

                # Try with a new key
                new_key = self.api_key_balancer.get_next_key()
                if not new_key:
                    if attempt < max_retries - 1:
                        # Wait before retrying
                        time.sleep(retry_delay)
                        retry_delay = min(
                            retry_delay * 2, 10
                        )  # Exponential backoff, max 10 seconds
                        continue
                    raise ValueError("All API keys failed after multiple retries")

                self.llm.google_api_key = new_key
                logger.info(f"Switched to new API key for retry {attempt + 1}")
                continue

        raise ValueError("All API keys failed after multiple retries")

    def _setup_prompt_template(self) -> None:
        """Set up the chat prompt template with system message and placeholders."""
        self.messages_template = ChatPromptTemplate.from_messages(
            [
                ("system", BasePrompts.PORTFOLIO_QUERY),
                MessagesPlaceholder("history", optional=True),
                ("user", "{{ input }}"),
            ],
            template_format="mustache",
        )

    async def _ensure_all_details(self) -> None:
        """
        Ensure all resume details are loaded.

        This method fetches all resume-related information if not already loaded.
        """
        try:
            # Fetch all details
            await self.info_service.initialize()

            self.details.resume_text = self.info_service.resume_text
            self.details.full_name = self.info_service.full_name
            self.details.summary = self.info_service.summary
            self.details.skills = self.info_service.skills
            self.details.languages = self.info_service.languages
            self.details.experience = self.info_service.experience
            self.details.projects = self.info_service.projects
            self.details.education = self.info_service.education
            self.details.certifications = self.info_service.certifications
            self.details.contact_details = self.info_service.contact_details

            # Check if any required data is missing
            missing_fields = [
                field for field, value in self.details.__dict__.items() if value is None
            ]
            if missing_fields:
                raise Exception(
                    f"Failed to load required fields: {', '.join(missing_fields)}"
                )

        except Exception as e:
            logger.error(f"Error loading resume details: {str(e)}")
            logger.error(traceback.format_exc())
            raise Exception("Failed to load resume details") from e

    async def process_query(
        self,
        query: str,
        history: Optional[ChatHistory] = None,
        query_message_id: Optional[uuid.UUID] = None,
    ) -> Tuple[str, ChatHistory, uuid.UUID]:
        """
        Process a chat query and return the response.

        Args:
            query (str): The user's query text
            history (Optional[ChatHistory]): Optional chat history for context
            query_message_id (Optional[uuid.UUID]): Optional message ID for the user's query

        Returns:
            Tuple[str, ChatHistory, uuid.UUID]: The AI's response, updated chat history, and message ID

        Raises:
            Exception: If there's an error processing the query
        """
        return await self._retry_with_new_key(
            self._process_query_impl, query, history, query_message_id
        )

    async def _process_query_impl(
        self,
        query: str,
        history: Optional[ChatHistory] = None,
        query_message_id: Optional[uuid.UUID] = None,
    ) -> Tuple[str, ChatHistory, uuid.UUID]:
        """Implementation of process_query with error handling."""
        try:
            # Ensure resume text is loaded
            await self._ensure_all_details()

            # Prepare messages for the LLM
            messages = self.messages_template.invoke(
                {
                    "full_name": self.details.full_name,
                    "summary": self.details.summary,
                    "skills": self.details.skills,
                    "languages": self.details.languages,
                    "experience": self.details.experience,
                    "projects": self.details.projects,
                    "education": self.details.education,
                    "certifications": self.details.certifications,
                    "contact_details": self.details.contact_details,
                    "history": self._format_history(history),
                    "resume": self.details.resume_text,
                    "input": query,
                }
            )

            # Get response from LLM
            response = self.llm.invoke(messages)

            # Update chat history with the query message ID
            updated_history = self._update_history(
                history, query, response.content, query_message_id
            )

            # Get the message ID of the assistant's response (last message in history)
            message_id = updated_history.messages[-1].message_id

            return response.content, updated_history, message_id

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            logger.error(traceback.format_exc())
            raise Exception(f"Error processing query: {str(e)}") from e

    async def process_query_stream(
        self,
        query: str,
        history: Optional[ChatHistory] = None,
        query_message_id: Optional[uuid.UUID] = None,
    ) -> AsyncGenerator[Tuple[Message, bool], None]:
        """
        Process a chat query and stream the response chunks.

        Args:
            query (str): The user's query text
            history (Optional[ChatHistory]): Optional chat history for context
            query_message_id (Optional[uuid.UUID]): Optional message ID for the user's query

        Yields:
            Tuple[Message, bool]: Message object and whether it's the final chunk

        Raises:
            Exception: If there's an error processing the query
        """
        try:
            # Ensure resume text is loaded
            await self._ensure_all_details()

            # Create a temporary message to get its ID
            temp_message = Message(role=MessageRole.ASSISTANT, content="")
            message_id = temp_message.message_id

            # Update history with the query message ID
            # if history is not None:
            #     history = self._update_history(history, query, "", query_message_id)

            # Prepare messages for the LLM
            messages = self.messages_template.invoke(
                {
                    "full_name": self.details.full_name,
                    "summary": self.details.summary,
                    "skills": self.details.skills,
                    "languages": self.details.languages,
                    "experience": self.details.experience,
                    "projects": self.details.projects,
                    "education": self.details.education,
                    "certifications": self.details.certifications,
                    "contact_details": self.details.contact_details,
                    "history": self._format_history(history),
                    "resume": self.details.resume_text,
                    "input": query,
                }
            )

            # Stream response from LLM
            async for chunk in self.llm.astream(messages):
                is_final = chunk.response_metadata.get("finish_reason") == "STOP"
                yield Message(
                    role=MessageRole.ASSISTANT,
                    content=chunk.content,
                    message_id=message_id,
                ), is_final

        except Exception as e:
            logger.error(f"Error processing streaming query: {str(e)}")
            traceback.format_exc()
            raise Exception(f"Error processing streaming query: {str(e)}") from e

    @staticmethod
    def _format_history(history: Optional[ChatHistory]) -> List[Tuple[str, str]]:
        """
        Format chat history for the prompt template.

        Args:
            history (Optional[ChatHistory]): The chat history to format

        Returns:
            List[Tuple[str, str]]: Formatted history as list of (role, content) tuples
        """
        if history is None:
            return []
        return [(msg.role.value, msg.content) for msg in history.messages]

    @staticmethod
    def _update_history(
        history: Optional[ChatHistory],
        query: str,
        response: str,
        query_message_id: Optional[uuid.UUID] = None,
    ) -> ChatHistory:
        """
        Update chat history with new query and response.

        Args:
            history (Optional[ChatHistory]): Existing chat history
            query (str): User's query
            response (str): AI's response
            query_message_id (Optional[uuid.UUID]): Optional message ID for the user's query

        Returns:
            ChatHistory: Updated chat history
        """
        if history is None:
            history = ChatHistory(messages=[])

        # Add user query with timestamp and optional message ID
        user_message = Message(role=MessageRole.USER, content=query)
        if query_message_id:
            user_message.message_id = query_message_id
        history.messages.append(user_message)

        # Add AI response with timestamp
        history.messages.append(Message(role=MessageRole.ASSISTANT, content=response))

        return history
