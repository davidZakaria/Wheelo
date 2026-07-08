import random

import pandas as pd
import streamlit as st

from apify_fetch import fetch_facebook_comments, fetch_instagram_comments
from contestants_loader import load_contestants, save_enriched_winners
from filtering import (
    build_contestants,
    normalize_facebook_df,
    normalize_instagram_df,
    normalize_uploaded_df,
)
from roulette import render_roulette

st.set_page_config(
    page_title="Green Avenue · Live Roulette",
    page_icon="🎡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700;900&family=Outfit:wght@300;500;700&display=swap');
    .stApp {
        background:
            radial-gradient(circle at top, rgba(36,92,63,0.25), transparent 35%),
            linear-gradient(180deg, #040a07 0%, #07150f 45%, #040805 100%);
        color: #f5f0e1;
        font-family: 'Outfit', sans-serif;
    }
    .block-container { padding-top: 1.2rem; max-width: 1200px; }
    h1, h2, h3 {
        font-family: 'Cinzel', serif !important;
        color: #d4af37 !important;
        letter-spacing: 0.08em;
    }
    .hero {
        text-align: center;
        padding: 0.5rem 0 1.2rem;
    }
    .hero p {
        color: #c8be9d;
        font-size: 1.05rem;
        margin-top: -0.4rem;
    }
    .metric-card {
        background: linear-gradient(145deg, rgba(18,42,30,0.9), rgba(8,18,13,0.95));
        border: 1px solid rgba(212,175,55,0.25);
        border-radius: 18px;
        padding: 16px 18px;
        text-align: center;
        box-shadow: 0 12px 30px rgba(0,0,0,0.25);
    }
    .metric-card h2 {
        margin: 0;
        font-size: 2rem !important;
    }
    .metric-card span {
        color: #b7aa84;
        font-size: 0.85rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    .finalist-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        gap: 12px;
        margin-top: 10px;
    }
    .finalist-card {
        background: rgba(10,24,17,0.85);
        border: 1px solid rgba(212,175,55,0.18);
        border-radius: 16px;
        padding: 10px 8px 12px;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .finalist-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 24px rgba(212,175,55,0.12);
    }
    .finalist-card img {
        width: 58px;
        height: 58px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid rgba(212,175,55,0.55);
        margin-bottom: 8px;
    }
    .finalist-card .name {
        font-size: 0.78rem;
        line-height: 1.2;
        color: #f4eedc;
        font-weight: 600;
    }
    .finalist-card .source {
        font-size: 0.65rem;
        color: #8fd6ad;
        margin-top: 4px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .stButton > button {
        background: linear-gradient(135deg, #f8e7b0 0%, #d4af37 45%, #9f7c16 100%) !important;
        color: #1d1404 !important;
        border: none !important;
        border-radius: 999px !important;
        font-family: 'Cinzel', serif !important;
        letter-spacing: 0.14em !important;
        text-transform: uppercase !important;
        font-weight: 700 !important;
        padding: 0.8rem 2rem !important;
        box-shadow: 0 10px 28px rgba(212,175,55,0.28) !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 14px 34px rgba(212,175,55,0.36) !important;
    }
    div[data-testid="stExpander"] {
        background: rgba(8,18,13,0.75);
        border: 1px solid rgba(212,175,55,0.15);
        border-radius: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "contestants" not in st.session_state:
    save_enriched_winners()
    st.session_state["contestants"] = load_contestants()

if "spin_id" not in st.session_state:
    st.session_state["spin_id"] = 0

contestants = st.session_state["contestants"]

st.markdown(
    """
    <div class="hero">
        <h1>Green Avenue Live Roulette</h1>
        <p>Twenty-three finalists. One property. One spin decides it all.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        f'<div class="metric-card"><span>Finalists</span><h2>{len(contestants)}</h2></div>',
        unsafe_allow_html=True,
    )
with col2:
    fb_count = sum(1 for c in contestants if c.get("source") == "Facebook")
    st.markdown(
        f'<div class="metric-card"><span>Facebook</span><h2>{fb_count}</h2></div>',
        unsafe_allow_html=True,
    )
with col3:
    ig_count = sum(1 for c in contestants if c.get("source") == "Instagram")
    st.markdown(
        f'<div class="metric-card"><span>Instagram</span><h2>{ig_count}</h2></div>',
        unsafe_allow_html=True,
    )

st.markdown("### Finalists on the Wheel")

cards_html = ['<div class="finalist-grid">']
for person in contestants:
    avatar = person.get("avatar_url", "")
    name = person["username"]
    source = person.get("source", "")
    if avatar:
        img = f'<img src="{avatar}" alt="{name}" onerror="this.style.display=\'none\'" />'
    else:
        initial = name.strip()[:1].upper() or "?"
        img = (
            f'<div style="width:58px;height:58px;border-radius:50%;display:grid;place-items:center;'
            f'margin:0 auto 8px;background:#2f6a4d;border:2px solid rgba(212,175,55,0.55);'
            f'font-weight:700;">{initial}</div>'
        )
    cards_html.append(
        f'<div class="finalist-card">{img}<div class="name">{name}</div>'
        f'<div class="source">{source}</div></div>'
    )
cards_html.append("</div>")
st.markdown("".join(cards_html), unsafe_allow_html=True)

st.markdown("---")

if not contestants:
    st.error("No contestants found. Load or process winners first.")
else:
    launch_col, reset_col = st.columns([2, 1])
    with launch_col:
        launch = st.button("Launch Suspense Roulette", use_container_width=True)
    with reset_col:
        if st.button("Reload Finalists", use_container_width=True):
            st.session_state["contestants"] = load_contestants()
            st.session_state.pop("winner_index", None)
            st.rerun()

    if launch:
        st.session_state["winner_index"] = random.randrange(len(contestants))
        st.session_state["spin_id"] += 1

    if "winner_index" in st.session_state:
        st.markdown("### The Arena")
        render_roulette(
            contestants,
            st.session_state["winner_index"],
            st.session_state["spin_id"],
        )

with st.expander("Admin · Scrape & Filter Comments"):
    egypt_score = st.text_input("Egypt Score", value="2")
    arg_score = st.text_input("Argentina Score", value="3")
    fb_url = st.text_input(
        "Facebook Post URL",
        value="https://www.facebook.com/share/p/1JEXadnG8f/",
    )
    ig_url = st.text_input(
        "Instagram Post URL",
        value="https://www.instagram.com/p/DafbvzHoEd1/",
    )
    fb_max_comments = st.number_input("Max Facebook comments", 1, 50000, 27000)
    ig_max_comments = st.number_input("Max Instagram comments", 1, 50000, 800)
    uploaded_file = st.file_uploader(
        "Upload CSV / Excel",
        type=["csv", "xlsx", "xls"],
    )

    if st.button("Download & Process Comments"):
        normalized_dfs: list[pd.DataFrame] = []
        if fb_url:
            try:
                fb_df = fetch_facebook_comments(fb_url, max_comments=fb_max_comments)
                if not fb_df.empty:
                    normalized_dfs.append(normalize_facebook_df(fb_df))
            except Exception as exc:
                st.error(f"Facebook error: {exc}")
        if ig_url:
            try:
                ig_df = fetch_instagram_comments(ig_url, max_comments=ig_max_comments)
                if not ig_df.empty:
                    normalized_dfs.append(normalize_instagram_df(ig_df))
            except Exception as exc:
                st.error(f"Instagram error: {exc}")
        if uploaded_file is not None:
            try:
                upload_df = (
                    pd.read_csv(uploaded_file)
                    if uploaded_file.name.endswith(".csv")
                    else pd.read_excel(uploaded_file)
                )
                normalized_dfs.append(normalize_uploaded_df(upload_df))
            except Exception as exc:
                st.error(f"Upload error: {exc}")

        if normalized_dfs:
            winners_df, winner_count = build_contestants(
                normalized_dfs, egypt_score, arg_score
            )
            winners_df.to_csv("winners.csv", index=False, encoding="utf-8-sig")
            save_enriched_winners()
            st.session_state["contestants"] = load_contestants()
            st.success(f"Processed {winner_count} winners and refreshed the wheel.")
