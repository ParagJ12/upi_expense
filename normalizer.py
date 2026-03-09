import pandas as pd
import re
try:
    from rapidfuzz import process, fuzz as _fuzz
    def _fuzzy_match(query, choices, cutoff=75):
        result = process.extractOne(query, choices, scorer=_fuzz.token_set_ratio, score_cutoff=cutoff)
        return result[0] if result else None
except ImportError:
    from difflib import SequenceMatcher
    def _fuzzy_match(query, choices, cutoff=75):
        best, best_score = None, 0
        q = query.lower()
        for c in choices:
            score = SequenceMatcher(None, q, c.lower()).ratio() * 100
            if score > best_score and score >= cutoff:
                best, best_score = c, score
        return best

# ── Master merchant dictionary ────────────────────────────────────────────────
# Maps raw name patterns → (display_name, category)
MERCHANT_MAP = {
    # Food & Dining
    "ZOMATO": ("Zomato", "Food & Dining"),
    "BUNDL": ("Zomato", "Food & Dining"),
    "BUNDLTECH": ("Zomato", "Food & Dining"),
    "BUNDL TECHNOLOGIES": ("Zomato", "Food & Dining"),
    "SWIGGY": ("Swiggy", "Food & Dining"),
    "SWGY": ("Swiggy", "Food & Dining"),
    "BUNDL TECH": ("Zomato", "Food & Dining"),
    "MCDONALDS": ("McDonald's", "Food & Dining"),
    "MCDONALD": ("McDonald's", "Food & Dining"),
    "DOMINOS": ("Domino's", "Food & Dining"),
    "JUBILANT": ("Domino's", "Food & Dining"),
    "JUBILANT FOODWORKS": ("Domino's", "Food & Dining"),
    "SUBWAY": ("Subway", "Food & Dining"),
    "BURGER KING": ("Burger King", "Food & Dining"),
    "BKIL": ("Burger King", "Food & Dining"),
    "KFC": ("KFC", "Food & Dining"),
    "DEVYANI": ("KFC", "Food & Dining"),
    "PIZZA HUT": ("Pizza Hut", "Food & Dining"),
    "YUMRESTAURANTS": ("Pizza Hut", "Food & Dining"),
    "STARBUCKS": ("Starbucks", "Food & Dining"),
    "TATA STARBUCKS": ("Starbucks", "Food & Dining"),
    "CAFE COFFEE DAY": ("Café Coffee Day", "Food & Dining"),
    "CCD": ("Café Coffee Day", "Food & Dining"),
    "CHAAYOS": ("Chaayos", "Food & Dining"),
    "CHAI POINT": ("Chai Point", "Food & Dining"),
    "BOX8": ("Box8", "Food & Dining"),
    "FRESHMENU": ("Freshmenu", "Food & Dining"),
    "FAASOS": ("Faasos", "Food & Dining"),
    "REBEL FOODS": ("Faasos", "Food & Dining"),
    "LUNCHBOX": ("Lunchbox", "Food & Dining"),

    # Transport
    "UBER": ("Uber", "Transport"),
    "UBER INDIA": ("Uber", "Transport"),
    "OLA": ("Ola", "Transport"),
    "ANI TECHNOLOGIES": ("Ola", "Transport"),
    "RAPIDO": ("Rapido", "Transport"),
    "ROPPEN": ("Rapido", "Transport"),
    "METRO": ("Metro Rail", "Transport"),
    "DMRC": ("Metro Rail", "Transport"),
    "BMRC": ("Metro Rail", "Transport"),
    "IRCTC": ("IRCTC", "Transport"),
    "INDIAN RAILWAY": ("Indian Railways", "Transport"),
    "RAILWAYS": ("Indian Railways", "Transport"),
    "REDBUS": ("RedBus", "Transport"),
    "MAKEMYTRIP": ("MakeMyTrip", "Transport"),
    "GOIBIBO": ("Goibibo", "Transport"),
    "CLEARTRIP": ("Cleartrip", "Transport"),
    "IXIGO": ("Ixigo", "Transport"),
    "YATRA": ("Yatra", "Transport"),
    "INDIGO": ("IndiGo Airlines", "Transport"),
    "INTERGLOBE": ("IndiGo Airlines", "Transport"),
    "AIRINDIA": ("Air India", "Transport"),
    "AIR INDIA": ("Air India", "Transport"),
    "SPICEJET": ("SpiceJet", "Transport"),
    "AKASA": ("Akasa Air", "Transport"),
    "VISTARA": ("Vistara", "Transport"),
    "PETROL": ("Fuel", "Transport"),
    "FUEL": ("Fuel", "Transport"),
    "HINDUSTAN PETROLEUM": ("HPCL Fuel", "Transport"),
    "HPCL": ("HPCL Fuel", "Transport"),
    "BPCL": ("BPCL Fuel", "Transport"),
    "INDIAN OIL": ("Indian Oil", "Transport"),

    # Shopping
    "AMAZON": ("Amazon", "Shopping"),
    "AMZN": ("Amazon", "Shopping"),
    "FLIPKART": ("Flipkart", "Shopping"),
    "FK ": ("Flipkart", "Shopping"),
    "MYNTRA": ("Myntra", "Shopping"),
    "MEESHO": ("Meesho", "Shopping"),
    "AJIO": ("AJIO", "Shopping"),
    "NYKAA": ("Nykaa", "Shopping"),
    "PEPPERFRY": ("Pepperfry", "Shopping"),
    "IKEA": ("IKEA", "Shopping"),
    "CROMA": ("Croma", "Shopping"),
    "RELIANCE DIGITAL": ("Reliance Digital", "Shopping"),
    "VIJAY SALES": ("Vijay Sales", "Shopping"),
    "TANISHQ": ("Tanishq", "Shopping"),
    "WESTSIDE": ("Westside", "Shopping"),
    "ZARA": ("Zara", "Shopping"),
    "H&M": ("H&M", "Shopping"),
    "PANTALOONS": ("Pantaloons", "Shopping"),
    "MAX FASHION": ("Max Fashion", "Shopping"),
    "SHOPPERS STOP": ("Shoppers Stop", "Shopping"),
    "SNAPDEAL": ("Snapdeal", "Shopping"),
    "1MG": ("1mg", "Shopping"),
    "PHARMEASY": ("PharmEasy", "Shopping"),
    "NETMEDS": ("Netmeds", "Shopping"),
    "MEDPLUS": ("MedPlus", "Shopping"),
    "APOLLO PHARMACY": ("Apollo Pharmacy", "Shopping"),

    # Bills & Utilities
    "AIRTEL": ("Airtel", "Bills & Utilities"),
    "JIO": ("Jio", "Bills & Utilities"),
    "RELIANCE JIO": ("Jio", "Bills & Utilities"),
    "BSNL": ("BSNL", "Bills & Utilities"),
    "VODAFONE": ("Vi (Vodafone)", "Bills & Utilities"),
    "VI ": ("Vi (Vodafone)", "Bills & Utilities"),
    "IDEA": ("Vi (Vodafone)", "Bills & Utilities"),
    "TATA PLAY": ("Tata Play", "Bills & Utilities"),
    "DISH TV": ("Dish TV", "Bills & Utilities"),
    "D2H": ("Dish TV", "Bills & Utilities"),
    "HATHWAY": ("Hathway", "Bills & Utilities"),
    "ACT FIBERNET": ("ACT Fibernet", "Bills & Utilities"),
    "BESCOM": ("BESCOM (Electricity)", "Bills & Utilities"),
    "MSEDCL": ("MSEDCL (Electricity)", "Bills & Utilities"),
    "TPDDL": ("TPDDL (Electricity)", "Bills & Utilities"),
    "BSES": ("BSES (Electricity)", "Bills & Utilities"),
    "TORRENT POWER": ("Torrent Power", "Bills & Utilities"),
    "ADANI ELECTRICITY": ("Adani Electricity", "Bills & Utilities"),
    "GAS": ("Gas Bill", "Bills & Utilities"),
    "MGL": ("Mahanagar Gas", "Bills & Utilities"),
    "IGL": ("Indraprastha Gas", "Bills & Utilities"),
    "HOUSING SOCIETY": ("Housing Society", "Bills & Utilities"),
    "MAINTENANCE": ("Society Maintenance", "Bills & Utilities"),
    "SULEKHA": ("Sulekha Services", "Bills & Utilities"),
    "BBMP": ("BBMP", "Bills & Utilities"),
    "MUNICIPAL": ("Municipal Taxes", "Bills & Utilities"),
    "LIC": ("LIC Insurance", "Bills & Utilities"),
    "ICICI LOMBARD": ("ICICI Lombard", "Bills & Utilities"),
    "HDFC ERGO": ("HDFC Ergo", "Bills & Utilities"),
    "STAR HEALTH": ("Star Health Insurance", "Bills & Utilities"),
    "NAVI INSURANCE": ("Navi Insurance", "Bills & Utilities"),

    # Groceries
    "BIGBASKET": ("BigBasket", "Groceries"),
    "BB ": ("BigBasket", "Groceries"),
    "BLINKIT": ("Blinkit", "Groceries"),
    "GROFERS": ("Blinkit", "Groceries"),
    "ZEPTO": ("Zepto", "Groceries"),
    "DUNZO": ("Dunzo", "Groceries"),
    "SWIGGY INSTAMART": ("Swiggy Instamart", "Groceries"),
    "INSTAMART": ("Swiggy Instamart", "Groceries"),
    "DMART": ("DMart", "Groceries"),
    "D-MART": ("DMart", "Groceries"),
    "AVENUE SUPERMARTS": ("DMart", "Groceries"),
    "RELIANCE FRESH": ("Reliance Fresh", "Groceries"),
    "RELIANCE SMART": ("Reliance Smart", "Groceries"),
    "MORE SUPERMARKET": ("More Supermarket", "Groceries"),
    "NATURE BASKET": ("Nature's Basket", "Groceries"),
    "SPAR": ("SPAR", "Groceries"),
    "LICIOUS": ("Licious", "Groceries"),
    "FRESHTOHOME": ("FreshToHome", "Groceries"),
    "MILK BASKET": ("MilkBasket", "Groceries"),
    "AMAZON FRESH": ("Amazon Fresh", "Groceries"),
    "SUPR DAILY": ("SuprDaily", "Groceries"),
    "COUNTRY DELIGHT": ("Country Delight", "Groceries"),

    # Entertainment
    "BOOKMYSHOW": ("BookMyShow", "Entertainment"),
    "BMS": ("BookMyShow", "Entertainment"),
    "PVR": ("PVR Cinemas", "Entertainment"),
    "INOX": ("INOX", "Entertainment"),
    "CINEPOLIS": ("Cinepolis", "Entertainment"),
    "CARNIVAL CINEMAS": ("Carnival Cinemas", "Entertainment"),
    "WONDERLA": ("Wonderla", "Entertainment"),
    "ESCAPE ROOMS": ("Escape Rooms", "Entertainment"),
    "SMAAASH": ("Smaaash", "Entertainment"),
    "GAMESCRAFT": ("Games", "Entertainment"),

    # Subscriptions
    "NETFLIX": ("Netflix", "Subscriptions"),
    "HOTSTAR": ("Disney+ Hotstar", "Subscriptions"),
    "DISNEY": ("Disney+ Hotstar", "Subscriptions"),
    "STAR DISNEY": ("Disney+ Hotstar", "Subscriptions"),
    "SONYLIV": ("SonyLIV", "Subscriptions"),
    "ZEE5": ("ZEE5", "Subscriptions"),
    "PRIME VIDEO": ("Amazon Prime", "Subscriptions"),
    "AMAZON PRIME": ("Amazon Prime", "Subscriptions"),
    "SPOTIFY": ("Spotify", "Subscriptions"),
    "YOUTUBE PREMIUM": ("YouTube Premium", "Subscriptions"),
    "GOOGLE ONE": ("Google One", "Subscriptions"),
    "APPLE": ("Apple", "Subscriptions"),
    "MICROSOFT": ("Microsoft 365", "Subscriptions"),
    "LINKEDIN": ("LinkedIn Premium", "Subscriptions"),
    "NOTION": ("Notion", "Subscriptions"),
    "CANVA": ("Canva Pro", "Subscriptions"),
    "ZOOM": ("Zoom", "Subscriptions"),
    "DROPBOX": ("Dropbox", "Subscriptions"),
    "TIMES PRIME": ("Times Prime", "Subscriptions"),
    "JIOCINEMA": ("JioCinema", "Subscriptions"),
    "MXPLAYER": ("MX Player", "Subscriptions"),
    "GAANA": ("Gaana", "Subscriptions"),
    "SAAVN": ("JioSaavn", "Subscriptions"),
    "WYNK": ("Wynk Music", "Subscriptions"),
    "LENSKART": ("Lenskart", "Shopping"),
    "VEDANTU": ("Vedantu", "Subscriptions"),
    "BYJUS": ("BYJU'S", "Subscriptions"),
    "UNACADEMY": ("Unacademy", "Subscriptions"),
    "COURSERA": ("Coursera", "Subscriptions"),
    "UDEMY": ("Udemy", "Subscriptions"),
    "CHESS": ("Chess.com", "Subscriptions"),

    # Finance
    "GROWW": ("Groww", "Finance"),
    "ZERODHA": ("Zerodha", "Finance"),
    "UPSTOX": ("Upstox", "Finance"),
    "COIN": ("Zerodha Coin", "Finance"),
    "SMALLCASE": ("smallcase", "Finance"),
    "PAYTM MONEY": ("Paytm Money", "Finance"),
    "ANGEL BROKING": ("Angel One", "Finance"),
    "MOTILAL": ("Motilal Oswal", "Finance"),
    "SIP": ("SIP Investment", "Finance"),
    "MUTUAL FUND": ("Mutual Fund", "Finance"),
    "NAVI": ("Navi", "Finance"),
    "CRED": ("CRED", "Finance"),
    "JUPITER": ("Jupiter", "Finance"),
    "SLICE": ("Slice", "Finance"),
    "FAMPAY": ("FamPay", "Finance"),
    "NIYO": ("Niyo", "Finance"),
}

# Fuzzy match candidates (cleaned keys)
_FUZZY_KEYS = list(MERCHANT_MAP.keys())


def _clean(s: str) -> str:
    """Aggressive cleaning of raw merchant strings."""
    s = str(s).upper().strip()
    # Remove UPI prefix patterns
    s = re.sub(r"^UPI[-/]?", "", s)
    s = re.sub(r"^NEFT[-/]?", "", s)
    s = re.sub(r"^IMPS[-/]?", "", s)
    # Remove reference numbers
    s = re.sub(r"\b\d{6,}\b", "", s)
    # Remove common suffixes
    s = re.sub(r"\b(PVT|LTD|TECHNOLOGIES|TECH|INDIA|PRIVATE|LIMITED|SOLUTIONS|SERVICES|PTE|INC|LLC)\b", "", s)
    # Remove punctuation and extra spaces
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_merchants(df: pd.DataFrame) -> pd.DataFrame:
    """Add merchant_display and category_hint columns based on merchant_raw."""
    df = df.copy()
    if "merchant_raw" not in df.columns:
        df["merchant_raw"] = df.get("merchant", "Unknown")

    merchant_display = []
    category_hint = []

    for raw in df["merchant_raw"]:
        display, cat = _resolve_merchant(str(raw))
        merchant_display.append(display)
        category_hint.append(cat)

    df["merchant_display"] = merchant_display
    df["category_hint"] = category_hint
    return df


def _resolve_merchant(raw: str) -> tuple:
    """L1 exact → L2 fuzzy → L3 pattern → L4 fallback."""
    cleaned = _clean(raw)

    # L1 — exact substring match on cleaned keys
    for key, (display, cat) in MERCHANT_MAP.items():
        if key in cleaned:
            return display, cat

    # L2 — fuzzy match
    key = _fuzzy_match(cleaned, _FUZZY_KEYS)
    if key:
        return MERCHANT_MAP[key]

    # L3 — detect peer transfer patterns
    if _is_peer_transfer(raw):
        name = _extract_person_name(raw)
        return name, "Peer Transfers"

    # L4 — return cleaned name, unknown category
    display = _make_readable(raw)
    return display, None


def _is_peer_transfer(raw: str) -> bool:
    """Detect person-to-person transfers."""
    peer_signals = ["@OKAXIS", "@OKSBI", "@YBL", "@PAYTM", "@IDFCFIRST", "@NAVIAXIS",
                    "@OKHDFCBANK", "@OKICICI", "@AXISBANK", "SEND MONEY", "PAY TO"]
    upper = raw.upper()
    return any(sig in upper for sig in peer_signals)


def _extract_person_name(raw: str) -> str:
    """Try to extract a human name from a peer transfer string."""
    cleaned = re.sub(r"UPI[-/]?|SEND MONEY|PAY TO", "", raw, flags=re.IGNORECASE).strip()
    # Remove UPI ID suffix
    cleaned = re.sub(r"@\w+", "", cleaned).strip()
    # Remove ref numbers
    cleaned = re.sub(r"\b\d{4,}\b", "", cleaned).strip()
    cleaned = re.sub(r"[^\w\s]", " ", cleaned).strip()
    words = [w for w in cleaned.split() if len(w) > 1 and not w.isdigit()]
    if words:
        return " ".join(w.title() for w in words[:3])
    return "Personal Transfer"


def _make_readable(raw: str) -> str:
    """Convert raw merchant string to something readable."""
    s = re.sub(r"UPI[-/]?|NEFT[-/]?|IMPS[-/]?", "", str(raw), flags=re.IGNORECASE)
    s = re.sub(r"\b\d{6,}\b", "", s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    words = [w.capitalize() for w in s.split() if len(w) > 1]
    return " ".join(words[:4]) if words else "Unknown"
