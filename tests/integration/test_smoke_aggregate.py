"""
Integration smoke test for end-to-end aggregation flow.

Tests the complete pipeline from provider queries to CSV output.
"""

import pytest
import os
from pathlib import Path

from src.aggregator.schemas import QueryRequest
from src.aggregator.engine import AggregationEngine
from src.aggregator.io import CSVWriter


@pytest.mark.integration
@pytest.mark.asyncio
async def test_smoke_aggregate_single_keyword():
    """
    Smoke test: Query a single keyword from both providers and save to CSV.
    
    Requires valid API keys in .env file.
    """
    # Skip if API keys not configured
    from Config import BOCHA_API_KEY, TAVILY_API_KEY
    if not BOCHA_API_KEY or not TAVILY_API_KEY:
        pytest.skip("API keys not configured in .env")
    
    request = QueryRequest(
        keywords=["test"],
        providers=["bocha", "tavily"]
    )
    
    engine = AggregationEngine(use_cache=False)  # Disable cache for fresh test
    
    try:
        response = await engine.aggregate(request)
        
        # Assertions
        assert response.total_count > 0, "Should have at least some results"
        assert "bocha" in response.by_provider or "tavily" in response.by_provider
        
        # Test CSV writing
        csv_writer = CSVWriter(output_dir="data/test_results")
        output_path = csv_writer.write_results(response.results, "smoke_test.csv")
        
        assert output_path.exists(), "CSV file should be created"
        
        # Cleanup
        output_path.unlink()
        
    finally:
        await engine.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_smoke_aggregate_with_cache():
    """
    Smoke test: Verify caching works by querying same keyword twice.
    """
    from Config import BOCHA_API_KEY
    if not BOCHA_API_KEY:
        pytest.skip("BOCHA_API_KEY not configured")
    
    request = QueryRequest(
        keywords=["cache_test"],
        providers=["bocha"]
    )
    
    engine = AggregationEngine(use_cache=True, cache_ttl=300)
    
    try:
        # First query (cache miss)
        response1 = await engine.aggregate(request)
        count1 = response1.total_count
        
        # Second query (should hit cache)
        response2 = await engine.aggregate(request)
        count2 = response2.total_count
        
        # Results should be identical (from cache)
        assert count1 == count2, "Cache should return same result count"
        
    finally:
        await engine.close()
        # Cleanup cache
        await engine.cache.clear()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_csv_collision_handling():
    """
    Test that CSV writer creates new file with timestamp when collision occurs.
    """
    csv_writer = CSVWriter(output_dir="data/test_results")
    
    # Create minimal fake results
    from src.aggregator.schemas import QueryResult
    from datetime import datetime
    
    results = [
        QueryResult(
            keyword="test",
            provider="bocha",
            title="Test Result",
            url="https://example.com",
            snippet="Test snippet",
            timestamp=datetime.utcnow(),
            request_id="test-001"
        )
    ]
    
    # Write first file
    path1 = csv_writer.write_results(results, "collision_test.csv")
    assert path1.exists()
    
    # Write second file (should have timestamp suffix)
    path2 = csv_writer.write_results(results, "collision_test.csv")
    assert path2.exists()
    assert path1 != path2, "Second file should have different name"
    
    # Cleanup
    path1.unlink()
    path2.unlink()
