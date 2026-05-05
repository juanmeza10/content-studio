import os
import json
import re
from datetime import datetime
from typing import Optional
import anthropic
from dotenv import load_dotenv

load_dotenv()


STRATEGIST_PROMPT = """You are a senior brand strategist. Analyze the brand and write a tight creative brief \
that a copywriter will use to generate ad copy.

Structure your brief with exactly these sections:

Brand Essence: One sentence capturing what this brand truly stands for.

Audience Insight: What the target customer deeply wants, fears, or aspires to — go beyond demographics.

Key Differentiator: The one thing that makes this brand impossible to ignore or replace.

Tone Direction: 3–5 adjectives followed by a single sentence describing the brand's voice in action.

Campaign Angles: Three distinct creative directions worth exploring, each with a one-line rationale.

Be concrete and specific to this brand. Every line must give the copywriter something real to work with."""

COPYWRITER_PROMPT = """You are an expert advertising copywriter specializing in social media ads.
Your job is to generate 5 distinct ad copies for a brand, each using a different sell angle.

For each ad copy, provide:
1. The sell angle name (e.g. FOMO, Curiosity Hook, Social Proof, Aspiration, Pain-Solution, etc.)
2. The ad copy itself — 1-2 punchy sentences, ready to post
3. A brief explanation of why this angle works specifically for this brand

Format your response exactly like this for each of the 5 ideas:

IDEA [N]  |  Angle: [ANGLE NAME]

  "[AD COPY]"

  Why this works:
  [EXPLANATION]

────────────────────────────────────────────────────────────

Make each angle genuinely distinct. Draw on the brand's unique value proposition, tone,
target audience, and pain point to make every copy feel tailor-made — not generic."""

BRANDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brands")


# ── Brand storage ─────────────────────────────────────────────────────────────

def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def brand_path(brand_name: str) -> str:
    return os.path.join(BRANDS_DIR, f"{slug(brand_name)}.json")


def list_brands() -> list[dict]:
    if not os.path.isdir(BRANDS_DIR):
        return []
    brands = []
    for fname in sorted(os.listdir(BRANDS_DIR)):
        if fname.endswith(".json"):
            with open(os.path.join(BRANDS_DIR, fname), encoding="utf-8") as f:
                brands.append(json.load(f))
    return brands


def load_brand(brand_name: str) -> Optional[dict]:
    path = brand_path(brand_name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_brand(info: dict) -> None:
    os.makedirs(BRANDS_DIR, exist_ok=True)
    with open(brand_path(info["brand_name"]), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)


# ── Interactive brand collection ───────────────────────────────────────────────

def prompt_new_brand() -> Optional[dict]:
    print("Fill in your brand details (all fields required).\n")
    fields = [
        ("brand_name", "Brand name: "),
        ("what_sells",  "What you sell and what makes it unique:\n   "),
        ("tone",        "Brand personality/tone (e.g. bold, playful, premium):\n   "),
        ("audience",    "Target audience:\n   "),
        ("pain_point",  "Main pain point your brand solves:\n   "),
        ("language",    "Preferred language for ad copies (e.g. English, Spanish):\n   "),
    ]
    info = {}
    for key, label in fields:
        value = input(label).strip()
        if not value:
            print("Error: This field cannot be empty.")
            return None
        info[key] = value
        print()
    return info


def select_or_create_brand() -> Optional[dict]:
    brands = list_brands()

    if brands:
        print("Saved brands:\n")
        for i, b in enumerate(brands, 1):
            print(f"  [{i}] {b['brand_name']}  —  {b['tone']} · {b['language']}")
        print(f"  [N] Create a new brand\n")

        choice = input("Select a number or N: ").strip().lower()
        if choice == "n":
            pass  # fall through to creation
        elif choice.isdigit() and 1 <= int(choice) <= len(brands):
            return brands[int(choice) - 1]
        else:
            print("Invalid choice.")
            return None

    print()
    info = prompt_new_brand()
    if info is None:
        return None

    save_brand(info)
    print(f"Brand '{info['brand_name']}' saved.\n")
    return info


# ── Ad copy generation ─────────────────────────────────────────────────────────

def _stream_claude(system: str, user: str, max_tokens: int, echo: bool) -> str:
    client = anthropic.Anthropic()
    chunks = []
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
    ) as stream:
        for text in stream.text_stream:
            if echo:
                print(text, end="", flush=True)
            chunks.append(text)
    return "".join(chunks)


def generate_ad_copies(info: dict, echo: bool = True) -> str:
    _div = "═" * 60

    # ── Step 1: Brand strategist writes the creative brief ──────────────────
    if echo:
        print(f"{_div}\nSTEP 1 — BRAND STRATEGIST\n{_div}\n")

    brief = _stream_claude(
        system=STRATEGIST_PROMPT,
        user=(
            f"Write a creative brief for this brand. "
            f"Write the brief in {info['language']}.\n\n"
            f"Brand: {info['brand_name']}\n"
            f"What they sell: {info['what_sells']}\n"
            f"Tone: {info['tone']}\n"
            f"Audience: {info['audience']}\n"
            f"Pain point: {info['pain_point']}"
        ),
        max_tokens=768,
        echo=echo,
    )

    # ── Step 2: Copywriter uses the brief to write ad copies ────────────────
    if echo:
        print(f"\n\n{_div}\nSTEP 2 — COPYWRITER\n{_div}\n")

    copy = _stream_claude(
        system=COPYWRITER_PROMPT,
        user=(
            f"Generate 5 ad copies for this brand. "
            f"Write everything — the ad copies, angle names, and explanations — in {info['language']}.\n\n"
            f"Brand name: {info['brand_name']}\n"
            f"What they sell / what makes them unique: {info['what_sells']}\n"
            f"Brand personality/tone: {info['tone']}\n"
            f"Target audience: {info['audience']}\n"
            f"Main pain point they solve: {info['pain_point']}\n\n"
            f"Creative Brief:\n{brief}"
        ),
        max_tokens=2048,
        echo=echo,
    )

    return (
        f"{_div}\nCREATIVE BRIEF\n{_div}\n\n"
        f"{brief}\n\n"
        f"{_div}\nAD COPY IDEAS\n{_div}\n\n"
        f"{copy}"
    )


# ── Output saving ──────────────────────────────────────────────────────────────

def get_output_path(brand_name: str) -> str:
    folder = os.path.expanduser(f"~/Desktop/{slug(brand_name)}-copy")
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%I-%M%p").lower()
    return os.path.join(folder, f"copy_{timestamp}.txt")


def save_output(text: str, info: dict, path: str) -> None:
    header = (
        f"Brand:     {info['brand_name']}\n"
        f"Language:  {info['language']}\n"
        f"Generated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}\n"
        f"{'─' * 60}\n\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + text)


# ── Main ───────────────────────────────────────────────────────────────────────

def print_divider():
    print("\n" + "─" * 60 + "\n")


def main():
    print("=" * 60)
    print("           CONTENT STUDIO")
    print("=" * 60)
    print()

    info = select_or_create_brand()
    if info is None:
        return

    print_divider()
    print(f"  Brand:     {info['brand_name']}")
    print(f"  Tone:      {info['tone']}")
    print(f"  Audience:  {info['audience']}")
    print(f"  Language:  {info['language']}")
    print_divider()
    print("Generating your custom ad copies...\n")

    output_path = get_output_path(info["brand_name"])
    try:
        output_text = generate_ad_copies(info)
        save_output(output_text, info, output_path)
    except anthropic.AuthenticationError:
        print("\nError: Invalid or missing ANTHROPIC_API_KEY.")
        return
    except anthropic.APIConnectionError:
        print("\nError: Could not connect to the Anthropic API.")
        return
    except anthropic.APIStatusError as e:
        print(f"\nAPI error ({e.status_code}): {e.message}")
        return

    print_divider()
    print(f"  Saved to: {output_path}")
    print("\nRun the script again for a fresh set of ideas.\n")


if __name__ == "__main__":
    main()
