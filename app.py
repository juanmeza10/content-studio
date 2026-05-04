import sys
import os
import re
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content_studio import (
    list_brands, save_brand, generate_ad_copies,
    get_output_path, save_output,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def parse_ideas(text: str) -> list[dict]:
    sections = re.split(r"─{10,}", text)
    ideas = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        angle_match = re.search(r"Angle:\s*(.+)", section)
        copy_match = re.search(r'"(.+?)"', section, re.DOTALL)
        why_match = re.search(r"Why this works:[ \t]*\n?([\s\S]+)", section)
        if angle_match and copy_match:
            ideas.append({
                "angle": angle_match.group(1).strip(),
                "copy": copy_match.group(1).strip(),
                "why": why_match.group(1).strip() if why_match else "",
            })
    return ideas


# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Content Studio", page_icon="✦", layout="wide")

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ✦ Content Studio")
    st.divider()

    brands = list_brands()
    brand_map = {b["brand_name"]: b for b in brands}
    options = ["➕ Create New Brand"] + list(brand_map.keys())

    selected = st.selectbox("Brand", options, key="brand_selector")
    st.divider()

    is_new = selected == "➕ Create New Brand"
    existing = {} if is_new else brand_map[selected]

    st.subheader("New Brand" if is_new else f"Edit: {selected}")

    with st.form("brand_form", clear_on_submit=is_new):
        brand_name = st.text_input("Brand name", value=existing.get("brand_name", ""))
        what_sells = st.text_area(
            "What you sell & what makes it unique",
            value=existing.get("what_sells", ""),
            height=80,
        )
        tone = st.text_input(
            "Brand tone (e.g. bold, playful, premium)",
            value=existing.get("tone", ""),
        )
        audience = st.text_input("Target audience", value=existing.get("audience", ""))
        pain_point = st.text_area(
            "Main pain point your brand solves",
            value=existing.get("pain_point", ""),
            height=80,
        )
        language = st.text_input(
            "Preferred language",
            value=existing.get("language", "English"),
        )

        submitted = st.form_submit_button(
            "Save Brand" if is_new else "Update Brand",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        if not all([brand_name, what_sells, tone, audience, pain_point, language]):
            st.error("All fields are required.")
        else:
            info = {
                "brand_name": brand_name,
                "what_sells": what_sells,
                "tone": tone,
                "audience": audience,
                "pain_point": pain_point,
                "language": language,
            }
            save_brand(info)
            st.success(f"{'Saved' if is_new else 'Updated'}: {brand_name}")
            st.rerun()


# ── Main area ──────────────────────────────────────────────────────────────────

if is_new:
    st.markdown("### Welcome to Content Studio")
    st.info("Create your first brand profile in the sidebar to get started.")
    st.stop()

brand = brand_map[selected]

col1, col2, col3 = st.columns(3)
col1.metric("Brand", brand["brand_name"])
col2.metric("Tone", brand["tone"])
col3.metric("Language", brand["language"])

with st.expander("Brand details"):
    st.markdown(f"**What they sell:** {brand['what_sells']}")
    st.markdown(f"**Target audience:** {brand['audience']}")
    st.markdown(f"**Pain point:** {brand['pain_point']}")

st.divider()

if st.button("✦ Generate Ad Copy", type="primary", use_container_width=True):
    with st.spinner("Writing your ad copies..."):
        raw_text = generate_ad_copies(brand)
        output_path = get_output_path(brand["brand_name"])
        save_output(raw_text, brand, output_path)
        st.session_state.ideas = parse_ideas(raw_text)
        st.session_state.output_path = output_path
        st.session_state.generated_for = brand["brand_name"]

# ── Results ────────────────────────────────────────────────────────────────────

if (
    st.session_state.get("ideas")
    and st.session_state.get("generated_for") == brand["brand_name"]
):
    st.success(f"Saved to `{st.session_state.output_path}`")
    st.subheader("Ad Copy Ideas")

    for i, idea in enumerate(st.session_state.ideas, 1):
        with st.container(border=True):
            st.markdown(f"**Idea {i} — {idea['angle']}**")
            st.markdown(f"> {idea['copy']}")
            with st.expander("Why this works"):
                st.markdown(idea["why"])
