"""FastAPI main application - AI Code Review Swarm"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import uuid
import logging
from datetime import datetime

from app.config import settings
from app.models import (
    ReviewRequest, ReviewResponse, HealthResponse,
    AgentResult, CodeSubmission, AgentStatus
)
from app.agents import SecurityAgent, PerformanceAgent, QualityAgent
from db.connection import db_connection
from db.operations import code_review_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting AI Code Review Swarm...")
    
    try:
        # Connect to Tiger Cloud
        await db_connection.connect()
        
        # Setup database schema
        await code_review_db.setup_schema()
        
        logger.info("✅ Application started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down...")
    await db_connection.disconnect()


# Initialize FastAPI app
app = FastAPI(
    title="AI Code Review Swarm",
    description="Multi-agent code review system powered by Tiger Cloud Agentic Postgres",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "AI Code Review Swarm API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    tiger_connected = await db_connection.test_connection()
    
    return HealthResponse(
        status="healthy" if tiger_connected else "degraded",
        tiger_connected=tiger_connected,
        agents_available=["security", "performance", "quality"],
        version="0.1.0"
    )


async def run_agent_analysis(
    agent,
    code: str,
    language: str,
    review_id: str,
    use_hybrid_search: bool = True
):
    """Run single agent analysis"""
    
    # Get similar patterns using hybrid search
    similar_patterns = []
    if use_hybrid_search:
        try:
            similar_patterns = await code_review_db.hybrid_search(
                query_text=code[:500],  # First 500 chars for search
                limit=3
            )
        except Exception as e:
            logger.warning(f"Hybrid search failed: {e}")
    
    # Run agent analysis
    result = await agent.analyze_code(code, language, similar_patterns)
    
    # Save result to database
    await code_review_db.save_agent_result(
        review_id=review_id,
        agent_type=result.agent_type.value,
        status=result.status.value,
        issues=[issue.model_dump() for issue in result.issues],
        summary=result.summary,
        execution_time=result.execution_time,
        fork_id=result.fork_id,
        error=result.error
    )
    
    return result


async def run_parallel_review(
    review_id: str,
    submission: CodeSubmission,
    agents_to_run: list
):
    """Run all agents in parallel"""
    
    logger.info(f"🔄 Starting parallel review {review_id}")
    
    # Create agent instances
    agent_map = {
        "security": SecurityAgent(),
        "performance": PerformanceAgent(),
        "quality": QualityAgent()
    }
    
    # Run agents in parallel
    tasks = []
    for agent_type in agents_to_run:
        if agent_type.value in agent_map:
            agent = agent_map[agent_type.value]
            task = run_agent_analysis(
                agent,
                submission.code,
                submission.language,
                review_id,
                use_hybrid_search=True
            )
            tasks.append(task)
    
    # Wait for all agents to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Count total issues
    total_issues = sum(
        len(r.issues) for r in results 
        if isinstance(r, AgentResult) and r.status == AgentStatus.COMPLETED
    )
    
    # Update review status
    await code_review_db.update_review_status(
        review_id=review_id,
        status="completed",
        total_issues=total_issues
    )
    
    logger.info(f"✅ Review {review_id} completed - {total_issues} issues found")


@app.post("/review", response_model=ReviewResponse, tags=["Review"])
async def create_review(
    request: ReviewRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit code for review by AI agents
    
    This will:
    1. Save the code submission
    2. Create database forks for each agent (if enabled)
    3. Run agents in parallel
    4. Use hybrid search (BM25 + vector) to find similar patterns
    5. Return aggregated results
    """
    
    try:
        # Generate review ID
        review_id = f"review_{uuid.uuid4().hex[:12]}"
        
        # Save submission to database
        submission_id = await code_review_db.save_submission(
            code=request.submission.code,
            language=request.submission.language,
            filename=request.submission.filename,
            metadata=request.submission.metadata
        )
        
        # Create review record
        await code_review_db.create_review(submission_id, review_id)
        
        # Start parallel review in background
        background_tasks.add_task(
            run_parallel_review,
            review_id,
            request.submission,
            request.agents
        )
        
        # Return immediate response
        return ReviewResponse(
            review_id=review_id,
            status="running",
            submission=request.submission,
            results=[],
            total_issues=0,
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to create review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/review/{review_id}", response_model=ReviewResponse, tags=["Review"])
async def get_review(review_id: str):
    """
    Get review results by ID
    """
    
    try:
        review_data = await code_review_db.get_review(review_id)
        
        if not review_data:
            raise HTTPException(status_code=404, detail="Review not found")
        
        # Parse agent results
        agent_results = []
        for result_data in review_data['agent_results']:
            agent_results.append(AgentResult(**result_data))
        
        # Build submission
        submission = CodeSubmission(
            code=review_data['code'],
            language=review_data['language'],
            filename=review_data['filename']
        )
        
        # Calculate total time
        total_time = None
        if review_data['completed_at']:
            total_time = (
                review_data['completed_at'] - review_data['created_at']
            ).total_seconds()
        
        return ReviewResponse(
            review_id=review_id,
            status=review_data['status'],
            submission=submission,
            results=agent_results,
            total_issues=review_data['total_issues'],
            created_at=review_data['created_at'],
            completed_at=review_data['completed_at'],
            total_time=total_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", tags=["Stats"])
async def get_stats():
    """Get system statistics"""
    
    try:
        stats_query = """
            SELECT 
                COUNT(DISTINCT r.review_id) as total_reviews,
                COUNT(DISTINCT cs.id) as total_submissions,
                SUM(r.total_issues) as total_issues_found,
                AVG(ar.execution_time) as avg_execution_time
            FROM reviews r
            JOIN code_submissions cs ON r.submission_id = cs.id
            LEFT JOIN agent_results ar ON r.review_id = ar.review_id
        """
        
        stats = await db_connection.execute_one(stats_query)
        
        return {
            "total_reviews": stats['total_reviews'] or 0,
            "total_submissions": stats['total_submissions'] or 0,
            "total_issues_found": stats['total_issues_found'] or 0,
            "avg_execution_time": float(stats['avg_execution_time'] or 0),
            "agents": ["security", "performance", "quality"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {
            "error": str(e),
            "total_reviews": 0,
            "total_submissions": 0
        }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
