from typing import Optional, Dict, Any, Tuple, List, AsyncGenerator
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage
from dotenv import load_dotenv
import logging
import traceback
from dataclasses import dataclass
import os
import uuid

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
        self.llm = ChatGoogleGenerativeAI(
            model=model_name or os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite"),
            temperature=temperature,
        )
        self.resume_service = InfoService()
        self.redis_service = RedisService()
        self.details = ResumeDetails()
        self._setup_prompt_template()

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

    async def _fetch_with_cache(self, key: str, fetch_func) -> Optional[str]:
        """
        Fetch data with Redis caching.

        Args:
            key (str): Cache key
            fetch_func: Async function to fetch data if not in cache

        Returns:
            Optional[str]: Fetched data
        """
        # Try to get from cache first
        cached_value = self.redis_service.get(key)
        if cached_value is not None:
            logger.debug(f"Cache hit for key: {key}")
            return cached_value

        # If not in cache, fetch and store
        try:
            value = await fetch_func()
            if value:
                self.redis_service.set(key, value, CACHE_EXPIRE)
                logger.debug(f"Cached value for key: {key}")
            return value
        except Exception as e:
            logger.error(f"Error fetching data for key {key}: {str(e)}")
            return None

    async def _ensure_all_details(self) -> None:
        """
        Ensure all resume details are loaded.

        This method fetches all resume-related information if not already loaded.
        """
        try:
            # Fetch all details with caching
            self.details.resume_text = await self._fetch_with_cache(
                CACHE_KEYS["resume_text"], self.resume_service.fetch_resume_text
            )
            self.details.full_name = await self._fetch_with_cache(
                CACHE_KEYS["full_name"], self.resume_service.fetch_name
            )
            self.details.summary = await self._fetch_with_cache(
                CACHE_KEYS["summary"], self.resume_service.fetch_summary
            )
            self.details.skills = await self._fetch_with_cache(
                CACHE_KEYS["skills"], self.resume_service.fetch_skills
            )
            self.details.languages = await self._fetch_with_cache(
                CACHE_KEYS["languages"], self.resume_service.fetch_languages
            )
            self.details.experience = await self._fetch_with_cache(
                CACHE_KEYS["experience"], self.resume_service.fetch_experience
            )
            self.details.projects = await self._fetch_with_cache(
                CACHE_KEYS["projects"], self.resume_service.fetch_projects
            )
            self.details.education = await self._fetch_with_cache(
                CACHE_KEYS["education"], self.resume_service.fetch_education
            )
            self.details.certifications = await self._fetch_with_cache(
                CACHE_KEYS["certifications"], self.resume_service.fetch_certifications
            )
            self.details.contact_details = await self._fetch_with_cache(
                CACHE_KEYS["contact_details"], self.resume_service.fetch_contact_details
            )

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
            logger.error(traceback.format_exc())
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
