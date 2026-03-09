import pandas as pd
import io
import re
from datetime import datetime
import sys

def parse_uploaded_file(uploaded_file) -> pd.DataFrame:
    """
    Route uploaded file to the correct parser.
    Returns a DataFrame with columns: date, merchant_raw, amount, source
    """
    fname = uploaded_file.name.lower()
    content = uploaded_file.read()
    uploaded_file.seek(0)

    if fname.endswith(".csv"):
        return _parse_csv(content, uploaded_file.name)
    elif fname.endswith(".pdf"):
        return _parse_pdf(content, uploaded_file.name)
    elif fname.endswith((".xlsx", ".xls")):
        return _parse_excel(content, uploaded_file.name)
    else:
        raise ValueError(f"Unsupported file type: {fname}")


# ── CSV Parser ────────────────────────────────────────────────────────────────
def _parse_csv(content: bytes, fname: str) -> pd.DataFrame:
    """
    Handles:
    - Google Pay transaction history CSV
    - Generic bank/UPI CSV exports
    """
    text = content.decode("utf-8", errors="replace")
    
    # Try Google Pay format detection
    if "google pay" in text.lower() or "gpay" in text.lower() or "Transaction ID" in text:
        return _parse_gpay_csv(text, fname)
    
    # Try to detect PhonePe CSV
    if "phonepe" in text.lower():
        return _parse_phonepe_csv(text, fname)
    
    # Generic CSV fallback
    return _parse_generic_csv(text, fname)


def _parse_gpay_csv(text: str, fname: str) -> pd.DataFrame:
    """Parse Google Pay CSV export."""
    try:
        df = pd.read_csv(io.StringIO(text), skiprows=_find_header_row(text))
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        # Common GPay column names
        date_cols = [c for c in df.columns if any(x in c for x in ["date", "time", "timestamp"])]
        amount_cols = [c for c in df.columns if any(x in c for x in ["amount", "debit", "credit", "dr", "cr"])]
        desc_cols = [c for c in df.columns if any(x in c for x in ["description", "narration", "merchant", "name", "party", "recipient", "paid_to", "paid_by"])]

        if not date_cols or not amount_cols:
            return _parse_generic_csv(text, fname)

        result = pd.DataFrame()
        result["date"] = pd.to_datetime(df[date_cols[0]], dayfirst=True, errors="coerce")
        result["merchant_raw"] = df[desc_cols[0]].astype(str) if desc_cols else "Unknown"
        
        # Handle split debit/credit columns
        if len(amount_cols) >= 2:
            # Check if separate debit/credit columns
            col1 = df[amount_cols[0]].astype(str).str.replace(",", "").str.replace("₹", "")
            col2 = df[amount_cols[1]].astype(str).str.replace(",", "").str.replace("₹", "")
            debit = pd.to_numeric(col1, errors="coerce").fillna(0)
            credit = pd.to_numeric(col2, errors="coerce").fillna(0)
            result["amount"] = credit - debit
        else:
            raw_amt = df[amount_cols[0]].astype(str).str.replace(",", "").str.replace("₹", "").str.replace("+", "")
            result["amount"] = pd.to_numeric(raw_amt, errors="coerce")

        result["source"] = "Google Pay"
        result = result.dropna(subset=["date", "amount"])
        return result[result["amount"] != 0]
    except Exception as e:
        return _parse_generic_csv(text, fname)


def _parse_phonepe_csv(text: str, fname: str) -> pd.DataFrame:
    """Parse PhonePe CSV export."""
    try:
        df = pd.read_csv(io.StringIO(text), skiprows=_find_header_row(text))
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        
        date_cols = [c for c in df.columns if "date" in c or "time" in c]
        amount_cols = [c for c in df.columns if "amount" in c or "debit" in c or "credit" in c]
        desc_cols = [c for c in df.columns if any(x in c for x in ["description", "narration", "merchant", "to", "from", "name"])]
        
        result = pd.DataFrame()
        result["date"] = pd.to_datetime(df[date_cols[0]], dayfirst=True, errors="coerce") if date_cols else pd.NaT
        result["merchant_raw"] = df[desc_cols[0]].astype(str) if desc_cols else "Unknown"
        
        if amount_cols:
            raw_amt = df[amount_cols[0]].astype(str).str.replace(",", "").str.replace("₹", "").str.strip()
            result["amount"] = pd.to_numeric(raw_amt, errors="coerce")
        
        # Check for debit/credit indicators
        for col in df.columns:
            if "type" in col or "dr_cr" in col or "transaction_type" in col:
                result["amount"] = result["amount"].where(
                    df[col].astype(str).str.upper().isin(["CREDIT", "CR", "IN"]),
                    -result["amount"].abs()
                )
                break
        else:
            result["amount"] = -result["amount"].abs()  # Default to debit if no indicator
        
        result["source"] = "PhonePe"
        result = result.dropna(subset=["date", "amount"])
        return result
    except:
        return _parse_generic_csv(text, fname)


def _parse_generic_csv(text: str, fname: str) -> pd.DataFrame:
    """Generic CSV parser — tries to detect columns intelligently."""
    try:
        skip = _find_header_row(text)
        df = pd.read_csv(io.StringIO(text), skiprows=skip)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        # Find best columns
        date_col = _find_col(df.columns, ["date", "time", "timestamp", "txn_date", "value_date"])
        amount_col = _find_col(df.columns, ["amount", "debit", "dr", "withdrawal", "paid"])
        credit_col = _find_col(df.columns, ["credit", "cr", "deposit", "received"])
        desc_col = _find_col(df.columns, ["description", "narration", "merchant", "particulars",
                                           "remarks", "details", "name", "payee", "beneficiary"])

        if date_col is None or (amount_col is None and credit_col is None):
            # Last resort: use first 3 columns
            cols = list(df.columns)
            result = pd.DataFrame()
            result["date"] = pd.to_datetime(df[cols[0]], dayfirst=True, errors="coerce")
            result["merchant_raw"] = df[cols[1]].astype(str) if len(cols) > 1 else "Unknown"
            result["amount"] = pd.to_numeric(df[cols[2]].astype(str).str.replace(",","").str.replace("₹",""), errors="coerce") if len(cols) > 2 else 0
            result["source"] = _guess_source(fname)
            return result.dropna(subset=["date"])

        result = pd.DataFrame()
        result["date"] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
        result["merchant_raw"] = df[desc_col].astype(str) if desc_col else "Unknown"

        if amount_col and credit_col:
            debit = pd.to_numeric(df[amount_col].astype(str).str.replace(",","").str.replace("₹",""), errors="coerce").fillna(0)
            credit = pd.to_numeric(df[credit_col].astype(str).str.replace(",","").str.replace("₹",""), errors="coerce").fillna(0)
            result["amount"] = credit - debit
        elif amount_col:
            raw = df[amount_col].astype(str).str.replace(",","").str.replace("₹","")
            result["amount"] = pd.to_numeric(raw, errors="coerce")
        else:
            raw = df[credit_col].astype(str).str.replace(",","").str.replace("₹","")
            result["amount"] = pd.to_numeric(raw, errors="coerce")

        result["source"] = _guess_source(fname)
        result = result.dropna(subset=["date", "amount"])
        return result[result["amount"] != 0]
    except Exception as e:
        raise ValueError(f"Could not parse CSV: {e}")


def _find_header_row(text: str) -> int:
    """Find the actual header row (skip metadata rows at top)."""
    lines = text.split("\n")
    for i, line in enumerate(lines[:20]):
        lower = line.lower()
        if any(x in lower for x in ["date", "amount", "narration", "description", "merchant"]):
            return i
    return 0


def _find_col(columns, keywords):
    """Find best matching column from a list of keywords."""
    for kw in keywords:
        for col in columns:
            if kw in col:
                return col
    return None


def _guess_source(fname: str) -> str:
    fname = fname.lower()
    if "gpay" in fname or "google" in fname:
        return "Google Pay"
    if "phonepe" in fname or "phone_pe" in fname:
        return "PhonePe"
    if "paytm" in fname:
        return "Paytm"
    if "navi" in fname:
        return "Navi"
    if "amazon" in fname:
        return "Amazon Pay"
    return "Bank Statement"


# ── PDF Parser ────────────────────────────────────────────────────────────────
def _parse_pdf(content: bytes, fname: str) -> pd.DataFrame:
    """Parse PDF transaction statements using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber not installed. Run: pip install pdfplumber")

    source = _guess_source(fname)
    rows = []

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            # Try table extraction first
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row and any(row):
                        rows.append([str(c or "").strip() for c in row])

            # Fallback: raw text extraction
            if not rows:
                text = page.extract_text()
                if text:
                    for line in text.split("\n"):
                        rows.append([line])

    if not rows:
        raise ValueError("No data found in PDF. Try exporting as CSV instead.")

    # Convert rows to DataFrame and try to parse
    return _rows_to_df(rows, source)


def _rows_to_df(rows: list, source: str) -> pd.DataFrame:
    """Convert raw table rows to structured DataFrame."""
    if not rows:
        return pd.DataFrame(columns=["date", "merchant_raw", "amount", "source"])

    # Use first row as headers if it looks like headers
    headers = rows[0]
    data = rows[1:]

    df = pd.DataFrame(data, columns=[str(h).lower().strip() for h in headers])
    df.columns = [re.sub(r"\s+", "_", c) for c in df.columns]

    date_col = _find_col(df.columns, ["date", "time", "txn", "value"])
    amount_col = _find_col(df.columns, ["amount", "debit", "dr", "withdrawal"])
    credit_col = _find_col(df.columns, ["credit", "cr"])
    desc_col = _find_col(df.columns, ["description", "narration", "particulars", "merchant", "remarks"])

    result = pd.DataFrame()

    if date_col:
        result["date"] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
    else:
        # Try each column for date-like content
        for col in df.columns:
            dates = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
            if dates.notna().sum() > len(df) * 0.5:
                result["date"] = dates
                break

    result["merchant_raw"] = df[desc_col].astype(str) if desc_col else "Unknown"

    if amount_col and credit_col:
        debit = pd.to_numeric(df[amount_col].astype(str).str.replace(",","").str.replace("₹",""), errors="coerce").fillna(0)
        credit = pd.to_numeric(df[credit_col].astype(str).str.replace(",","").str.replace("₹",""), errors="coerce").fillna(0)
        result["amount"] = credit - debit
    elif amount_col:
        result["amount"] = pd.to_numeric(df[amount_col].astype(str).str.replace(",","").str.replace("₹",""), errors="coerce")
    elif credit_col:
        result["amount"] = pd.to_numeric(df[credit_col].astype(str).str.replace(",","").str.replace("₹",""), errors="coerce")
    else:
        # Scan all columns for numeric data that looks like amounts
        for col in df.columns:
            numeric = pd.to_numeric(df[col].astype(str).str.replace(",",""), errors="coerce")
            if numeric.notna().sum() > len(df) * 0.5:
                result["amount"] = numeric
                break

    if "date" not in result.columns:
        result["date"] = pd.NaT
    if "amount" not in result.columns:
        result["amount"] = 0

    result["source"] = source
    result = result.dropna(subset=["date"])
    result = result[result["amount"].notna() & (result["amount"] != 0)]
    return result


# ── Excel Parser ──────────────────────────────────────────────────────────────
def _parse_excel(content: bytes, fname: str) -> pd.DataFrame:
    """Parse Excel (.xlsx/.xls) transaction statements."""
    source = _guess_source(fname)
    try:
        # Try all sheets
        xl = pd.ExcelFile(io.BytesIO(content))
        best_df = None
        best_score = 0

        for sheet in xl.sheet_names:
            try:
                df = xl.parse(sheet, header=None)
                # Find header row
                for i, row in df.iterrows():
                    row_str = " ".join(str(v).lower() for v in row if pd.notnull(v))
                    score = sum(1 for x in ["date", "amount", "narration", "description", "debit", "credit"] if x in row_str)
                    if score > best_score:
                        best_score = score
                        best_df = xl.parse(sheet, header=i)

                if best_df is None:
                    best_df = xl.parse(sheet)
            except:
                continue

        if best_df is None:
            raise ValueError("Could not parse Excel file")

        best_df.columns = [str(c).strip().lower().replace(" ", "_") for c in best_df.columns]
        text = best_df.to_csv(index=False)
        return _parse_generic_csv(text.encode(), fname)

    except Exception as e:
        raise ValueError(f"Could not parse Excel file: {e}")
