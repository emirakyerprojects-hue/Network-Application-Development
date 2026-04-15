"""
Lecture 5 - Exchange Office Client (Basic)

Connects to the skeleton exchange office service and tests
the operations that are already implemented.

Start exchange_office_server.py first!

needs: pip install zeep
"""

from zeep import Client
from zeep.exceptions import Fault
import sys


def main():
    wsdl = "http://localhost:8000/?wsdl"

    print("\nExchange Office Client (Basic)")
    print("-" * 40)

    # connect
    print(f"  Connecting to {wsdl}...")
    try:
        client = Client(wsdl)
        print("  Connected!\n")
    except Exception as e:
        print(f"  Failed: {e}")
        print("  -> start exchange_office_server.py first")
        sys.exit(1)

    # list operations from WSDL
    print("  Operations found in WSDL:")
    for svc in client.wsdl.services.values():
        for port in svc.ports.values():
            for op in port.binding._operations.values():
                print(f"    - {op.name}")
    print()

    # --- 1. register a user ---
    print("  1) Registering user 'testuser'...")
    try:
        user = client.service.register_user(
            username="testuser", password="pass123"
        )
        user_id = user.user_id
        print(f"     User created: {user.username} (id: {user_id})")
        print(f"     Created at: {user.created_at}")
    except Fault as f:
        print(f"     Error: {f.message}")
        return

    # --- 2. deposit PLN ---
    print("\n  2) Depositing 10000 PLN...")
    balance = client.service.deposit(user_id=user_id, amount=10000.0)
    print(f"     New PLN balance: {balance}")

    # --- 3. check balance ---
    print("\n  3) Checking balance...")
    balances = client.service.get_balance(user_id=user_id)
    if balances:
        for b in balances:
            print(f"     {b.currency_code}: {b.balance}")

    # --- 4. get exchange rate ---
    print("\n  4) Getting exchange rates...")
    for code in ["USD", "EUR", "GBP"]:
        try:
            rate = client.service.get_rate(currency_code=code)
            print(f"     {code}: {rate.mid} PLN ({rate.date})")
        except Fault as f:
            print(f"     {code}: error - {f.message}")

    # --- 5. get buy/sell rate ---
    print("\n  5) Buy/sell rates:")
    try:
        rate = client.service.get_buy_sell_rate(currency_code="USD")
        print(f"     USD buy:  {rate.bid} PLN")
        print(f"     USD sell: {rate.ask} PLN")
        print(f"     Spread:  {rate.spread} PLN")
    except Fault as f:
        print(f"     Error: {f.message}")

    # --- 6. test buy (stub) ---
    print("\n  6) Trying to buy currency (should return TODO)...")
    result = client.service.buy_currency(
        user_id=user_id, currency_code="USD", amount=100.0
    )
    print(f"     Success: {result.success}")
    print(f"     Message: {result.message}")

    # --- 7. transaction history ---
    print("\n  7) Transaction history:")
    txns = client.service.get_transaction_history(user_id=user_id)
    if txns:
        for t in txns:
            print(f"     [{t.tx_type}] {t.amount} {t.currency_code} "
                  f"@ {t.rate} = {t.pln_amount} PLN")
    else:
        print("     (no transactions yet - buy/sell not implemented)")

    print("\n  Architecture is set up!")
    print("  Next step: implement buy/sell logic in Lecture 6")
    print()


if __name__ == "__main__":
    main()
