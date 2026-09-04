# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: Iteratively built/refined across 8 sessions (2026-06-24 to 2026-07-04) -- fixing broken links, adding CSV export, freezing events/networking into a toggle, project rename, UI load-time/like-dislike-button fixes -- see docs/ai_usage/prompt_log.md#src-pipeline-ui-apppy for full text
# Usage: Streamlit UI: search/browse, tag filters, digest view, score histograms, save/not-interested workflow buttons, events toggle, performance fixes
# -------------------------------------------------------------------------

"""Streamlit dashboard. Run as: streamlit run src/pipeline/ui/app.py
Reads directly from the SQLite DB -- no caching of stale state beyond
Streamlit's own rerun model.
"""
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo/src on path

import pandas as pd
import streamlit as st

from pipeline.storage.db import get_connection

st.set_page_config(page_title="Jobs Pipeline", layout="wide", initial_sidebar_state="expanded")


UI_COLUMNS = [
    "id", "source", "url", "title", "SUBSTR(raw_text, 1, 1000) AS raw_text",
    "category", "seniority", "engagement_type", "spam_risk", "deadline",
    "role_expectation_notes", "feedback", "application_status",
    "not_interested_reason", "preference_score", "urgency_score", "general_score",
]

PAGE_SIZE = 20

# Fixed one-click reasons for "Not Interested", plus a free-text "Other" --
# kept as short stable labels (not full sentences) so later per-source
# analysis can GROUP BY this column meaningfully.
NOT_INTERESTED_REASONS = [
    ("Too Senior", "too_senior"),
    ("Too Junior", "too_junior"),
    ("Unrelated Field", "unrelated_field"),
    ("Bad Location", "bad_location"),
    ("Low Pay/Engagement", "low_pay_or_engagement"),
]

# Editorial/terminal direction: light paper background, ink text, one
# restrained accent (used only for the primary action and score figures).
# Deliberately avoids colored pill badges / dark glassmorphism -- see
# HISTORY.md UI redesign entry for why.
INK = "#1a1a18"
INK_SECONDARY = "#5c5b56"
INK_MUTED = "#9c9a92"
PAPER = "#fbfaf7"
PAPER_RAISED = "#f3f1ec"
RULE = "#ddd9d0"
ACCENT = "#8a3324"  # muted brick -- reads as "trade tool," not "SaaS product"
STATUS_WARN = "#a06a00"
STATUS_CRITICAL = "#a02418"

CUSTOM_CSS = f"""
<style>
html, body, [class*="css"] {{
    font-family: Georgia, "Iowan Old Style", "Times New Roman", serif;
}}
.stApp {{
    background: {PAPER};
}}
[data-testid="stSidebar"] {{
    background: {PAPER_RAISED};
    border-right: 1px solid {RULE};
}}

/* Monospace for anything numeric / identifier-like */
.mono {{
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}}

.block-container {{
    padding-top: 1.75rem;
    padding-bottom: 2rem;
    max-width: 1180px;
}}

h1 {{
    font-weight: 400;
    letter-spacing: -0.01em;
    color: {INK};
    border-bottom: 2px solid {INK};
    padding-bottom: 0.4rem;
}}
h3, .stTabs [aria-selected="true"] {{
    color: {INK};
}}
p, span, div, label {{
    color: {INK};
}}

/* Masthead stat strip -- plain numbers over a rule, not tiles */
.stat-strip {{
    display: flex;
    gap: 2.5rem;
    padding: 0.6rem 0 1rem 0;
    border-bottom: 1px solid {RULE};
    margin-bottom: 1.2rem;
}}
.stat-item {{ text-align: left; }}
.stat-value {{
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 1.3rem;
    font-weight: 700;
    color: {INK};
}}
.stat-label {{
    font-size: 0.72rem;
    color: {INK_MUTED};
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}

/* Item row -- ruled list, not floating cards */
.item-row {{
    padding: 14px 0;
    border-bottom: 1px solid {RULE};
}}
.item-title {{
    font-size: 1.08rem;
    font-weight: 700;
    color: {INK};
    margin-bottom: 3px;
    line-height: 1.3;
}}
.item-tags {{
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 0.74rem;
    color: {INK_SECONDARY};
    text-transform: uppercase;
    letter-spacing: 0.03em;
    margin-bottom: 5px;
}}
.item-tags .score {{
    color: {ACCENT};
    font-weight: 700;
}}
.item-tags .flag-warn {{ color: {STATUS_WARN}; font-weight: 700; }}
.item-tags .flag-critical {{ color: {STATUS_CRITICAL}; font-weight: 700; }}
.item-meta {{
    color: {INK_MUTED};
    font-size: 0.8rem;
    margin-bottom: 5px;
}}
.item-meta a {{
    color: {INK_SECONDARY};
}}
.item-note {{
    color: {INK_SECONDARY};
    font-size: 0.85rem;
    font-style: italic;
    margin-bottom: 4px;
}}

/* Buttons -- flat, square, text-first */
.stButton > button, .stDownloadButton > button, .stPopover > button {{
    border-radius: 3px;
    border: 1px solid {INK};
    background: {PAPER};
    color: {INK};
    font-size: 0.82rem;
    padding: 0.25rem 0.7rem;
}}
.stButton > button:hover, .stDownloadButton > button:hover, .stPopover > button:hover {{
    background: {INK};
    color: {PAPER};
    border-color: {INK};
}}
.stButton > button[kind="primary"] {{
    background: {ACCENT};
    border-color: {ACCENT};
    color: {PAPER};
}}
.stButton > button[kind="primary"]:hover {{
    background: {INK};
    border-color: {INK};
}}
.stButton > button p, .stDownloadButton > button p, .stPopover > button p {{
    color: inherit;
}}

hr {{ border-color: {RULE}; }}
</style>
"""

@st.cache_data(ttl=30)
def load_items() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT {', '.join(UI_COLUMNS)} FROM items", conn)
    conn.close()
    return df


def set_application_status(item_id: int, status: str | None, reason: str | None = None) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE items SET application_status=?, not_interested_reason=?, status_updated_at=? WHERE id=?",
        (status, reason, datetime.now(timezone.utc).isoformat(), item_id),
    )
    conn.commit()
    conn.close()
    # Patch the session-stored DataFrame in place instead of clearing the
    # cache -- avoids re-querying all ~29k rows from SQLite on every click.
    mask = st.session_state.items_df["id"] == item_id
    st.session_state.items_df.loc[mask, "application_status"] = status
    st.session_state.items_df.loc[mask, "not_interested_reason"] = reason


def stat_item(label: str, value: str) -> str:
    return f"""<div class="stat-item"><div class="stat-value">{value}</div>
    <div class="stat-label">{label}</div></div>"""


def render_item(row: pd.Series, sort_by: str, key_prefix: str = "") -> None:
    title = row["title"] if pd.notna(row["title"]) else row["raw_text"][:80]
    item_id = int(row["id"])
    item_url = row["url"]

    tag_parts = []
    if pd.notna(row["category"]):
        tag_parts.append(str(row["category"]))
    if pd.notna(row["seniority"]):
        tag_parts.append(str(row["seniority"]))
    if pd.notna(row["engagement_type"]):
        tag_parts.append(str(row["engagement_type"]))
    if pd.notna(row.get(sort_by)):
        tag_parts.append(f'<span class="score">{sort_by.replace("_", " ")} {row[sort_by]:.1f}</span>')
    if sort_by == "urgency_score" and pd.notna(row.get("deadline")):
        tag_parts.append(f'<span class="score">deadline {row["deadline"]}</span>')
    if row.get("spam_risk") == "likely_spam":
        tag_parts.append('<span class="flag-critical">! likely spam</span>')
    elif row.get("spam_risk") == "suspicious":
        tag_parts.append('<span class="flag-warn">! suspicious</span>')

    note_html = ""
    if pd.notna(row.get("role_expectation_notes")):
        note_html = f'<div class="item-note">{row["role_expectation_notes"]}</div>'

    st.markdown(
        f"""<div class="item-row">
            <div class="item-title">{title}</div>
            <div class="item-tags">{' &nbsp;/&nbsp; '.join(tag_parts)}</div>
            <div class="item-meta">{row['source']} &middot; <a href="{item_url}" target="_blank">{item_url}</a></div>
            {note_html}
        </div>""",
        unsafe_allow_html=True,
    )

    with st.expander("Details"):
        st.write(row["raw_text"][:1000])

    status = row.get("application_status")

    action_cols = st.columns([1, 1, 1, 1, 1])

    with action_cols[0]:
        if status == "saved":
            if st.button("Unsave", key=f"{key_prefix}unsave_{item_id}"):
                set_application_status(item_id, None, None)
        elif status not in ("not_interested", "applied", "callback", "interview", "offer"):
            if st.button("Save", key=f"{key_prefix}save_{item_id}"):
                set_application_status(item_id, "saved")

    with action_cols[1]:
        if status == "applied":
            if st.button("Unapply", key=f"{key_prefix}unapply_{item_id}"):
                set_application_status(item_id, None, None)
        elif status in ("callback", "interview", "offer"):
            st.caption(f"Applied ({status})")
        elif status != "not_interested":
            if st.button("Apply", key=f"{key_prefix}apply_{item_id}", type="primary"):
                set_application_status(item_id, "applied")
                st.toast(
                    "Marked as applied. Agentic/assisted application flow is not built yet -- "
                    "this just records status for now."
                )

    with action_cols[2]:
        if st.button("Research", key=f"{key_prefix}research_{item_id}"):
            st.session_state[f"{key_prefix}show_research_{item_id}"] = True

    with action_cols[3]:
        with st.popover("Share"):
            subject = urllib.parse.quote(f"Job lead: {title}")
            body = urllib.parse.quote(f"{title}\n{item_url}")
            st.markdown(f"[Email]({f'mailto:?subject={subject}&body={body}'})")
            st.markdown(f"[Telegram](https://t.me/share/url?url={urllib.parse.quote(item_url)}&text={urllib.parse.quote(title)})")
            st.code(item_url, language=None)

    with action_cols[4]:
        if status == "not_interested":
            reason = row.get("not_interested_reason") or "unspecified"
            st.caption(f"Not interested ({reason})")
            if st.button("Undo", key=f"{key_prefix}undo_ni_{item_id}"):
                set_application_status(item_id, None, None)
        elif status not in ("applied", "callback", "interview", "offer"):
            with st.popover("Not Interested"):
                for label, reason_code in NOT_INTERESTED_REASONS:
                    if st.button(label, key=f"{key_prefix}ni_{reason_code}_{item_id}"):
                        set_application_status(item_id, "not_interested", reason_code)
                        st.rerun(scope="fragment")
                other_reason = st.text_input("Other reason", key=f"{key_prefix}ni_other_text_{item_id}")
                if st.button("Submit", key=f"{key_prefix}ni_other_submit_{item_id}"):
                    set_application_status(item_id, "not_interested", f"other: {other_reason}" if other_reason else "other")
                    st.rerun(scope="fragment")

    if st.session_state.get(f"{key_prefix}show_research_{item_id}"):
        st.info(
            "Research (stub): future work will gather founder background, company "
            "stage/funding, industry niche, and culture signals here, and produce an "
            "upside/fit assessment. Not implemented yet -- see TODO.md."
        )


def render_browse_filters(df: pd.DataFrame) -> dict:
    with st.sidebar:
        st.markdown("### Filters")
        search = st.text_input("Search title/text")
        categories = ["(any)"] + sorted(df["category"].dropna().unique().tolist())
        category = st.selectbox("Category", categories)
        seniorities = ["(any)"] + sorted(df["seniority"].dropna().unique().tolist())
        seniority = st.selectbox("Seniority", seniorities)
        engagement_types = ["(any)"] + sorted(df["engagement_type"].dropna().unique().tolist())
        engagement_type = st.selectbox("Engagement type", engagement_types)
        sort_by = st.selectbox(
            "Sort by",
            ["preference_score", "urgency_score", "general_score"],
            format_func=lambda s: s.replace("_", " ").title(),
        )
        hide_spam = st.checkbox("Hide suspicious/spam", value=True)
        show_not_interested = st.checkbox(
            "Show items marked Not Interested",
            value=False,
            help="In case you hit the button by accident and need to find/undo it.",
        )
    return {
        "search": search,
        "category": category,
        "seniority": seniority,
        "engagement_type": engagement_type,
        "sort_by": sort_by,
        "hide_spam": hide_spam,
        "show_not_interested": show_not_interested,
    }


@st.fragment
def render_browse_tab(df: pd.DataFrame, filters: dict) -> None:
    search = filters["search"]
    category = filters["category"]
    seniority = filters["seniority"]
    engagement_type = filters["engagement_type"]
    sort_by = filters["sort_by"]
    hide_spam = filters["hide_spam"]
    show_not_interested = filters["show_not_interested"]

    filtered = df
    if not show_not_interested:
        filtered = filtered[filtered["application_status"] != "not_interested"]
    if search:
        mask = (
            filtered["title"].fillna("").str.contains(search, case=False, regex=False)
            | filtered["raw_text"].fillna("").str.contains(search, case=False, regex=False)
        )
        filtered = filtered[mask]
    if category != "(any)":
        filtered = filtered[filtered["category"] == category]
    if seniority != "(any)":
        filtered = filtered[filtered["seniority"] == seniority]
    if engagement_type != "(any)":
        filtered = filtered[filtered["engagement_type"] == engagement_type]
    if hide_spam and "spam_risk" in filtered.columns:
        filtered = filtered[~filtered["spam_risk"].isin(["suspicious", "likely_spam"])]
    filtered = filtered.sort_values(sort_by, ascending=False, na_position="last")

    cap_col, dl_col = st.columns([6, 1])
    with cap_col:
        st.caption(f"{len(filtered)} of {len(df)} items")
    with dl_col:
        st.download_button(
            "Download CSV",
            filtered.to_csv(index=False),
            file_name="opportunity_pipeline_export.csv",
            mime="text/csv",
        )

    page_key = "browse_page"
    if page_key not in st.session_state:
        st.session_state[page_key] = 0
    n_pages = max(1, (len(filtered) - 1) // PAGE_SIZE + 1)
    page = min(st.session_state[page_key], n_pages - 1)

    page_slice = filtered.iloc[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]
    for _, row in page_slice.iterrows():
        render_item(row, sort_by, key_prefix="browse_")

    prev_col, label_col, next_col = st.columns([1, 4, 1])
    with prev_col:
        if st.button("← Prev", key="browse_prev", disabled=page <= 0):
            st.session_state[page_key] = page - 1
            st.rerun(scope="fragment")
    with label_col:
        st.caption(f"Page {page + 1} of {n_pages}")
    with next_col:
        if st.button("Next →", key="browse_next", disabled=page >= n_pages - 1):
            st.session_state[page_key] = page + 1
            st.rerun(scope="fragment")


@st.fragment
def render_saved_tab(df: pd.DataFrame) -> None:
    saved_items = df[df["application_status"] == "saved"]
    st.caption(f"{len(saved_items)} saved item(s)")
    if saved_items.empty:
        st.info("No saved items yet. Use the Save button on an item in Browse.")
        return
    saved_sorted = saved_items.sort_values("preference_score", ascending=False, na_position="last")
    for _, row in saved_sorted.iterrows():
        render_item(row, "preference_score", key_prefix="saved_")


@st.fragment
def render_metrics_tab(df: pd.DataFrame) -> None:
    tagged = df[df["category"].notna() & (df["category"] != "irrelevant")]
    if tagged.empty:
        st.info("No tagged items yet to build metrics from.")
        return
    st.subheader("Score distribution")
    digest_sort = st.selectbox(
        "Metrics sort/distribution field",
        ["preference_score", "urgency_score", "general_score"],
        format_func=lambda s: s.replace("_", " ").title(),
        key="digest_sort",
    )
    st.bar_chart(tagged[digest_sort].value_counts().sort_index())

    st.subheader("Top items")
    top = tagged.sort_values(digest_sort, ascending=False).head(20)
    display_cols = ["title", "category", "seniority", "engagement_type", digest_sort,
                     "spam_risk", "role_expectation_notes", "url"]
    if digest_sort == "urgency_score":
        display_cols.insert(display_cols.index(digest_sort) + 1, "deadline")
    st.dataframe(
        top[display_cols],
        width="stretch",
        column_config={"url": st.column_config.LinkColumn("url")},
    )
    st.download_button(
        "Download CSV",
        top.to_csv(index=False),
        file_name="opportunity_pipeline_digest.csv",
        mime="text/csv",
    )


st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

if "items_df" not in st.session_state:
    st.session_state.items_df = load_items()
df = st.session_state.items_df

st.title("Jobs Pipeline")

if df.empty:
    st.warning("No items in the database yet. Run `python -m pipeline.ingest` first.")
    st.stop()

n_tagged = df["category"].notna().sum()
if n_tagged == 0:
    st.info(
        f"{len(df)} items ingested, but none are tagged yet (LLM tagger needs "
        "ANTHROPIC_API_KEY in .env). Showing raw untagged items below; run "
        "`python -m pipeline.tagger.run_tagging` once a key is set."
    )

show_events = st.sidebar.checkbox("Show events & networking", value=True)
if not show_events:
    df = df[~df["category"].isin(["event", "networking"])]

n_saved = int((df["application_status"] == "saved").sum())
n_new = int(df["application_status"].isna().sum())

st.markdown(
    f"""<div class="stat-strip">
        {stat_item("Total items", f"{len(df):,}")}
        {stat_item("Tagged", f"{n_tagged:,}")}
        {stat_item("Saved", f"{n_saved:,}")}
        {stat_item("Untriaged", f"{n_new:,}")}
    </div>""",
    unsafe_allow_html=True,
)

browse_filters = render_browse_filters(df)

tab_browse, tab_saved, tab_metrics = st.tabs(["Browse", "Saved", "Metrics"])

with tab_browse:
    render_browse_tab(df, browse_filters)

with tab_saved:
    render_saved_tab(df)

with tab_metrics:
    render_metrics_tab(df)
