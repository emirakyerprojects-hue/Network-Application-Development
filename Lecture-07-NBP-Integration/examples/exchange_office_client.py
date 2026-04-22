"""
Lecture 7 - Exchange Office Client (Full NBP Integration Demo)

Demonstrates all the new features added in Lecture 7:
1. Register user and deposit PLN (from Lecture 6)
2. Check current rates (cached)
3. Multi-currency rate queries
4. Effective rates (our buy/sell with spread)
5. Historical rates and date ranges
6. Rate statistics and trends
7. Gold prices
8. Available currencies list
9. Buy and sell currencies
10. Cache statistics
11. Transaction history

Start exchange_office_server.py first!

needs: pip install zeep
"""

from zeep import Client
from zeep.exceptions import Fault
import sys
from datetime import datetime, timedelta


def separator(title):
    print(f"\n  {'='*50}")
    print(f"  {title}")
    print(f"  {'='*50}")


def main():
    wsdl = "http://localhost:8000/?wsdl"

    print("\n" + "=" * 55)
    print("  Exchange Office - Lecture 7 (Full NBP Integration)")
    print("=" * 55)

    # connect
    print(f"\n  Connecting to {wsdl}...")
    try:
        client = Client(wsdl)
        print("  Connected!")
    except Exception as e:
        print(f"  Failed: {e}")
        print("  -> start exchange_office_server.py first")
        sys.exit(1)

    # list all operations
    print("\n  Available operations:")
    for svc in client.wsdl.services.values():
        for port in svc.ports.values():
            for op in port.binding._operations.values():
                print(f"    - {op.name}")

    # =============================================
    # STEP 1: Register & Deposit
    # =============================================
    separator("Step 1: Register User & Deposit PLN")

    user = client.service.register_user(
        username="anna_nowak", password="mypass456"
    )
    user_id = user.user_id
    print(f"  User: {user.username} (ID: {user_id})")

    balance = client.service.deposit(user_id=user_id, amount=15000.0)
    print(f"  Deposited: 15,000 PLN")
    print(f"  Balance:   {balance} PLN")

    # =============================================
    # STEP 2: Current Rates (cached)
    # =============================================
    separator("Step 2: Current Exchange Rates")

    print("\n  Mid rates (Table A):")
    for code in ["USD", "EUR", "GBP", "CHF"]:
        try:
            rate = client.service.get_rate(currency_code=code)
            print(f"    {code}: {rate.mid} PLN ({rate.date})")
        except Fault as f:
            print(f"    {code}: {f.message}")

    print("\n  Buy/Sell rates (Table C):")
    for code in ["USD", "EUR"]:
        try:
            rate = client.service.get_buy_sell_rate(currency_code=code)
            print(f"    {code}: bid={rate.bid}, ask={rate.ask}, "
                  f"spread={rate.spread}")
        except Fault as f:
            print(f"    {code}: {f.message}")

    # =============================================
    # STEP 3: Multi-currency rates (NEW)
    # =============================================
    separator("Step 3: Multi-Currency Rates (NEW)")

    print("\n  Fetching USD, EUR, GBP, CHF, JPY in one call...")
    rates = client.service.get_multiple_rates(
        currency_codes="USD,EUR,GBP,CHF,JPY"
    )
    if rates:
        print(f"\n  {'Code':<6} {'Currency':<25} {'Mid':>8}")
        print(f"  {'-'*6} {'-'*25} {'-'*8}")
        for r in rates:
            print(f"  {r.code:<6} {r.currency:<25} {r.mid:>8.4f}")

    # =============================================
    # STEP 4: Effective rates (NEW)
    # =============================================
    separator("Step 4: Our Exchange Rates (with spread)")

    print("\n  What clients actually pay/receive:")
    for code in ["USD", "EUR", "GBP"]:
        try:
            eff = client.service.get_effective_rate(currency_code=code)
            print(f"\n    {code} (source: {eff.source}):")
            print(f"      Buy at:  {eff.our_buy_rate} PLN/{code}")
            print(f"      Sell at: {eff.our_sell_rate} PLN/{code}")
            print(f"      Spread:  {eff.our_spread} PLN")
        except Fault as f:
            print(f"    {code}: {f.message}")

    # =============================================
    # STEP 5: Historical rate for a date (NEW)
    # =============================================
    separator("Step 5: Historical Rate for a Date")

    # try a recent weekday
    target = datetime.now() - timedelta(days=7)
    # skip to Monday if weekend
    while target.weekday() >= 5:
        target -= timedelta(days=1)
    date_str = target.strftime("%Y-%m-%d")

    print(f"\n  EUR rate on {date_str}:")
    try:
        rate = client.service.get_rate_for_date(
            currency_code="EUR", date=date_str
        )
        print(f"    Mid: {rate.mid} PLN")
        print(f"    Date: {rate.date}")
    except Fault as f:
        print(f"    Error: {f.message}")

    # =============================================
    # STEP 6: Rate history (NEW)
    # =============================================
    separator("Step 6: Rate History (Last 10)")

    print("\n  Last 10 USD rates:")
    history = client.service.get_rate_history(currency_code="USD", last_n=10)
    if history:
        print(f"  {'Date':<12} {'Mid':>8} {'Change':>8}")
        print(f"  {'-'*12} {'-'*8} {'-'*8}")
        prev = None
        for h in history:
            change = ""
            if prev is not None:
                diff = h.mid - prev
                arrow = "↑" if diff > 0 else "↓" if diff < 0 else "="
                change = f"{arrow} {abs(diff):.4f}"
            print(f"  {h.date:<12} {h.mid:>8.4f} {change:>8}")
            prev = h.mid

    # =============================================
    # STEP 7: Rate date range (NEW)
    # =============================================
    separator("Step 7: Rate Date Range")

    end = datetime.now()
    start = end - timedelta(days=30)
    # skip weekends
    while start.weekday() >= 5:
        start += timedelta(days=1)
    while end.weekday() >= 5:
        end -= timedelta(days=1)

    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    print(f"\n  EUR rates from {start_str} to {end_str}:")
    try:
        range_rates = client.service.get_rate_date_range(
            currency_code="EUR",
            start_date=start_str,
            end_date=end_str,
        )
        if range_rates:
            print(f"  Found {len(range_rates)} entries")
            # show first 3 and last 3
            for r in range_rates[:3]:
                print(f"    {r.date}: {r.mid}")
            if len(range_rates) > 6:
                print(f"    ... ({len(range_rates) - 6} more) ...")
            for r in range_rates[-3:]:
                print(f"    {r.date}: {r.mid}")
    except Fault as f:
        print(f"  Error: {f.message}")

    # =============================================
    # STEP 8: Rate statistics (NEW)
    # =============================================
    separator("Step 8: Rate Statistics")

    for code in ["USD", "EUR"]:
        try:
            stats = client.service.get_rate_statistics(
                currency_code=code, last_n=30
            )
            print(f"\n  {code} (last {stats.period_days} trading days):")
            print(f"    Min:     {stats.min_rate}")
            print(f"    Max:     {stats.max_rate}")
            print(f"    Average: {stats.avg_rate}")
            print(f"    Current: {stats.current_rate}")
            print(f"    Change:  {stats.change} ({stats.change_pct}%)")
            print(f"    Trend:   {stats.trend}")
            print(f"    Period:  {stats.start_date} to {stats.end_date}")
        except Fault as f:
            print(f"  {code}: {f.message}")

    # =============================================
    # STEP 9: Gold price (NEW)
    # =============================================
    separator("Step 9: Gold Price")

    try:
        gold = client.service.get_gold_price()
        print(f"\n  Current gold price: {gold.price} PLN/gram")
        print(f"  Date: {gold.date}")

        print("\n  Gold price history (last 5):")
        gold_hist = client.service.get_gold_price_history(last_n=5)
        if gold_hist:
            for g in gold_hist:
                print(f"    {g.date}: {g.price} PLN/gram")
    except Fault as f:
        print(f"  Error: {f.message}")

    # =============================================
    # STEP 10: Available currencies (NEW)
    # =============================================
    separator("Step 10: Available Currencies")

    currencies = client.service.get_available_currencies()
    if currencies:
        print(f"\n  {len(currencies)} currencies available in Table A:")
        for i, c in enumerate(currencies):
            print(f"    {c.code:<5} {c.name}")
            if i >= 14:
                print(f"    ... and {len(currencies) - 15} more")
                break

    # =============================================
    # STEP 11: Trading with cached rates
    # =============================================
    separator("Step 11: Buy/Sell with Cached Rates")

    # buy USD
    print("\n  Buying 300 USD...")
    result = client.service.buy_currency(
        user_id=user_id, currency_code="USD", amount=300.0
    )
    print(f"    Success:  {result.success}")
    print(f"    Message:  {result.message}")
    print(f"    Rate:     {result.rate} PLN/USD")
    print(f"    Cost:     {result.pln_amount} PLN")
    print(f"    PLN left: {result.new_pln_balance}")
    print(f"    USD now:  {result.new_currency_balance}")

    # buy EUR
    print("\n  Buying 200 EUR...")
    result = client.service.buy_currency(
        user_id=user_id, currency_code="EUR", amount=200.0
    )
    print(f"    Success:  {result.success}")
    print(f"    Rate:     {result.rate} PLN/EUR")
    print(f"    Cost:     {result.pln_amount} PLN")
    print(f"    PLN left: {result.new_pln_balance}")

    # sell some USD
    print("\n  Selling 100 USD...")
    result = client.service.sell_currency(
        user_id=user_id, currency_code="USD", amount=100.0
    )
    print(f"    Success:  {result.success}")
    print(f"    Rate:     {result.rate} PLN/USD")
    print(f"    Revenue:  {result.pln_amount} PLN")
    print(f"    PLN now:  {result.new_pln_balance}")
    print(f"    USD left: {result.new_currency_balance}")

    # =============================================
    # STEP 12: Cache statistics (NEW)
    # =============================================
    separator("Step 12: Cache Statistics")

    cache = client.service.get_cache_stats()
    print(f"\n  API calls:      {cache.api_calls}")
    print(f"  Cache hits:     {cache.cache_hits}")
    print(f"  Cached entries: {cache.cached_entries}")
    print(f"  Hit rate:       {cache.hit_rate}")

    # =============================================
    # STEP 13: Transaction history
    # =============================================
    separator("Step 13: Transaction History")

    txns = client.service.get_transaction_history(user_id=user_id)
    if txns:
        print(f"\n  {'Type':<6} {'Currency':<10} {'Amount':>8} {'Rate':>8} "
              f"{'PLN':>10}  {'Time'}")
        print(f"  {'-'*6} {'-'*10} {'-'*8} {'-'*8} {'-'*10}  {'-'*19}")
        for t in txns:
            time_short = t.timestamp[:19] if t.timestamp else ""
            print(f"  {t.tx_type:<6} {t.currency_code:<10} {t.amount:>8.2f} "
                  f"{t.rate:>8.4f} {t.pln_amount:>10.2f}  {time_short}")

    # =============================================
    # STEP 14: Final balances
    # =============================================
    separator("Step 14: Final Portfolio")

    balances = client.service.get_balance(user_id=user_id)
    print("\n  Final balances:")
    for b in balances:
        print(f"    {b.currency_code}: {b.balance}")

    total_txns = len(txns) if txns else 0
    print(f"\n  Total transactions: {total_txns}")
    print(f"\n  Demo complete! All Lecture 7 features tested.")
    print()


if __name__ == "__main__":
    main()
