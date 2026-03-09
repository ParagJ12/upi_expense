import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime
import io
import sys
import os

sys.path.append(os.path.dirname(__file__))
from parser import parse_uploaded_file
from normalizer import normalize_merchants
from categorizer import categorize_transactions
from sample_data import get_sample_data

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UPI Lens — Spending Intelligence",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg: #0f0f13;
    --surface: #17171f;
    --surface2: #1e1e28;
    --border: #2a2a38;
    --accent: #7c6af7;
    --accent2: #f97b6b;
    --accent3: #4fd1a5;
    --text: #e8e8f0;
    --muted: #7a7a92;
    --food: #f97b6b;
    --transport: #4fd1a5;
    --shopping: #7c6af7;
    --bills: #f9c56b;
    --entertainment: #f96bb0;
    --subscriptions: #6bcff9;
    --transfers: #c56bf9;
    --groceries: #6bf97c;
    --other: #999;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

.main { background: var(--bg); }
.block-container { padding: 2rem 3rem; max-width: 1400px; }

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* Hero header */
.hero {
    padding: 3rem 0 2rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}
.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 3.2rem;
    line-height: 1.1;
    background: linear-gradient(135deg, #e8e8f0 30%, #7c6af7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.hero-sub {
    color: var(--muted);
    font-size: 1.05rem;
    margin-top: 0.5rem;
    font-weight: 300;
}
.hero-badge {
    display: inline-block;
    background: rgba(124,106,247,0.15);
    border: 1px solid rgba(124,106,247,0.4);
    color: #a89cf9;
    padding: 0.2rem 0.8rem;
    border-radius: 100px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

/* Stat cards */
.stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    position: relative;
    overflow: hidden;
}
.stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
}
.stat-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.5rem;
}
.stat-value {
    font-family: 'DM Serif Display', serif;
    font-size: 2.2rem;
    line-height: 1;
    color: var(--text);
}
.stat-sub {
    font-size: 0.8rem;
    color: var(--muted);
    margin-top: 0.3rem;
}

/* Upload area */
.upload-zone {
    background: var(--surface);
    border: 2px dashed var(--border);
    border-radius: 20px;
    padding: 3rem 2rem;
    text-align: center;
    transition: border-color 0.2s;
}
.upload-zone:hover { border-color: var(--accent); }
.upload-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.6rem;
    margin-bottom: 0.5rem;
}
.upload-sub { color: var(--muted); font-size: 0.9rem; }

/* Transaction table */
.txn-row {
    display: flex;
    align-items: center;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border);
    gap: 1rem;
}
.txn-row:hover { background: var(--surface2); border-radius: 8px; }

/* Category pill */
.cat-pill {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 100px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}

/* Section header */
.section-head {
    font-family: 'DM Serif Display', serif;
    font-size: 1.4rem;
    margin: 2rem 0 1rem;
    color: var(--text);
}

/* Info box */
.info-box {
    background: rgba(124,106,247,0.08);
    border: 1px solid rgba(124,106,247,0.25);
    border-radius: 12px;
    padding: 1rem 1.4rem;
    font-size: 0.88rem;
    color: #a89cf9;
    margin-bottom: 1.5rem;
}

/* Stacked bar legend */
.legend-item {
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 0.82rem; color: var(--muted);
}
.legend-dot {
    width: 10px; height: 10px;
    border-radius: 50%; flex-shrink: 0;
}

/* Streamlit widget overrides */
.stFileUploader > div {
    background: var(--surface) !important;
    border: 2px dashed var(--border) !important;
    border-radius: 16px !important;
}
.stButton > button {
    background: linear-gradient(135deg, #7c6af7, #9b8cf9) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.8rem !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }
.stSelectbox > div > div {
    background: var(--surface) !important;
    border-color: var(--border) !important;
    border-radius: 10px !important;
}
div[data-testid="metric-container"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1rem 1.5rem;
}
div[data-testid="stMetricValue"] { font-family: 'DM Serif Display', serif; font-size: 2rem !important; }
div[data-testid="stMetricLabel"] { font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted) !important; }
div[data-testid="stMetricDelta"] { font-size: 0.8rem !important; }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 8px !important;
    color: var(--muted) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background: var(--accent) !important;
    color: white !important;
}

/* Dataframe */
.stDataFrame { border-radius: 12px; overflow: hidden; }

/* Divider */
hr { border-color: var(--border) !important; margin: 2rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Category colours ───────────────────────────────────────────────────────────
CAT_COLORS = {
    "Food & Dining":    "#f97b6b",
    "Transport":        "#4fd1a5",
    "Shopping":         "#7c6af7",
    "Bills & Utilities":"#f9c56b",
    "Entertainment":    "#f96bb0",
    "Subscriptions":    "#6bcff9",
    "Peer Transfers":   "#c56bf9",
    "Groceries":        "#6bf97c",
    "Other":            "#888899",
}

# ── Session state ──────────────────────────────────────────────────────────────
if "transactions" not in st.session_state:
    st.session_state.transactions = None
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-badge">UPI Intelligence</div>
  <h1 class="hero-title">UPI Lens</h1>
  <p class="hero-sub">Upload statements from any UPI app. Get your complete spending picture — automatically.</p>
</div>
""", unsafe_allow_html=True)

# ── Upload / Demo section ──────────────────────────────────────────────────────
df = st.session_state.transactions

if df is None:
    st.markdown('<p class="section-head">Get Started</p>', unsafe_allow_html=True)

    col_upload, col_gap, col_demo = st.columns([3, 0.3, 1.5])

    with col_upload:
        st.markdown("""
        <div class="info-box">
            📂 &nbsp; Supports <strong>Google Pay CSV</strong>, <strong>PhonePe PDF</strong>, and <strong>Paytm Excel/CSV</strong> exports. Your data never leaves your browser session.
        </div>
        """, unsafe_allow_html=True)

        uploaded_files = st.file_uploader(
            "Drop your UPI statement(s) here",
            type=["csv", "pdf", "xlsx", "xls"],
            accept_multiple_files=True,
            help="Export your statement from Google Pay → Profile → Transactions → Download"
        )

        if uploaded_files:
            all_dfs = []
            errors = []
            for f in uploaded_files:
                with st.spinner(f"Extracting transactions from {f.name}..."):
                    try:
                        parsed = parse_uploaded_file(f)
                        if parsed is not None and len(parsed) > 0:
                            all_dfs.append(parsed)
                            st.success(f"✓ {f.name} — {len(parsed)} transactions extracted")
                        else:
                            errors.append(f.name)
                    except Exception as e:
                        errors.append(f"{f.name} ({str(e)[:60]})")

            if errors:
                for e in errors:
                    st.warning(f"⚠️ Could not parse: {e}. Try exporting as CSV.")

            if all_dfs:
                combined = pd.concat(all_dfs, ignore_index=True)
                with st.spinner("Normalising merchants and categorising..."):
                    combined = normalize_merchants(combined)
                    combined = categorize_transactions(combined)
                    combined = combined.drop_duplicates(subset=["date","amount","merchant_raw"])
                    combined = combined.sort_values("date", ascending=False).reset_index(drop=True)

                st.session_state.transactions = combined
                st.session_state.demo_mode = False
                st.rerun()

    with col_demo:
        st.markdown("""
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius:16px; padding:1.5rem; text-align:center;">
            <div style="font-family: DM Serif Display, serif; font-size:1.1rem; margin-bottom:0.5rem;">Try Sample Data</div>
            <div style="color: var(--muted); font-size:0.82rem; margin-bottom:1.2rem;">
                See the full dashboard with realistic mock transactions — no upload needed
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀  Load Demo Data", use_container_width=True):
            with st.spinner("Loading sample transactions..."):
                sample = get_sample_data()
                sample = normalize_merchants(sample)
                sample = categorize_transactions(sample)
                st.session_state.transactions = sample
                st.session_state.demo_mode = True
                st.rerun()

        st.markdown("""
        <div style="margin-top:1rem;">
            <p style="color:var(--muted); font-size:0.78rem; text-align:center;">
                Export your statement:<br>
                <strong style="color:var(--text)">Google Pay</strong> → Profile → Manage Google Account → Data → Download<br><br>
                <strong style="color:var(--text)">PhonePe</strong> → Profile → Transaction History → Request Statement
            </p>
        </div>
        """, unsafe_allow_html=True)

else:
    # ── Dashboard ──────────────────────────────────────────────────────────────
    if st.session_state.demo_mode:
        st.markdown("""
        <div class="info-box">
            🎭 &nbsp; You're viewing <strong>demo data</strong> — realistic mock transactions across Google Pay, PhonePe, and Navi.
        </div>
        """, unsafe_allow_html=True)

    # Reset button
    col_r1, col_r2 = st.columns([8, 1])
    with col_r2:
        if st.button("↩ Reset"):
            st.session_state.transactions = None
            st.session_state.demo_mode = False
            st.rerun()

    # ── Top KPI cards ──────────────────────────────────────────────────────────
    total_spend = df[df["amount"] < 0]["amount"].abs().sum()
    total_received = df[df["amount"] > 0]["amount"].sum()
    txn_count = len(df)
    top_cat = df[df["amount"] < 0].groupby("category")["amount"].sum().abs().idxmax() if len(df) > 0 else "—"
    avg_txn = df[df["amount"] < 0]["amount"].abs().mean() if len(df) > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Spent", f"₹{total_spend:,.0f}")
    with c2:
        st.metric("Transactions", f"{txn_count}")
    with c3:
        st.metric("Avg Transaction", f"₹{avg_txn:,.0f}")
    with c4:
        st.metric("Top Category", top_cat)

    st.markdown("---")

    # ── Tabs ───────────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📊  Spending Insights", "🧾  Transactions", "🏪  Merchants"])

    # ──────────── TAB 1: INSIGHTS ────────────────────────────────────────────
    with tab1:
        spend_df = df[df["amount"] < 0].copy()
        spend_df["amount_abs"] = spend_df["amount"].abs()

        col_left, col_right = st.columns([1.1, 1])

        with col_left:
            st.markdown('<p class="section-head">Spending by Category</p>', unsafe_allow_html=True)

            cat_summary = spend_df.groupby("category")["amount_abs"].sum().sort_values(ascending=False).reset_index()
            cat_summary.columns = ["Category", "Amount"]
            cat_summary["Pct"] = (cat_summary["Amount"] / cat_summary["Amount"].sum() * 100).round(1)

            colors = [CAT_COLORS.get(c, "#888") for c in cat_summary["Category"]]

            fig_donut = go.Figure(go.Pie(
                labels=cat_summary["Category"],
                values=cat_summary["Amount"],
                hole=0.62,
                marker=dict(colors=colors, line=dict(color="#0f0f13", width=3)),
                textinfo="none",
                hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>"
            ))
            fig_donut.add_annotation(
                text=f"₹{total_spend/1000:.1f}k",
                x=0.5, y=0.52, showarrow=False,
                font=dict(size=26, color="#e8e8f0", family="DM Serif Display")
            )
            fig_donut.add_annotation(
                text="total spent",
                x=0.5, y=0.42, showarrow=False,
                font=dict(size=12, color="#7a7a92", family="DM Sans")
            )
            fig_donut.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False, margin=dict(t=10, b=10, l=10, r=10),
                height=320
            )
            st.plotly_chart(fig_donut, use_container_width=True)

            # Category breakdown bars
            for _, row in cat_summary.iterrows():
                color = CAT_COLORS.get(row["Category"], "#888")
                pct = row["Pct"]
                st.markdown(f"""
                <div style="margin-bottom:0.6rem;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span style="font-size:0.85rem; font-weight:500;">{row['Category']}</span>
                        <span style="font-size:0.85rem; color:var(--muted);">₹{row['Amount']:,.0f} <span style="font-size:0.75rem;">({pct}%)</span></span>
                    </div>
                    <div style="background:var(--border); border-radius:100px; height:6px;">
                        <div style="background:{color}; width:{pct}%; height:6px; border-radius:100px; transition: width 0.6s ease;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with col_right:
            st.markdown('<p class="section-head">Spending Over Time</p>', unsafe_allow_html=True)

            # Monthly trend
            spend_df["month"] = pd.to_datetime(spend_df["date"]).dt.to_period("M").astype(str)
            monthly = spend_df.groupby(["month","category"])["amount_abs"].sum().reset_index()

            if monthly["month"].nunique() > 1:
                fig_bar = px.bar(
                    monthly, x="month", y="amount_abs", color="category",
                    color_discrete_map=CAT_COLORS,
                    labels={"amount_abs": "Amount (₹)", "month": "", "category": "Category"}
                )
                fig_bar.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="DM Sans", color="#7a7a92"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
                    xaxis=dict(showgrid=False, tickfont=dict(color="#7a7a92")),
                    yaxis=dict(showgrid=True, gridcolor="#2a2a38", tickprefix="₹", tickfont=dict(color="#7a7a92")),
                    margin=dict(t=40, b=20, l=10, r=10), height=320, barmode="stack"
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                # single month — show daily
                spend_df["day"] = pd.to_datetime(spend_df["date"]).dt.strftime("%b %d")
                daily = spend_df.groupby(["day","category"])["amount_abs"].sum().reset_index()
                fig_bar = px.bar(
                    daily, x="day", y="amount_abs", color="category",
                    color_discrete_map=CAT_COLORS,
                    labels={"amount_abs": "Amount (₹)", "day": "", "category": ""}
                )
                fig_bar.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="DM Sans", color="#7a7a92"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
                    xaxis=dict(showgrid=False, tickfont=dict(color="#7a7a92")),
                    yaxis=dict(showgrid=True, gridcolor="#2a2a38", tickprefix="₹", tickfont=dict(color="#7a7a92")),
                    margin=dict(t=40, b=20, l=10, r=10), height=320, barmode="stack"
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            # Smart insights
            st.markdown('<p class="section-head">Smart Insights</p>', unsafe_allow_html=True)
            insights = []

            # Top category insight
            if len(cat_summary) > 0:
                top = cat_summary.iloc[0]
                insights.append(f"🍽️  **{top['Category']}** is your biggest spend — ₹{top['Amount']:,.0f} ({top['Pct']}% of total)")

            # Most frequent merchant
            merchant_freq = spend_df.groupby("merchant_display").size().sort_values(ascending=False)
            if len(merchant_freq) > 0:
                top_m = merchant_freq.index[0]
                insights.append(f"🔁  **{top_m}** is your most visited merchant ({merchant_freq.iloc[0]} transactions)")

            # Peer transfers
            peer = spend_df[spend_df["category"] == "Peer Transfers"]["amount_abs"].sum()
            if peer > 0:
                insights.append(f"👥  You sent ₹{peer:,.0f} in peer transfers this period")

            # Uncategorised
            uncat = spend_df[spend_df["category"] == "Other"]
            if len(uncat) > 0:
                insights.append(f"❓  {len(uncat)} transactions ({len(uncat)/len(spend_df)*100:.0f}%) are uncategorised — expanding merchant database will improve this")

            for ins in insights:
                st.markdown(f"""
                <div style="background:var(--surface); border:1px solid var(--border); border-radius:10px;
                     padding:0.75rem 1rem; margin-bottom:0.5rem; font-size:0.88rem; line-height:1.5;">
                    {ins}
                </div>
                """, unsafe_allow_html=True)

    # ──────────── TAB 2: TRANSACTIONS ──────────────────────────────────────────
    with tab2:
        col_f1, col_f2, col_f3 = st.columns([2, 2, 1.5])
        with col_f1:
            search = st.text_input("🔍 Search merchant", placeholder="e.g. Zomato, Uber...", label_visibility="collapsed")
        with col_f2:
            cats = ["All Categories"] + sorted(df["category"].unique().tolist())
            selected_cat = st.selectbox("Category", cats, label_visibility="collapsed")
        with col_f3:
            txn_type = st.selectbox("Type", ["All", "Debit (spent)", "Credit (received)"], label_visibility="collapsed")

        filtered = df.copy()
        if search:
            filtered = filtered[filtered["merchant_display"].str.contains(search, case=False, na=False)]
        if selected_cat != "All Categories":
            filtered = filtered[filtered["category"] == selected_cat]
        if txn_type == "Debit (spent)":
            filtered = filtered[filtered["amount"] < 0]
        elif txn_type == "Credit (received)":
            filtered = filtered[filtered["amount"] > 0]

        st.markdown(f"<p style='color:var(--muted); font-size:0.82rem; margin-bottom:1rem;'>{len(filtered)} transactions</p>", unsafe_allow_html=True)

        # Render transaction rows
        for _, row in filtered.head(200).iterrows():
            color = CAT_COLORS.get(row["category"], "#888")
            amt = row["amount"]
            amt_str = f"−₹{abs(amt):,.0f}" if amt < 0 else f"+₹{amt:,.0f}"
            amt_color = "#f97b6b" if amt < 0 else "#4fd1a5"
            date_str = pd.to_datetime(row["date"]).strftime("%d %b") if pd.notnull(row["date"]) else "—"
            source = row.get("source", "")
            source_badge = f'<span style="font-size:0.68rem; background:rgba(255,255,255,0.06); padding:1px 6px; border-radius:4px; color:var(--muted);">{source}</span>' if source else ""

            st.markdown(f"""
            <div style="display:flex; align-items:center; padding:0.7rem 1rem; border-bottom:1px solid var(--border);
                 gap:1rem; border-radius:8px; transition: background 0.15s;" 
                 onmouseover="this.style.background='var(--surface2)'" 
                 onmouseout="this.style.background='transparent'">
                <div style="width:44px; text-align:center;">
                    <div style="width:38px; height:38px; border-radius:10px; background:rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.18);
                         display:flex; align-items:center; justify-content:center; font-size:1rem;">
                        {get_cat_emoji(row['category'])}
                    </div>
                </div>
                <div style="flex:1; min-width:0;">
                    <div style="font-weight:500; font-size:0.9rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                        {row['merchant_display']} {source_badge}
                    </div>
                    <div style="color:var(--muted); font-size:0.75rem; margin-top:2px;">
                        {date_str} &nbsp;·&nbsp; 
                        <span style="color:{color}; font-weight:600; font-size:0.7rem;">{row['category']}</span>
                    </div>
                </div>
                <div style="text-align:right; font-family:'DM Serif Display', serif; font-size:1.05rem; color:{amt_color}; white-space:nowrap;">
                    {amt_str}
                </div>
            </div>
            """, unsafe_allow_html=True)

        if len(filtered) > 200:
            st.markdown(f"<p style='color:var(--muted); font-size:0.82rem; text-align:center; margin-top:1rem;'>Showing 200 of {len(filtered)} transactions</p>", unsafe_allow_html=True)

    # ──────────── TAB 3: MERCHANTS ─────────────────────────────────────────────
    with tab3:
        spend_df2 = df[df["amount"] < 0].copy()
        spend_df2["amount_abs"] = spend_df2["amount"].abs()

        merchant_summary = spend_df2.groupby(["merchant_display","category"]).agg(
            total=("amount_abs","sum"),
            count=("amount_abs","count"),
            avg=("amount_abs","mean")
        ).reset_index().sort_values("total", ascending=False)

        col_m1, col_m2 = st.columns([1.3, 1])

        with col_m1:
            st.markdown('<p class="section-head">Top Merchants by Spend</p>', unsafe_allow_html=True)

            top20 = merchant_summary.head(20)
            colors_m = [CAT_COLORS.get(c, "#888") for c in top20["category"]]

            fig_h = go.Figure(go.Bar(
                y=top20["merchant_display"][::-1],
                x=top20["total"][::-1],
                orientation="h",
                marker=dict(color=colors_m[::-1], line=dict(color="rgba(0,0,0,0)")),
                hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>"
            ))
            fig_h.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="DM Sans", color="#7a7a92"),
                xaxis=dict(showgrid=True, gridcolor="#2a2a38", tickprefix="₹", tickfont=dict(color="#7a7a92")),
                yaxis=dict(showgrid=False, tickfont=dict(color="#e8e8f0", size=12)),
                margin=dict(t=10, b=20, l=10, r=20),
                height=520
            )
            st.plotly_chart(fig_h, use_container_width=True)

        with col_m2:
            st.markdown('<p class="section-head">Merchant Details</p>', unsafe_allow_html=True)

            for _, row in merchant_summary.head(15).iterrows():
                color = CAT_COLORS.get(row["category"], "#888")
                st.markdown(f"""
                <div style="display:flex; align-items:center; justify-content:space-between;
                     padding:0.65rem 1rem; border-bottom:1px solid var(--border);">
                    <div>
                        <div style="font-weight:500; font-size:0.88rem;">{row['merchant_display']}</div>
                        <div style="font-size:0.72rem; color:{color}; margin-top:2px;">{row['category']} · {int(row['count'])} txns · avg ₹{row['avg']:,.0f}</div>
                    </div>
                    <div style="font-family:'DM Serif Display',serif; font-size:1.05rem; color:var(--text);">
                        ₹{row['total']:,.0f}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── Add more files ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<p class="section-head" style="font-size:1rem;">Add Another Statement</p>', unsafe_allow_html=True)
    more_files = st.file_uploader(
        "Upload additional statements to merge",
        type=["csv","pdf","xlsx","xls"],
        accept_multiple_files=True,
        key="more_upload",
        label_visibility="collapsed"
    )
    if more_files:
        new_dfs = []
        for f in more_files:
            try:
                parsed = parse_uploaded_file(f)
                if parsed is not None and len(parsed) > 0:
                    new_dfs.append(parsed)
                    st.success(f"✓ {f.name} — {len(parsed)} transactions")
            except Exception as e:
                st.warning(f"Could not parse {f.name}")
        if new_dfs:
            combined = pd.concat([df] + new_dfs, ignore_index=True)
            combined = normalize_merchants(combined)
            combined = categorize_transactions(combined)
            combined = combined.drop_duplicates(subset=["date","amount","merchant_raw"])
            combined = combined.sort_values("date", ascending=False).reset_index(drop=True)
            st.session_state.transactions = combined
            st.rerun()


def get_cat_emoji(cat):
    return {
        "Food & Dining": "🍜",
        "Transport": "🚗",
        "Shopping": "🛍️",
        "Bills & Utilities": "⚡",
        "Entertainment": "🎬",
        "Subscriptions": "📺",
        "Peer Transfers": "👤",
        "Groceries": "🛒",
        "Other": "💳",
    }.get(cat, "💳")
