# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
P2-fitfindr/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── tools.py                   # The three core tools
├── agent.py                   # Planning loop and session state
├── app.py                     # Gradio UI
├── tests/
│   └── test_tools.py          # pytest tests for all three tools
├── conftest.py                # Lets pytest find the project root
├── planning.md                # Spec written before implementation
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

## Tool Inventory

### `search_listings(description, size, max_price)`
Searches the mock listings dataset for items matching the user's query. Filters by `size` (str, optional) and `max_price` (float, optional), then scores each remaining listing by keyword overlap with `description` (str) across title, description, tags, colors, and brand. Returns a list of matching listing dicts sorted by relevance score/best match first. Returns an empty list if nothing matches, never raises an exception.

### `suggest_outfit(new_item, wardrobe)`
Takes the selected listing dict (`new_item`) and the user's wardrobe dict (`wardrobe`, with an `items` key) and calls the LLM to suggest 1–2 complete outfit combinations. If the wardrobe has items, it references them by name. If the wardrobe is empty, it gives general styling advice instead. Always returns a non-empty string either way.

### `create_fit_card(outfit, new_item)`
Takes the outfit suggestion string (`outfit`) and the listing dict (`new_item`) and generates a 2–4 sentence Instagram-style caption. Mentions the item name, price, and platform naturally, once each. Uses a higher LLM temperature so the output varies between runs. Returns a descriptive error string if `outfit` is empty.

---

## How the Planning Loop Works

The agent parses the user's query with regex to extract a description, size, and max price. Then it runs the tools in sequence, but with one real branch: if `search_listings` returns nothing, the agent sets a helpful error message and returns immediately. It never calls `suggest_outfit` or `create_fit_card` with empty input. On the other hand, if results are found, the top result flows into `suggest_outfit`, and that output flows directly into `create_fit_card`. Everything is stored in a single session dict so nothing has to be re-entered between steps. The agent's behavior actually changes based on what it gets back.

---

## State Management

All state lives in a single session dict initialized at the start of each run. Here's what gets stored and when:

- `session["parsed"]` — description, size, max_price extracted from the query
- `session["search_results"]` — full list returned by search_listings
- `session["selected_item"]` — top result, passed directly into suggest_outfit
- `session["outfit_suggestion"]` — LLM output from suggest_outfit, passed directly into create_fit_card
- `session["fit_card"]` — final caption from create_fit_card
- `session["error"]` — set if the agent stops early; checked by the UI to decide what to show

No global variables. No re-prompting the user mid-session. The UI reads the final session dict and maps each field to the right output panel.

---

## Error Handling

**search_listings — no results:** Returns an empty list. The agent catches this immediately, sets `session["error"]` to a message explaining what was searched and suggesting the user broaden their query, and returns early. The other two tools are never called. Tested with `search_listings("designer ballgown", size="XXS", max_price=5)` —> returns `[]`, no exception.

**suggest_outfit — empty wardrobe:** Instead of crashing, the tool detects an empty `items` list and switches to a general styling prompt. The user still gets useful outfit ideas even with no wardrobe on file. Tested with `get_empty_wardrobe()` —> returns a non-empty string every time.

**create_fit_card — empty outfit string:** Guards against this at the top of the function. If `outfit` is empty or whitespace-only, returns `"Error: Cannot create a fit card without an outfit suggestion."` immediately without touching the LLM. Tested directly —> no exception, just a clean error string.

---

## Spec Reflection

Writing planning.md first ended up making everything way easier. Having the exact inputs, outputs, and failure modes already written down, gave me a clear picture of what “correct” even looked like before touching any code. The state section helped the most. Once I laid out the session fields, the flow for run_agent() basically wrote itself.

The only part that shifted from my original idea was the query parser. I thought I might lean on the LLM to pull out the description, size, and price, but simple regex turned out to be faster to work with and way easier to test. It handles the kinds of queries this app expects without any trouble. The main limitation is that very unusual phrasing might not parse perfectly, but it handles everything in the example queries without issues.

---

## AI Usage

**Tool implementations (Milestone 3):** For each tool, I used the specs from planning.md to guide the implementation and made sure I stayed in control of the logic. I checked the generated code myself first to confirm it matched what I outlined. After that, I tested everything from the terminal. For `search_listings`, I made sure the scoring actually made sense by trying different queries. For `suggest_outfit`, I tested both a full wardrobe and an empty one. And for `create_fit_card`, I ran it multiple times on the same input to confirm the caption varied the way I wanted.

**Planning loop (Milestone 4):** I used the architecture diagram, the Planning Loop and State Management sections to shape how `run_agent()` should work. I reviewed the implementation carefully to make sure it branched correctly on the search results instead of calling every tool, and that each step updated the session dict the way I planned. Then I ran both CLI test cases to confirm the normal flow and the no‑results path behaved exactly how I designed.