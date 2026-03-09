import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def get_sample_data() -> pd.DataFrame:
    """Generate realistic mock UPI transactions across 3 months."""
    random.seed(42)
    np.random.seed(42)

    base = datetime(2025, 4, 1)
    transactions = []

    # Aryan's typical spending patterns (college student)
    templates = [
        # (merchant_raw, min_amt, max_amt, frequency_per_month, source, is_debit)
        ("BUNDL TECHNOLOGIES PVT LTD", 150, 450, 12, "Google Pay", True),    # Zomato
        ("SWGY*SWIGGY", 120, 380, 10, "PhonePe", True),                       # Swiggy
        ("UBER INDIA SYSTEMS PVT", 80, 280, 14, "Google Pay", True),           # Uber
        ("ANI TECHNOLOGIES PVT LTD", 70, 200, 8, "Navi", True),               # Ola
        ("ROPPEN TRANSPORTATION", 40, 120, 10, "PhonePe", True),               # Rapido
        ("AMAZON SELLER SERVICES", 299, 2499, 4, "Google Pay", True),          # Amazon
        ("FLIPKART INTERNET PVT", 399, 1999, 3, "PhonePe", True),              # Flipkart
        ("BIGBASKET RETAIL IND", 400, 900, 3, "Google Pay", True),             # BigBasket
        ("BLINKIT", 150, 450, 6, "PhonePe", True),                            # Blinkit
        ("ZEPTO", 120, 380, 4, "Navi", True),                                  # Zepto
        ("NETFLIX ENTERTAINMENT", 649, 649, 1, "Google Pay", True),            # Netflix
        ("SPOTIFY AB", 119, 119, 1, "PhonePe", True),                         # Spotify
        ("DISNEY HOTSTAR", 299, 299, 1, "Google Pay", True),                   # Hotstar
        ("AIRTEL PAYMENTS", 599, 599, 1, "PhonePe", True),                    # Airtel
        ("RELIANCE JIO INFOCOMM", 249, 249, 1, "Google Pay", True),           # Jio
        ("BESCOM ELECTRICITY", 800, 1800, 1, "PhonePe", True),                # BESCOM
        ("PVR CINEMAS", 250, 650, 2, "Google Pay", True),                     # PVR
        ("BOOKMYSHOW INTERNET", 180, 420, 2, "PhonePe", True),                # BMS
        ("MCDONALDS INDIA", 180, 420, 3, "Google Pay", True),                 # McDonald's
        ("JUBILANT FOODWORKS", 350, 750, 2, "Navi", True),                    # Dominos
        ("STARBUCKS COFFEE", 280, 480, 3, "Google Pay", True),                # Starbucks
        ("GROWW INVEST TECH", 500, 2000, 2, "PhonePe", True),                 # Groww
        ("DMART AVENUE SUPERMARTS", 600, 1500, 2, "Google Pay", True),        # DMart
        ("UPI-RAHUL SHARMA@OKAXIS", 200, 1500, 3, "Google Pay", True),        # Peer transfer
        ("UPI-PRIYA NAIR@YBL", 150, 800, 2, "PhonePe", True),                # Peer transfer
        ("UPI-AMIT KUMAR@OKSBI", 300, 2000, 2, "Navi", True),                # Peer transfer
        ("GOOGLE ONE STORAGE", 130, 130, 1, "Google Pay", True),              # Google One
        ("UDEMY INC", 499, 999, 1, "PhonePe", True),                          # Udemy
        ("RAPIDO BIKE", 35, 90, 12, "Google Pay", True),                      # Rapido
        ("CHAAYOS RETAIL", 80, 180, 6, "Navi", True),                         # Chaayos
        # Credits
        ("NEFT-PARENT-TRANSFER", 8000, 15000, 1, "Google Pay", False),        # Allowance
        ("SPLITWISE-SETTLEMENT", 200, 1200, 2, "PhonePe", False),             # Reimbursement
        ("UPI-INTERNSHIP STIPEND", 5000, 10000, 1, "Google Pay", False),      # Internship
    ]

    for month_offset in range(3):
        month_start = base + timedelta(days=30 * month_offset)

        for merchant_raw, min_amt, max_amt, freq, source, is_debit in templates:
            count = max(1, freq + random.randint(-2, 2))
            if is_debit:
                count = min(count, freq + 2)

            for _ in range(count):
                day_offset = random.randint(0, 29)
                txn_date = month_start + timedelta(days=day_offset)

                amount = round(random.uniform(min_amt, max_amt), 0)
                if is_debit:
                    amount = -amount

                transactions.append({
                    "date": txn_date,
                    "merchant_raw": merchant_raw,
                    "amount": amount,
                    "source": source
                })

    df = pd.DataFrame(transactions)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date", ascending=False).reset_index(drop=True)
    return df
