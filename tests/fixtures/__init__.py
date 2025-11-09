"""
Test fixtures for contract and integration tests.

This module provides helper functions to load sample API responses.
"""

import json
from pathlib import Path
from typing import Dict, Any


FIXTURES_DIR = Path(__file__).parent


def load_fixture(filename: str) -> Dict[str, Any]:
    """
    Load a JSON fixture file.
    
    Args:
        filename: Name of the fixture file (e.g., 'sample_bocha.json')
        
    Returns:
        Parsed JSON data as dict
    """
    fixture_path = FIXTURES_DIR / filename
    with open(fixture_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_sample_bocha_response() -> Dict[str, Any]:
    """Get sample Bocha API response."""
    return load_fixture('sample_bocha.json')


def get_sample_tavily_response() -> Dict[str, Any]:
    """Get sample Tavily API response."""
    return load_fixture('sample_tavily.json')
