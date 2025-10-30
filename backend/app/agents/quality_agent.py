"""Code quality and best practices agent"""

from typing import List
from .base_agent import BaseAgent
from app.models import AgentType


class QualityAgent(BaseAgent):
    """Agent specialized in code quality and maintainability"""
    
    def __init__(self):
        super().__init__(AgentType.QUALITY)
    
    def get_system_prompt(self) -> str:
        return """You are a code quality expert reviewing code for maintainability.
Your mission is to identify quality issues like:
- Code duplication (DRY violations)
- Complex functions (high cyclomatic complexity)
- Poor naming conventions
- Missing error handling
- Lack of documentation
- Inconsistent code style
- Magic numbers and hardcoded values
- God classes/functions
- Tight coupling
- Poor separation of concerns

Focus on issues that affect long-term maintainability and team productivity.
Suggest refactoring approaches that improve code clarity."""
    
    def get_focus_areas(self) -> List[str]:
        return [
            "Code Duplication (DRY)",
            "Function Complexity",
            "Naming Conventions",
            "Error Handling",
            "Documentation",
            "Code Style Consistency",
            "Magic Numbers",
            "Single Responsibility",
            "Code Readability",
            "Design Patterns Usage"
        ]
