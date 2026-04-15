"""
Lecture 5 - Exchange Office Server (Skeleton)

This is the initial version of the exchange office service.
It has all the operations defined but only basic ones implemented.
The full exchange logic comes in Lecture 6.

For now:
- register_user and deposit work
- get_rate works (calls NBP API)
- buy/sell are stubs that return TODOs

WSDL: http://localhost:8000/?wsdl

needs: pip install spyne lxml requests
"""

import sys
import os

# add parent dir so we can import models
sys.path.insert(0, os.path.dirname(__file__))

from spyne import (
    Application, ServiceBase, rpc,
    Unicode, Float, Integer, Array,
)
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server
import requests

from models import (
    User, CurrencyAccount, Transaction,
    UserInfo, BalanceInfo, TransactionInfo, TransactionResult,
    ExchangeRateInfo, BuySellRateInfo,
)


NBP_BASE = "https://api.nbp.pl/api"

# --- in-memory storage ---
users = {}          # user_id -> User
accounts = {}       # (user_id, currency_code) -> CurrencyAccount
transactions = []   # list of Transaction


def fetch_nbp(endpoint):
    """call NBP API"""
    url = f"{NBP_BASE}/{endpoint}?format=json"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"  NBP API error: {e}")
        return None


class ExchangeOfficeService(ServiceBase):
    """Currency exchange office - SOAP service"""

    # --- user management ---

    @rpc(Unicode, Unicode, _returns=UserInfo)
    def register_user(ctx, username, password):
        """Create a new user account"""
        print(f"  -> register_user('{username}') called")

        # check if username already taken
        for u in users.values():
            if u.username == username:
                raise ValueError(f"Username '{username}' already exists")

        user = User(
            username=username,
            password_hash=User.hash_password(password),
        )
        users[user.id] = user

        # create initial PLN account with 0 balance
        pln_account = CurrencyAccount(
            user_id=user.id,
            currency_code="PLN",
            balance=0.0,
        )
        accounts[(user.id, "PLN")] = pln_account

        print(f"     Created user '{username}' with id={user.id}")

        return UserInfo(
            user_id=user.id,
            username=user.username,
            created_at=user.created_at.isoformat(),
        )

    # --- account operations ---

    @rpc(Unicode, Float, _returns=Float)
    def deposit(ctx, user_id, amount):
        """Add PLN to user's account (simulated bank transfer)"""
        print(f"  -> deposit('{user_id}', {amount}) called")

        if user_id not in users:
            raise ValueError(f"User '{user_id}' not found")
        if amount <= 0:
            raise ValueError("Amount must be positive")

        key = (user_id, "PLN")
        if key not in accounts:
            accounts[key] = CurrencyAccount(
                user_id=user_id, currency_code="PLN", balance=0.0
            )

        accounts[key].balance += amount
        new_balance = accounts[key].balance
        print(f"     Deposited {amount} PLN, new balance: {new_balance} PLN")
        return new_balance

    @rpc(Unicode, _returns=Array(BalanceInfo))
    def get_balance(ctx, user_id):
        """Get all currency balances for a user"""
        print(f"  -> get_balance('{user_id}') called")

        if user_id not in users:
            raise ValueError(f"User '{user_id}' not found")

        result = []
        for (uid, code), acc in accounts.items():
            if uid == user_id and acc.balance > 0:
                result.append(BalanceInfo(
                    currency_code=code,
                    balance=round(acc.balance, 2),
                ))

        # always show PLN even if 0
        if not any(b.currency_code == "PLN" for b in result):
            result.insert(0, BalanceInfo(currency_code="PLN", balance=0.0))

        return result

    # --- exchange rates ---

    @rpc(Unicode, _returns=ExchangeRateInfo)
    def get_rate(ctx, currency_code):
        """Get current mid exchange rate from NBP"""
        code = currency_code.upper().strip()
        print(f"  -> get_rate('{code}') called")

        data = fetch_nbp(f"exchangerates/rates/a/{code}/")
        if not data:
            raise ValueError(f"Currency '{code}' not found")

        rate = data["rates"][0]
        return ExchangeRateInfo(
            currency=data["currency"],
            code=data["code"],
            mid=rate["mid"],
            date=rate["effectiveDate"],
        )

    @rpc(Unicode, _returns=BuySellRateInfo)
    def get_buy_sell_rate(ctx, currency_code):
        """Get buy/sell rate from NBP Table C"""
        code = currency_code.upper().strip()
        print(f"  -> get_buy_sell_rate('{code}') called")

        data = fetch_nbp(f"exchangerates/rates/c/{code}/")
        if not data:
            raise ValueError(f"Currency '{code}' not available in Table C")

        rate = data["rates"][0]
        return BuySellRateInfo(
            currency=data["currency"],
            code=data["code"],
            bid=rate["bid"],
            ask=rate["ask"],
            spread=round(rate["ask"] - rate["bid"], 4),
            date=rate["effectiveDate"],
        )

    # --- trading (stubs for now, implemented in Lecture 6) ---

    @rpc(Unicode, Unicode, Float, _returns=TransactionResult)
    def buy_currency(ctx, user_id, currency_code, amount):
        """
        Buy foreign currency with PLN.
        TODO: implement in Lecture 6
        """
        print(f"  -> buy_currency('{user_id}', '{currency_code}', {amount})")
        return TransactionResult(
            success="false",
            transaction_id="",
            message="Not implemented yet - see Lecture 6",
            currency_code=currency_code,
            amount=amount,
            rate=0.0,
            pln_amount=0.0,
            new_pln_balance=0.0,
            new_currency_balance=0.0,
        )

    @rpc(Unicode, Unicode, Float, _returns=TransactionResult)
    def sell_currency(ctx, user_id, currency_code, amount):
        """
        Sell foreign currency for PLN.
        TODO: implement in Lecture 6
        """
        print(f"  -> sell_currency('{user_id}', '{currency_code}', {amount})")
        return TransactionResult(
            success="false",
            transaction_id="",
            message="Not implemented yet - see Lecture 6",
            currency_code=currency_code,
            amount=amount,
            rate=0.0,
            pln_amount=0.0,
            new_pln_balance=0.0,
            new_currency_balance=0.0,
        )

    @rpc(Unicode, _returns=Array(TransactionInfo))
    def get_transaction_history(ctx, user_id):
        """Get all past transactions for a user"""
        print(f"  -> get_transaction_history('{user_id}') called")

        if user_id not in users:
            raise ValueError(f"User '{user_id}' not found")

        user_txns = [t for t in transactions if t.user_id == user_id]
        return [
            TransactionInfo(
                transaction_id=t.id,
                tx_type=t.tx_type,
                currency_code=t.currency_code,
                amount=t.amount,
                rate=t.rate,
                pln_amount=t.pln_amount,
                timestamp=t.timestamp.isoformat(),
            )
            for t in user_txns
        ]


# --- app setup ---

application = Application(
    services=[ExchangeOfficeService],
    tns="lecture5.exchange.office",
    name="ExchangeOfficeWebService",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

wsgi_app = WsgiApplication(application)


if __name__ == "__main__":
    host, port = "localhost", 8000

    print(f"\nExchange Office Server (Skeleton)")
    print(f"  URL:  http://{host}:{port}/")
    print(f"  WSDL: http://{host}:{port}/?wsdl")
    print(f"\n  Operations:")
    print(f"    User:    register_user, deposit, get_balance")
    print(f"    Rates:   get_rate, get_buy_sell_rate")
    print(f"    Trading: buy_currency (TODO), sell_currency (TODO)")
    print(f"    History: get_transaction_history")
    print(f"\n  Ctrl+C to stop\n")

    server = make_server(host, port, wsgi_app)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
