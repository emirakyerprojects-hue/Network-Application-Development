"""
Lecture 7 - NBP Integration Demo (Standalone)

Demonstrates the NbpApiClient class without needing a SOAP server.
Shows caching, retries, multi-currency queries, historical data,
statistics, and gold prices.

No server needed — just calls the NBP API directly.

needs: pip install requests
"""

import sys
import os

# add current dir for nbp_client import
sys.path.insert(0, os.path.dirname(__file__))

from nbp_client import NbpApiClient
from datetime import datetime, timedelta


def separator(title):
    print(f"\n  {'='*50}")
    print(f"  {title}")
    print(f"  {'='*50}")


def main():
    print("\nLecture 7 - NBP API Integration Demo")
    print("-" * 45)

    # create client with 60s cache for demo
    client = NbpApiClient(cache_ttl=60, max_retries=3, timeout=10)

    # --- 1. single rate ---
    separator("1) Single Currency Rate")

    rate = client.get_mid_rate("USD")
    if rate:
        print(f"  USD mid rate: {rate['mid']} PLN")
        print(f"  Date: {rate['date']}")
        print(f"  Source: Table A ({rate['table_no']})")

    # --- 2. buy/sell rates ---
    separator("2) Buy/Sell Rates (Table C)")

    bs = client.get_buy_sell_rate("USD")
    if bs:
        print(f"  USD:")
        print(f"    Bid (bank buys):  {bs['bid']} PLN")
        print(f"    Ask (bank sells): {bs['ask']} PLN")
        print(f"    Spread: {bs['spread']} PLN")
    else:
        print("  Table C not available right now")

    # --- 3. multiple currencies at once ---
    separator("3) Multiple Currencies")

    rates = client.get_multiple_mid_rates(
        ["USD", "EUR", "GBP", "CHF", "JPY", "CZK", "SEK"]
    )
    print(f"\n  {'Code':<6} {'Currency':<25} {'Mid':>8}")
    print(f"  {'-'*6} {'-'*25} {'-'*8}")
    for r in rates:
        print(f"  {r['code']:<6} {r['currency']:<25} {r['mid']:>8.4f}")

    # --- 4. effective rates (our exchange office rates) ---
    separator("4) Our Exchange Office Rates")

    for code in ["USD", "EUR", "GBP"]:
        eff = client.get_effective_rate(code, spread_pct=1.5)
        if eff:
            print(f"\n  {code} (source: {eff['source']}):")
            print(f"    Our buy rate:  {eff['our_buy_rate']} PLN/{code}")
            print(f"    Our sell rate: {eff['our_sell_rate']} PLN/{code}")
            print(f"    Our spread:    {eff['our_spread']} PLN")
            print(f"    Spread %:      {eff['spread_pct']}%")

    # --- 5. historical rate for a date ---
    separator("5) Historical Rate")

    # find a recent weekday
    target = datetime.now() - timedelta(days=7)
    while target.weekday() >= 5:
        target -= timedelta(days=1)
    date_str = target.strftime("%Y-%m-%d")

    rate = client.get_rate_for_date("EUR", date_str)
    if rate:
        print(f"  EUR on {date_str}: {rate['mid']} PLN")
    else:
        print(f"  No data for {date_str} (might be a holiday)")

    # --- 6. rate history ---
    separator("6) Rate History (Last 10)")

    history = client.get_rate_history("USD", last_n=10)
    if history:
        print(f"\n  {'Date':<12} {'Mid':>8} {'Change':>10}")
        print(f"  {'-'*12} {'-'*8} {'-'*10}")
        prev = None
        for h in history:
            change = ""
            if prev is not None:
                diff = h["mid"] - prev
                arrow = "↑" if diff > 0 else "↓" if diff < 0 else "="
                change = f"{arrow} {abs(diff):.4f}"
            print(f"  {h['date']:<12} {h['mid']:>8.4f} {change:>10}")
            prev = h["mid"]

    # --- 7. date range ---
    separator("7) Rate Date Range")

    end = datetime.now()
    start = end - timedelta(days=14)
    while start.weekday() >= 5:
        start += timedelta(days=1)
    while end.weekday() >= 5:
        end -= timedelta(days=1)

    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    range_rates = client.get_rate_date_range("EUR", start_str, end_str)
    if range_rates:
        print(f"\n  EUR from {start_str} to {end_str}: {len(range_rates)} entries")
        for r in range_rates:
            print(f"    {r['date']}: {r['mid']} PLN")

    # --- 8. statistics ---
    separator("8) Rate Statistics")

    for code in ["USD", "EUR", "GBP"]:
        stats = client.get_rate_statistics(code, last_n=30)
        if stats:
            print(f"\n  {code} (last {stats['period_days']} trading days):")
            print(f"    Min:     {stats['min']}")
            print(f"    Max:     {stats['max']}")
            print(f"    Average: {stats['avg']}")
            print(f"    Current: {stats['current']}")
            print(f"    Change:  {stats['change']} ({stats['change_pct']}%)")
            print(f"    Trend:   {stats['trend']}")

    # --- 9. gold prices ---
    separator("9) Gold Prices")

    gold = client.get_gold_price()
    if gold:
        print(f"\n  Current gold price: {gold['price']} PLN/gram")
        print(f"  Date: {gold['date']}")

    gold_hist = client.get_gold_price_history(last_n=5)
    if gold_hist:
        print(f"\n  Last 5 gold prices:")
        for g in gold_hist:
            print(f"    {g['date']}: {g['price']} PLN/gram")

    # --- 10. available currencies ---
    separator("10) Available Currencies")

    currencies = client.get_available_currencies()
    if currencies:
        print(f"\n  {len(currencies)} currencies in Table A:")
        for c in currencies[:10]:
            print(f"    {c['code']:<5} {c['name']}")
        if len(currencies) > 10:
            print(f"    ... and {len(currencies) - 10} more")

    # --- 11. caching demo ---
    separator("11) Caching Demo")

    print("\n  Calling get_mid_rate('USD') 5 times...")
    for i in range(5):
        r = client.get_mid_rate("USD")
        if r:
            print(f"    Call {i+1}: {r['mid']} PLN")

    stats = client.get_cache_stats()
    print(f"\n  Cache stats after demo:")
    print(f"    Total API calls: {stats['api_calls']}")
    print(f"    Cache hits:      {stats['cache_hits']}")
    print(f"    Cached entries:  {stats['cached_entries']}")
    print(f"    Hit rate:        {stats['hit_rate']}")

    # --- 12. currency check ---
    separator("12) Currency Validation")

    for code in ["USD", "EUR", "XYZ", "BTC"]:
        supported = client.is_currency_supported(code)
        status = "✓ supported" if supported else "✗ not found"
        print(f"    {code}: {status}")

    print(f"\n--- Key points ---")
    print(f"  - NbpApiClient caches responses (TTL: {client.cache_ttl}s)")
    print(f"  - Retries failed requests up to {client.max_retries} times")
    print(f"  - Supports Table A (mid), Table C (bid/ask), and gold prices")
    print(f"  - Historical data: last N, date range, specific date")
    print(f"  - Statistics: min, max, avg, trend analysis")
    print()


if __name__ == "__main__":
    main()
