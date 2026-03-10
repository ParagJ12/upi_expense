import pandas as pd
import re

# Keyword-based fallback rules — checked against merchant_raw (uppercased)
# These fire AFTER the normalizer's hint (category_hint) but BEFORE "Other"
KEYWORD_RULES = [
    # Food
    (["RESTAURANT", "FOOD", "KITCHEN", "DHABA", "HOTEL", "CAFE", "CANTEEN",
      "BIRYANI", "DOSA", "IDLI", "CHAI", "TEA", "BAKERY", "SWEETS", "MITHAI",
      "MESS", "TIFFIN", "EATERY", "BHOJNALAYA", "DARBAR"], "Food & Dining"),
    # Transport
    (["PETROL", "DIESEL", "FUEL", "PUMP", "STATION", "AUTO", "CAB", "TAXI",
      "PARKING", "TOLL", "BUS", "TRAIN", "TICKET", "FLIGHT", "AIRWAYS",
      "AIRLINES", "TRAVELS", "TRANSPORT", "LOGISTICS"], "Transport"),
    # Groceries
    (["GROCERY", "GROCERIES", "SUPERMARKET", "HYPERMARKET", "KIRANA",
      "VEGETABLES", "FRUITS", "DAIRY", "MILK", "PROVISION"], "Groceries"),
    # Shopping
    (["PHARMACY", "MEDICAL", "CHEMIST", "CLINIC", "HOSPITAL", "SALON",
      "BEAUTY", "SPA", "PARLOUR", "BARBER", "FASHION", "CLOTHES", "CLOTHING",
      "GARMENTS", "TEXTILES", "SHOES", "FOOTWEAR", "OPTICALS", "JEWELLERY",
      "ELECTRONICS", "MOBILE", "GADGET", "BOOK", "STATIONERY"], "Shopping"),
    # Bills
    (["RECHARGE", "BROADBAND", "INTERNET", "WIFI", "ELECTRICITY", "POWER",
      "GAS", "WATER", "MAINTENANCE", "SOCIETY", "INSURANCE", "PREMIUM",
      "POSTPAID", "PREPAID", "DTH", "CABLE"], "Bills & Utilities"),
    # Entertainment
    (["CINEMA", "THEATRE", "THEATER", "MULTIPLEX", "MOVIES", "CONCERT",
      "EVENT", "SHOW", "GAMING", "GAMES", "AMUSEMENT", "SPORTS", "GYM",
      "FITNESS", "YOGA", "POOL", "BOWLING", "KARTING"], "Entertainment"),
    # Subscriptions
    (["SUBSCRIPTION", "PREMIUM", "MEMBERSHIP", "ANNUAL", "MONTHLY PLAN"], "Subscriptions"),
    # Finance
    (["INVESTMENT", "MUTUAL FUND", "SIP", "TRADING", "BROKER", "LOAN",
      "EMI", "CREDIT CARD", "WALLET", "RECHARGE", "PAYMENT GATEWAY"], "Finance"),
]


def categorize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def _assign(row):
        hint      = row.get("category_hint")
        display   = str(row.get("merchant_display", ""))
        raw       = str(row.get("merchant_raw", "")).upper()
        amount    = row.get("amount", 0)

        # 1. Normalizer gave a confident hint → use it
        if hint and pd.notnull(hint):
            return hint

        # 2. Credits → Income
        if pd.notnull(amount) and float(amount) > 0:
            return "Income / Credit"

        # 3. Keyword scan on raw merchant string
        for keywords, category in KEYWORD_RULES:
            if any(kw in raw for kw in keywords):
                return category

        # 4. Fallback
        return "Other"

    df["category"] = df.apply(_assign, axis=1)
    return df
