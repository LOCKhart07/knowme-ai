import os
from typing import Optional
import requests
from langchain_community.document_loaders.pdf import OnlinePDFLoader
from dotenv import load_dotenv
from typing import List, TypedDict, AnyStr
from collections import defaultdict
import traceback

load_dotenv()


class InfoService:
    def __init__(self):
        self.datocms_api_token = os.getenv("DATOCMS_API_TOKEN")
        self.dato_cms_url = "https://graphql.datocms.com"
        self.datocms_headers = {
            "Authorization": f"Bearer {self.datocms_api_token}",
            "Content-Type": "application/json",
        }

    async def fetch_resume_text(self) -> Optional[str]:
        """Fetch resume text"""
        try:
            # GraphQL query to fetch resume data
            query = """
            query {
                resumeUncompiled {
                    text
                }
            }
            """

            # Make GraphQL request
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

            # Extract resume link from response
            # print(data)
            resume_text = data.get("data", {}).get("resumeUncompiled", {}).get("text")

            if not resume_text:

                print("No resume URL text in response")
                return None

            return resume_text

        except Exception as e:
            print(f"Error fetching resume from DatoCMS: {str(e)}")
            return None

    async def fetch_skills(self):
        try:
            # GraphQL query to fetch resume data
            query = """
            query {
                allSkills(first: 100, orderBy: order_ASC) {
                    name
                    category
                    description
                }
            }
            """

            # Make GraphQL request
            response = requests.post(
                self.dato_cms_url,
                json={"query": query},
                headers=self.datocms_headers,
            )
            response.raise_for_status()

            data = response.json()
            # print(data)

            # Check for errors in GraphQL response
            if "errors" in data:
                print(f"GraphQL errors: {data['errors']}")
                return None

            skills_list = data.get("data", {}).get("allSkills", {})

            if not skills_list:

                print("No skills list in response")
                return None

            return self._format_skills(skills_list)

        except Exception as e:
            print(f"Error fetching skills from DatoCMS: {str(e)}")
            return None

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

    async def fetch_experience(self):
        try:
            query = """
                {
                    allTimelines(filter: { timelineType: { eq: "work" } }) {
                        title
                        timelineType
                        summaryPoints
                        name
                        dateRange
                        techStack
                    }
                }
            """

            # Make GraphQL request
            response = requests.post(
                self.dato_cms_url,
                json={"query": query},
                headers=self.datocms_headers,
            )
            response.raise_for_status()

            data = response.json()
            # print(data)

            # Check for errors in GraphQL response
            if "errors" in data:
                print(f"GraphQL errors: {data['errors']}")
                return None

            experience_list = data.get("data", {}).get("allTimelines", {})

            if not experience_list:

                print("No experience list in response")
                return None

            return self._format_experience(experience_list)

        except Exception as e:
            print(f"Error fetching experience from DatoCMS: {str(e)}")
            return None

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

    async def fetch_projects(self):
        try:
            query = """
                {
                    allProjects {
                        description
                        link
                        techUsed
                        title
                    }
                }
            """

            # Make GraphQL request
            response = requests.post(
                self.dato_cms_url,
                json={"query": query},
                headers=self.datocms_headers,
            )
            response.raise_for_status()

            data = response.json()
            # print(data)

            # Check for errors in GraphQL response
            if "errors" in data:
                print(f"GraphQL errors: {data['errors']}")
                return None

            project_list = data.get("data", {}).get("allProjects", [])

            if not project_list:

                print("No project list in response")
                return None
            # print(project_list)
            return self._format_projects(project_list)
            return project_list

        except Exception as e:
            print(f"Error fetching projects from DatoCMS: {str(e)}")
            return None

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

    async def fetch_education(self):
        try:
            query = """
                {
                    allTimelines(filter: { timelineType: { eq: "education" } }) {
                        title
                        timelineType
                        summaryPoints
                        name
                        dateRange
                        techStack
                    }
                }
            """

            # Make GraphQL request
            response = requests.post(
                self.dato_cms_url,
                json={"query": query},
                headers=self.datocms_headers,
            )
            response.raise_for_status()

            data = response.json()
            # print(data)

            # Check for errors in GraphQL response
            if "errors" in data:
                print(f"GraphQL errors: {data['errors']}")
                return None

            education_list = data.get("data", {}).get("allTimelines", {})

            if not education_list:
                print("No education list in response")
                return None

            return self._format_education(education_list)

        except Exception as e:
            print(f"Error fetching education from DatoCMS: {str(e)}")
            return None

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

    async def fetch_certifications(self):
        try:
            query = """
                {
                allCertifications {
                    issuedDate
                    issuer
                    link
                    title
                }
                }
            """

            # Make GraphQL request
            response = requests.post(
                self.dato_cms_url,
                json={"query": query},
                headers=self.datocms_headers,
            )
            response.raise_for_status()

            data = response.json()
            # print(data)

            # Check for errors in GraphQL response
            if "errors" in data:
                print(f"GraphQL errors: {data['errors']}")
                return None

            certification_list = data.get("data", {}).get("allCertifications", {})

            if not certification_list:
                print("No certification list in response")
                return None
            # print(certification_list)
            return self._format_certifications(certification_list)

        except Exception as e:
            print(f"Error fetching certifications from DatoCMS: {str(e)}")
            return None

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

    async def fetch_contact_details(self):
        try:
            query = """
                {
                    contactMe {
                        email
                        linkedinLink
                        phoneNumber
                    }
                }
            """

            # Make GraphQL request
            response = requests.post(
                self.dato_cms_url,
                json={"query": query},
                headers=self.datocms_headers,
            )
            response.raise_for_status()

            data = response.json()
            # print(data)

            # Check for errors in GraphQL response
            if "errors" in data:
                print(f"GraphQL errors: {data['errors']}")
                return None
            # print(data)
            contact_details = data.get("data", {}).get("contactMe", {})

            if not contact_details:
                print("No contact details in response")
                return None
            # print(contact_details)
            return self._format_contact_details(contact_details)

        except Exception as e:
            print(f"Error fetching contact details from DatoCMS: {str(e)}")
            return None

    @staticmethod
    def _format_contact_details(contact_details: dict) -> str:
        """Format the experience list into a desired structure."""

        # Format the output as a string
        return f"Email: {contact_details['email']}\nLinkedin: {contact_details['email']}\nPhone: {contact_details['phoneNumber']}"

    async def fetch_name(self):
        try:
            query = """
                {
                    contactMe {
                        name
                    }
                }
            """

            # Make GraphQL request
            response = requests.post(
                self.dato_cms_url,
                json={"query": query},
                headers=self.datocms_headers,
            )
            response.raise_for_status()

            data = response.json()
            # print(data)

            # Check for errors in GraphQL response
            if "errors" in data:
                print(f"GraphQL errors: {data['errors']}")
                return None
            # print(data)
            full_name = data.get("data", {}).get("contactMe", {}).get("name")

            if not full_name:
                print("No full name in response")
                return None
            # print(contact_details)
            return full_name

        except Exception as e:
            print(f"Error fetching contact details from DatoCMS: {str(e)}")
            return None

    async def fetch_summary(self):
        try:
            query = """
                {
                    profilebanner {
                        profileSummary
                    }
                }
            """

            # Make GraphQL request
            response = requests.post(
                self.dato_cms_url,
                json={"query": query},
                headers=self.datocms_headers,
            )
            response.raise_for_status()

            data = response.json()
            # print(data)

            # Check for errors in GraphQL response
            if "errors" in data:
                print(f"GraphQL errors: {data['errors']}")
                return None
            # print(data)
            full_name = (
                data.get("data", {}).get("profilebanner", {}).get("profileSummary")
            )

            if not full_name:
                print("No full summary in response")
                return None
            # print(contact_details)
            return full_name

        except Exception as e:
            print(f"Error fetching summary from DatoCMS: {str(e)}")
            return None

    async def fetch_languages(self):
        # TODO:
        return "English, Hindi, Marathi"
