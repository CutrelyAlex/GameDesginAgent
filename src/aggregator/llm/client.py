"""
Small LLM client for keyword variant generation.

Supports OpenAI-compatible APIs (Ollama, etc.) for generating
keyword variations to improve search recall.
"""

import logging
from typing import List, Optional
import httpx

from Config import SMALL_LLM_URL, SMALL_LLM_MODEL, SMALL_LLM_API_KEY

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for small LLM keyword variant generation.
    
    Compatible with OpenAI-compatible API endpoints (Ollama, local LLMs, etc.).
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize LLM client.
        
        Args:
            api_url: LLM API base URL (default from Config.SMALL_LLM_URL)
            model: Model name (default from Config.SMALL_LLM_MODEL)
            api_key: API key if required (default from Config.SMALL_LLM_API_KEY)
            timeout: Request timeout in seconds
        """
        self.api_url = api_url or SMALL_LLM_URL
        self.model = model or SMALL_LLM_MODEL or "llama2"
        self.api_key = api_key or SMALL_LLM_API_KEY
        self.timeout = timeout
        
        if not self.api_url:
            raise ValueError(
                "SMALL_LLM_URL is required. Set it in .env or pass to constructor. "
                "Example: http://localhost:11434 for Ollama"
            )
        
        logger.info(f"LLM client initialized: {self.api_url}, model={self.model}")
    
    async def generate_completion(self, prompt: str) -> str:
        """
        Generate text completion from prompt.
        
        Args:
            prompt: Input prompt for the LLM
            
        Returns:
            Generated text response
            
        Raises:
            httpx.HTTPError: On API request failure
        """
        # Try OpenAI-compatible /v1/chat/completions endpoint first
        try:
            return await self._generate_openai_format(prompt)
        except httpx.HTTPError as e:
            logger.warning(f"OpenAI format failed: {e}, trying Ollama format")
            # Fallback to Ollama /api/generate format
            return await self._generate_ollama_format(prompt)
    
    async def _generate_openai_format(self, prompt: str) -> str:
        """Generate using OpenAI-compatible API format."""
        # Check if URL already contains path components
        base_url = self.api_url.rstrip('/')
        if '/v1' in base_url:
            # URL already includes /v1, just append /chat/completions
            url = f"{base_url}/chat/completions"
        else:
            # Standard OpenAI format
            url = f"{base_url}/v1/chat/completions"
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 200
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    
    async def _generate_ollama_format(self, prompt: str) -> str:
        """Generate using Ollama API format."""
        url = f"{self.api_url.rstrip('/')}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data["response"].strip()
    
    async def close(self):
        """Close any open connections."""
        # httpx.AsyncClient is created per request with context manager
        pass


async def test_llm_connection() -> bool:
    """
    Test LLM connection and return True if available.
    
    Returns:
        True if LLM is reachable, False otherwise
    """
    try:
        client = LLMClient()
        response = await client.generate_completion("Hello")
        logger.info(f"LLM test successful: {response[:50]}...")
        return True
    except Exception as e:
        logger.warning(f"LLM not available: {e}")
        return False
