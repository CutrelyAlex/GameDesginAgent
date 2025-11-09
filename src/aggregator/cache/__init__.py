"""Cache module exports."""

from src.aggregator.cache.interface import CacheInterface
from src.aggregator.cache.file_cache import FileCache

__all__ = ["CacheInterface", "FileCache"]
