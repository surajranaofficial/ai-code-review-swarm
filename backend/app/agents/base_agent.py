"""Base agent class for code review"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import time
import logging
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import google.generativeai as genai
from app.config import settings
from app.models import ReviewIssue, AgentResult, AgentStatus, AgentType

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all review agents"""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.fork_id: Optional[str] = None
        
        # Initialize AI clients
        self.openai_client = None
        self.anthropic_client = None
        self.gemini_model = None
        
        if settings.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        if settings.anthropic_api_key:
            self.anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return agent-specific system prompt"""
        pass
    
    @abstractmethod
    def get_focus_areas(self) -> List[str]:
        """Return areas this agent focuses on"""
        pass
    
    async def analyze_code(
        self, 
        code: str, 
        language: str,
        similar_patterns: Optional[List[Dict]] = None
    ) -> AgentResult:
        """
        Main analysis method
        Returns AgentResult with issues found
        """
        start_time = time.time()
        
        try:
            logger.info(f"🤖 {self.agent_type.value} agent starting analysis...")
            
            # Build prompt with context
            prompt = self._build_prompt(code, language, similar_patterns)
            
            # Call AI model
            analysis = await self._call_ai_model(prompt)
            
            # Parse issues
            issues = self._parse_issues(analysis)
            
            # Generate summary
            summary = self._generate_summary(issues)
            
            execution_time = time.time() - start_time
            
            logger.info(
                f"✅ {self.agent_type.value} completed in {execution_time:.2f}s "
                f"- Found {len(issues)} issues"
            )
            
            return AgentResult(
                agent_type=self.agent_type,
                status=AgentStatus.COMPLETED,
                issues=issues,
                summary=summary,
                execution_time=execution_time,
                fork_id=self.fork_id
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ {self.agent_type.value} failed: {e}")
            
            return AgentResult(
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                issues=[],
                summary=f"Analysis failed: {str(e)}",
                execution_time=execution_time,
                error=str(e)
            )
    
    def _build_prompt(
        self, 
        code: str, 
        language: str,
        similar_patterns: Optional[List[Dict]] = None
    ) -> str:
        """Build comprehensive prompt for AI"""
        
        prompt = f"""{self.get_system_prompt()}

**Code to Review:**
Language: {language}
```{language}
{code}
```

**Focus Areas:**
{chr(10).join(f"- {area}" for area in self.get_focus_areas())}
"""
        
        if similar_patterns:
            prompt += "\n**Similar Code Patterns Found (via Hybrid Search):**\n"
            for i, pattern in enumerate(similar_patterns[:3], 1):
                prompt += f"\n{i}. {pattern.get('pattern_name', 'Unknown')}\n"
                prompt += f"   Similarity: {pattern.get('similarity', 0):.2%}\n"
                if pattern.get('description'):
                    prompt += f"   Context: {pattern['description']}\n"
        
        prompt += """

**Output Format (JSON):**
{
  "issues": [
    {
      "severity": "critical|high|medium|low",
      "title": "Brief title",
      "description": "Detailed description",
      "line_number": 10,
      "category": "Category name",
      "suggestion": "How to fix"
    }
  ]
}

Please analyze the code and return issues in the JSON format above.
"""
        
        return prompt
    
    async def _call_ai_model(self, prompt: str) -> str:
        """Call AI model (Gemini, OpenAI, or Anthropic)"""
        
        # Try Gemini first (you have the API key!)
        if self.gemini_model:
            try:
                response = await self.gemini_model.generate_content_async(prompt)
                return response.text
                
            except Exception as e:
                logger.warning(f"Gemini call failed: {e}")
        
        # Try OpenAI second
        if self.openai_client:
            try:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",  # Fast and cost-effective
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )
                return response.choices[0].message.content
                
            except Exception as e:
                logger.warning(f"OpenAI call failed: {e}")
        
        # Fallback to Anthropic
        if self.anthropic_client:
            try:
                response = await self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",  # Fast and affordable
                    max_tokens=2000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text
                
            except Exception as e:
                logger.error(f"Anthropic call failed: {e}")
                raise
        
        raise Exception("No AI provider available")
    
    def _parse_issues(self, analysis: str) -> List[ReviewIssue]:
        """Parse AI response into ReviewIssue objects"""
        import json
        import re
        
        issues = []
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', analysis, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                for issue_data in data.get('issues', []):
                    issues.append(ReviewIssue(**issue_data))
            
        except Exception as e:
            logger.error(f"Failed to parse issues: {e}")
            # Create a fallback issue
            issues.append(ReviewIssue(
                severity="low",
                title="Analysis completed with parsing errors",
                description=analysis[:500],
                category="general"
            ))
        
        return issues
    
    def _generate_summary(self, issues: List[ReviewIssue]) -> str:
        """Generate summary from issues"""
        if not issues:
            return f"✅ No {self.agent_type.value} issues found!"
        
        severity_counts = {}
        for issue in issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        summary = f"Found {len(issues)} issue(s): "
        summary += ", ".join(f"{count} {sev}" for sev, count in severity_counts.items())
        
        return summary
