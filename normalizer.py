import pandas as pd
import re
try:
    from rapidfuzz import process, fuzz as _fuzz
    def _fuzzy_match(query, choices, cutoff=72):
        result = process.extractOne(query, choices, scorer=_fuzz.token_set_ratio, score_cutoff=cutoff)
        return result[0] if result else None
except ImportError:
    from difflib import SequenceMatcher
    def _fuzzy_match(query, choices, cutoff=72):
        best, best_score = None, 0
        q = query.lower()
        for c in choices:
            score = SequenceMatcher(None, q, c.lower()).ratio() * 100
            if score > best_score and score >= cutoff:
                best, best_score = c, score
        return best

# ── Master merchant dictionary ────────────────────────────────────────────────
# Maps raw name patterns → (display_name, category)
# NOTE: Keys are checked as SUBSTRINGS in the CLEANED merchant string (uppercased, no spaces stripped)
# So "CAFECOFFEEDAY" will match "CAFECOFFEE DAY IIT MADRAS" after space removal
MERCHANT_MAP = {
    # Food & Dining
    "ZOMATO":               ("Zomato",           "Food & Dining"),
    "BUNDL":                ("Zomato",           "Food & Dining"),
    "SWIGGY":               ("Swiggy",           "Food & Dining"),
    "SWGY":                 ("Swiggy",           "Food & Dining"),
    "MCDONALDS":            ("McDonald's",        "Food & Dining"),
    "MCDONALD":             ("McDonald's",        "Food & Dining"),
    "DOMINOS":              ("Domino's",          "Food & Dining"),
    "JUBILANT":             ("Domino's",          "Food & Dining"),
    "SUBWAY":               ("Subway",            "Food & Dining"),
    "BURGERKING":           ("Burger King",       "Food & Dining"),
    "BURGER KING":          ("Burger King",       "Food & Dining"),
    "BKIL":                 ("Burger King",       "Food & Dining"),
    "KFC":                  ("KFC",               "Food & Dining"),
    "DEVYANI":              ("KFC",               "Food & Dining"),
    "PIZZAHUT":             ("Pizza Hut",         "Food & Dining"),
    "PIZZA HUT":            ("Pizza Hut",         "Food & Dining"),
    "STARBUCKS":            ("Starbucks",         "Food & Dining"),
    "CAFECOFFEEDAY":        ("Café Coffee Day",   "Food & Dining"),
    "CAFE COFFEE DAY":      ("Café Coffee Day",   "Food & Dining"),
    "CCD":                  ("Café Coffee Day",   "Food & Dining"),
    "CHAAYOS":              ("Chaayos",           "Food & Dining"),
    "CHAIPOINT":            ("Chai Point",        "Food & Dining"),
    "CHAI POINT":           ("Chai Point",        "Food & Dining"),
    "BOX8":                 ("Box8",              "Food & Dining"),
    "FRESHMENU":            ("Freshmenu",         "Food & Dining"),
    "FAASOS":               ("Faasos",            "Food & Dining"),
    "REBEL FOODS":          ("Faasos",            "Food & Dining"),
    "REBELFOODS":           ("Faasos",            "Food & Dining"),
    "LUNCHBOX":             ("Lunchbox",          "Food & Dining"),
    "VENDIFY":              ("Vendify",           "Food & Dining"),  # campus food
    "ISTHARA":              ("Isthara Cafeteria", "Food & Dining"),  # campus cafeteria
    "ZAITOON":              ("Zaitoon",           "Food & Dining"),
    "SARDAR":               ("Sardar Restaurant", "Food & Dining"),

    # Transport
    "UBER":                 ("Uber",              "Transport"),
    "OLA":                  ("Ola",               "Transport"),
    "ANITECH":              ("Ola",               "Transport"),
    "ANI TECH":             ("Ola",               "Transport"),
    "ANI TECHNOLOGIES":     ("Ola",               "Transport"),
    "ANI ":                 ("Ola",               "Transport"),
    "RAPIDO":               ("Rapido",            "Transport"),
    "ROPPEN":               ("Rapido",            "Transport"),
    "METRO":                ("Metro Rail",        "Transport"),
    "DMRC":                 ("Metro Rail",        "Transport"),
    "BMRC":                 ("Metro Rail",        "Transport"),
    "IRCTC":                ("IRCTC",             "Transport"),
    "INDIAN RAILWAY":       ("Indian Railways",   "Transport"),
    "INDIANRAILWAY":        ("Indian Railways",   "Transport"),
    "RAILWAYS":             ("Indian Railways",   "Transport"),
    "REDBUS":               ("RedBus",            "Transport"),
    "MAKEMYTRIP":           ("MakeMyTrip",        "Transport"),
    "GOIBIBO":              ("Goibibo",           "Transport"),
    "CLEARTRIP":            ("Cleartrip",         "Transport"),
    "IXIGO":                ("Ixigo",             "Transport"),
    "YATRA":                ("Yatra",             "Transport"),
    "INDIGO":               ("IndiGo Airlines",   "Transport"),
    "INTERGLOBE":           ("IndiGo Airlines",   "Transport"),
    "AIRINDIA":             ("Air India",         "Transport"),
    "AIR INDIA":            ("Air India",         "Transport"),
    "SPICEJET":             ("SpiceJet",          "Transport"),
    "AKASA":                ("Akasa Air",         "Transport"),
    "VISTARA":              ("Vistara",           "Transport"),
    "HPCL":                 ("HPCL Fuel",         "Transport"),
    "BPCL":                 ("BPCL Fuel",         "Transport"),
    "INDIAN OIL":           ("Indian Oil",        "Transport"),
    "INDIANOIL":            ("Indian Oil",        "Transport"),
    "PETROL":               ("Fuel",              "Transport"),

    # Shopping
    "AMAZON":               ("Amazon",            "Shopping"),
    "AMZN":                 ("Amazon",            "Shopping"),
    "FLIPKART":             ("Flipkart",          "Shopping"),
    "MYNTRA":               ("Myntra",            "Shopping"),
    "MEESHO":               ("Meesho",            "Shopping"),
    "AJIO":                 ("AJIO",              "Shopping"),
    "NYKAA":                ("Nykaa",             "Shopping"),
    "PEPPERFRY":            ("Pepperfry",         "Shopping"),
    "IKEA":                 ("IKEA",              "Shopping"),
    "CROMA":                ("Croma",             "Shopping"),
    "RELIANCEDIGITAL":      ("Reliance Digital",  "Shopping"),
    "RELIANCE DIGITAL":     ("Reliance Digital",  "Shopping"),
    "VIJAYSALES":           ("Vijay Sales",       "Shopping"),
    "VIJAY SALES":          ("Vijay Sales",       "Shopping"),
    "TANISHQ":              ("Tanishq",           "Shopping"),
    "WESTSIDE":             ("Westside",          "Shopping"),
    "ZARA":                 ("Zara",              "Shopping"),
    "H&M":                  ("H&M",               "Shopping"),
    "PANTALOONS":           ("Pantaloons",        "Shopping"),
    "MAXFASHION":           ("Max Fashion",       "Shopping"),
    "MAX FASHION":          ("Max Fashion",       "Shopping"),
    "SHOPPERSSTOP":         ("Shoppers Stop",     "Shopping"),
    "SHOPPERS STOP":        ("Shoppers Stop",     "Shopping"),
    "SNAPDEAL":             ("Snapdeal",          "Shopping"),
    "1MG":                  ("1mg",               "Shopping"),
    "PHARMEASY":            ("PharmEasy",         "Shopping"),
    "NETMEDS":              ("Netmeds",           "Shopping"),
    "MEDPLUS":              ("MedPlus",           "Shopping"),
    "APOLLOPHARMACY":       ("Apollo Pharmacy",   "Shopping"),
    "APOLLO PHARMACY":      ("Apollo Pharmacy",   "Shopping"),
    "LENSKART":             ("Lenskart",          "Shopping"),
    "HABIBS":               ("Habibs Salon",      "Shopping"),   # from Navi txn
    "HABIB":                ("Habibs Salon",      "Shopping"),

    # Bills & Utilities
    "AIRTEL":               ("Airtel",            "Bills & Utilities"),
    "MYJIO":                ("Jio",               "Bills & Utilities"),
    "JIO":                  ("Jio",               "Bills & Utilities"),
    "RELIANCEJIO":          ("Jio",               "Bills & Utilities"),
    "RELIANCE JIO":         ("Jio",               "Bills & Utilities"),
    "BSNL":                 ("BSNL",              "Bills & Utilities"),
    "VODAFONE":             ("Vi",                "Bills & Utilities"),
    "TATAPLAY":             ("Tata Play",         "Bills & Utilities"),
    "TATA PLAY":            ("Tata Play",         "Bills & Utilities"),
    "DISHTV":               ("Dish TV",           "Bills & Utilities"),
    "DISH TV":              ("Dish TV",           "Bills & Utilities"),
    "HATHWAY":              ("Hathway",           "Bills & Utilities"),
    "ACTFIBERNET":          ("ACT Fibernet",      "Bills & Utilities"),
    "ACT FIBERNET":         ("ACT Fibernet",      "Bills & Utilities"),
    "BESCOM":               ("Electricity",       "Bills & Utilities"),
    "MSEDCL":               ("Electricity",       "Bills & Utilities"),
    "TPDDL":                ("Electricity",       "Bills & Utilities"),
    "BSES":                 ("Electricity",       "Bills & Utilities"),
    "TORRENTPOWER":         ("Torrent Power",     "Bills & Utilities"),
    "TORRENT POWER":        ("Torrent Power",     "Bills & Utilities"),
    "ADANIELECTRICITY":     ("Adani Electricity", "Bills & Utilities"),
    "MGL":                  ("Mahanagar Gas",     "Bills & Utilities"),
    "IGL":                  ("IGL Gas",           "Bills & Utilities"),
    "LIC":                  ("LIC",               "Bills & Utilities"),
    "ICICILOMBARD":         ("ICICI Lombard",     "Bills & Utilities"),
    "HDFCERGO":             ("HDFC Ergo",         "Bills & Utilities"),
    "STARHEALTH":           ("Star Health",       "Bills & Utilities"),
    "MAINTENANCE":          ("Maintenance",       "Bills & Utilities"),

    # Groceries
    "BIGBASKET":            ("BigBasket",         "Groceries"),
    "BLINKIT":              ("Blinkit",           "Groceries"),
    "GROFERS":              ("Blinkit",           "Groceries"),
    "ZEPTO":                ("Zepto",             "Groceries"),
    "DUNZO":                ("Dunzo",             "Groceries"),
    "INSTAMART":            ("Swiggy Instamart",  "Groceries"),
    "DMART":                ("DMart",             "Groceries"),
    "AVENUESUPERMARTS":     ("DMart",             "Groceries"),
    "RELIANCEFRESH":        ("Reliance Fresh",    "Groceries"),
    "RELIANCE FRESH":       ("Reliance Fresh",    "Groceries"),
    "RELIANCESMART":        ("Reliance Smart",    "Groceries"),
    "MORESUPERMARKET":      ("More Supermarket",  "Groceries"),
    "SPAR":                 ("SPAR",              "Groceries"),
    "LICIOUS":              ("Licious",           "Groceries"),
    "FRESHTOHOME":          ("FreshToHome",       "Groceries"),
    "MILKBASKET":           ("MilkBasket",        "Groceries"),
    "AMAZONFRESH":          ("Amazon Fresh",      "Groceries"),
    "AMAZON FRESH":         ("Amazon Fresh",      "Groceries"),
    "COUNTRYDELIGHT":       ("Country Delight",   "Groceries"),
    "COUNTRY DELIGHT":      ("Country Delight",   "Groceries"),

    # Entertainment
    "BOOKMYSHOW":           ("BookMyShow",        "Entertainment"),
    "BMS":                  ("BookMyShow",        "Entertainment"),
    "PVR":                  ("PVR Cinemas",       "Entertainment"),
    "INOX":                 ("INOX",              "Entertainment"),
    "CINEPOLIS":            ("Cinepolis",         "Entertainment"),
    "WONDERLA":             ("Wonderla",          "Entertainment"),
    "SMAAASH":              ("Smaaash",           "Entertainment"),

    # Subscriptions
    "NETFLIX":              ("Netflix",           "Subscriptions"),
    "HOTSTAR":              ("Disney+ Hotstar",   "Subscriptions"),
    "DISNEY":               ("Disney+ Hotstar",   "Subscriptions"),
    "SONYLIV":              ("SonyLIV",           "Subscriptions"),
    "ZEE5":                 ("ZEE5",              "Subscriptions"),
    "PRIMEVIDEO":           ("Amazon Prime",      "Subscriptions"),
    "PRIME VIDEO":          ("Amazon Prime",      "Subscriptions"),
    "AMAZONPRIME":          ("Amazon Prime",      "Subscriptions"),
    "SPOTIFY":              ("Spotify",           "Subscriptions"),
    "YOUTUBEPREMIUM":       ("YouTube Premium",   "Subscriptions"),
    "YOUTUBE PREMIUM":      ("YouTube Premium",   "Subscriptions"),
    "GOOGLEONE":            ("Google One",        "Subscriptions"),
    "GOOGLE ONE":           ("Google One",        "Subscriptions"),
    "APPLE":                ("Apple",             "Subscriptions"),
    "MICROSOFT":            ("Microsoft",         "Subscriptions"),
    "LINKEDIN":             ("LinkedIn",          "Subscriptions"),
    "NOTION":               ("Notion",            "Subscriptions"),
    "CANVA":                ("Canva",             "Subscriptions"),
    "ZOOM":                 ("Zoom",              "Subscriptions"),
    "DROPBOX":              ("Dropbox",           "Subscriptions"),
    "TIMESPRIME":           ("Times Prime",       "Subscriptions"),
    "TIMES PRIME":          ("Times Prime",       "Subscriptions"),
    "JIOCINEMA":            ("JioCinema",         "Subscriptions"),
    "GAANA":                ("Gaana",             "Subscriptions"),
    "SAAVN":                ("JioSaavn",          "Subscriptions"),
    "WYNK":                 ("Wynk Music",        "Subscriptions"),
    "VEDANTU":              ("Vedantu",           "Subscriptions"),
    "BYJUS":                ("BYJU'S",            "Subscriptions"),
    "UNACADEMY":            ("Unacademy",         "Subscriptions"),
    "COURSERA":             ("Coursera",          "Subscriptions"),
    "UDEMY":                ("Udemy",             "Subscriptions"),

    # Finance
    "GROWW":                ("Groww",             "Finance"),
    "ZERODHA":              ("Zerodha",           "Finance"),
    "UPSTOX":               ("Upstox",            "Finance"),
    "SMALLCASE":            ("Smallcase",         "Finance"),
    "PAYTMMONEY":           ("Paytm Money",       "Finance"),
    "ANGELBROKING":         ("Angel One",         "Finance"),
    "MOTILAL":              ("Motilal Oswal",     "Finance"),
    "CRED":                 ("CRED",              "Finance"),
    "JUPITER":              ("Jupiter",           "Finance"),
    "SLICE":                ("Slice",             "Finance"),
}

_FUZZY_KEYS = list(MERCHANT_MAP.keys())


def _clean(s: str) -> str:
    """Clean merchant string for matching. Preserves spaces for readability but uppercases."""
    s = str(s).upper().strip()
    # Remove UPI prefix patterns
    s = re.sub(r"^(UPI|NEFT|IMPS|RTGS)[-/\s]?", "", s)
    # Remove transaction ref numbers (8+ digits)
    s = re.sub(r"\b\d{8,}\b", "", s)
    # Remove common corporate suffixes
    s = re.sub(r"\b(PVT|PRIVATE|LIMITED|LTD|TECHNOLOGIES|TECH|INDIA|SOLUTIONS|SERVICES|PTE|INC|LLC|INFOTECH)\b", "", s)
    # Normalize spaces
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _clean_nospace(s: str) -> str:
    """Like _clean but also removes ALL spaces — for matching space-compressed GPay names."""
    return re.sub(r"\s+", "", _clean(s))


def normalize_merchants(df: pd.DataFrame) -> pd.DataFrame:
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
    """L1 exact → L1b space-stripped → L2 fuzzy → L3 peer → L4 fallback."""
    cleaned        = _clean(raw)
    cleaned_nospace = _clean_nospace(raw)

    # L1 — substring match on cleaned string (with spaces)
    for key, (display, cat) in MERCHANT_MAP.items():
        if key in cleaned:
            return display, cat

    # L1b — substring match on space-stripped string (catches GPay compressed names)
    for key, (display, cat) in MERCHANT_MAP.items():
        key_nospace = key.replace(" ", "")
        if key_nospace in cleaned_nospace:
            return display, cat

    # L2 — fuzzy match (try both versions)
    key = _fuzzy_match(cleaned, _FUZZY_KEYS) or _fuzzy_match(cleaned_nospace, _FUZZY_KEYS)
    if key:
        return MERCHANT_MAP[key]

    # L3 — detect peer transfer (person name in Paid to / Received from)
    if _is_peer_transfer(raw):
        name = _extract_person_name(raw)
        return name, "Peer Transfers"

    # L3b — detect if it looks like a person name (all-caps, 2-4 words, no digits)
    if _looks_like_person(raw):
        name = _make_readable(raw)
        return name, "Peer Transfers"

    # L4 — return readable name, unknown category
    return _make_readable(raw), None


def _is_peer_transfer(raw: str) -> bool:
    peer_signals = ["@OKAXIS", "@OKSBI", "@YBL", "@PAYTM", "@IDFCFIRST",
                    "@NAVIAXIS", "@OKHDFCBANK", "@OKICICI", "@AXISBANK",
                    "SEND MONEY", "PAY TO"]
    upper = raw.upper()
    return any(sig in upper for sig in peer_signals)


def _looks_like_person(raw: str) -> bool:
    """Detect all-caps person names (2-4 capitalised words, no digits, no brand keywords)."""
    s = raw.strip().upper()
    # Must be 2-4 words
    words = [w for w in re.split(r"\s+", s) if w]
    if not (2 <= len(words) <= 5):
        return False
    # No digits
    if re.search(r"\d", s):
        return False
    # No brand-like keywords
    brand_terms = {"PAY", "BANK", "UPI", "PAYMENT", "SERVICE", "TECH", "DIGITAL",
                   "PVTLTD", "LTD", "INC", "CAFE", "RESTAURANT", "SHOP", "STORE"}
    for w in words:
        if w in brand_terms:
            return False
    return True


def _extract_person_name(raw: str) -> str:
    cleaned = re.sub(r"UPI[-/]?|SEND MONEY|PAY TO", "", raw, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"@\w+", "", cleaned).strip()
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
    # Title-case
    words = [w.capitalize() for w in s.split() if len(w) > 1]
    return " ".join(words[:5]) if words else "Unknown"
