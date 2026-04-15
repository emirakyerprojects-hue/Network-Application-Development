"""
Lecture 4 - NBP API Demo

Explores the National Bank of Poland API to fetch currency exchange rates.
Shows how to get mid rates (Table A) and buy/sell rates (Table C).

No server needed, just calls the public API directly.

needs: pip install requests
"""

import requests
import json
from datetime import datetime, timedelta


NBP_BASE = "https://api.nbp.pl/api"


def get_rate(currency_code, table="a"):
    """fetch current exchange rate for a currency"""
    url = f"{NBP_BASE}/exchangerates/rates/{table}/{currency_code}/?format=json"
    resp = requests.get(url)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def get_table(table="a"):
    """fetch the full exchange rate table"""
    url = f"{NBP_BASE}/exchangerates/tables/{table}/?format=json"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def get_rate_by_date(currency_code, date_str, table="a"):
    """fetch exchange rate for a specific date (YYYY-MM-DD)"""
    url = f"{NBP_BASE}/exchangerates/rates/{table}/{currency_code}/{date_str}/?format=json"
    resp = requests.get(url)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def get_last_n_rates(currency_code, n=10, table="a"):
    """fetch last N exchange rates"""
    url = f"{NBP_BASE}/exchangerates/rates/{table}/{currency_code}/last/{n}/?format=json"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def main():
    print("\nLecture 4 - NBP API Demo")
    print("-" * 40)

    # --- 1. single currency rate (Table A - mid rate) ---
    print("\n1) Current USD rate (Table A - mid rate)")
    data = get_rate("USD")
    if data:
        rate = data["rates"][0]
        print(f"   Currency: {data['currency']} ({data['code']})")
        print(f"   Mid rate: {rate['mid']} PLN")
        print(f"   Date: {rate['effectiveDate']}")
        print(f"   Table: {rate['no']}")
    else:
        print("   Could not fetch USD rate")

    # --- 2. buy/sell rates (Table C) ---
    print("\n2) Current USD rate (Table C - buy/sell)")
    data = get_rate("USD", table="c")
    if data:
        rate = data["rates"][0]
        print(f"   Currency: {data['currency']} ({data['code']})")
        print(f"   Buy (bid):  {rate['bid']} PLN")
        print(f"   Sell (ask): {rate['ask']} PLN")
        print(f"   Spread: {rate['ask'] - rate['bid']:.4f} PLN")
        print(f"   -> bank buys USD from you at {rate['bid']}")
        print(f"   -> bank sells USD to you at {rate['ask']}")
    else:
        print("   Table C not available for USD right now")

    # --- 3. multiple currencies ---
    print("\n3) Rates for major currencies")
    currencies = ["USD", "EUR", "GBP", "CHF", "JPY"]
    print(f"   {'Code':<6} {'Currency':<20} {'Mid Rate':>10}")
    print(f"   {'-'*6} {'-'*20} {'-'*10}")
    for code in currencies:
        data = get_rate(code)
        if data:
            rate = data["rates"][0]
            print(f"   {data['code']:<6} {data['currency']:<20} {rate['mid']:>10.4f}")

    # --- 4. full table ---
    print("\n4) Full Table A (first 10 currencies)")
    table_data = get_table("a")
    if table_data:
        table = table_data[0]
        print(f"   Table: {table['no']} ({table['effectiveDate']})")
        print(f"   {'Code':<6} {'Currency':<30} {'Mid':>8}")
        print(f"   {'-'*6} {'-'*30} {'-'*8}")
        for rate in table["rates"][:10]:
            print(f"   {rate['code']:<6} {rate['currency']:<30} {rate['mid']:>8.4f}")
        print(f"   ... and {len(table['rates']) - 10} more")

    # --- 5. historical rate ---
    print("\n5) Historical rates (last 5 trading days for EUR)")
    data = get_last_n_rates("EUR", n=5)
    if data:
        print(f"   {'Date':<12} {'Mid':>8} {'Change':>8}")
        print(f"   {'-'*12} {'-'*8} {'-'*8}")
        prev = None
        for rate in data["rates"]:
            change = ""
            if prev is not None:
                diff = rate["mid"] - prev
                arrow = "↑" if diff > 0 else "↓" if diff < 0 else "="
                change = f"{arrow} {abs(diff):.4f}"
            print(f"   {rate['effectiveDate']:<12} {rate['mid']:>8.4f} {change:>8}")
            prev = rate["mid"]

    # --- 6. error handling ---
    print("\n6) Error handling (invalid currency)")
    data = get_rate("XYZ")
    if data is None:
        print("   get_rate('XYZ') -> None (404 - currency not found)")
        print("   -> API returns 404 for unknown currency codes")

    # --- 7. raw JSON ---
    print("\n7) Raw JSON response (for reference)")
    data = get_rate("EUR")
    if data:
        print(f"   {json.dumps(data, indent=2)[:300]}...")

    print("\n--- Key points ---")
    print("  - NBP API is free, no auth needed")
    print("  - Table A: mid rates (average)")
    print("  - Table C: buy/sell rates (what exchange offices use)")
    print("  - Returns JSON or XML")
    print("  - Our SOAP service wraps this REST API")
    print()


if __name__ == "__main__":
    main()
