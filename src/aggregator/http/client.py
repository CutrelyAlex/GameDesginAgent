"""
HTTP client utilities with retry, backoff, and authentication support.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class HTTPClient:
    """
    Async HTTP client wrapper with retry/backoff for provider API calls.
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        """
        Initialize HTTP client.
        
        Args:
            base_url: Base URL for API (e.g., https://api.bochaai.com)
            api_key: API key for Bearer authentication
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for 5xx/429 errors
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        
        self._client: Optional[httpx.AsyncClient] = None
    
    def _get_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Build request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "aiagent-info-aggregator/0.1.0"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        if extra_headers:
            headers.update(extra_headers)
        
        return headers
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True
            )
        return self._client
    
    async def post(
        self,
        endpoint: str,
        json_data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """
        POST request with retry and exponential backoff.
        
        Args:
            endpoint: API endpoint path (e.g., /v1/web-search)
            json_data: JSON request body
            headers: Optional extra headers
            
        Returns:
            httpx.Response object
            
        Raises:
            httpx.HTTPStatusError: On 4xx errors or exhausted retries
            httpx.RequestError: On network errors
        """
        url = f"{self.base_url}{endpoint}"
        request_headers = self._get_headers(headers)
        
        client = await self._get_client()
        
        for attempt in range(self.max_retries):
            try:
                response = await client.post(
                    url,
                    json=json_data,
                    headers=request_headers
                )
                
                # Success or 4xx client error (don't retry)
                if response.status_code < 500 and response.status_code != 429:
                    response.raise_for_status()
                    return response
                
                # 5xx or 429 - retry with backoff
                if attempt < self.max_retries - 1:
                    backoff = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"Request to {url} failed with {response.status_code}, "
                        f"retrying in {backoff}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(backoff)
                else:
                    # Last attempt, raise error
                    response.raise_for_status()
                    
            except httpx.RequestError as e:
                if attempt < self.max_retries - 1:
                    backoff = 2 ** attempt
                    logger.warning(
                        f"Network error for {url}: {e}, "
                        f"retrying in {backoff}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(backoff)
                else:
                    raise
        
        # Should not reach here, but satisfies type checker
        raise RuntimeError("Unexpected retry loop exit")
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
