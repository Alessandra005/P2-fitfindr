"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""
import re
from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }

def _parse_query(query: str) -> dict:
    """
    Extract description, size, and max_price from a natural language query.

    Examples:
        "vintage graphic tee under $30, size M"
        → {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}

        "looking for a flannel shirt"
        → {"description": "flannel shirt", "size": None, "max_price": None}
    """
    # Extract max price
    max_price = None
    price_match = re.search(r"(?:under|max|below|less than)?\s*\$?(\d+(?:\.\d+)?)", query, re.IGNORECASE)
    if price_match:
        max_price = float(price_match.group(1))

    # Extract size
    size = None
    size_match = re.search(r"\bsize\s+([A-Z0-9/]+)\b", query, re.IGNORECASE)
    if size_match:
        size = size_match.group(1).upper()

    description = query
    description = re.sub(r"(?:under|max|below|less than)?\s*\$\d+(?:\.\d+)?", "", description, flags=re.IGNORECASE)
    description = re.sub(r"\bsize\s+[A-Z0-9/]+\b", "", description, flags=re.IGNORECASE)
    description = re.sub(r"\b(looking for|i want|i need|find me|help me find)\b", "", description, flags=re.IGNORECASE)
    description = re.sub(r",", " ", description)
    description = " ".join(description.split())  

    return {"description": description, "size": size, "max_price": max_price}


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.
    """
    # Step 1: initialize session
    session = _new_session(query, wardrobe)

    # Step 2: parse the query
    parsed = _parse_query(query)
    session["parsed"] = parsed

    # Step 3: search listings
    results = search_listings(
        description=parsed["description"],
        size=parsed["size"],
        max_price=parsed["max_price"],
    )
    session["search_results"] = results
    if not results:
        size_info = f" in size {parsed['size']}" if parsed["size"] else ""
        price_info = f" under ${parsed['max_price']}" if parsed["max_price"] else ""
        session["error"] = (
            f"No listings found for \"{parsed['description']}\"{size_info}{price_info}. "
            "Try broadening your search — remove the size filter, raise your budget, "
            "or use different keywords."
        )
        return session

    # Step 4: select top result
    session["selected_item"] = results[0]

    # Step 5: suggest outfit
    outfit = suggest_outfit(session["selected_item"], session["wardrobe"])
    session["outfit_suggestion"] = outfit

    # Step 6: create fit card
    fit_card = create_fit_card(outfit, session["selected_item"])
    session["fit_card"] = fit_card

    # Step 7: return completed session
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")