import os
from typing import Optional
import anthropic


SYSTEM_PROMPT = """You are an expert advertising copywriter specializing in social media ads.
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


def print_divider():
    print("\n" + "─" * 60 + "\n")


def ask_language() -> Optional[str]:
    print("=" * 60)
    print("       SOCIAL MEDIA AD COPY GENERATOR")
    print("=" * 60)
    print()
    language = input("What language do you want the ad copies in? (e.g. English, Spanish, French):\n   ").strip()
    if not language:
        print("Error: This field cannot be empty.")
        return None
    print()
    return language


def collect_brand_info() -> Optional[dict]:
    print("Answer 5 questions and Claude will generate custom ad")
    print("copy tailored to your brand.\n")

    fields = [
        ("brand_name",  "1. Brand name: "),
        ("what_sells",  "2. What you sell and what makes it unique:\n   "),
        ("tone",        "3. Brand personality/tone (e.g. bold, playful, premium):\n   "),
        ("audience",    "4. Target audience:\n   "),
        ("pain_point",  "5. Main pain point your brand solves:\n   "),
    ]

    info = {}
    for key, prompt in fields:
        value = input(prompt).strip()
        if not value:
            print("Error: This field cannot be empty.")
            return None
        info[key] = value
        print()

    return info


def generate_ad_copies(info: dict, language: str) -> None:
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment

    user_message = (
        f"Generate 5 ad copies for this brand. Write everything — the ad copies, angle names, and explanations — in {language}.\n\n"
        f"Brand name: {info['brand_name']}\n"
        f"What they sell / what makes them unique: {info['what_sells']}\n"
        f"Brand personality/tone: {info['tone']}\n"
        f"Target audience: {info['audience']}\n"
        f"Main pain point they solve: {info['pain_point']}"
    )

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)


def main():
    language = ask_language()
    if language is None:
        return

    info = collect_brand_info()
    if info is None:
        return

    print_divider()
    print(f"  Brand:      {info['brand_name']}")
    print(f"  Tone:       {info['tone']}")
    print(f"  Audience:   {info['audience']}")
    print(f"  Language:   {language}")
    print_divider()
    print("Generating your custom ad copies...\n")

    try:
        generate_ad_copies(info, language)
    except anthropic.AuthenticationError:
        print("\nError: Invalid or missing ANTHROPIC_API_KEY.")
    except anthropic.APIConnectionError:
        print("\nError: Could not connect to the Anthropic API.")
    except anthropic.APIStatusError as e:
        print(f"\nAPI error ({e.status_code}): {e.message}")

    print_divider()
    print("Run the script again for a fresh set of ideas.\n")


if __name__ == "__main__":
    main()
