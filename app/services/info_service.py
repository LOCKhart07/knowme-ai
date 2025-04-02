import os
from typing import Optional
import requests
from dotenv import load_dotenv
from typing import List
from collections import defaultdict
import traceback
import json
import hashlib
from .redis_service import RedisService

load_dotenv()


class InfoService:
    def __init__(self):
        self.datocms_api_token = os.getenv("DATOCMS_API_TOKEN")
        self.dato_cms_url = "https://graphql.datocms.com"
        self.datocms_headers = {
            "Authorization": f"Bearer {self.datocms_api_token}",
            "Content-Type": "application/json",
        }
        self.redis_service = RedisService()

    def _get_cache_key(self, query: str) -> str:
        """Generate a unique cache key for the query"""
        # Create a hash of the query to use as the cache key
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return f"datocms:query:{query_hash}"

    def _query_datocms(self, query: str) -> Optional[dict]:
        """Execute a GraphQL query against DatoCMS with Redis caching"""
        try:
            # Generate cache key
            cache_key = self._get_cache_key(query)

            # Try to get cached data
            try:
                cached_data = self.redis_service.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                traceback.format_exc()
                print(f"Error getting cached data: {str(e)}")

            # If no cache, make the API request
            response = requests.post(
                self.dato_cms_url,
                json={"query": query},
                headers=self.datocms_headers,
            )
            response.raise_for_status()

            data = response.json()

            # Check for errors in GraphQL response
            if "errors" in data:
                print(f"GraphQL errors: {data['errors']}")
                return None

            # Cache the successful response
            self.redis_service.set(cache_key, json.dumps(data), 86400)  # 1 day

            return data

        except Exception as e:
            print(f"Error querying DatoCMS: {str(e)}")
            return None

    async def fetch_all_data(self) -> Optional[dict]:
        """Fetch all data from DatoCMS"""
        # GraphQL query to fetch resume data
        query = """
        query {
            resumeUncompiled {
                text
            }
            allSkills(first: 100, orderBy: order_ASC) {
                name
                category
                description
            }
            allTimelines {
                title
                timelineType
                summaryPoints
                name
                dateRange
                techStack
            }
            allProjects {
                description
                link
                techUsed
                title
            }
            allCertifications {
                issuedDate
                issuer
                link
                title
            }
            contactMe {
                name
                email
                linkedinLink
                phoneNumber
            }
            profilebanner {
                profileSummary
            }
        }
        """

        return self._query_datocms(query)

    async def initialize(self) -> None:
        """Initialize the service"""
        self.data = await self.fetch_all_data()

        self.resume_text = self._extract_resume_text()
        self.skills = self._format_skills(self._extract_skills())
        self.experience = self._format_experience(self._extract_experience())
        self.projects = self._format_projects(self._extract_projects())
        self.education = self._format_education(self._extract_education())
        self.certifications = self._format_certifications(
            self._extract_certifications()
        )
        self.contact_details = self._format_contact_details(
            self._extract_contact_details()
        )
        self.full_name = self._extract_name()
        self.summary = self._extract_summary()
        self.languages = self._extract_languages()

    def _extract_resume_text(self) -> Optional[str]:
        """Fetch resume text"""
        return self.data.get("data", {}).get("resumeUncompiled", {}).get("text")

    def _extract_skills(self):
        skills_list = self.data.get("data", {}).get("allSkills", [])

        return skills_list

    @staticmethod
    def _format_skills(skills: List[dict]) -> str:
        """Format the skills list into a desired structure."""

        # Group skills by category
        categorized_skills = defaultdict(list)
        for skill in skills:
            category = skill.get("category", "Uncategorized")
            name = skill.get("name", "Unnamed")
            categorized_skills[category].append(name)

        # Format the output as a string
        formatted_text = ""
        for category, skill_names in categorized_skills.items():
            formatted_text += f"{category}: {', '.join(skill_names)}\n"

        return formatted_text.strip()

    def _extract_experience(self):
        experience_list = self.data.get("data", {}).get("allTimelines", [])
        # Filter for work experience only
        experience_list = [
            exp for exp in experience_list if exp.get("timelineType") == "work"
        ]
        return experience_list

    @staticmethod
    def _format_experience(experience_list: List[dict]) -> str:
        """Format the experience list into a desired structure."""

        # Format the output as a string
        return "\n\n".join(
            [
                f"Company: {experience['name']}\nTitle: {experience['title']}\nSummary: {experience['summaryPoints']}\nMain Tech Stack: {experience['techStack']}\nDuration: {experience['dateRange']}"
                for experience in experience_list
            ]
        )

    def _extract_projects(self):
        project_list = self.data.get("data", {}).get("allProjects", [])

        return project_list

    @staticmethod
    def _format_projects(project_list: List[dict]) -> str:
        """Format the projects list into a desired structure."""

        # Format the output as a string
        return "\n\n".join(
            [
                f"Name: {project['title']}\nDescription: {project['description']}\nTechnologies used: {project['techUsed']}\nLink: {project['link'] if project['link'] else 'Not available publicly'}"
                for project in project_list
            ]
        )

    def _extract_education(self):
        education_list = self.data.get("data", {}).get("allTimelines", [])
        education_list = [
            edu for edu in education_list if edu.get("timelineType") == "education"
        ]
        return education_list

    @staticmethod
    def _format_education(education_list: List[dict]) -> str:
        """Format the experience list into a desired structure."""

        # Format the output as a string
        return "\n\n".join(
            [
                f"University/School: {education['name']}\nTitle: {education['title']}\nSummary: {education['summaryPoints'] if education['summaryPoints'] else 'NA'}\nDuration: {education['dateRange']}"
                for education in education_list
            ]
        )

    def _extract_certifications(self):
        certification_list = self.data.get("data", {}).get("allCertifications", [])

        return certification_list

    @staticmethod
    def _format_certifications(certification_list: List[dict]) -> str:
        """Format the experience list into a desired structure."""

        # Format the output as a string
        return "\n\n".join(
            [
                f"Title: {certification['title']}\nIssuer: {certification['issuer']}\nIssue date: {certification['issuedDate']}\nLink: {certification['link']}"
                for certification in certification_list
            ]
        )

    def _extract_contact_details(self):
        contact_details = self.data.get("data", {}).get("contactMe", {})

        return contact_details

    @staticmethod
    def _format_contact_details(contact_details: dict) -> str:
        """Format the experience list into a desired structure."""

        # Format the output as a string
        return f"Email: {contact_details['email']}\nLinkedin: {contact_details['email']}\nPhone: {contact_details['phoneNumber']}"

    def _extract_name(self):
        return self.data.get("data", {}).get("contactMe", {}).get("name")

    def _extract_summary(self):
        return self.data.get("data", {}).get("profilebanner", {}).get("profileSummary")

    def _extract_languages(self):
        # TODO: Add languages from DatoCMS
        return "English, Hindi, Marathi"
