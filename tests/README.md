# Tests Directory

This directory contains all tests for the 信息整理模块 (Info Aggregation Module).

## Structure

- `contract/` - Contract tests for external API providers (Bocha, Tavily)
- `unit/` - Unit tests for internal components
- `integration/` - Integration tests for end-to-end scenarios
- `fixtures/` - Sample API responses and test data

## Running Tests

```bash
# Run all tests
pytest

# Run specific test category
pytest -m unit
pytest -m contract
pytest -m integration

# Run with coverage
pytest --cov=src --cov-report=html
```

## Test Fixtures

Sample provider responses are stored in `fixtures/` for contract testing:
- `sample_bocha.json` - Bocha API response example
- `sample_tavily.json` - Tavily API response example
