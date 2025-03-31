from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import traceback
from ..prompts import BasePrompts
from ..models import ChatHistory, Message
from .resume_service import ResumeService

load_dotenv()


class LLMService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite", temperature=0.7
        )
        self.resume_service = ResumeService()
        self.chain = BasePrompts.PORTFOLIO_QUERY | self.llm
        self._resume_text = None

    async def _ensure_resume_text(self):
        """Ensure resume text is loaded"""
        if self._resume_text is None:
            self._resume_text = await self.resume_service.get_resume_text()
            if self._resume_text:
                # Update the prompt with resume data
                formatted_resume = self.resume_service.format_resume_for_prompt(
                    self._resume_text
                )
                self.chain = (
                    BasePrompts.PORTFOLIO_QUERY.partial(
                        full_name="Your Name"  # Replace with actual name from resume
                    )
                    | self.llm
                )

    async def process_query(
        self, query: str, history: ChatHistory = None
    ) -> tuple[str, ChatHistory]:
        try:
            # Ensure resume text is loaded
            await self._ensure_resume_text()

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

    async def process_career_query(
        self, query: str, history: ChatHistory = None
    ) -> tuple[str, ChatHistory]:
        try:
            # Ensure resume text is loaded
            await self._ensure_resume_text()

            chain = BasePrompts.PORTFOLIO_QUERY | self.llm
            formatted_history = BasePrompts.format_history(
                history.messages if history else []
            )

            response = chain.invoke({"history": formatted_history, "query": query})

            new_message = Message(role="assistant", content=response.content)

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
            raise Exception(f"Error processing career query: {str(e)}")

    async def process_skills_query(self, query: str) -> str:
        try:
            chain = BasePrompts.SKILLS_QUERY | self.llm
            response = chain.invoke([{"role": "user", "content": query}])
            return response.content
        except Exception as e:
            traceback.print_exc()
            raise Exception(f"Error processing skills query: {str(e)}")
