import os
import logging
from typing import List
from dotenv import load_dotenv
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import ScoredPoint
from pydantic import BaseModel
from agents import function_tool

# Load environment variables
load_dotenv()

# Constants
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "math-content"
EMBEDDING_MODEL = "text-embedding-3-small"

# Initialize clients
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
qdrant_client = AsyncQdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Logging
logger = logging.getLogger(__name__)

class RAGSearchResult(BaseModel):
    """Search result from Qdrant"""
    content_id: str
    problem: str
    solution: str
    section: str
    difficulty_level: str
    similarity_score: float

async def generate_embedding(text: str) -> List[float]:
    try:
        response = await openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise

@function_tool
async def rag_search(query: str, num_chunks: int = 4) -> List[RAGSearchResult]:
    try:
        if not query.strip():
            raise ValueError("Query cannot be empty")

        num_chunks = max(1, min(num_chunks, 10))

        logger.info(f"Searching Qdrant for: {query}")
        query_embedding = await generate_embedding(query)

        search_results: List[ScoredPoint] = await qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=num_chunks,
            score_threshold=0.3,
        )

        # Log what was retrieved
        logger.info(f"Found {len(search_results)} results from vector database")
        
        results = []
        for i, point in enumerate(search_results):
            payload = point.payload
            result = RAGSearchResult(
                content_id=payload.get("content_id", ""),
                problem=payload.get("problem", ""),
                solution=payload.get("solution", ""),
                section=payload.get("section", ""),
                difficulty_level=payload.get("difficulty_level", ""),
                similarity_score=point.score,
            )
            results.append(result)
            
            # Log details of each retrieved item
            logger.info(f"Result {i+1}:")
            logger.info(f"  Score: {point.score:.4f}")
            logger.info(f"  Section: {result.section}")
            logger.info(f"  Problem: {result.problem[:100]}...")
            logger.info(f"  Solution: {result.solution[:100]}...")

        return results

    except Exception as e:
        logger.error(f"❌ RAG search failed: {e}")
        return []
