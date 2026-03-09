# UPI Lens — Spending Intelligence Platform

> A PM portfolio project demonstrating cross-app UPI expense analysis.  
> Upload statements from Google Pay, PhonePe, Paytm, or any bank — get instant category-level spending insights.

---

## 🚀 Quick Start (Local)

```bash
# 1. Clone or unzip the project
cd upi_app

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

Opens at: `http://localhost:8501`

---

## ☁️ Deploy to Streamlit Cloud (Free)

1. Push this folder to a **GitHub repo**
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select your repo → set **Main file path** to `app.py`
4. Click **Deploy** — done in ~2 minutes

Your shareable link will be: `https://your-app-name.streamlit.app`

---

## 📁 How to Export Your UPI Statements

### Google Pay
1. Open Google Pay → tap your profile photo
2. Go to **Manage your Google Account** → **Data & privacy**
3. Scroll to **Download your data** → select Google Pay
4. Or: In the app, go to **Transactions** → filter by month → **Download**

### PhonePe
1. Open PhonePe → **Profile** → **Transaction History**
2. Tap the filter icon → select date range
3. Tap **Request Statement** → sent to your registered email as PDF

### Paytm
1. Open Paytm → **Profile** → **Passbook**
2. Tap **Download Statement** → choose format (CSV preferred)

---

## 🏗️ Architecture

```
User uploads PDF/CSV/Excel
        ↓
parser.py       — format-specific extraction → standard DataFrame
        ↓
normalizer.py   — L1 exact match → L2 fuzzy → L3 pattern → L4 fallback
        ↓
categorizer.py  — merchant → category assignment
        ↓
app.py          — Streamlit dashboard (insights + feed + merchants)
```

## 📊 Features

- **Multi-format upload** — PDF, CSV, Excel from any UPI app
- **Merchant normalisation** — maps "BUNDL TECHNOLOGIES" → Zomato
- **Category breakdown** — Food, Transport, Shopping, Bills, Entertainment, Subscriptions, Groceries
- **Interactive charts** — donut chart, monthly trend, merchant bar chart
- **Unified transaction feed** — searchable, filterable
- **Smart insights** — auto-generated observations about spending
- **Demo mode** — realistic sample data, no upload needed

---

## 🛠️ Tech Stack

| Layer | Tool |
|---|---|
| UI | Streamlit |
| Data | pandas |
| PDF parsing | pdfplumber |
| Fuzzy matching | rapidfuzz |
| Charts | Plotly |
| Storage | Session state (no DB) |

---

*Built as part of a product management portfolio project.*
