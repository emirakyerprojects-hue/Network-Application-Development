"""
Lecture 4 - Exchange Rate SOAP Client

Calls the exchange rate SOAP service using Zeep.
Shows that the client doesn't need to know about the NBP API —
it just calls SOAP methods and gets structured data back.

Start exchange_rate_server.py first!

needs: pip install zeep
"""

from zeep import Client
from zeep.exceptions import Fault
import sys


def main():
    wsdl = "http://localhost:8000/?wsdl"

    print("\nExchange Rate Client (using Zeep)")
    print("-" * 40)

    # connect
    print(f"  Connecting to {wsdl}...")
    try:
        client = Client(wsdl)
        print("  Connected!\n")
    except Exception as e:
        print(f"  Failed: {e}")
        print("  -> start exchange_rate_server.py first")
        sys.exit(1)

    # list available operations
    print("  Available operations:")
    for svc in client.wsdl.services.values():
        for port in svc.ports.values():
            for op in port.binding._operations.values():
                print(f"    - {op.name}")
    print()

    # --- 1. get mid rate ---
    print("  1) Mid rate for USD:")
    result = client.service.get_rate(currency_code="USD")
    print(f"     {result.currency} ({result.code})")
    print(f"     Mid rate: {result.mid} PLN")
    print(f"     Date: {result.date}")

    # --- 2. get buy/sell rate ---
    print("\n  2) Buy/Sell rate for EUR:")
    try:
        result = client.service.get_buy_sell_rate(currency_code="EUR")
        print(f"     {result.currency} ({result.code})")
        print(f"     Buy (bid):  {result.bid} PLN")
        print(f"     Sell (ask): {result.ask} PLN")
        print(f"     Spread: {result.spread} PLN")
    except Fault as f:
        print(f"     SOAP Fault: {f.message}")
        print("     (Table C might not be available for this currency)")

    # --- 3. multiple currencies ---
    print("\n  3) Rates for major currencies:")
    for code in ["USD", "EUR", "GBP", "CHF"]:
        result = client.service.get_rate(currency_code=code)
        print(f"     {code}: {result.mid} PLN")

    # --- 4. rate history ---
    print("\n  4) USD rate history (last 5 days):")
    history = client.service.get_rate_history(currency_code="USD", last_n=5)
    if history:
        for entry in history:
            print(f"     {entry.date}: {entry.mid} PLN")

    # --- 5. supported currencies ---
    print("\n  5) Supported currencies (first 10):")
    currencies = client.service.get_supported_currencies()
    if currencies:
        for c in currencies[:10]:
            print(f"     {c.code} - {c.name}")
        print(f"     ... total: {len(currencies)} currencies")

    # --- 6. error handling ---
    print("\n  6) Error handling (invalid currency):")
    try:
        client.service.get_rate(currency_code="INVALID")
    except Fault as f:
        print(f"     SOAP Fault: {f.message}")
        print("     -> service returns a proper SOAP error")

    # --- 7. historical rate ---
    print("\n  7) EUR rate on specific date:")
    try:
        result = client.service.get_rate_by_date(
            currency_code="EUR", date="2024-12-02"
        )
        print(f"     EUR on {result.date}: {result.mid} PLN")
    except Fault as f:
        print(f"     SOAP Fault: {f.message}")

    print("\n  Summary:")
    print("  - Client only knows about SOAP, not REST/JSON")
    print("  - Zeep generated the proxy from WSDL automatically")
    print("  - NBP API details are hidden inside the server")
    print("  - This is the whole point of service abstraction")
    print()


if __name__ == "__main__":
    main()
