"""
信息整理模块 (Info Aggregation Module)

A module for aggregating search results from multiple providers (Bocha, Tavily)
with optional LLM-based keyword variant generation and CSV output.
"""

__version__ = "0.1.0"

from src.aggregator.schemas import (
    QueryRequest,
    QueryResult,
    CacheRecord,
    KeywordVariant,
    AggregationResponse
)
from src.aggregator.providers import BochaClient, TavilyClient
from src.aggregator.engine import AggregationEngine
from src.aggregator.io import CSVWriter
from src.aggregator.llm import LLMClient
from src.aggregator.keywords import KeywordVariantGenerator

__all__ = [
    "QueryRequest",
    "QueryResult", 
    "CacheRecord",
    "KeywordVariant",
    "AggregationResponse",
    "BochaClient",
    "TavilyClient",
    "AggregationEngine",
    "CSVWriter",
    "LLMClient",
    "KeywordVariantGenerator"
]
