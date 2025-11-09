"""
Aggregation engine for coordinating parallel keyword searches across providers.

Implements concurrency control, caching, and result merging.
"""

import asyncio
import logging
import hashlib
from typing import List, Dict, Optional, Literal
from collections import defaultdict

from src.aggregator.schemas import QueryRequest, QueryResult, AggregationResponse
from src.aggregator.providers import BochaClient, TavilyClient
from src.aggregator.cache import CacheInterface, FileCache

logger = logging.getLogger(__name__)


class AggregationEngine:
    """
    Async engine for aggregating search results from multiple providers.
    
    Features:
    - Parallel provider queries with concurrency limits
    - TTL-based caching of keyword results
    - Configurable provider selection
    """
    
    def __init__(
        self,
        cache: Optional[CacheInterface] = None,
        max_concurrent_keywords: int = 5,
        cache_ttl: int = 86400,
        use_cache: bool = True
    ):
        """
        Initialize aggregation engine.
        
        Args:
            cache: Cache implementation (default: FileCache)
            max_concurrent_keywords: Max concurrent keyword queries (default: 5)
            cache_ttl: Cache TTL in seconds (default: 24h)
            use_cache: Whether to use caching (default: True)
        """
        self.cache = cache or FileCache()
        self.max_concurrent_keywords = max_concurrent_keywords
        self.cache_ttl = cache_ttl
        self.use_cache = use_cache
        
        self._bocha_client: Optional[BochaClient] = None
        self._tavily_client: Optional[TavilyClient] = None
    
    def _get_cache_key(self, provider: str, keyword: str) -> str:
        """Generate cache key for provider+keyword combination."""
        # Use hash for consistent key format
        key_str = f"{provider}|{keyword}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def _get_provider_client(
        self,
        provider: Literal["bocha", "tavily"]
    ) -> BochaClient | TavilyClient:
        """Get or create provider client (lazy initialization)."""
        if provider == "bocha":
            if self._bocha_client is None:
                self._bocha_client = BochaClient()
            return self._bocha_client
        elif provider == "tavily":
            if self._tavily_client is None:
                self._tavily_client = TavilyClient()
            return self._tavily_client
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _search_with_cache(
        self,
        provider: Literal["bocha", "tavily"],
        keyword: str,
        max_results: int = 10
    ) -> List[QueryResult]:
        """
        Search a provider for a keyword, using cache if available.
        
        Args:
            provider: Provider name
            keyword: Search keyword
            max_results: Maximum results to return from this provider
            
        Returns:
            List of QueryResult objects
        """
        cache_key = self._get_cache_key(provider, keyword)
        
        # Check cache first
        if self.use_cache:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                logger.info(f"[Cache HIT] {provider}|{keyword}")
                # Apply max_results limit to cached results
                return cached[:max_results]
            logger.debug(f"[Cache MISS] {provider}|{keyword}")
        
        # Cache miss or disabled, query provider
        client = await self._get_provider_client(provider)
        results = await client.search(keyword, max_results=max_results)
        
        # Store in cache
        if self.use_cache and results:
            await self.cache.set(cache_key, results, ttl=self.cache_ttl)
            logger.debug(f"[Cache SET] {provider}|{keyword} with {len(results)} results")
        
        return results
    
    async def aggregate(self, request: QueryRequest) -> AggregationResponse:
        """
        Aggregate search results for multiple keywords across providers.
        
        Args:
            request: QueryRequest with keywords and provider selection
            
        Returns:
            AggregationResponse with merged results
        """
        logger.info(
            f"Starting aggregation for {len(request.keywords)} keywords "
            f"across providers: {request.providers}"
        )
        
        # Create tasks for all keyword+provider combinations
        tasks = []
        for keyword in request.keywords:
            for provider in request.providers:
                tasks.append(
                    self._search_with_cache(provider, keyword, request.max_results_per_provider)
                )
        
        # Execute with concurrency limit using semaphore
        semaphore = asyncio.Semaphore(self.max_concurrent_keywords)
        
        async def bounded_search(task):
            async with semaphore:
                return await task
        
        # Gather all results
        results_lists = await asyncio.gather(
            *[bounded_search(task) for task in tasks],
            return_exceptions=True
        )
        
        # Flatten and filter errors
        all_results = []
        for result in results_lists:
            if isinstance(result, Exception):
                logger.error(f"Search task failed: {result}")
                continue
            elif isinstance(result, list):
                all_results.extend(result)
        
        # Group by provider for response
        by_provider = defaultdict(list)
        for result in all_results:
            by_provider[result.provider].append(result)
        
        logger.info(
            f"Aggregation complete: {len(all_results)} total results "
            f"({dict((k, len(v)) for k, v in by_provider.items())})"
        )
        
        return AggregationResponse(
            results=all_results,
            total_count=len(all_results),
            by_provider=dict(by_provider),
            request_id=request.client_request_id
        )
    
    async def close(self):
        """Close all provider clients and cache."""
        if self._bocha_client:
            await self._bocha_client.close()
        if self._tavily_client:
            await self._tavily_client.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
