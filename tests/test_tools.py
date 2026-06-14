"""
tests/test_tools.py

Tests for each tool's happy path and failure mode.
Run with: pytest tests/
"""

from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=30)
    assert all(item["price"] <= 30 for item in results)

def test_search_size_filter():
    results = search_listings("tee", size="M", max_price=None)
    assert all("m" in item["size"].lower() for item in results)

def test_search_no_exception_on_garbage_input():
    results = search_listings("xyzzy123nonsense", size=None, max_price=None)
    assert isinstance(results, list)
    assert results == []


def test_suggest_outfit_with_wardrobe():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    output = suggest_outfit(results[0], get_example_wardrobe())
    assert isinstance(output, str)
    assert len(output) > 0

def test_suggest_outfit_empty_wardrobe():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    output = suggest_outfit(results[0], get_empty_wardrobe())
    assert isinstance(output, str)
    assert len(output) > 0


def test_fit_card_returns_string():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    outfit = suggest_outfit(results[0], get_example_wardrobe())
    card = create_fit_card(outfit, results[0])
    assert isinstance(card, str)
    assert len(card) > 0

def test_fit_card_empty_outfit_returns_error():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    card = create_fit_card("", results[0])
    assert "Error" in card

def test_fit_card_whitespace_outfit_returns_error():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    card = create_fit_card("   ", results[0])
    assert "Error" in card