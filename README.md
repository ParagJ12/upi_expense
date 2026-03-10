# UPI Lens — Spending Intelligence Platform

> A PM portfolio project demonstrating cross-app UPI expense analysis.  
> Upload statements from Google Pay, PhonePe, Paytm, or any bank — get instant category-level spending insights.

---
## Architecture

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

## Features

- **Multi-format upload** — PDF, CSV, Excel from any UPI app
- **Merchant normalisation** — maps "BUNDL TECHNOLOGIES" → Zomato
- **Category breakdown** — Food, Transport, Shopping, Bills, Entertainment, Subscriptions, Groceries
- **Interactive charts** — donut chart, monthly trend, merchant bar chart
- **Unified transaction feed** — searchable, filterable
- **Smart insights** — auto-generated observations about spending
- **Demo mode** — realistic sample data, no upload needed

---

## Tech Stack

| Layer | Tool |
|---|---|
| UI | Streamlit |
| Data | pandas |
| PDF parsing | pdfplumber |
| Fuzzy matching | rapidfuzz |
| Charts | Plotly |
| Storage | Session state (no DB) |

---
## Categorisation Issues
UPI merchant strings are notoriously dirty, as the raw name in a transaction is whatever the merchant registered with their bank/PSP, which could be their legal entity name, a random abbreviation, or a payment gateway ID. Even GPay and PhonePe's own apps struggle with this and use server-side ML models trained on millions of transactions to get it right.
The current rule-based approach covers ~85-90% of common merchants. The production path would be a lightweight ML classifier trained on UPI transaction data, with a user-correction loop that lets users re-tag transactions, which feed back into the model.
---
Demo: https://upiexpense-j12.streamlit.app/ 
