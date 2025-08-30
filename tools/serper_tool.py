"""
Serper Tool for searching social profiles
"""
from crewai_tools import SerperDevTool
from crewai.tools.base_tool import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional
import re
import json


class ProfileSearchInput(BaseModel):
    """Input for profile search"""
    person_name: str = Field(description="The person's name to search for")
    email: Optional[str] = Field(None, description="Optional email to refine search")


class ProfileSearchTool(BaseTool):
    """Tool for searching GitHub and LinkedIn profiles using Serper"""
    
    name: str = "Search Social Profiles"
    description: str = (
        "Search for a person's GitHub and LinkedIn profiles. "
        "Provide the person's name to find their professional social media presence."
    )
    args_schema: Type[BaseModel] = ProfileSearchInput
    
    def _extract_url(self, search_results, domain: str) -> Optional[str]:
        """Extract the first matching URL from search results"""
        try:
            # Handle dict response from Serper API
            if isinstance(search_results, dict):
                # Check organic results
                organic_results = search_results.get('organic', [])
                for result in organic_results:
                    link = result.get('link', '')
                    if domain in link:
                        return link
            
            # Fallback to string parsing if needed
            elif isinstance(search_results, str):
                # Look for URLs in the text
                url_pattern = rf'https?://(?:www\.)?{re.escape(domain)}[^\s"\'>]*'
                matches = re.findall(url_pattern, search_results)
                if matches:
                    # Return the first clean URL
                    url = matches[0].rstrip('.,;:)')
                    return url
            return None
        except Exception as e:
            print(f"Error extracting URL: {e}")
            return None
    
    def _run(self, person_name: str, email: Optional[str] = None) -> str:
        """Execute the profile search"""
        try:
            # Initialize SerperDevTool
            serper = SerperDevTool()
            
            results = {
                "person_searched": person_name,
                "profiles_found": {}
            }
            
            # Search for GitHub profile
            github_query = f'site:github.com "{person_name}"'
            if email:
                # Add email domain to refine search if available
                email_domain = email.split('@')[1] if '@' in email else ""
                if email_domain:
                    github_query += f' OR {email_domain}'
            
            try:
                github_results = serper.run(query=github_query)
                github_url = self._extract_url(github_results, "github.com")
                if github_url:
                    results["profiles_found"]["github"] = github_url
            except Exception as e:
                print(f"GitHub search error: {e}")
                results["profiles_found"]["github"] = None
            
            # Search for LinkedIn profile
            linkedin_query = f'site:linkedin.com/in "{person_name}"'
            try:
                linkedin_results = serper.run(query=linkedin_query)
                linkedin_url = self._extract_url(linkedin_results, "linkedin.com/in")
                if linkedin_url:
                    results["profiles_found"]["linkedin"] = linkedin_url
            except Exception as e:
                print(f"LinkedIn search error: {e}")
                results["profiles_found"]["linkedin"] = None
            
            # Format the response
            response_parts = [f"Profile search results for {person_name}:"]
            
            if results["profiles_found"].get("github"):
                response_parts.append(f"GitHub: {results['profiles_found']['github']}")
            else:
                response_parts.append("GitHub: Not found")
            
            if results["profiles_found"].get("linkedin"):
                response_parts.append(f"LinkedIn: {results['profiles_found']['linkedin']}")
            else:
                response_parts.append("LinkedIn: Not found")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"Error searching for profiles: {str(e)}"