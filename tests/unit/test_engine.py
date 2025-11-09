"""
Unit tests for aggregation engine logic.

Tests concurrency control, caching, and result merging without real API calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.aggregator.schemas import QueryRequest, QueryResult
from src.aggregator.engine import AggregationEngine
from src.aggregator.cache import FileCache


@pytest.fixture
def mock_query_results():
    """Fixture providing sample QueryResult objects."""
    return [
        QueryResult(
            keyword="test",
            provider="bocha",
            title="Result 1",
            url="https://example.com/1",
            snippet="Test snippet 1",
            timestamp=datetime.utcnow(),
            request_id="req-001"
        ),
        QueryResult(
            keyword="test",
            provider="bocha",
            title="Result 2",
            url="https://example.com/2",
            snippet="Test snippet 2",
            timestamp=datetime.utcnow(),
            request_id="req-001"
        )
    ]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_engine_cache_hit(mock_query_results):
    """Test that engine returns cached results when available."""
    # Mock cache with pre-populated results
    mock_cache = AsyncMock(spec=FileCache)
    mock_cache.get = AsyncMock(return_value=mock_query_results)
    
    engine = AggregationEngine(cache=mock_cache, use_cache=True)
    
    request = QueryRequest(keywords=["test"], providers=["bocha"])
    
    # Should not call provider since cache hits
    with patch.object(engine, '_get_provider_client') as mock_provider:
        response = await engine.aggregate(request)
        
        # Verify cache was checked
        mock_cache.get.assert_called_once()
        
        # Verify provider was NOT called (cache hit)
        mock_provider.assert_not_called()
        
        # Verify results match cached data
        assert response.total_count == len(mock_query_results)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_engine_cache_miss_and_set(mock_query_results):
    """Test that engine queries provider on cache miss and stores result."""
    # Mock cache that returns None (cache miss)
    mock_cache = AsyncMock(spec=FileCache)
    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.set = AsyncMock()
    
    # Mock provider client
    mock_client = AsyncMock()
    mock_client.search = AsyncMock(return_value=mock_query_results)
    
    engine = AggregationEngine(cache=mock_cache, use_cache=True)
    
    with patch.object(engine, '_get_provider_client', return_value=mock_client):
        request = QueryRequest(keywords=["test"], providers=["bocha"])
        response = await engine.aggregate(request)
        
        # Verify cache was checked (miss)
        mock_cache.get.assert_called_once()
        
        # Verify provider was called
        mock_client.search.assert_called_once_with("test")
        
        # Verify result was stored in cache
        mock_cache.set.assert_called_once()
        
        # Verify response contains provider results
        assert response.total_count == len(mock_query_results)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_engine_parallel_execution():
    """Test that engine executes multiple keyword+provider combinations in parallel."""
    mock_cache = AsyncMock(spec=FileCache)
    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.set = AsyncMock()
    
    # Track call order/timing
    call_log = []
    
    async def mock_search(keyword):
        call_log.append(keyword)
        # Simulate async work
        import asyncio
        await asyncio.sleep(0.01)
        return [
            QueryResult(
                keyword=keyword,
                provider="bocha",
                title=f"Result for {keyword}",
                url="https://example.com",
                snippet="test",
                timestamp=datetime.utcnow(),
                request_id="test-001"
            )
        ]
    
    mock_client = AsyncMock()
    mock_client.search = mock_search
    
    engine = AggregationEngine(cache=mock_cache, use_cache=False, max_concurrent_keywords=5)
    
    with patch.object(engine, '_get_provider_client', return_value=mock_client):
        request = QueryRequest(
            keywords=["kw1", "kw2", "kw3"],
            providers=["bocha"]
        )
        response = await engine.aggregate(request)
        
        # All keywords should be processed
        assert len(call_log) == 3
        assert response.total_count == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_engine_handles_provider_errors():
    """Test that engine handles provider errors gracefully."""
    mock_cache = AsyncMock(spec=FileCache)
    mock_cache.get = AsyncMock(return_value=None)
    
    # Mock provider that raises error
    mock_client = AsyncMock()
    mock_client.search = AsyncMock(side_effect=Exception("API Error"))
    
    engine = AggregationEngine(cache=mock_cache, use_cache=False)
    
    with patch.object(engine, '_get_provider_client', return_value=mock_client):
        request = QueryRequest(keywords=["test"], providers=["bocha"])
        response = await engine.aggregate(request)
        
        # Should return empty results, not crash
        assert response.total_count == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_engine_merges_multiple_providers():
    """Test that engine correctly merges results from multiple providers."""
    bocha_results = [
        QueryResult(
            keyword="test",
            provider="bocha",
            title="Bocha Result",
            url="https://bocha.example.com",
            snippet="from bocha",
            timestamp=datetime.utcnow(),
            request_id="b-001"
        )
    ]
    
    tavily_results = [
        QueryResult(
            keyword="test",
            provider="tavily",
            title="Tavily Result",
            url="https://tavily.example.com",
            snippet="from tavily",
            timestamp=datetime.utcnow(),
            request_id="t-001"
        )
    ]
    
    mock_cache = AsyncMock(spec=FileCache)
    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.set = AsyncMock()
    
    async def mock_get_client(provider):
        client = AsyncMock()
        if provider == "bocha":
            client.search = AsyncMock(return_value=bocha_results)
        else:
            client.search = AsyncMock(return_value=tavily_results)
        return client
    
    engine = AggregationEngine(cache=mock_cache, use_cache=False)
    
    with patch.object(engine, '_get_provider_client', side_effect=mock_get_client):
        request = QueryRequest(keywords=["test"], providers=["bocha", "tavily"])
        response = await engine.aggregate(request)
        
        # Should have results from both providers
        assert response.total_count == 2
        assert len(response.by_provider["bocha"]) == 1
        assert len(response.by_provider["tavily"]) == 1
