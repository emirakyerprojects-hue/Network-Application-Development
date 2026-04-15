"""
Lecture 6 - Exchange Office Client (Full Demo)

Demonstrates the complete flow:
1. Register a user
2. Deposit PLN
3. Check exchange rates
4. Buy foreign currencies
5. Sell some back
6. View transaction history
7. Check final balances

Start exchange_office_server.py first!

needs: pip install zeep
"""

from zeep import Client
from zeep.exceptions import Fault
import sys


def separator(title):
    print(f"\n  {'='*45}")
    print(f"  {title}")
    print(f"  {'='*45}")


def main():
    wsdl = "http://localhost:8000/?wsdl"

    print("\n" + "=" * 50)
    print("  Exchange Office - Full Demo")
    print("=" * 50)

    # connect
    print(f"\n  Connecting to {wsdl}...")
    try:
        client = Client(wsdl)
        print("  Connected!")
    except Exception as e:
        print(f"  Failed: {e}")
        print("  -> start exchange_office_server.py first")
        sys.exit(1)

    # list operations
    print("\n  Available operations:")
    for svc in client.wsdl.services.values():
        for port in svc.ports.values():
            for op in port.binding._operations.values():
                print(f"    - {op.name}")

    # =============================================
    # STEP 1: Register
    # =============================================
    separator("Step 1: Register User")

    user = client.service.register_user(
        username="jan_kowalski", password="securepass123"
    )
    user_id = user.user_id
    print(f"  User: {user.username}")
    print(f"  ID:   {user_id}")
    print(f"  Date: {user.created_at}")

    # =============================================
    # STEP 2: Deposit PLN
    # =============================================
    separator("Step 2: Deposit PLN")

    balance = client.service.deposit(user_id=user_id, amount=10000.0)
    print(f"  Deposited: 10,000 PLN")
    print(f"  Balance:   {balance} PLN")

    # =============================================
    # STEP 3: Check rates
    # =============================================
    separator("Step 3: Check Exchange Rates")

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
            print(f"    {code}: buy={rate.bid}, sell={rate.ask}, "
                  f"spread={rate.spread}")
        except Fault as f:
            print(f"    {code}: {f.message}")

    # =============================================
    # STEP 4: Buy currencies
    # =============================================
    separator("Step 4: Buy Currencies")

    # buy USD
    print("\n  Buying 200 USD...")
    result = client.service.buy_currency(
        user_id=user_id, currency_code="USD", amount=200.0
    )
    print(f"    Success:  {result.success}")
    print(f"    Rate:     {result.rate} PLN/USD")
    print(f"    Cost:     {result.pln_amount} PLN")
    print(f"    PLN left: {result.new_pln_balance}")
    print(f"    USD now:  {result.new_currency_balance}")
    print(f"    Tx ID:    {result.transaction_id}")

    # buy EUR
    print("\n  Buying 150 EUR...")
    result = client.service.buy_currency(
        user_id=user_id, currency_code="EUR", amount=150.0
    )
    print(f"    Success:  {result.success}")
    print(f"    Rate:     {result.rate} PLN/EUR")
    print(f"    Cost:     {result.pln_amount} PLN")
    print(f"    PLN left: {result.new_pln_balance}")
    print(f"    EUR now:  {result.new_currency_balance}")

    # buy GBP
    print("\n  Buying 50 GBP...")
    result = client.service.buy_currency(
        user_id=user_id, currency_code="GBP", amount=50.0
    )
    print(f"    Success:  {result.success}")
    print(f"    Rate:     {result.rate} PLN/GBP")
    print(f"    Cost:     {result.pln_amount} PLN")
    print(f"    PLN left: {result.new_pln_balance}")
    print(f"    GBP now:  {result.new_currency_balance}")

    # =============================================
    # STEP 5: Check balance after buying
    # =============================================
    separator("Step 5: Current Portfolio")

    balances = client.service.get_balance(user_id=user_id)
    print("\n  Balances:")
    for b in balances:
        print(f"    {b.currency_code}: {b.balance}")

    # =============================================
    # STEP 6: Sell some currency
    # =============================================
    separator("Step 6: Sell Currencies")

    # sell 100 USD
    print("\n  Selling 100 USD...")
    result = client.service.sell_currency(
        user_id=user_id, currency_code="USD", amount=100.0
    )
    print(f"    Success:  {result.success}")
    print(f"    Rate:     {result.rate} PLN/USD")
    print(f"    Revenue:  {result.pln_amount} PLN")
    print(f"    PLN now:  {result.new_pln_balance}")
    print(f"    USD left: {result.new_currency_balance}")

    # sell 50 EUR
    print("\n  Selling 50 EUR...")
    result = client.service.sell_currency(
        user_id=user_id, currency_code="EUR", amount=50.0
    )
    print(f"    Success:  {result.success}")
    print(f"    Rate:     {result.rate} PLN/EUR")
    print(f"    Revenue:  {result.pln_amount} PLN")
    print(f"    PLN now:  {result.new_pln_balance}")
    print(f"    EUR left: {result.new_currency_balance}")

    # =============================================
    # STEP 7: Try to sell more than we have (error case)
    # =============================================
    separator("Step 7: Error Handling")

    print("\n  Trying to sell 999 GBP (we only have 50)...")
    result = client.service.sell_currency(
        user_id=user_id, currency_code="GBP", amount=999.0
    )
    print(f"    Success: {result.success}")
    print(f"    Message: {result.message}")

    print("\n  Trying to buy with invalid currency...")
    try:
        client.service.buy_currency(
            user_id=user_id, currency_code="XYZ", amount=10.0
        )
    except Fault as f:
        print(f"    SOAP Fault: {f.message}")

    # =============================================
    # STEP 8: Transaction history
    # =============================================
    separator("Step 8: Transaction History")

    txns = client.service.get_transaction_history(user_id=user_id)
    if txns:
        print(f"\n  {'Type':<6} {'Currency':<10} {'Amount':>8} {'Rate':>8} "
              f"{'PLN':>10}  {'Time'}")
        print(f"  {'-'*6} {'-'*10} {'-'*8} {'-'*8} {'-'*10}  {'-'*19}")
        for t in txns:
            time_short = t.timestamp[:19] if t.timestamp else ""
            print(f"  {t.tx_type:<6} {t.currency_code:<10} {t.amount:>8.2f} "
                  f"{t.rate:>8.4f} {t.pln_amount:>10.2f}  {time_short}")
    else:
        print("  (no transactions)")

    # =============================================
    # STEP 9: Final balances
    # =============================================
    separator("Step 9: Final Portfolio")

    balances = client.service.get_balance(user_id=user_id)
    print("\n  Final balances:")
    for b in balances:
        print(f"    {b.currency_code}: {b.balance}")

    total_txns = len(txns) if txns else 0
    print(f"\n  Total transactions: {total_txns}")
    print(f"\n  Demo complete!")
    print()


if __name__ == "__main__":
    main()
