"""Database operations for code review system"""

from typing import List, Dict, Any, Optional
from db.connection import db_connection
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class CodeReviewDB:
    """Database operations for code review"""
    
    @staticmethod
    async def setup_schema():
        """Create tables and enable extensions"""
        try:
            # Enable extensions
            await db_connection.execute_write(
                "CREATE EXTENSION IF NOT EXISTS vector;"
            )
            
            logger.info("✅ Extensions enabled")
            
            # Create code_submissions table
            await db_connection.execute_write("""
                CREATE TABLE IF NOT EXISTS code_submissions (
                    id SERIAL PRIMARY KEY,
                    code TEXT NOT NULL,
                    language VARCHAR(50) DEFAULT 'python',
                    filename VARCHAR(255),
                    repository_url TEXT,
                    metadata JSONB,
                    embedding vector(1536),
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create reviews table
            await db_connection.execute_write("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id SERIAL PRIMARY KEY,
                    submission_id INTEGER REFERENCES code_submissions(id),
                    review_id VARCHAR(100) UNIQUE NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    total_issues INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP
                );
            """)
            
            # Create agent_results table
            await db_connection.execute_write("""
                CREATE TABLE IF NOT EXISTS agent_results (
                    id SERIAL PRIMARY KEY,
                    review_id VARCHAR(100) REFERENCES reviews(review_id),
                    agent_type VARCHAR(50) NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    issues JSONB,
                    summary TEXT,
                    execution_time FLOAT,
                    fork_id VARCHAR(100),
                    error TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create code_patterns table for hybrid search
            await db_connection.execute_write("""
                CREATE TABLE IF NOT EXISTS code_patterns (
                    id SERIAL PRIMARY KEY,
                    pattern_name VARCHAR(255),
                    code_snippet TEXT NOT NULL,
                    description TEXT,
                    category VARCHAR(100),
                    language VARCHAR(50),
                    embedding vector(1536),
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create indexes
            await db_connection.execute_write("""
                CREATE INDEX IF NOT EXISTS idx_submissions_created 
                ON code_submissions(created_at DESC);
            """)
            
            await db_connection.execute_write("""
                CREATE INDEX IF NOT EXISTS idx_reviews_status 
                ON reviews(status);
            """)
            
            logger.info("✅ Database schema created successfully")
            
        except Exception as e:
            logger.error(f"❌ Schema setup failed: {e}")
            raise
    
    @staticmethod
    async def save_submission(
        code: str, 
        language: str, 
        filename: Optional[str] = None,
        metadata: Optional[Dict] = None,
        embedding: Optional[List[float]] = None
    ) -> int:
        """Save code submission"""
        query = """
            INSERT INTO code_submissions 
            (code, language, filename, metadata, embedding)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """
        
        result = await db_connection.execute_one(
            query,
            code,
            language,
            filename,
            json.dumps(metadata) if metadata else None,
            embedding
        )
        
        return result['id']
    
    @staticmethod
    async def create_review(submission_id: int, review_id: str) -> bool:
        """Create a new review record"""
        query = """
            INSERT INTO reviews (submission_id, review_id, status)
            VALUES ($1, $2, 'running')
        """
        
        await db_connection.execute_write(query, submission_id, review_id)
        return True
    
    @staticmethod
    async def save_agent_result(
        review_id: str,
        agent_type: str,
        status: str,
        issues: List[Dict],
        summary: str,
        execution_time: float,
        fork_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Save agent result"""
        query = """
            INSERT INTO agent_results 
            (review_id, agent_type, status, issues, summary, execution_time, fork_id, error)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        await db_connection.execute_write(
            query,
            review_id,
            agent_type,
            status,
            json.dumps(issues),
            summary,
            execution_time,
            fork_id,
            error
        )
    
    @staticmethod
    async def update_review_status(review_id: str, status: str, total_issues: int):
        """Update review completion status"""
        query = """
            UPDATE reviews 
            SET status = $1, total_issues = $2, completed_at = NOW()
            WHERE review_id = $3
        """
        
        await db_connection.execute_write(query, status, total_issues, review_id)
    
    @staticmethod
    async def get_review(review_id: str) -> Optional[Dict]:
        """Get review with all agent results"""
        query = """
            SELECT 
                r.*,
                cs.code, cs.language, cs.filename,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'agent_type', ar.agent_type,
                            'status', ar.status,
                            'issues', ar.issues,
                            'summary', ar.summary,
                            'execution_time', ar.execution_time,
                            'fork_id', ar.fork_id
                        )
                    ) FILTER (WHERE ar.id IS NOT NULL),
                    '[]'
                ) as agent_results
            FROM reviews r
            JOIN code_submissions cs ON r.submission_id = cs.id
            LEFT JOIN agent_results ar ON r.review_id = ar.review_id
            WHERE r.review_id = $1
            GROUP BY r.id, cs.id
        """
        
        result = await db_connection.execute_one(query, review_id)
        return dict(result) if result else None
    
    @staticmethod
    async def hybrid_search(
        query_text: str, 
        embedding: Optional[List[float]] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Hybrid search using BM25 (via pg_textsearch when available) 
        and vector similarity
        """
        
        # For now, use vector search if embedding provided
        if embedding:
            query = """
                SELECT 
                    code_snippet,
                    pattern_name,
                    description,
                    1 - (embedding <=> $1::vector) as similarity
                FROM code_patterns
                ORDER BY embedding <=> $1::vector
                LIMIT $2
            """
            
            results = await db_connection.execute_query(query, embedding, limit)
            return [dict(r) for r in results]
        
        # Fallback to text search
        query = """
            SELECT 
                code_snippet,
                pattern_name,
                description,
                0.5 as similarity
            FROM code_patterns
            WHERE code_snippet ILIKE $1
            LIMIT $2
        """
        
        results = await db_connection.execute_query(
            query, 
            f"%{query_text}%", 
            limit
        )
        return [dict(r) for r in results]


# Global instance
code_review_db = CodeReviewDB()
