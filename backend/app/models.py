"""Pydantic models for API requests and responses"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AgentType(str, Enum):
    """Types of review agents"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    QUALITY = "quality"


class AgentStatus(str, Enum):
    """Agent execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CodeSubmission(BaseModel):
    """Code submission for review"""
    code: str = Field(..., description="Code to review")
    language: str = Field(default="python", description="Programming language")
    filename: Optional[str] = Field(None, description="Original filename")
    repository_url: Optional[str] = Field(None, description="GitHub repo URL")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ReviewIssue(BaseModel):
    """Single issue found by an agent"""
    severity: str = Field(..., description="critical, high, medium, low")
    title: str
    description: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None
    category: str = Field(..., description="Issue category")


class AgentResult(BaseModel):
    """Result from a single agent"""
    agent_type: AgentType
    status: AgentStatus
    issues: List[ReviewIssue] = Field(default_factory=list)
    summary: str
    execution_time: float = Field(..., description="Time in seconds")
    fork_id: Optional[str] = Field(None, description="DB fork ID used")
    error: Optional[str] = None


class ReviewRequest(BaseModel):
    """Request to start a code review"""
    submission: CodeSubmission
    agents: List[AgentType] = Field(
        default=[AgentType.SECURITY, AgentType.PERFORMANCE, AgentType.QUALITY],
        description="Agents to run"
    )
    use_hybrid_search: bool = Field(
        default=True, 
        description="Use BM25 + vector search for similar patterns"
    )


class ReviewResponse(BaseModel):
    """Complete review response"""
    review_id: str
    status: str
    submission: CodeSubmission
    results: List[AgentResult]
    total_issues: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_time: Optional[float] = None


class SearchResult(BaseModel):
    """Hybrid search result"""
    code_snippet: str
    similarity_score: float
    source: str = Field(..., description="BM25 or vector")
    metadata: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """API health check response"""
    status: str
    tiger_connected: bool
    agents_available: List[str]
    version: str
