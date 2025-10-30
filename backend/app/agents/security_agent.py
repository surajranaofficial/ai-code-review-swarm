"""Security-focused code review agent"""

from typing import List
from .base_agent import BaseAgent
from app.models import AgentType


class SecurityAgent(BaseAgent):
    """Agent specialized in security vulnerabilities"""
    
    def __init__(self):
        super().__init__(AgentType.SECURITY)
    
    def get_system_prompt(self) -> str:
        return """You are a security expert reviewing code for vulnerabilities.
Your mission is to identify security issues like:
- SQL injection vulnerabilities
- XSS (Cross-Site Scripting) risks
- Authentication/authorization flaws
- Insecure data handling
- Hardcoded secrets or credentials
- Unsafe deserialization
- Path traversal vulnerabilities
- CSRF vulnerabilities
- Insecure cryptography usage
- Information disclosure

Be thorough but practical. Focus on real security risks, not theoretical ones.
Provide clear explanations and actionable fixes."""
    
    def get_focus_areas(self) -> List[str]:
        return [
            "SQL Injection and NoSQL Injection",
            "Cross-Site Scripting (XSS)",
            "Authentication & Authorization",
            "Sensitive Data Exposure",
            "Security Misconfiguration",
            "Insecure Dependencies",
            "Injection Flaws",
            "Broken Access Control",
            "Cryptographic Issues",
            "Input Validation"
        ]
