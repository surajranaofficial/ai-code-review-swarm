"""Tiger Cloud database connection management"""

import asyncpg
import psycopg
from psycopg_pool import ConnectionPool
from typing import Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class TigerConnection:
    """Manages connections to Tiger Cloud PostgreSQL"""
    
    def __init__(self):
        self.pool: Optional[ConnectionPool] = None
        self._async_pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Initialize connection pool"""
        try:
            # Async pool for high-performance operations
            self._async_pool = await asyncpg.create_pool(
                host=settings.tiger_db_host,
                port=settings.tiger_db_port,
                database=settings.tiger_db_name,
                user=settings.tiger_db_user,
                password=settings.tiger_db_password,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            
            logger.info("✅ Connected to Tiger Cloud successfully")
            
            # Test connection and check extensions
            async with self._async_pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                logger.info(f"PostgreSQL version: {version}")
                
                # Check for required extensions
                extensions = await conn.fetch(
                    "SELECT extname FROM pg_extension WHERE extname IN ('vector', 'timescaledb')"
                )
                logger.info(f"Available extensions: {[e['extname'] for e in extensions]}")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Tiger Cloud: {e}")
            raise
    
    async def disconnect(self):
        """Close all connections"""
        if self._async_pool:
            await self._async_pool.close()
            logger.info("Disconnected from Tiger Cloud")
    
    async def execute_query(self, query: str, *args):
        """Execute a query and return results"""
        async with self._async_pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_one(self, query: str, *args):
        """Execute query and return single result"""
        async with self._async_pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def execute_write(self, query: str, *args):
        """Execute write operation"""
        async with self._async_pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def test_connection(self) -> bool:
        """Test if connection is alive"""
        try:
            async with self._async_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


# Global connection instance
db_connection = TigerConnection()
