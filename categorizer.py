import pandas as pd

# Category mapping from known merchant display names
DISPLAY_TO_CATEGORY = {
    # Food & Dining
    "Zomato": "Food & Dining", "Swiggy": "Food & Dining", "McDonald's": "Food & Dining",
    "Domino's": "Food & Dining", "Subway": "Food & Dining", "Burger King": "Food & Dining",
    "KFC": "Food & Dining", "Pizza Hut": "Food & Dining", "Starbucks": "Food & Dining",
    "Café Coffee Day": "Food & Dining", "Chaayos": "Food & Dining", "Chai Point": "Food & Dining",
    "Box8": "Food & Dining", "Freshmenu": "Food & Dining", "Faasos": "Food & Dining",
    "Lunchbox": "Food & Dining",
    # Transport
    "Uber": "Transport", "Ola": "Transport", "Rapido": "Transport", "Metro Rail": "Transport",
    "IRCTC": "Transport", "Indian Railways": "Transport", "RedBus": "Transport",
    "MakeMyTrip": "Transport", "Goibibo": "Transport", "Cleartrip": "Transport",
    "Ixigo": "Transport", "Yatra": "Transport", "IndiGo Airlines": "Transport",
    "Air India": "Transport", "SpiceJet": "Transport", "Akasa Air": "Transport",
    "Vistara": "Transport", "Fuel": "Transport", "HPCL Fuel": "Transport",
    "BPCL Fuel": "Transport", "Indian Oil": "Transport",
    # Shopping
    "Amazon": "Shopping", "Flipkart": "Shopping", "Myntra": "Shopping",
    "Meesho": "Shopping", "AJIO": "Shopping", "Nykaa": "Shopping",
    "Pepperfry": "Shopping", "IKEA": "Shopping", "Croma": "Shopping",
    "Reliance Digital": "Shopping", "Vijay Sales": "Shopping", "Tanishq": "Shopping",
    "Westside": "Shopping", "Zara": "Shopping", "H&M": "Shopping",
    "Pantaloons": "Shopping", "Max Fashion": "Shopping", "Shoppers Stop": "Shopping",
    "Snapdeal": "Shopping", "1mg": "Shopping", "PharmEasy": "Shopping",
    "Netmeds": "Shopping", "MedPlus": "Shopping", "Apollo Pharmacy": "Shopping",
    "Lenskart": "Shopping",
    # Bills & Utilities
    "Airtel": "Bills & Utilities", "Jio": "Bills & Utilities", "BSNL": "Bills & Utilities",
    "Vi (Vodafone)": "Bills & Utilities", "Tata Play": "Bills & Utilities",
    "Dish TV": "Bills & Utilities", "Hathway": "Bills & Utilities",
    "ACT Fibernet": "Bills & Utilities", "BESCOM (Electricity)": "Bills & Utilities",
    "MSEDCL (Electricity)": "Bills & Utilities", "TPDDL (Electricity)": "Bills & Utilities",
    "BSES (Electricity)": "Bills & Utilities", "Torrent Power": "Bills & Utilities",
    "Adani Electricity": "Bills & Utilities", "Gas Bill": "Bills & Utilities",
    "Mahanagar Gas": "Bills & Utilities", "Indraprastha Gas": "Bills & Utilities",
    "Housing Society": "Bills & Utilities", "Society Maintenance": "Bills & Utilities",
    "LIC Insurance": "Bills & Utilities", "ICICI Lombard": "Bills & Utilities",
    "HDFC Ergo": "Bills & Utilities", "Star Health Insurance": "Bills & Utilities",
    "Navi Insurance": "Bills & Utilities",
    # Groceries
    "BigBasket": "Groceries", "Blinkit": "Groceries", "Zepto": "Groceries",
    "Dunzo": "Groceries", "Swiggy Instamart": "Groceries", "DMart": "Groceries",
    "Reliance Fresh": "Groceries", "Reliance Smart": "Groceries",
    "More Supermarket": "Groceries", "Nature's Basket": "Groceries", "SPAR": "Groceries",
    "Licious": "Groceries", "FreshToHome": "Groceries", "MilkBasket": "Groceries",
    "Amazon Fresh": "Groceries", "SuprDaily": "Groceries", "Country Delight": "Groceries",
    # Entertainment
    "BookMyShow": "Entertainment", "PVR Cinemas": "Entertainment", "INOX": "Entertainment",
    "Cinepolis": "Entertainment", "Carnival Cinemas": "Entertainment",
    "Wonderla": "Entertainment", "Smaaash": "Entertainment", "Games": "Entertainment",
    # Subscriptions
    "Netflix": "Subscriptions", "Disney+ Hotstar": "Subscriptions", "SonyLIV": "Subscriptions",
    "ZEE5": "Subscriptions", "Amazon Prime": "Subscriptions", "Spotify": "Subscriptions",
    "YouTube Premium": "Subscriptions", "Google One": "Subscriptions", "Apple": "Subscriptions",
    "Microsoft 365": "Subscriptions", "LinkedIn Premium": "Subscriptions", "Notion": "Subscriptions",
    "Canva Pro": "Subscriptions", "Zoom": "Subscriptions", "Dropbox": "Subscriptions",
    "Times Prime": "Subscriptions", "JioCinema": "Subscriptions", "MX Player": "Subscriptions",
    "Gaana": "Subscriptions", "JioSaavn": "Subscriptions", "Wynk Music": "Subscriptions",
    "Vedantu": "Subscriptions", "BYJU'S": "Subscriptions", "Unacademy": "Subscriptions",
    "Coursera": "Subscriptions", "Udemy": "Subscriptions", "Chess.com": "Subscriptions",
    # Finance
    "Groww": "Finance", "Zerodha": "Finance", "Upstox": "Finance",
    "Zerodha Coin": "Finance", "smallcase": "Finance", "Paytm Money": "Finance",
    "Angel One": "Finance", "Motilal Oswal": "Finance", "SIP Investment": "Finance",
    "Mutual Fund": "Finance", "Navi": "Finance", "CRED": "Finance",
    "Jupiter": "Finance", "Slice": "Finance",
    # Peer Transfers
    "Personal Transfer": "Peer Transfers",
}


def categorize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Assign final category to each transaction."""
    df = df.copy()

    def _assign(row):
        # 1. Use hint from normalizer if it's confident
        if pd.notnull(row.get("category_hint")) and row["category_hint"] is not None:
            return row["category_hint"]
        # 2. Look up display name in category map
        display = row.get("merchant_display", "")
        if display in DISPLAY_TO_CATEGORY:
            return DISPLAY_TO_CATEGORY[display]
        # 3. Peer transfer detection
        if row.get("category_hint") == "Peer Transfers":
            return "Peer Transfers"
        # 4. Credits (money received) — don't assign spend category
        amount = row.get("amount", 0)
        if pd.notnull(amount) and float(amount) > 0:
            return "Income / Credit"
        # 5. Fallback
        return "Other"

    df["category"] = df.apply(_assign, axis=1)
    return df
