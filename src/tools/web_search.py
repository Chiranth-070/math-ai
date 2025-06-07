import logging
import os
import httpx
from typing import List, Dict
from dotenv import load_dotenv
from agents import function_tool

# Load environment variables
load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Set up logging
logger = logging.getLogger(__name__)

@function_tool
async def web_search(queries: List[str]) -> Dict:
    """
    Search the web for information using Tavily API.
    
    Args:
        queries: List of search queries to run
        
    Returns:
        Dictionary containing search results
    """
    if not queries:
        logger.warning("No search queries provided")
        return {
            "status": "error",
            "error": "No search queries provided",
            "results": {}
        }
    
    if not TAVILY_API_KEY:
        logger.error("TAVILY_API_KEY not set in environment variables")
        return {
            "status": "error",
            "error": "Tavily API key not configured",
            "results": {}
        }
    
    results = {}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for query in queries:
            logger.info(f"Web searching for: {query}")
            try:
                # Use Tavily directly rather than going through MCP
                search_payload = {
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "search_depth": "advanced",
                    "include_answer": True,
                    "include_domains": ["*.edu", "*.org", "*.gov", "wikipedia.org", "mathworld.wolfram.com", "brilliant.org", "khanacademy.org"],
                    "max_results": 5
                }
                
                response = await client.post(
                    "https://api.tavily.com/search",
                    json=search_payload
                )
                
                if response.status_code != 200:
                    logger.warning(f"Tavily API error: {response.status_code} - {response.text}")
                    results[query] = {
                        "error": f"API error: {response.status_code}",
                        "search_results": [],
                        "citations": [],
                        "result_count": 0
                    }
                    continue
                
                result_data = response.json()
                
                # Log what was retrieved
                logger.info(f"Found {len(result_data.get('results', []))} web results")
                
                # Process and log results
                search_results = result_data.get("results", [])
                for i, result in enumerate(search_results[:3]):  # Log first 3 results
                    logger.info(f"Web Result {i+1}: {result.get('title', 'No title')}")
                    logger.info(f"  Source: {result.get('url', 'No URL')}")
                    logger.info(f"  Content: {result.get('content', 'No content')[:100]}...")
                
                results[query] = {
                    "summary": f"Found {len(search_results)} sources for '{query}'",
                    "search_results": search_results,
                    "citations": [
                        {"title": r.get("title", ""), "url": r.get("url", "")}
                        for r in search_results
                    ],
                    "result_count": len(search_results),
                    "answer": result_data.get("answer", "")
                }
                
            except Exception as e:
                logger.error(f"Web search error for query '{query}': {str(e)}")
                results[query] = {
                    "error": str(e),
                    "search_results": [],
                    "citations": [],
                    "result_count": 0
                }
    
    return {
        "status": "success",
        "metadata": {
            "query_count": len(queries)
        },
        "results": results
    }
