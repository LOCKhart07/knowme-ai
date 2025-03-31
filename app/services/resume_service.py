import os
from typing import Optional
import requests
from langchain_community.document_loaders.pdf import OnlinePDFLoader
from dotenv import load_dotenv

load_dotenv()


class ResumeService:
    def __init__(self):
        self.api_token = os.getenv("DATOCMS_API_TOKEN")
        self.resume_id = os.getenv("DATOCMS_RESUME_ID")
        self.api_url = "https://graphql.datocms.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def fetch_resume_pdf(self) -> Optional[str]:
        """Fetch resume PDF URL from DatoCMS using GraphQL"""
        try:
            # GraphQL query to fetch resume data
            query = """
            query {
                profilebanner {
                    backgroundImage {
                        url
                    }
                    headline
                    resumeLink 
                    linkedinLink
                    profileSummary
                }
            }
            """

            # Make GraphQL request
            response = requests.post(
                self.api_url,
                json={"query": query},
                headers=self.headers,
            )
            response.raise_for_status()

            data = response.json()

            # Check for errors in GraphQL response
            if "errors" in data:
                print(f"GraphQL errors: {data['errors']}")
                return None

            # Extract resume link from response
            resume_data = data.get("data", {}).get("profilebanner", {})
            resume_url = resume_data.get("resumeLink")

            if not resume_url:
                print("No resume URL found in response")
                return None

            return resume_url

        except Exception as e:
            print(f"Error fetching resume from DatoCMS: {str(e)}")
            return None

    def extract_text_from_pdf(self, pdf_url: str) -> str:
        """Extract text from PDF using LangChain's OnlinePDFLoader"""
        try:
            # Use LangChain's OnlinePDFLoader
            loader = OnlinePDFLoader(pdf_url)
            pages = loader.load()

            # Combine text from all pages
            text = "\n".join(page.page_content for page in pages)
            return text.strip()

        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
            return ""

    async def get_resume_text(self) -> Optional[str]:
        """Get resume text by fetching PDF URL and extracting text"""
        try:
            # Fetch PDF URL from DatoCMS
            pdf_url = await self.fetch_resume_pdf()
            if not pdf_url:
                return None

            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_url)
            return text if text else None
        except Exception as e:
            print(f"Error getting resume text: {str(e)}")
            return None

    def format_resume_for_prompt(self, resume_text: str) -> str:
        """Format resume text for use in LLM prompt"""
        return f"""--- DATA ABOUT {{ full_name }} START ---

{resume_text}

--- DATA ABOUT {{ full_name }} END ---"""
