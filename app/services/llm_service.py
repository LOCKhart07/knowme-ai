from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import traceback
from ..prompts import BasePrompts
from ..models import ChatHistory, Message
from .info_service import InfoService
from langchain_core.prompts.chat import ChatPromptTemplate

load_dotenv()


class LLMService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite", temperature=0.7
        )
        self.resume_service = InfoService()
        self.chain = BasePrompts.PORTFOLIO_QUERY | self.llm
        self._resume = None
        self._full_name = None
        self._summary = None
        self._skills = None
        self._languages = None
        self.experience = None
        self.projects = None
        self.education = None
        self.certifications = None
        self.contact_details = None

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
        if self.experience is None:
            self.experience = await self.resume_service.fetch_experience()
        if self.projects is None:
            self.projects = await self.resume_service.fetch_projects()
        if self.education is None:
            self.education = await self.resume_service.fetch_education()
        if self.certifications is None:
            self.certifications = await self.resume_service.fetch_certifications()
        if self.contact_details is None:
            self.contact_details = await self.resume_service.fetch_contact_details()

        # Update the prompt with resume data
        self.chain = (
            BasePrompts.PORTFOLIO_QUERY.partial(
                full_name=self._full_name,
                summary=self._summary,
                skills=self._skills,
                languages=self._languages,
                experience=self.experience,
                projects=self.projects,
                education=self.education,
                certifications=self.certifications,
                contact_details=self.contact_details,
            )
            | self.llm
        )

    async def process_query(
        self, query: str, history: ChatHistory = None
    ) -> tuple[str, ChatHistory]:
        try:
            # Ensure resume text is loaded
            await self._ensure_all_details()

            # Format the chat history
            formatted_history = BasePrompts.format_history(
                history.messages if history else []
            )

            # Get response from LLM
            response = self.chain.invoke({"history": formatted_history, "query": query})

            # Create new message for the response
            new_message = Message(role="assistant", content=response.content)

            # Update chat history
            if history:
                history.messages.append(Message(role="user", content=query))
                history.messages.append(new_message)
            else:
                history = ChatHistory(
                    messages=[Message(role="user", content=query), new_message]
                )

            return response.content, history
        except Exception as e:
            traceback.print_exc()
            raise Exception(f"Error processing query: {str(e)}")
