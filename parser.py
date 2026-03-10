import pandas as pd
import io
import re
from datetime import datetime

def parse_uploaded_file(uploaded_file) -> pd.DataFrame:
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

# ── DATE PATTERNS ─────────────────────────────────────────────────────────────
DATE_PATTERNS = [
    r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b',
    r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b',
    r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})\b',
    r'\b(\d{4}[\/\-]\d{2}[\/\-]\d{2})\b',
    r'\b(\d{2}[\/\-]\d{2}[\/\-]\d{4})\b',
]

AMOUNT_PATTERN = re.compile(
    r'(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d{1,2})?)\s*(?:Dr|Cr|DR|CR)?'
)

def _try_parse_date(s):
    for fmt in ["%d/%m/%Y","%d-%m-%Y","%d/%m/%y","%d-%m-%y",
                "%Y-%m-%d","%Y/%m/%d","%d %b %Y","%d %B %Y",
                "%b %d, %Y","%B %d, %Y","%d %b %y","%d-%b-%Y","%d-%b-%y"]:
        try:
            return pd.to_datetime(s, format=fmt)
        except:
            pass
    try:
        return pd.to_datetime(s, dayfirst=True)
    except:
        return None

# ── CSV ───────────────────────────────────────────────────────────────────────
def _parse_csv(content: bytes, fname: str) -> pd.DataFrame:
    text = content.decode("utf-8", errors="replace")
    fname_l = fname.lower()
    if "gpay" in fname_l or "google" in fname_l:
        return _parse_gpay_csv(text, fname)
    if "phonepe" in fname_l:
        return _parse_phonepe_csv(text, fname)
    if "navi" in fname_l:
        return _parse_navi_csv(text, fname)
    if "paytm" in fname_l:
        return _parse_paytm_csv(text, fname)
    return _parse_generic_csv(text, fname)

def _parse_gpay_csv(text: str, fname: str) -> pd.DataFrame:
    skip = _find_header_row(text)
    try:
        df = pd.read_csv(io.StringIO(text), skiprows=skip)
        df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
        date_col = _find_col(df.columns, ["date","time","timestamp","transaction_date"])
        desc_col = _find_col(df.columns, ["description","narration","merchant","name","paid_to","recipient","party"])
        dr_col   = _find_col(df.columns, ["debit","dr","amount_debited","withdrawal","paid_out"])
        cr_col   = _find_col(df.columns, ["credit","cr","amount_credited","deposit","paid_in"])
        amt_col  = _find_col(df.columns, ["amount","net","value"])
        result = pd.DataFrame()
        result["date"] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce") if date_col else pd.NaT
        result["merchant_raw"] = df[desc_col].astype(str) if desc_col else "Unknown"
        if dr_col and cr_col:
            dr = _to_num(df[dr_col]); cr = _to_num(df[cr_col])
            result["amount"] = cr - dr
        elif amt_col:
            result["amount"] = _to_num(df[amt_col])
        else:
            result["amount"] = 0
        result["source"] = "Google Pay"
        return _clean_result(result)
    except Exception as e:
        return _parse_generic_csv(text, fname)

def _parse_phonepe_csv(text: str, fname: str) -> pd.DataFrame:
    skip = _find_header_row(text)
    try:
        df = pd.read_csv(io.StringIO(text), skiprows=skip)
        df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
        date_col = _find_col(df.columns, ["date","timestamp","transaction_date","txn_date"])
        desc_col = _find_col(df.columns, ["description","narration","merchant","name","to","paid_to"])
        dr_col   = _find_col(df.columns, ["debit","dr","withdrawal","amount_debited"])
        cr_col   = _find_col(df.columns, ["credit","cr","deposit","amount_credited"])
        amt_col  = _find_col(df.columns, ["amount"])
        type_col = _find_col(df.columns, ["type","transaction_type","txn_type","dr/cr"])
        result = pd.DataFrame()
        result["date"] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce") if date_col else pd.NaT
        result["merchant_raw"] = df[desc_col].astype(str) if desc_col else "Unknown"
        if dr_col and cr_col:
            dr = _to_num(df[dr_col]); cr = _to_num(df[cr_col])
            result["amount"] = cr - dr
        elif amt_col and type_col:
            amt = _to_num(df[amt_col])
            is_cr = df[type_col].astype(str).str.upper().str.contains("CR|CREDIT|IN")
            result["amount"] = amt.where(is_cr, -amt.abs())
        elif amt_col:
            result["amount"] = -_to_num(df[amt_col]).abs()
        else:
            result["amount"] = 0
        result["source"] = "PhonePe"
        return _clean_result(result)
    except:
        return _parse_generic_csv(text, fname)

def _parse_navi_csv(text: str, fname: str) -> pd.DataFrame:
    skip = _find_header_row(text)
    try:
        df = pd.read_csv(io.StringIO(text), skiprows=skip)
        df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
        date_col = _find_col(df.columns, ["date","time","timestamp"])
        desc_col = _find_col(df.columns, ["description","merchant","name","narration","to","beneficiary"])
        dr_col   = _find_col(df.columns, ["debit","dr","withdrawal","amount_debited"])
        cr_col   = _find_col(df.columns, ["credit","cr","deposit","amount_credited"])
        amt_col  = _find_col(df.columns, ["amount"])
        result = pd.DataFrame()
        result["date"] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce") if date_col else pd.NaT
        result["merchant_raw"] = df[desc_col].astype(str) if desc_col else "Unknown"
        if dr_col and cr_col:
            dr = _to_num(df[dr_col]); cr = _to_num(df[cr_col])
            result["amount"] = cr - dr
        elif amt_col:
            result["amount"] = _to_num(df[amt_col])
        else:
            result["amount"] = 0
        result["source"] = "Navi"
        return _clean_result(result)
    except:
        return _parse_generic_csv(text, fname)

def _parse_paytm_csv(text: str, fname: str) -> pd.DataFrame:
    skip = _find_header_row(text)
    try:
        df = pd.read_csv(io.StringIO(text), skiprows=skip)
        df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
        date_col = _find_col(df.columns, ["date","transaction_date","txn_date"])
        desc_col = _find_col(df.columns, ["description","details","merchant","name","comment"])
        dr_col   = _find_col(df.columns, ["debit","dr","debited"])
        cr_col   = _find_col(df.columns, ["credit","cr","credited"])
        amt_col  = _find_col(df.columns, ["amount","net_amount"])
        result = pd.DataFrame()
        result["date"] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce") if date_col else pd.NaT
        result["merchant_raw"] = df[desc_col].astype(str) if desc_col else "Unknown"
        if dr_col and cr_col:
            dr = _to_num(df[dr_col]); cr = _to_num(df[cr_col])
            result["amount"] = cr - dr
        elif amt_col:
            result["amount"] = _to_num(df[amt_col])
        else:
            result["amount"] = 0
        result["source"] = "Paytm"
        return _clean_result(result)
    except:
        return _parse_generic_csv(text, fname)

def _parse_generic_csv(text: str, fname: str) -> pd.DataFrame:
    skip = _find_header_row(text)
    try:
        df = pd.read_csv(io.StringIO(text), skiprows=skip)
        df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
        date_col = _find_col(df.columns, ["date","time","timestamp","txn_date","value_date","posting_date"])
        desc_col = _find_col(df.columns, ["description","narration","merchant","particulars","remarks","details","name","payee","beneficiary","transaction_remarks"])
        dr_col   = _find_col(df.columns, ["debit","dr","withdrawal","amount_debited","withdraw_amt"])
        cr_col   = _find_col(df.columns, ["credit","cr","deposit","amount_credited","deposit_amt"])
        amt_col  = _find_col(df.columns, ["amount","net","transaction_amount"])
        result = pd.DataFrame()
        result["date"] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce") if date_col else pd.NaT
        result["merchant_raw"] = df[desc_col].astype(str) if desc_col else (df.iloc[:,1].astype(str) if len(df.columns)>1 else "Unknown")
        if dr_col and cr_col:
            dr = _to_num(df[dr_col]); cr = _to_num(df[cr_col])
            result["amount"] = cr - dr
        elif amt_col:
            result["amount"] = _to_num(df[amt_col])
        else:
            for col in df.columns:
                n = _to_num(df[col])
                if n.notna().sum() > len(df)*0.5:
                    result["amount"] = n; break
            else:
                result["amount"] = 0
        result["source"] = _guess_source(fname)
        return _clean_result(result)
    except Exception as e:
        raise ValueError(f"Could not parse CSV: {e}")

# ── PDF ───────────────────────────────────────────────────────────────────────
def _parse_pdf(content: bytes, fname: str) -> pd.DataFrame:
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber not installed")

    source = _guess_source(fname)
    fname_l = fname.lower()

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        # 1. Try table extraction first (works for some bank PDFs)
        all_table_rows = []
        full_text = ""
        for page in pdf.pages:
            tables = page.extract_tables({"vertical_strategy":"lines","horizontal_strategy":"lines"})
            for table in tables:
                for row in table:
                    if row and any(cell and str(cell).strip() for cell in row):
                        all_table_rows.append([str(c or "").strip() for c in row])
            t = page.extract_text()
            if t:
                full_text += t + "\n"

        # If we got good tables (>5 rows with enough cols), use them
        valid_table_rows = [r for r in all_table_rows if len(r) >= 3]
        if len(valid_table_rows) > 5:
            try:
                result = _rows_to_df(valid_table_rows, source)
                if len(result) > 3:
                    return result
            except:
                pass

        # 2. Regex-based text parsing — handles Navi, GPay, PhonePe text PDFs
        if "navi" in fname_l or "navi" in full_text.lower()[:200]:
            result = _parse_navi_pdf_text(full_text, source)
            if len(result) > 0:
                return result

        if "gpay" in fname_l or "google pay" in full_text.lower()[:500]:
            result = _parse_gpay_pdf_text(full_text, source)
            if len(result) > 0:
                return result

        if "phonepe" in fname_l or "phonepe" in full_text.lower()[:500]:
            result = _parse_phonepe_pdf_text(full_text, source)
            if len(result) > 0:
                return result

        # 3. Generic text line parser
        result = _parse_generic_pdf_text(full_text, source)
        if len(result) > 0:
            return result

    raise ValueError("Could not extract transactions. Please export as CSV from the app settings.")


def _parse_navi_pdf_text(text: str, source: str) -> pd.DataFrame:
    """
    Navi PDF actual format (confirmed from real statement):
    Each transaction appears as a single line:
    "9 Mar 2026 Paid to KUNDUKANDATHIL KUNHIMOIDEEN ₹15"
    "3 Mar 2026 Received from Vankudoth Praneeth Pamar ₹1,013"
    Text has normal spaces (unlike GPay which compresses spaces).
    """
    records = []
    for line in text.split("\n"):
        line = line.strip()
        # Match: date + "Paid to" or "Received from" + merchant + amount
        m = re.match(
            r'(\d{1,2}\s+\w{3}\s+\d{4})\s+(Paid to|Received from|Self transfer to)\s+(.+?)\s+(₹[\d,]+\.?\d*)$',
            line
        )
        if not m:
            continue
        date_str, txn_type, merchant, amount_str = m.groups()
        if 'Self transfer' in txn_type:
            continue
        dt = _try_parse_date(date_str)
        if dt is None:
            continue
        amt = float(amount_str.replace('₹', '').replace(',', ''))
        if 'Received from' not in txn_type:
            amt = -amt
        records.append({"date": dt, "merchant_raw": merchant.strip(), "amount": amt, "source": source})

    return pd.DataFrame(records) if records else pd.DataFrame()


def _parse_gpay_pdf_text(text: str, source: str) -> pd.DataFrame:
    """
    GPay PDF actual format (confirmed from real statement):
    pdfplumber compresses spaces between words, so:
    "03Dec,2025 PaidtoKUNDUKANDATHILKUNHIMOIDEEN ₹40"
    "05Dec,2025 ReceivedfromSahilDamke ₹1,000"
    "01Dec,2025 SelftransfertoIndianBank7469 ₹1,000"
    Date format: DDMon,YYYY (no spaces inside date either)
    """
    records = []
    for line in text.split("\n"):
        line = line.strip()
        # Match compressed GPay format: date + Paidto/Receivedfrom/Selftransferto + merchant + amount
        m = re.match(
            r'(\d{1,2}\w{3},\d{4})\s+(Paidto|Receivedfrom|Selftransferto)(.+?)\s+(₹[\d,]+\.?\d*)$',
            line
        )
        if not m:
            continue
        date_str, txn_type, merchant, amount_str = m.groups()
        if 'Selftransfer' in txn_type:
            continue
        # Parse compressed date: "03Dec,2025" -> datetime
        try:
            dt = datetime.strptime(date_str, "%d%b,%Y")
        except:
            continue
        amt = float(amount_str.replace('₹', '').replace(',', ''))
        is_credit = 'Receivedfrom' in txn_type
        if not is_credit:
            amt = -amt
        records.append({"date": dt, "merchant_raw": merchant.strip(), "amount": amt, "source": source})

    return pd.DataFrame(records) if records else pd.DataFrame()


def _parse_phonepe_pdf_text(text: str, source: str) -> pd.DataFrame:
    return _parse_generic_pdf_text(text, source)


def _parse_generic_pdf_text(text: str, source: str) -> pd.DataFrame:
    """
    Generic: scan every line for a date + amount pair.
    Works across many bank/UPI PDF layouts.
    """
    records = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    for i, line in enumerate(lines):
        # Find date in line
        dt = None
        for pat in DATE_PATTERNS:
            m = re.search(pat, line, re.IGNORECASE)
            if m:
                dt = _try_parse_date(m.group(1))
                if dt:
                    break
        if dt is None:
            continue

        # Find amount — check current line and next 2 lines
        amt = None
        dr_cr = None
        search_text = " ".join(lines[i:i+3])

        # Look for Dr/Cr marker
        dr_match = re.search(r'([\d,]+\.\d{2})\s*(Dr|DR|Debit|DEBIT)', search_text)
        cr_match = re.search(r'([\d,]+\.\d{2})\s*(Cr|CR|Credit|CREDIT)', search_text)
        sign_match = re.search(r'([+\-])\s*(?:₹|Rs\.?)?\s*([\d,]+(?:\.\d{2})?)', search_text)
        plain_match = re.search(r'(?:₹|Rs\.?)\s*([\d,]+(?:\.\d{2})?)', search_text)

        if dr_match:
            amt = -float(dr_match.group(1).replace(",",""))
        elif cr_match:
            amt = float(cr_match.group(1).replace(",",""))
        elif sign_match:
            val = float(sign_match.group(2).replace(",",""))
            amt = val if sign_match.group(1) == "+" else -val
        elif plain_match:
            val = float(plain_match.group(1).replace(",",""))
            amt = -val if val > 0 else val  # assume debit

        if amt is None or amt == 0:
            continue

        # Description: everything between date and amount on the line
        desc = re.sub(r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}', '', line)
        desc = re.sub(r'[\d,]+\.\d{2}', '', desc)
        desc = re.sub(r'(Dr|Cr|DR|CR|Debit|Credit|₹|Rs\.?)', '', desc)
        desc = re.sub(r'\s+', ' ', desc).strip()
        if not desc or len(desc) < 3:
            # Try pulling from next line
            if i+1 < len(lines):
                desc = lines[i+1][:60]
        if not desc:
            desc = "Transaction"

        records.append({"date": dt, "merchant_raw": desc, "amount": amt, "source": source})

    return pd.DataFrame(records) if records else pd.DataFrame()


def _parse_two_line_format(lines: list, source: str) -> list:
    """
    Some PDFs put date on one line, description+amount on the next.
    """
    records = []
    i = 0
    while i < len(lines) - 1:
        line = lines[i].strip()
        dt = None
        for pat in DATE_PATTERNS:
            m = re.search(pat, line, re.IGNORECASE)
            if m:
                dt = _try_parse_date(m.group(1))
                if dt:
                    break
        if dt:
            next_line = lines[i+1].strip()
            amt_m = re.search(r'([\d,]+\.\d{2})\s*(Dr|Cr|DR|CR)?', next_line)
            if amt_m:
                val = float(amt_m.group(1).replace(",",""))
                dr_cr = (amt_m.group(2) or "").upper()
                amt = -val if "DR" in dr_cr or not dr_cr else val
                desc = re.sub(r'[\d,]+\.\d{2}.*', '', next_line).strip()
                desc = desc or line
                records.append({"date": dt, "merchant_raw": desc, "amount": amt, "source": source})
                i += 2
                continue
        i += 1
    return records


def _rows_to_df(rows: list, source: str) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["date","merchant_raw","amount","source"])
    headers = rows[0]
    data = rows[1:]
    try:
        df = pd.DataFrame(data, columns=[str(h).lower().strip() for h in headers])
    except:
        return pd.DataFrame(columns=["date","merchant_raw","amount","source"])
    df.columns = [re.sub(r"\s+","_",c) for c in df.columns]
    date_col = _find_col(df.columns,["date","time","txn","value"])
    amount_col = _find_col(df.columns,["amount","debit","dr","withdrawal"])
    credit_col = _find_col(df.columns,["credit","cr"])
    desc_col = _find_col(df.columns,["description","narration","particulars","merchant","remarks"])
    result = pd.DataFrame()
    if date_col:
        result["date"] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
    else:
        for col in df.columns:
            dates = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
            if dates.notna().sum() > len(df)*0.5:
                result["date"] = dates; break
    result["merchant_raw"] = df[desc_col].astype(str) if desc_col else "Unknown"
    if amount_col and credit_col:
        result["amount"] = _to_num(df[credit_col]) - _to_num(df[amount_col])
    elif amount_col:
        result["amount"] = _to_num(df[amount_col])
    elif credit_col:
        result["amount"] = _to_num(df[credit_col])
    else:
        for col in df.columns:
            n = _to_num(df[col])
            if n.notna().sum() > len(df)*0.5:
                result["amount"] = n; break
        else:
            result["amount"] = 0
    if "date" not in result.columns: result["date"] = pd.NaT
    if "amount" not in result.columns: result["amount"] = 0
    result["source"] = source
    return _clean_result(result)


# ── EXCEL ─────────────────────────────────────────────────────────────────────
def _parse_excel(content: bytes, fname: str) -> pd.DataFrame:
    source = _guess_source(fname)
    try:
        xl = pd.ExcelFile(io.BytesIO(content))
        best_df = None; best_score = 0
        for sheet in xl.sheet_names:
            try:
                df = xl.parse(sheet, header=None)
                for i, row in df.iterrows():
                    row_str = " ".join(str(v).lower() for v in row if pd.notnull(v))
                    score = sum(1 for x in ["date","amount","narration","description","debit","credit"] if x in row_str)
                    if score > best_score:
                        best_score = score; best_df = xl.parse(sheet, header=i)
                if best_df is None:
                    best_df = xl.parse(sheet)
            except: continue
        if best_df is None:
            raise ValueError("Could not parse Excel")
        best_df.columns = [str(c).strip().lower().replace(" ","_") for c in best_df.columns]
        csv_text = best_df.to_csv(index=False)
        result = _parse_generic_csv(csv_text.encode(), fname)
        result["source"] = source
        return result
    except Exception as e:
        raise ValueError(f"Could not parse Excel: {e}")


# ── HELPERS ───────────────────────────────────────────────────────────────────
def _to_num(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",","").str.replace("₹","").str.replace("Rs.","").str.strip(),
        errors="coerce"
    )

def _clean_result(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["date"])
    df = df[df["date"].notna()]
    if "amount" in df.columns:
        df = df[df["amount"].notna() & (df["amount"] != 0)]
    return df.reset_index(drop=True)

def _find_header_row(text: str) -> int:
    lines = text.split("\n")
    for i, line in enumerate(lines[:25]):
        lower = line.lower()
        if sum(1 for x in ["date","amount","narration","description","merchant","debit","credit"] if x in lower) >= 2:
            return i
    return 0

def _find_col(columns, keywords):
    for kw in keywords:
        for col in columns:
            if kw in col:
                return col
    return None

def _guess_source(fname: str) -> str:
    fname = fname.lower()
    if "gpay" in fname or "google" in fname: return "Google Pay"
    if "phonepe" in fname or "phone_pe" in fname: return "PhonePe"
    if "paytm" in fname: return "Paytm"
    if "navi" in fname: return "Navi"
    if "amazon" in fname: return "Amazon Pay"
    if "axis" in fname: return "Axis Bank"
    if "hdfc" in fname: return "HDFC Bank"
    if "icici" in fname: return "ICICI Bank"
    if "sbi" in fname: return "SBI"
    if "kotak" in fname: return "Kotak Bank"
    return "Bank Statement"
