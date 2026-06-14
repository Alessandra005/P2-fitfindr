# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
Searches the mock listings dataset for items that match what the user is looking for. It filters by price and size if provided, then scores each listing by how many of the user's keywords appear in the title, description, tags, and colors — returning the best matches first.

**Input parameters:**
- `description` (str): Keywords describing what the user wants, e.g. "vintage graphic tee". Extracted from the natural language query.
- `size` (str | None): Size to filter by, e.g. "M" or "W30". Case-insensitive. None means no size filter.
- `max_price` (float | None): Maximum price the user is willing to pay, inclusive. None means no price filter.

**What it returns:**
A list of listing dicts sorted by relevance score (highest first). Each dict has: `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand`, and `platform`. Returns an empty list if nothing matches — never raises an exception.

**What happens if it fails or returns nothing:**
If the list is empty, the agent sets a helpful error message in `session["error"]` explaining what was searched and suggesting the user broaden their query (remove size filter, raise the budget, or try different keywords). The agent returns the session immediately and does not call the next tools.

---

### Tool 2: suggest_outfit

**What it does:**
Takes the thrifted item the user is considering and their current wardrobe, and asks the LLM to suggest 1–2 complete outfit combinations using specific pieces from the wardrobe. If the wardrobe is empty, it gives general styling advice instead.

**Input parameters:**
- `new_item` (dict): The listing dict for the item being considered — the top result from search_listings.
- `wardrobe` (dict): A wardrobe dict with an `items` key containing a list of wardrobe item dicts. Each wardrobe item has: `id`, `name`, `category`, `colors`, `style_tags`, and optional `notes`.

**What it returns:**
A non-empty string with outfit suggestions. If the wardrobe has items, the suggestions name specific pieces from it. If the wardrobe is empty, the response gives general styling direction for the item type and vibe.

**What happens if it fails or returns nothing:**
If the wardrobe is empty, the tool still runs — it just switches to a general styling prompt instead of crashing. If the LLM call fails for any reason, the tool catches the exception and returns a descriptive error string so the agent can surface it to the user without crashing.

---

### Tool 3: create_fit_card

**What it does:**
Generates a short, casual Instagram/TikTok-style caption for the outfit. It takes the outfit suggestion and the listing details, and asks the LLM to write something that sounds like a real person posted it — not a product description.

**Input parameters:**
- `outfit` (str): The outfit suggestion string returned by suggest_outfit.
- `new_item` (dict): The listing dict for the thrifted item — used to pull the title, price, and platform into the caption naturally.

**What it returns:**
A 2–4 sentence string that reads like an OOTD caption. Mentions the item name, price, and platform once each. Uses a higher LLM temperature so the output varies across runs. If `outfit` is empty or whitespace-only, returns a descriptive error string instead of calling the LLM.

**What happens if it fails or returns nothing:**
If `outfit` is empty or blank, the tool returns `"Error: Cannot create a fit card without an outfit suggestion."` — no exception, no crash. If the LLM call fails, the exception is caught and returned as a readable error string.

---

### Additional Tools (if any)

None for the required features. Stretch features would add a price comparison tool here.

---

## Planning Loop

**How does your agent decide which tool to call next?**

The loop runs in a fixed sequence, but it has a real branch: if `search_listings` returns nothing, the agent stops immediately and never calls the other two tools. Here's the actual logic:

1. Parse the user's query using regex to extract `description`, `size`, and `max_price`. Store in `session["parsed"]`.
2. Call `search_listings()` with the parsed values. Store results in `session["search_results"]`.
3. **Branch:** if `results` is empty → set `session["error"]` to a helpful message and `return session` early. Do not proceed.
4. If results exist → set `session["selected_item"] = results[0]` (top result).
5. Call `suggest_outfit(selected_item, wardrobe)`. Store result in `session["outfit_suggestion"]`.
6. Call `create_fit_card(outfit_suggestion, selected_item)`. Store result in `session["fit_card"]`.
7. Return the completed session.

The agent knows it's done when it either hits the early return (error path) or finishes step 6. It never calls all three tools unconditionally.

---

## State Management

**How does information from one tool get passed to the next?**

Everything lives in a single `session` dict that gets initialized at the start of each run and passed through every step. No global variables, no re-prompting the user between steps.

What gets stored and when:
- `session["parsed"]` — set after query parsing, used to call search_listings
- `session["search_results"]` — set after search_listings, used to check for empty results
- `session["selected_item"]` — set to `results[0]`, passed directly into suggest_outfit
- `session["outfit_suggestion"]` — set after suggest_outfit, passed directly into create_fit_card
- `session["fit_card"]` — set after create_fit_card, returned to the UI
- `session["error"]` — set if anything goes wrong, checked by the UI to decide what to display

The UI (`app.py`) reads from the final session dict and maps each field to the right output panel. State never needs to be re-entered by the user mid-session.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Sets `session["error"]` with a message explaining what was searched and suggesting the user try broader keywords, remove the size filter, or raise their budget. Returns early — suggest_outfit and create_fit_card are never called. |
| suggest_outfit | Wardrobe is empty | Switches to a general styling prompt instead of a wardrobe-specific one. Still calls the LLM and returns useful advice. Never crashes or returns an empty string. |
| create_fit_card | Outfit input is missing or empty | Returns `"Error: Cannot create a fit card without an outfit suggestion."` immediately, without calling the LLM. No exception raised. |

---

## Architecture

```
User query (natural language)
        │
        ▼
_parse_query()
extracts: description, size, max_price
        │
        ▼
run_agent (Planning Loop)
        │
        ├─► search_listings(description, size, max_price)
        │        │
        │        ├── results == [] 
        │        │        set session["error"]
        │        │        return session early → UI shows error
        │        │
        │        └── results found
        │                 session["selected_item"] = results[0]
        │
        ├─► suggest_outfit(selected_item, wardrobe)
        │        │
        │        ├── wardrobe empty → general styling advice
        │        └── wardrobe has items → specific outfit combos
        │                 session["outfit_suggestion"] = result
        │
        └─► create_fit_card(outfit_suggestion, selected_item)
                 │
                 ├── outfit empty → return error string (no LLM call)
                 └── outfit valid → generate caption
                        session["fit_card"] = result

        ▼
return session
        ▼
UI maps session fields to 3 output panels
```


---

## AI Tool Plan

**Milestone 3 — Individual tool implementations:**

I used Claude for all three tools. For each one, I gave it the spec block from this file, and asked it to implement that function in `tools.py` using `load_listings()` from the data loader. Before running anything, I read through the generated code to make sure it matched my spec: right parameter names, correct failure handling, nothing extra added. Then I tested each tool from the terminal with a few different inputs. For `search_listings` I confirmed the price and size filters worked and that it returned an empty list (not an exception) when nothing matched. For `suggest_outfit` I tested both a full wardrobe and an empty one. For `create_fit_card` I checked the empty outfit guard and ran it multiple times to confirm the output actually varied.

**Milestone 4 — Planning loop and state management:**

Based on the architecture diagram and the Planning Loop and State Management sections from this file, we implemented `run_agent()` in `agent.py`. I reviewed the output before running it making sure that it branched on the search results and stored values in the session dict between steps. I also tested the no-results path with an impossible query and confirmed `session["fit_card"]` stayed `None` and the error message was helpful.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
`_parse_query()` would extract the description, max price, and size and store them in session["parsed"]. Then the agent would call `search_listings("vintage graphic tee", None, 30.0)` to filter, score, and sort the listings. In this example, it would return several matches, with the Y2K Baby Tee at $18 as the top result.

**Step 2:**
Since results aren’t empty, the agent would set `session["selected_item"]` to the top listing and call `suggest_outfit(selected_item, wardrobe)`. The tool would generate outfit ideas using named wardrobe pieces, and the result would be stored in `session["outfit_suggestion"]`.

**Step 3:**
Next, `create_fit_card(outfit_suggestion, selected_item)` would run. Because the outfit text isn’t empty, it would generate a short, casual caption and store it in `session["fit_card"]`.

**Final output to user:**
The UI would read from the session and show:
- the top listing found
- the outfit idea
- the fit card caption

If step 1 returned no results, only the first panel would show an error message and the other two would stay empty.