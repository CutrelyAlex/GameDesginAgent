"""
Tavily search provider client.

Implements async search interface for Tavily search API.
"""

import logging
import uuid
from typing import List, Optional
from datetime import datetime

from src.aggregator.http import HTTPClient
from src.aggregator.schemas import QueryResult
from Config import TAVILY_API_URL, TAVILY_API_KEY

logger = logging.getLogger(__name__)


class TavilyClient:
    """
    Async client for Tavily search API.
    
    Endpoint: POST /search
    Request: {"query": "keyword"} or {"q": "keyword"}
    Response: {"query": "...", "results": [...]}
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize Tavily client.
        
        Args:
            api_url: Tavily API base URL (default from Config)
            api_key: Tavily API key (default from Config)
            timeout: Request timeout in seconds
        """
        self.api_url = api_url or TAVILY_API_URL
        self.api_key = api_key or TAVILY_API_KEY
        
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY is required (set in .env or pass to constructor)")
        
        self.client = HTTPClient(
            base_url=self.api_url,
            api_key=self.api_key,
            timeout=timeout
        )
    
    async def search(self, keyword: str, max_results: int = 10) -> List[QueryResult]:
        """
        Search Tavily for a keyword and return mapped results.
        
        Args:
            keyword: Search keyword
            max_results: Maximum results to return (default: 10)
            
        Returns:
            List of QueryResult objects
            
        Raises:
            httpx.HTTPStatusError: On API errors
            httpx.RequestError: On network errors
        """
        logger.info(f"[Tavily] Searching for keyword: {keyword}")
        
        # Tavily typically supports up to 20 results per request
        # If user requests more, we'll try the maximum supported
        actual_max_results = min(max_results, 20)
        if max_results > 20:
            logger.info(f"[Tavily] Requested {max_results} results, capping at 20 (Tavily API limit)")
        
        # Try primary request format first, fallback to alternate
        request_bodies = [
            {"query": keyword, "max_results": actual_max_results},
            {"query": keyword, "limit": actual_max_results},
            {"query": keyword, "count": actual_max_results},
            {"q": keyword, "max_results": actual_max_results},
            {"q": keyword, "limit": actual_max_results},
            {"q": keyword, "count": actual_max_results},
            {"query": keyword},  # Fallback without count
            {"q": keyword}       # Final fallback
        ]
        
        last_error = None
        for request_body in request_bodies:
            try:
                response = await self.client.post(
                    "/search",
                    json_data=request_body
                )
                
                data = response.json()
                request_id = str(uuid.uuid4())  # Tavily doesn't provide request_id
                
                # Parse Tavily response structure
                search_results = data.get("results", [])
                
                results = []
                for item in search_results:
                    try:
                        result = QueryResult(
                            keyword=keyword,
                            provider="tavily",
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            snippet=item.get("content", ""),  # Tavily uses 'content' field
                            summary=None,
                            timestamp=datetime.utcnow(),
                            request_id=request_id
                        )
                        results.append(result)
                    except Exception as e:
                        logger.warning(f"[Tavily] Failed to parse result item: {e}")
                        continue
                
                logger.info(f"[Tavily] Found {len(results)} results for '{keyword}'")
                return results
                
            except Exception as e:
                last_error = e
                logger.debug(f"[Tavily] Request format {request_body} failed: {e}")
                continue
        
        # All formats failed
        logger.error(f"[Tavily] Search failed for '{keyword}': {last_error}")
        raise last_error
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
