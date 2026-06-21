"""
PgVector Configuration and Vector Store Manager
"""
from typing import List, Optional

from sqlalchemy import Column, Integer, String, Text, JSON, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Base class for models
Base = declarative_base()


class Embedding(Base):
    """Embedding model for PgVector"""
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, name="metadata")
    embedding = Column(Vector(settings.pgvector.PGVECTOR_DIMENSION))
    collection = Column(String, index=True, default="default")


class VectorStoreManager:
    """
    PgVector Store Manager
    Handles vector storage and retrieval operations
    """

    def __init__(self):
        self._engine = None
        self._async_engine = None
        self._session_factory = None
        self._async_session_factory = None

    def get_engine(self, async_mode: bool = True):
        """Get SQLAlchemy engine"""
        if async_mode:
            if self._async_engine is None:
                self._async_engine = create_async_engine(
                    settings.pgvector.connection_string,
                    pool_size=settings.database.DB_POOL_SIZE,
                    max_overflow=settings.database.DB_MAX_OVERFLOW,
                    pool_timeout=settings.database.DB_POOL_TIMEOUT,
                    echo=settings.app.DEBUG
                )
                logger.info("Async PgVector engine created")
            return self._async_engine
        else:
            if self._engine is None:
                self._engine = create_engine(
                    settings.database.DATABASE_URL_SYNC,
                    pool_size=settings.database.DB_POOL_SIZE,
                    max_overflow=settings.database.DB_MAX_OVERFLOW,
                    echo=settings.app.DEBUG
                )
                logger.info("Sync PgVector engine created")
            return self._engine

    def get_session_factory(self, async_mode: bool = True):
        """Get session factory"""
        if async_mode:
            if self._async_session_factory is None:
                engine = self.get_engine(async_mode=True)
                self._async_session_factory = sessionmaker(
                    engine,
                    class_=AsyncSession,
                    expire_on_commit=False
                )
            return self._async_session_factory
        else:
            if self._session_factory is None:
                engine = self.get_engine(async_mode=False)
                self._session_factory = sessionmaker(bind=engine)
            return self._session_factory

    async def get_session(self) -> AsyncSession:
        """Get async database session"""
        session_factory = self.get_session_factory(async_mode=True)
        return session_factory()

    async def init_db(self):
        """Initialize database tables"""
        from sqlalchemy import text
        engine = self.get_engine(async_mode=True)
        async with engine.begin() as conn:
            # Enable pgvector extension
            await conn.execute(
                text("CREATE EXTENSION IF NOT EXISTS vector")
            )
            # Enable pg_trgm extension for keyword search
            await conn.execute(
                text("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            )
            # Create tables
            await conn.run_sync(Base.metadata.create_all)
            # Create GIN index for trigram similarity search
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_embeddings_content_trgm
                ON embeddings USING gin (content gin_trgm_ops)
            """))
        logger.info("PgVector database initialized")

    async def add_embedding(
        self,
        content: str,
        embedding: List[float],
        metadata: Optional[dict] = None,
        collection: str = "default"
    ) -> int:
        """Add embedding to vector store"""
        async with AsyncSession(self.get_engine(async_mode=True)) as session:
            async with session.begin():
                db_embedding = Embedding(
                    content=content,
                    embedding=embedding,
                    metadata_json=metadata,
                    collection=collection
                )
                session.add(db_embedding)
                await session.flush()
                embedding_id = db_embedding.id
                logger.debug(f"Added embedding {embedding_id} to collection '{collection}'")
                return embedding_id

    async def search_similar(
        self,
        query_embedding: List[float],
        collection: str = "default",
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[dict]:
        """Search for similar embeddings"""
        from sqlalchemy import text

        async with AsyncSession(self.get_engine(async_mode=True)) as session:
            # Use cosine similarity search
            query = text("""
                SELECT
                    id,
                    content,
                    metadata,
                    1 - (embedding <=> :query_embedding) AS similarity
                FROM embeddings
                WHERE collection = :collection
                  AND 1 - (embedding <=> :query_embedding) >= :threshold
                ORDER BY embedding <=> :query_embedding
                LIMIT :top_k
            """)

            result = await session.execute(
                query,
                {
                    "query_embedding": str(query_embedding),
                    "collection": collection,
                    "threshold": similarity_threshold,
                    "top_k": top_k
                }
            )

            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "content": row[1],
                    "metadata": row[2],
                    "similarity": float(row[3])
                }
                for row in rows
            ]

    async def delete_embedding(self, embedding_id: int) -> bool:
        """Delete embedding by ID"""
        from sqlalchemy import text
        async with AsyncSession(self.get_engine(async_mode=True)) as session:
            async with session.begin():
                result = await session.execute(
                    text("DELETE FROM embeddings WHERE id = :id"),
                    {"id": embedding_id}
                )
                deleted = result.rowcount > 0
                if deleted:
                    logger.debug(f"Deleted embedding {embedding_id}")
                return deleted

    async def delete_collection(self, collection: str) -> int:
        """Delete all embeddings in a collection"""
        from sqlalchemy import text
        async with AsyncSession(self.get_engine(async_mode=True)) as session:
            async with session.begin():
                result = await session.execute(
                    text("DELETE FROM embeddings WHERE collection = :collection"),
                    {"collection": collection}
                )
                count = result.rowcount
                logger.info(f"Deleted {count} embeddings from collection '{collection}'")
                return count

    async def get_collection_stats(self, collection: str) -> dict:
        """Get statistics for a collection"""
        from sqlalchemy import text

        async with AsyncSession(self.get_engine(async_mode=True)) as session:
            query = text("""
                SELECT COUNT(*) as total_count
                FROM embeddings
                WHERE collection = :collection
            """)
            result = await session.execute(query, {"collection": collection})
            row = result.fetchone()
            return {
                "collection": collection,
                "count": row[0] if row else 0
            }

    async def close(self):
        """Close database connections"""
        if self._async_engine:
            await self._async_engine.dispose()
            logger.info("Async PgVector engine disposed")
        if self._engine:
            self._engine.dispose()
            logger.info("Sync PgVector engine disposed")

    async def keyword_search(
        self,
        query: str,
        user_id: int,
        top_k: int = 5
    ) -> List[dict]:
        """Keyword search using pg_trgm similarity"""
        from sqlalchemy import text

        async with AsyncSession(self.get_engine(async_mode=True)) as session:
            stmt = text("""
                SELECT
                    id,
                    content,
                    metadata,
                    similarity(content, :query) AS similarity
                FROM embeddings
                WHERE metadata->>'user_id' = :user_id
                  AND similarity(content, :query) > 0.05
                ORDER BY similarity DESC
                LIMIT :top_k
            """)

            result = await session.execute(
                stmt,
                {
                    "query": query,
                    "user_id": str(user_id),
                    "top_k": top_k
                }
            )

            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "content": row[1],
                    "metadata": row[2],
                    "similarity": float(row[3])
                }
                for row in rows
            ]

    async def hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        user_id: int,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[dict]:
        """Hybrid search combining vector similarity and keyword matching with RRF"""
        from sqlalchemy import text

        # Step 1: Vector search by user_id
        async with AsyncSession(self.get_engine(async_mode=True)) as session:
            vector_stmt = text("""
                SELECT
                    id, content, metadata,
                    1 - (embedding <=> :query_embedding) AS similarity
                FROM embeddings
                WHERE metadata->>'user_id' = :user_id
                  AND 1 - (embedding <=> :query_embedding) >= :threshold
                ORDER BY embedding <=> :query_embedding
                LIMIT :top_k
            """)
            vector_result = await session.execute(vector_stmt, {
                "query_embedding": str(query_embedding),
                "user_id": str(user_id),
                "threshold": similarity_threshold,
                "top_k": top_k * 2
            })
            vector_rows = vector_result.fetchall()

        # Step 2: Keyword search by user_id
        keyword_results = await self.keyword_search(query, user_id, top_k * 2)

        # Step 3: RRF fusion
        RRF_K = 60
        merged = {}

        for rank, row in enumerate(vector_rows):
            chunk_id = row[0]
            merged[chunk_id] = {
                "id": chunk_id,
                "content": row[1],
                "metadata": row[2],
                "vector_rank": rank,
                "keyword_rank": None,
                "rrf_score": 1.0 / (RRF_K + rank)
            }

        for rank, item in enumerate(keyword_results):
            chunk_id = item["id"]
            if chunk_id in merged:
                merged[chunk_id]["keyword_rank"] = rank
                merged[chunk_id]["rrf_score"] += 1.0 / (RRF_K + rank)
            else:
                merged[chunk_id] = {
                    "id": chunk_id,
                    "content": item["content"],
                    "metadata": item["metadata"],
                    "vector_rank": None,
                    "keyword_rank": rank,
                    "rrf_score": 1.0 / (RRF_K + rank)
                }

        # Step 4: Sort by rrf_score descending, return top_k
        results = sorted(merged.values(), key=lambda x: x["rrf_score"], reverse=True)[:top_k]

        return [
            {
                "id": item["id"],
                "content": item["content"],
                "metadata": item["metadata"],
                "similarity": round(item["rrf_score"], 6)
            }
            for item in results
        ]


# Global vector store instance
vector_store = VectorStoreManager()
