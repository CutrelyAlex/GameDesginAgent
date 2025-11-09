"""
Cache interface and implementations for query result caching.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from src.aggregator.schemas import QueryResult, CacheRecord


class CacheInterface(ABC):
    """Abstract interface for cache implementations."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[List[QueryResult]]:
        """
        Retrieve cached results for a key.
        
        Args:
            key: Cache key (typically provider|keyword hash)
            
        Returns:
            List of QueryResult if cache hit and not expired, None otherwise
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, results: List[QueryResult], ttl: int = 86400) -> None:
        """
        Store results in cache with TTL.
        
        Args:
            key: Cache key
            results: Query results to cache
            ttl: Time-to-live in seconds (default 24h)
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        Delete a cache entry.
        
        Args:
            key: Cache key to delete
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass
