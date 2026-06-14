"""
app.py

Gradio interface for FitFindr. The layout and wiring are already set up —
your job is to fill in handle_query() so it calls run_agent() and maps
the session results to the three output panels.

Run with:
    python app.py

Then open the localhost URL shown in your terminal (usually http://localhost:7860,
but check your terminal — the port may differ).
"""

import gradio as gr

from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# ── query handler ─────────────────────────────────────────────────────────────

def handle_query(user_query: str, wardrobe_choice: str) -> tuple[str, str, str]:
    if not user_query or not user_query.strip():
        return "Please enter a search query.", "", ""

    if wardrobe_choice == "Empty wardrobe (new user)":
        wardrobe = get_empty_wardrobe()
    else:
        wardrobe = get_example_wardrobe()

    session = run_agent(user_query, wardrobe)

    if session["error"]:
        return session["error"], "", ""

    item = session["selected_item"]
    listing_text = (
        f"✦  {item['title']}\n\n"
        f"💰  ${item['price']}   |   📦  {item['platform'].capitalize()}   |   📐  {item['size']}\n"
        f"🏷️  {item['condition'].capitalize()}   |   🎨  {', '.join(item['colors']).title()}\n\n"
        f"─────────────────────────────\n"
        f"{item['description']}\n\n"
        f"Tags: {', '.join(item['style_tags'])}"
    )

    return listing_text, session["outfit_suggestion"], session["fit_card"]


# ── interface ─────────────────────────────────────────────────────────────────

EXAMPLE_QUERIES = [
    "vintage graphic tee under $30",
    "90s track jacket in size M",
    "flowy midi skirt under $40",
    "black combat boots size 8",
    "designer ballgown size XXS under $5",
]

custom_css = """
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');

/* ── page background ── */
body, .gradio-container {
    background: linear-gradient(135deg, #fdf6f0 0%, #fce4ec 50%, #f3e5f5 100%) !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── title ── */
.fitfindr-title {
    text-align: center;
    padding: 2rem 1rem 0.5rem;
}
.fitfindr-title h1 {
    font-family: 'DM Serif Display', serif !important;
    font-size: 3rem !important;
    color: #5c2d6e !important;
    letter-spacing: -0.5px;
    margin-bottom: 0.25rem;
}
.fitfindr-title p {
    color: #9c6aab;
    font-size: 1rem;
    font-weight: 300;
}

/* ── cards / panels ── */
.gr-box, .gr-form, .gr-panel,
div[class*="block"], div[class*="panel"] {
    background: rgba(255,255,255,0.72) !important;
    border: 1px solid #f0d6f5 !important;
    border-radius: 18px !important;
    backdrop-filter: blur(8px);
}

/* ── textboxes ── */
textarea, input[type="text"] {
    background: rgba(255,255,255,0.9) !important;
    border: 1.5px solid #e8b4f0 !important;
    border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    color: #3d1a4f !important;
    transition: border-color 0.2s ease;
}
textarea:focus, input[type="text"]:focus {
    border-color: #b469cc !important;
    box-shadow: 0 0 0 3px rgba(180,105,204,0.15) !important;
}

/* ── labels ── */
label span, .gr-form label {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    color: #7b3fa0 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.3px;
    text-transform: uppercase;
}

/* ── submit button ── */
button.primary {
    background: linear-gradient(135deg, #b469cc, #e880a0) !important;
    border: none !important;
    border-radius: 50px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 1rem !important;
    color: white !important;
    padding: 0.65rem 2.5rem !important;
    letter-spacing: 0.3px;
    transition: opacity 0.2s ease, transform 0.1s ease;
    box-shadow: 0 4px 15px rgba(180,105,204,0.35);
}
button.primary:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px);
}
button.primary:active {
    transform: translateY(0px);
}

/* ── radio buttons ── */
input[type="radio"] + span {
    color: #7b3fa0 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── examples section ── */
.gr-samples-table {
    background: rgba(255,255,255,0.5) !important;
    border-radius: 12px !important;
}
.gr-sample-textbox {
    color: #9c5db5 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── output panel text ── */
.gr-textbox textarea[readonly] {
    color: #3d1a4f !important;
    line-height: 1.7 !important;
    font-size: 0.92rem !important;
}

/* ── scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #d4a0e0; border-radius: 10px; }
"""

def build_interface():
    with gr.Blocks(title="FitFindr ✨", css=custom_css) as demo:

        gr.HTML("""
        <div class="fitfindr-title">
            <h1>✨ FitFindr</h1>
            <p>Describe what you're looking for, we'll style it for you</p>
        </div>
        """)

        with gr.Row():
            query_input = gr.Textbox(
                label="What are you looking for?",
                placeholder="e.g. vintage graphic tee under $30, size M  🛍️",
                lines=2,
                scale=3,
            )
            wardrobe_choice = gr.Radio(
                choices=["Example wardrobe", "Empty wardrobe (new user)"],
                value="Example wardrobe",
                label="Wardrobe",
                scale=1,
            )

        submit_btn = gr.Button("Find my fit ✨", variant="primary")

        with gr.Row():
            listing_output = gr.Textbox(
                label="🛍️  Top listing found",
                lines=9,
                interactive=False,
            )
            outfit_output = gr.Textbox(
                label="👗  Outfit idea",
                lines=9,
                interactive=False,
            )
            fitcard_output = gr.Textbox(
                label="💌  Your fit card",
                lines=9,
                interactive=False,
            )

        gr.Examples(
            examples=[[q, "Example wardrobe"] for q in EXAMPLE_QUERIES],
            inputs=[query_input, wardrobe_choice],
            label="✦  Try these searches",
        )

        submit_btn.click(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[listing_output, outfit_output, fitcard_output],
        )
        query_input.submit(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[listing_output, outfit_output, fitcard_output],
        )

    return demo


if __name__ == "__main__":
    demo = build_interface()
    demo.launch()