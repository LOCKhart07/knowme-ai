from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import traceback
from ..prompts import BasePrompts
from ..models import ChatHistory
from .info_service import InfoService
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv()


class LLMService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite", temperature=0.7
        )
        self.resume_service = InfoService()
        self._resume = None
        self._full_name = None
        self._summary = None
        self._skills = None
        self._languages = None
        self._experience = None
        self._projects = None
        self._education = None
        self._certifications = None
        self._contact_details = None

        self.messages_template = ChatPromptTemplate.from_messages(
            [
                ("system", BasePrompts.PORTFOLIO_QUERY),
                MessagesPlaceholder("history", optional=True),
                ("user", "{{ input }}"),
            ],
            template_format="mustache",
        )

    async def _ensure_all_details(self):
        """Ensure all resume details are loaded"""
        if self._resume is None:
            self._resume = await self.resume_service.fetch_resume_text()
        if self._full_name is None:
            self._full_name = await self.resume_service.fetch_name()
        if self._summary is None:
            self._summary = await self.resume_service.fetch_summary()
        if self._skills is None:
            self._skills = await self.resume_service.fetch_skills()
        if self._languages is None:
            self._languages = await self.resume_service.fetch_languages()
        if self._experience is None:
            self._experience = await self.resume_service.fetch_experience()
        if self._projects is None:
            self._projects = await self.resume_service.fetch_projects()
        if self._education is None:
            self._education = await self.resume_service.fetch_education()
        if self._certifications is None:
            self._certifications = await self.resume_service.fetch_certifications()
        if self._contact_details is None:
            self._contact_details = await self.resume_service.fetch_contact_details()

    async def process_query(
        self, query: str, history: ChatHistory = None
    ) -> tuple[str, ChatHistory]:
        try:
            # Ensure resume text is loaded
            await self._ensure_all_details()

            messages = self.messages_template.invoke(
                {
                    "full_name": self._full_name,
                    "summary": self._summary,
                    "skills": self._skills,
                    "languages": self._languages,
                    "experience": self._experience,
                    "projects": self._projects,
                    "education": self._education,
                    "certifications": self._certifications,
                    "contact_details": self._contact_details,
                    "history": self._format_history(history),
                    "resume": self._resume,
                    "input": query,
                }
            )

            # Get response from LLM
            response = self.llm.invoke(messages)
            return response.content, history
        except Exception as e:
            traceback.print_exc()
            raise Exception(f"Error processing query: {str(e)}")

    @staticmethod
    def _format_history(history: ChatHistory) -> str:
        if history is None:
            return []
        return [(msg.role, msg.content) for msg in history.messages]
