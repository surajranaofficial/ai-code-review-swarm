"""Performance-focused code review agent"""

from typing import List
from .base_agent import BaseAgent
from app.models import AgentType


class PerformanceAgent(BaseAgent):
    """Agent specialized in performance optimization"""
    
    def __init__(self):
        super().__init__(AgentType.PERFORMANCE)
    
    def get_system_prompt(self) -> str:
        return """You are a performance optimization expert reviewing code.
Your mission is to identify performance issues like:
- Inefficient algorithms (O(n²) where O(n) possible)
- N+1 query problems
- Missing database indexes
- Memory leaks
- Unnecessary loops or iterations
- Inefficient data structures
- Missing caching opportunities
- Blocking I/O operations
- Resource-intensive operations in loops
- Inefficient string operations

Be practical and focus on issues that will have measurable impact.
Suggest specific optimizations with expected improvements."""
    
    def get_focus_areas(self) -> List[str]:
        return [
            "Algorithm Efficiency",
            "Database Query Optimization",
            "N+1 Query Detection",
            "Memory Management",
            "Caching Opportunities",
            "Async/Await Usage",
            "Loop Optimization",
            "Data Structure Selection",
            "I/O Operations",
            "Resource Usage"
        ]
