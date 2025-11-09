"""
Bocha (博查) search provider client.

Implements async search interface for Bocha web search API.
"""

import logging
import uuid
from typing import List, Optional
from datetime import datetime

from src.aggregator.http import HTTPClient
from src.aggregator.schemas import QueryResult
from Config import BOCHA_API_URL, BOCHA_API_KEY

logger = logging.getLogger(__name__)


class BochaClient:
    """
    Async client for Bocha web search API.
    
    Endpoint: POST /v1/web-search
    Request: {"query": "keyword"}
    Response: {"request_id": "...", "data": {"webPages": {"value": [...]}}}
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize Bocha client.
        
        Args:
            api_url: Bocha API base URL (default from Config)
            api_key: Bocha API key (default from Config)
            timeout: Request timeout in seconds
        """
        self.api_url = api_url or BOCHA_API_URL
        self.api_key = api_key or BOCHA_API_KEY
        
        if not self.api_key:
            raise ValueError("BOCHA_API_KEY is required (set in .env or pass to constructor)")
        
        self.client = HTTPClient(
            base_url=self.api_url,
            api_key=self.api_key,
            timeout=timeout
        )
    
    async def search(self, keyword: str, max_results: int = 10) -> List[QueryResult]:
        """
        Search Bocha for a keyword and return mapped results.
        
        Args:
            keyword: Search keyword
            max_results: Maximum results to return (1-50, default: 10)
            
        Returns:
            List of QueryResult objects
            
        Raises:
            httpx.HTTPStatusError: On API errors
            httpx.RequestError: On network errors
        """
        logger.info(f"[Bocha] Searching for keyword: {keyword}")
        
        try:
            # Validate max_results range (Bocha supports 1-50)
            # If user requests more than 50, we cap at 50 since that's Bocha's limit
            actual_max_results = min(max_results, 50)
            if max_results > 50:
                logger.info(f"[Bocha] Requested {max_results} results, capping at 50 (Bocha API limit)")
            
            response = await self.client.post(
                "/v1/web-search",
                json_data={"query": keyword, "count": actual_max_results}
            )
            
            data = response.json()
            request_id = data.get("request_id", str(uuid.uuid4()))
            
            # Parse Bocha response structure
            web_pages = data.get("data", {}).get("webPages", {}).get("value", [])
            
            results = []
            for item in web_pages:
                try:
                    result = QueryResult(
                        keyword=keyword,
                        provider="bocha",
                        title=item.get("name", ""),
                        url=item.get("url", ""),
                        snippet=item.get("snippet", ""),
                        summary=None,  # Bocha doesn't provide summary by default
                        timestamp=datetime.utcnow(),
                        request_id=request_id
                    )
                    results.append(result)
                except Exception as e:
                    logger.warning(f"[Bocha] Failed to parse item {item.get('id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"[Bocha] Found {len(results)} results for '{keyword}'")
            return results
            
        except Exception as e:
            logger.error(f"[Bocha] Search failed for '{keyword}': {e}")
            raise
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
