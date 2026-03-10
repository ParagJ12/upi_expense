import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.append(os.path.dirname(__file__))
from parser import parse_uploaded_file
from normalizer import normalize_merchants
from categorizer import categorize_transactions
from sample_data import get_sample_data

st.set_page_config(
    page_title="UPI Lens",
    page_icon="₹",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
  --bg:        #080b12;
  --bg2:       #0d1117;
  --surface:   #111622;
  --surface2:  #161d2e;
  --border:    #1e2a40;
  --border2:   #253450;
  --accent:    #4f8ef7;
  --accent2:   #7b5ef8;
  --green:     #22c55e;
  --red:       #f87171;
  --gold:      #f5a623;
  --text:      #e2e8f8;
  --muted:     #64748b;
  --muted2:    #94a3b8;
}

html, body, [class*="css"] {
  font-family: 'Outfit', sans-serif !important;
  background-color: var(--bg) !important;
  color: var(--text) !important;
}
.main { background: var(--bg); }
.block-container { padding: 0 2.5rem 3rem; max-width: 1380px; }
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── BACKGROUND SYMBOLS ──────────────────────────────── */
.bg-symbols {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  pointer-events: none; z-index: 0; overflow: hidden;
}
.sym {
  position: absolute;
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  color: rgba(79,142,247,0.055);
  user-select: none;
  line-height: 1;
  animation: floatSym linear infinite;
}
@keyframes floatSym {
  0%   { transform: translateY(0px) rotate(0deg); }
  50%  { transform: translateY(-18px) rotate(4deg); }
  100% { transform: translateY(0px) rotate(0deg); }
}
.sym-r { color: rgba(123,94,248,0.05); }
.sym-g { color: rgba(34,197,94,0.04); }

/* ── HERO ────────────────────────────────────────────── */
.hero-wrap {
  position: relative;
  padding: 2.8rem 0 2rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 2rem;
  z-index: 1;
}
.hero-eyebrow {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(79,142,247,0.1);
  border: 1px solid rgba(79,142,247,0.25);
  border-radius: 100px;
  padding: 3px 12px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #7aadff;
  margin-bottom: 1rem;
}
.hero-dot { width:6px; height:6px; border-radius:50%; background:#4f8ef7; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(.8)} }
.hero-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 3rem; font-weight: 700; line-height: 1.1;
  background: linear-gradient(120deg, #e2e8f8 0%, #7aadff 50%, #a78bfa 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  margin: 0 0 0.6rem;
}
.hero-sub { color: var(--muted2); font-size: 1rem; font-weight: 400; }

/* ── CARDS ───────────────────────────────────────────── */
.kpi-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1.4rem 1.6rem;
  position: relative; overflow: hidden;
  transition: border-color .2s;
}
.kpi-card:hover { border-color: var(--border2); }
.kpi-card::after {
  content: ''; position: absolute;
  top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(79,142,247,.5), transparent);
}
.kpi-label {
  font-size: .72rem; font-weight: 600;
  letter-spacing: .1em; text-transform: uppercase;
  color: var(--muted); margin-bottom: .5rem;
}
.kpi-value {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 2rem; font-weight: 700; color: var(--text); line-height: 1;
}
.kpi-sub { font-size: .78rem; color: var(--muted); margin-top: .3rem; }

/* ── UPLOAD ──────────────────────────────────────────── */
.upload-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.5rem;
}
.demo-card {
  background: linear-gradient(135deg, #0d1a35 0%, #12173a 100%);
  border: 1px solid rgba(79,142,247,.25);
  border-radius: 16px;
  padding: 1.8rem 1.5rem;
  text-align: center;
}
.demo-title { font-family: 'Space Grotesk',sans-serif; font-size:1.1rem; font-weight:600; margin-bottom:.5rem; }
.demo-sub { color: var(--muted2); font-size:.82rem; line-height:1.5; margin-bottom:1.2rem; }

/* ── INFO BOX ────────────────────────────────────────── */
.info-box {
  background: rgba(79,142,247,.07);
  border: 1px solid rgba(79,142,247,.2);
  border-left: 3px solid #4f8ef7;
  border-radius: 10px;
  padding: .85rem 1.2rem;
  font-size: .85rem; color: #93bbff;
  margin-bottom: 1.4rem;
}

/* ── SECTION TITLES ──────────────────────────────────── */
.sec-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.15rem; font-weight: 600;
  color: var(--text); margin: 1.8rem 0 1rem;
}

/* ── PROGRESS BARS ───────────────────────────────────── */
.bar-row { margin-bottom: .7rem; }
.bar-meta { display:flex; justify-content:space-between; margin-bottom:5px; }
.bar-name { font-size:.84rem; font-weight:500; }
.bar-amt  { font-size:.84rem; color:var(--muted2); }
.bar-track { background:var(--border); border-radius:100px; height:5px; }
.bar-fill  { height:5px; border-radius:100px; transition:width .6s ease; }

/* ── TRANSACTIONS ────────────────────────────────────── */
.txn-item {
  display: flex; align-items: center; gap: 12px;
  padding: .65rem .8rem;
  border-bottom: 1px solid var(--border);
  border-radius: 8px;
  transition: background .15s;
}
.txn-item:hover { background: var(--surface2); }
.txn-icon {
  width: 36px; height: 36px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: .95rem; flex-shrink: 0;
}
.txn-name { font-weight: 500; font-size: .88rem; }
.txn-meta { font-size: .72rem; color: var(--muted); margin-top: 2px; }
.txn-amt  { font-family:'Space Grotesk',sans-serif; font-size:1rem; font-weight:600; }

/* ── INSIGHT CARDS ───────────────────────────────────── */
.insight-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: .8rem 1rem;
  font-size: .85rem; line-height: 1.6;
  margin-bottom: .5rem;
}

/* ── TABS ────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  padding: 4px !important; gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important; color: var(--muted) !important;
  border-radius: 8px !important; font-family: 'Outfit',sans-serif !important;
  font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, #4f8ef7, #7b5ef8) !important;
  color: white !important;
}

/* ── BUTTONS ─────────────────────────────────────────── */
.stButton > button {
  background: linear-gradient(135deg, #4f8ef7, #7b5ef8) !important;
  color: white !important; border: none !important;
  border-radius: 10px !important; font-family: 'Outfit',sans-serif !important;
  font-weight: 600 !important; font-size: .9rem !important;
  padding: .6rem 1.6rem !important; transition: opacity .2s !important;
}
.stButton > button:hover { opacity: .85 !important; }

/* ── INPUTS ──────────────────────────────────────────── */
.stTextInput input, .stSelectbox > div > div {
  background: var(--surface) !important;
  border-color: var(--border) !important;
  border-radius: 10px !important;
  color: var(--text) !important;
}
.stFileUploader > div {
  background: var(--surface) !important;
  border: 2px dashed var(--border2) !important;
  border-radius: 14px !important;
}
.stFileUploader > div:hover { border-color: #4f8ef7 !important; }

/* ── METRIC ──────────────────────────────────────────── */
div[data-testid="metric-container"] {
  background: var(--surface); border:1px solid var(--border);
  border-radius:14px; padding:1rem 1.5rem;
}
div[data-testid="stMetricValue"] {
  font-family:'Space Grotesk',sans-serif !important;
  font-size:1.9rem !important; font-weight:700 !important;
}
div[data-testid="stMetricLabel"] {
  font-size:.7rem !important; text-transform:uppercase;
  letter-spacing:.1em; color:var(--muted) !important;
}

hr { border-color: var(--border) !important; margin: 2rem 0 !important; }
.stSuccess > div { background: rgba(34,197,94,.1) !important; border-color: rgba(34,197,94,.3) !important; color:#4ade80 !important; border-radius:10px !important; }
.stWarning > div { background: rgba(245,166,35,.08) !important; border-color: rgba(245,166,35,.25) !important; color:#fbbf24 !important; border-radius:10px !important; }
</style>

<!-- Background symbols -->
<div class="bg-symbols">
  <!-- Large anchor symbols -->
  <span class="sym" style="font-size:220px;top:2%;left:1%;animation-duration:9s;animation-delay:0s;">₹</span>
  <span class="sym sym-r" style="font-size:180px;top:55%;right:2%;animation-duration:11s;animation-delay:2s;">₹</span>
  <span class="sym" style="font-size:160px;top:30%;left:44%;animation-duration:13s;animation-delay:1s;">₹</span>
  <!-- Medium symbols -->
  <span class="sym sym-r" style="font-size:110px;top:8%;left:22%;animation-duration:8s;animation-delay:3s;">$</span>
  <span class="sym" style="font-size:100px;top:68%;left:12%;animation-duration:10s;animation-delay:0.5s;">€</span>
  <span class="sym sym-g" style="font-size:120px;top:80%;left:55%;animation-duration:12s;animation-delay:4s;">₹</span>
  <span class="sym" style="font-size:90px;top:18%;right:8%;animation-duration:7s;animation-delay:1.5s;">%</span>
  <span class="sym sym-r" style="font-size:95px;top:45%;left:6%;animation-duration:9s;animation-delay:2.5s;">₹</span>
  <span class="sym" style="font-size:85px;top:35%;right:22%;animation-duration:15s;animation-delay:0s;">$</span>
  <!-- Small decorative -->
  <span class="sym sym-g" style="font-size:60px;top:12%;left:65%;animation-duration:6s;animation-delay:1s;">₹</span>
  <span class="sym" style="font-size:65px;top:88%;right:30%;animation-duration:8s;animation-delay:3s;">€</span>
  <span class="sym sym-r" style="font-size:55px;top:50%;left:80%;animation-duration:10s;animation-delay:2s;">₹</span>
  <span class="sym" style="font-size:70px;top:72%;right:15%;animation-duration:7s;animation-delay:4s;">%</span>
  <span class="sym sym-g" style="font-size:50px;top:25%;left:33%;animation-duration:11s;animation-delay:0.8s;">$</span>
</div>
""", unsafe_allow_html=True)

# ── Category config ────────────────────────────────────────────────────────────
CAT_COLORS = {
    "Food & Dining":    "#f87171",
    "Transport":        "#34d399",
    "Shopping":         "#818cf8",
    "Bills & Utilities":"#fbbf24",
    "Entertainment":    "#f472b6",
    "Subscriptions":    "#38bdf8",
    "Peer Transfers":   "#c084fc",
    "Groceries":        "#4ade80",
    "Finance":          "#fb923c",
    "Other":            "#475569",
    "Income / Credit":  "#22c55e",
}
CAT_EMOJI = {
    "Food & Dining":"🍜","Transport":"🚗","Shopping":"🛍️",
    "Bills & Utilities":"⚡","Entertainment":"🎬","Subscriptions":"📺",
    "Peer Transfers":"👤","Groceries":"🛒","Finance":"📈",
    "Other":"💳","Income / Credit":"💰",
}

# ── Session state ──────────────────────────────────────────────────────────────
if "transactions" not in st.session_state:
    st.session_state.transactions = None
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False

df = st.session_state.transactions

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
  <div class="hero-eyebrow"><div class="hero-dot"></div>UPI Intelligence Platform</div>
  <div class="hero-title">UPI Lens</div>
  <div class="hero-sub">Upload statements from any UPI app — get a complete, categorised picture of your spending.</div>
</div>
""", unsafe_allow_html=True)

# ── UPLOAD STATE ──────────────────────────────────────────────────────────────
if df is None:
    col_l, col_gap, col_r = st.columns([3, 0.3, 1.6])

    with col_l:
        st.markdown("""
        <div class="info-box">
            Supports <strong>Google Pay CSV</strong>, <strong>PhonePe PDF</strong>, <strong>Navi PDF</strong>, 
            and <strong>any bank statement (PDF/CSV/Excel)</strong>. Your data stays in your browser session only.
        </div>
        """, unsafe_allow_html=True)

        uploaded_files = st.file_uploader(
            "Drop your UPI statement(s) here",
            type=["csv","pdf","xlsx","xls"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )

        if uploaded_files:
            all_dfs = []
            for f in uploaded_files:
                with st.spinner(f"📄 Processing {f.name}..."):
                    try:
                        parsed = parse_uploaded_file(f)
                        if parsed is not None and len(parsed) > 0:
                            all_dfs.append(parsed)
                            st.success(f"✓  {f.name} — **{len(parsed)}** transactions found")
                        else:
                            st.warning(f"⚠️  {f.name} — No transactions extracted. Try exporting as CSV.")
                    except Exception as e:
                        st.warning(f"⚠️  {f.name} — {str(e)[:120]}")

            if all_dfs:
                with st.spinner("Normalising merchants and categorising..."):
                    combined = pd.concat(all_dfs, ignore_index=True)
                    combined = normalize_merchants(combined)
                    combined = categorize_transactions(combined)
                    # Dedup on date+amount+merchant_display (not merchant_raw, which differs by source format)
                    combined = combined.drop_duplicates(subset=["date","amount","merchant_display"])
                    combined = combined.sort_values("date", ascending=False).reset_index(drop=True)
                st.session_state.transactions = combined
                st.session_state.demo_mode = False
                st.rerun()

        # How to export guide
        st.markdown("""
        <div style="margin-top:1.5rem; padding:1.2rem; background:var(--surface); border:1px solid var(--border); border-radius:14px;">
          <div style="font-size:.8rem; font-weight:600; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); margin-bottom:.8rem;">How to export your statement</div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:.8rem;">
            <div style="font-size:.82rem; line-height:1.7;">
              <strong style="color:#4f8ef7;">Google Pay</strong><br>
              <span style="color:var(--muted2);">Profile → Manage Google Account<br>→ Data & Privacy → Download Data</span>
            </div>
            <div style="font-size:.82rem; line-height:1.7;">
              <strong style="color:#4f8ef7;">PhonePe / Navi</strong><br>
              <span style="color:var(--muted2);">Profile → Transaction History<br>→ Request Statement (email)</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_r:
        st.markdown("""
        <div class="demo-card">
          <div style="font-size:2rem; margin-bottom:.6rem;">₹</div>
          <div class="demo-title">Try with Demo Data</div>
          <div class="demo-sub">See the full dashboard with realistic mock transactions across Google Pay, PhonePe & Navi</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Load Demo Dashboard →", use_container_width=True):
            with st.spinner("Loading sample data..."):
                sample = get_sample_data()
                sample = normalize_merchants(sample)
                sample = categorize_transactions(sample)
                st.session_state.transactions = sample
                st.session_state.demo_mode = True
                st.rerun()

else:
    # ── DASHBOARD ─────────────────────────────────────────────────────────────
    if st.session_state.demo_mode:
        st.markdown("""
        <div class="info-box">🎭 &nbsp;Viewing <strong>demo data</strong> — 3 months of realistic mock transactions across Google Pay, PhonePe & Navi.</div>
        """, unsafe_allow_html=True)

    top_row = st.columns([8,1])
    with top_row[1]:
        if st.button("↩ Reset"):
            st.session_state.transactions = None
            st.session_state.demo_mode = False
            st.rerun()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    spend  = df[df["amount"] < 0].copy()
    credit = df[df["amount"] > 0].copy()
    spend["amount_abs"]  = spend["amount"].abs()
    credit["amount_abs"] = credit["amount"].abs()
    total_spent    = spend["amount_abs"].sum()
    total_received = credit["amount_abs"].sum()
    avg            = spend["amount_abs"].mean() if len(spend) else 0
    top_c          = spend.groupby("category")["amount_abs"].sum().idxmax() if len(spend) else "—"
    sources        = df["source"].nunique()
    n_debits       = len(spend)
    n_credits      = len(credit)

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class="kpi-card">
          <div class="kpi-label">Total Spent</div>
          <div class="kpi-value" style="color:#f87171;">₹{total_spent:,.0f}</div>
          <div class="kpi-sub">{n_debits} debit transactions</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="kpi-card">
          <div class="kpi-label">Total Received</div>
          <div class="kpi-value" style="color:#22c55e;">₹{total_received:,.0f}</div>
          <div class="kpi-sub">{n_credits} credit transactions</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="kpi-card">
          <div class="kpi-label">All Transactions</div>
          <div class="kpi-value">{len(df)}</div>
          <div class="kpi-sub">across {sources} app{"s" if sources>1 else ""}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="kpi-card">
          <div class="kpi-label">Avg Spend</div>
          <div class="kpi-value">₹{avg:,.0f}</div>
          <div class="kpi-sub">per debit payment</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class="kpi-card">
          <div class="kpi-label">Top Category</div>
          <div class="kpi-value" style="font-size:1.15rem;">{CAT_EMOJI.get(top_c,"")} {top_c}</div>
          <div class="kpi-sub">highest spend</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # ── TABS ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["  📊  Insights  ", "  🧾  Transactions  ", "  🏪  Merchants  "])

    # ──── INSIGHTS ────────────────────────────────────────────────────────────
    with tab1:
        col_l, col_r = st.columns([1.05, 1])

        with col_l:
            st.markdown('<div class="sec-title">Spending by Category</div>', unsafe_allow_html=True)

            cat_df = spend.groupby("category")["amount_abs"].sum().sort_values(ascending=False).reset_index()
            cat_df.columns = ["Category","Amount"]
            cat_df["Pct"] = (cat_df["Amount"] / cat_df["Amount"].sum() * 100).round(1)
            colors = [CAT_COLORS.get(c,"#475569") for c in cat_df["Category"]]

            fig = go.Figure(go.Pie(
                labels=cat_df["Category"], values=cat_df["Amount"], hole=0.65,
                marker=dict(colors=colors, line=dict(color="#080b12", width=3)),
                textinfo="none",
                hovertemplate="<b>%{label}</b><br>₹%{value:,.0f} (%{percent})<extra></extra>"
            ))
            fig.add_annotation(text=f"₹{total_spent/1000:.1f}k", x=0.5, y=0.54, showarrow=False,
                font=dict(size=24, color="#e2e8f8", family="Space Grotesk"))
            fig.add_annotation(text="total", x=0.5, y=0.44, showarrow=False,
                font=dict(size=12, color="#64748b", family="Outfit"))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False, margin=dict(t=10,b=10,l=10,r=10), height=300
            )
            st.plotly_chart(fig, use_container_width=True)

            for _, row in cat_df.iterrows():
                color = CAT_COLORS.get(row["Category"],"#475569")
                pct   = row["Pct"]
                emoji = CAT_EMOJI.get(row["Category"],"💳")
                st.markdown(f"""
                <div class="bar-row">
                  <div class="bar-meta">
                    <span class="bar-name">{emoji} {row['Category']}</span>
                    <span class="bar-amt">₹{row['Amount']:,.0f} <span style="font-size:.72rem;color:var(--muted)">({pct}%)</span></span>
                  </div>
                  <div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{color};"></div></div>
                </div>""", unsafe_allow_html=True)

        with col_r:
            st.markdown('<div class="sec-title">Monthly Trend</div>', unsafe_allow_html=True)
            spend["month"] = pd.to_datetime(spend["date"]).dt.to_period("M").astype(str)
            group_col = "month" if spend["month"].nunique() > 1 else "day"
            if group_col == "day":
                spend["day"] = pd.to_datetime(spend["date"]).dt.strftime("%d %b")
            monthly = spend.groupby([group_col,"category"])["amount_abs"].sum().reset_index()
            fig2 = px.bar(monthly, x=group_col, y="amount_abs", color="category",
                color_discrete_map=CAT_COLORS,
                labels={"amount_abs":"₹","category":"Category",group_col:""})
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Outfit", color="#64748b"),
                legend=dict(orientation="h", yanchor="bottom", y=1.01,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
                xaxis=dict(showgrid=False, tickfont=dict(color="#64748b")),
                yaxis=dict(showgrid=True, gridcolor="#1e2a40", tickprefix="₹", tickfont=dict(color="#64748b")),
                barmode="stack", margin=dict(t=40,b=20,l=10,r=10), height=300
            )
            st.plotly_chart(fig2, use_container_width=True)

            st.markdown('<div class="sec-title">Smart Insights</div>', unsafe_allow_html=True)
            insights = []
            if len(cat_df):
                t = cat_df.iloc[0]
                insights.append(f"**{CAT_EMOJI.get(t['Category'],'')} {t['Category']}** is your biggest spend at **₹{t['Amount']:,.0f}** ({t['Pct']}% of total).")
            mf = spend.groupby("merchant_display").size().sort_values(ascending=False)
            if len(mf):
                insights.append(f"**{mf.index[0]}** is your most visited merchant with **{mf.iloc[0]} visits**.")
            peer = spend[spend["category"]=="Peer Transfers"]["amount_abs"].sum()
            if peer > 0:
                insights.append(f"You sent **₹{peer:,.0f}** in peer-to-peer transfers this period.")
            uncat = (spend["category"]=="Other").sum()
            if uncat > 0:
                pct_u = uncat/len(spend)*100
                insights.append(f"**{uncat} transactions** ({pct_u:.0f}%) are uncategorised — typically hyperlocal merchants.")

            for ins in insights:
                st.markdown(f'<div class="insight-card">{ins}</div>', unsafe_allow_html=True)

    # ──── TRANSACTIONS ────────────────────────────────────────────────────────
    with tab2:
        fc1,fc2,fc3 = st.columns([2.5,2,1.5])
        with fc1:
            q = st.text_input("", placeholder="🔍  Search merchant...", label_visibility="collapsed")
        with fc2:
            cats = ["All Categories"] + sorted(df["category"].unique().tolist())
            sel_cat = st.selectbox("", cats, label_visibility="collapsed")
        with fc3:
            txn_type = st.selectbox("", ["All","Debits only","Credits only"], label_visibility="collapsed")

        fdf = df.copy()
        if q: fdf = fdf[fdf["merchant_display"].str.contains(q, case=False, na=False)]
        if sel_cat != "All Categories": fdf = fdf[fdf["category"]==sel_cat]
        if txn_type == "Debits only": fdf = fdf[fdf["amount"]<0]
        if txn_type == "Credits only": fdf = fdf[fdf["amount"]>0]

        st.markdown(f"<p style='color:var(--muted);font-size:.8rem;margin:.5rem 0 .8rem;'>{len(fdf)} transactions</p>",
            unsafe_allow_html=True)

        for _, row in fdf.head(250).iterrows():
            color = CAT_COLORS.get(row["category"],"#475569")
            amt   = row["amount"]
            amt_s = f"−₹{abs(amt):,.0f}" if amt < 0 else f"+₹{amt:,.0f}"
            amt_c = "#f87171" if amt < 0 else "#22c55e"
            date_s = pd.to_datetime(row["date"]).strftime("%d %b %Y") if pd.notnull(row["date"]) else "—"
            emoji = CAT_EMOJI.get(row["category"],"💳")
            src   = row.get("source","")
            src_b = f'<span style="font-size:.65rem;background:rgba(255,255,255,.06);padding:1px 6px;border-radius:4px;color:var(--muted);">{src}</span>' if src else ""

            r,g,b = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
            st.markdown(f"""
            <div class="txn-item">
              <div class="txn-icon" style="background:rgba({r},{g},{b},.15);">{emoji}</div>
              <div style="flex:1;min-width:0;">
                <div class="txn-name">{row['merchant_display']} {src_b}</div>
                <div class="txn-meta">{date_s} &nbsp;·&nbsp; <span style="color:{color};font-weight:600;">{row['category']}</span></div>
              </div>
              <div class="txn-amt" style="color:{amt_c};">{amt_s}</div>
            </div>""", unsafe_allow_html=True)

    # ──── MERCHANTS ───────────────────────────────────────────────────────────
    with tab3:
        ms = spend.groupby(["merchant_display","category"]).agg(
            total=("amount_abs","sum"), count=("amount_abs","count"),
            avg=("amount_abs","mean")).reset_index().sort_values("total",ascending=False)

        mc1, mc2 = st.columns([1.3, 1])
        with mc1:
            st.markdown('<div class="sec-title">Top 20 Merchants</div>', unsafe_allow_html=True)
            top20 = ms.head(20)
            fig3 = go.Figure(go.Bar(
                y=top20["merchant_display"][::-1], x=top20["total"][::-1],
                orientation="h",
                marker=dict(
                    color=[CAT_COLORS.get(c,"#475569") for c in top20["category"][::-1]],
                    line=dict(color="rgba(0,0,0,0)"),
                    opacity=0.85
                ),
                hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>"
            ))
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Outfit", color="#64748b"),
                xaxis=dict(showgrid=True, gridcolor="#1e2a40", tickprefix="₹", tickfont=dict(color="#64748b")),
                yaxis=dict(showgrid=False, tickfont=dict(color="#e2e8f8", size=11)),
                margin=dict(t=10,b=20,l=10,r=20), height=520
            )
            st.plotly_chart(fig3, use_container_width=True)

        with mc2:
            st.markdown('<div class="sec-title">Merchant Details</div>', unsafe_allow_html=True)
            for _, row in ms.head(15).iterrows():
                color = CAT_COLORS.get(row["category"],"#475569")
                emoji = CAT_EMOJI.get(row["category"],"💳")
                st.markdown(f"""
                <div style="display:flex;align-items:center;justify-content:space-between;
                     padding:.65rem .8rem;border-bottom:1px solid var(--border);">
                  <div>
                    <div style="font-weight:500;font-size:.87rem;">{emoji} {row['merchant_display']}</div>
                    <div style="font-size:.72rem;color:{color};margin-top:2px;">
                      {row['category']} &nbsp;·&nbsp; {int(row['count'])} visits &nbsp;·&nbsp; avg ₹{row['avg']:,.0f}
                    </div>
                  </div>
                  <div style="font-family:'Space Grotesk',sans-serif;font-size:1rem;font-weight:600;color:var(--text);">
                    ₹{row['total']:,.0f}
                  </div>
                </div>""", unsafe_allow_html=True)

    # ── ADD MORE FILES ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="sec-title" style="font-size:.95rem;margin-top:.5rem;">Add Another Statement</div>', unsafe_allow_html=True)
    more = st.file_uploader("", type=["csv","pdf","xlsx","xls"],
        accept_multiple_files=True, key="more", label_visibility="collapsed")
    if more:
        new_dfs = []
        for f in more:
            try:
                p = parse_uploaded_file(f)
                if p is not None and len(p) > 0:
                    new_dfs.append(p); st.success(f"✓ {f.name} — {len(p)} transactions")
            except Exception as e:
                st.warning(f"Could not parse {f.name}: {str(e)[:80]}")
        if new_dfs:
            combined = pd.concat([df]+new_dfs, ignore_index=True)
            combined = normalize_merchants(combined)
            combined = categorize_transactions(combined)
            combined = combined.drop_duplicates(subset=["date","amount","merchant_display"])
            combined = combined.sort_values("date",ascending=False).reset_index(drop=True)
            st.session_state.transactions = combined
            st.rerun()
