"""
File-based cache implementation for development and single-node deployments.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from src.aggregator.cache.interface import CacheInterface
from src.aggregator.schemas import QueryResult, CacheRecord


class FileCache(CacheInterface):
    """
    Simple file-based cache using JSON files.
    
    Not suitable for production multi-instance deployments (use Redis instead).
    """
    
    def __init__(self, cache_dir: str = ".cache"):
        """
        Initialize file cache.
        
        Args:
            cache_dir: Directory to store cache files (default: .cache)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_path(self, key: str) -> Path:
        """Get filesystem path for a cache key."""
        # Use hash to avoid filesystem issues with special chars
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"
    
    async def get(self, key: str) -> Optional[List[QueryResult]]:
        """Retrieve cached results if not expired."""
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            record = CacheRecord(**data)
            
            # Check expiration
            if record.is_expired():
                # Clean up expired entry
                await self.delete(key)
                return None
            
            return record.value
            
        except (json.JSONDecodeError, KeyError, ValueError):
            # Corrupted cache file, delete it
            cache_path.unlink(missing_ok=True)
            return None
    
    async def set(self, key: str, results: List[QueryResult], ttl: int = 86400) -> None:
        """Store results in cache file."""
        cache_path = self._get_cache_path(key)
        
        record = CacheRecord(
            key=key,
            value=results,
            ttl=ttl,
            created_at=datetime.utcnow()
        )
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            # Serialize using model_dump for Pydantic v2
            json.dump(record.model_dump(mode='json'), f, ensure_ascii=False, indent=2)
    
    async def delete(self, key: str) -> None:
        """Delete a cache entry."""
        cache_path = self._get_cache_path(key)
        cache_path.unlink(missing_ok=True)
    
    async def clear(self) -> None:
        """Clear all cache files."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink(missing_ok=True)
