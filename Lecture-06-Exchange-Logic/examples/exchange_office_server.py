"""
Lecture 6 - Exchange Office Server (Full Implementation)

Complete exchange office SOAP service with working buy/sell logic.
This extends the Lecture 5 skeleton with actual exchange operations.

Features:
- User registration and PLN deposits
- Live exchange rates from NBP API
- Buy foreign currency (uses ask rate + spread)
- Sell foreign currency (uses bid rate - spread)
- Transaction history
- Configurable spread (profit margin)

WSDL: http://localhost:8000/?wsdl

needs: pip install spyne lxml requests
"""

import sys
import os
from datetime import datetime

# add parent dir for model imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                "..", "..", "Lecture-05-Project-Architecture", "examples"))
sys.path.insert(0, os.path.dirname(__file__))

from spyne import (
    Application, ServiceBase, rpc,
    Unicode, Float, Integer, Array,
)
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server
import requests

# we reuse the models from Lecture 5
try:
    from models import (
        User, CurrencyAccount, Transaction,
        UserInfo, BalanceInfo, TransactionInfo, TransactionResult,
        ExchangeRateInfo, BuySellRateInfo,
    )
except ImportError:
    # if import fails, define them locally
    # (this makes the file self-contained as a fallback)
    from spyne import ComplexModel
    import uuid
    import hashlib
    from dataclasses import dataclass, field

    @dataclass
    class User:
        id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
        username: str = ""
        password_hash: str = ""
        created_at: datetime = field(default_factory=datetime.now)

        @staticmethod
        def hash_password(password: str) -> str:
            return hashlib.sha256(password.encode()).hexdigest()

    @dataclass
    class CurrencyAccount:
        user_id: str = ""
        currency_code: str = "PLN"
        balance: float = 0.0

    @dataclass
    class Transaction:
        id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
        user_id: str = ""
        tx_type: str = ""
        currency_code: str = ""
        amount: float = 0.0
        rate: float = 0.0
        pln_amount: float = 0.0
        timestamp: datetime = field(default_factory=datetime.now)

    class UserInfo(ComplexModel):
        user_id = Unicode
        username = Unicode
        created_at = Unicode

    class BalanceInfo(ComplexModel):
        currency_code = Unicode
        balance = Float

    class TransactionInfo(ComplexModel):
        transaction_id = Unicode
        tx_type = Unicode
        currency_code = Unicode
        amount = Float
        rate = Float
        pln_amount = Float
        timestamp = Unicode

    class TransactionResult(ComplexModel):
        success = Unicode
        transaction_id = Unicode
        message = Unicode
        currency_code = Unicode
        amount = Float
        rate = Float
        pln_amount = Float
        new_pln_balance = Float
        new_currency_balance = Float

    class ExchangeRateInfo(ComplexModel):
        currency = Unicode
        code = Unicode
        mid = Float
        date = Unicode

    class BuySellRateInfo(ComplexModel):
        currency = Unicode
        code = Unicode
        bid = Float
        ask = Float
        spread = Float
        date = Unicode


# ============================================================
# Configuration
# ============================================================

NBP_BASE = "https://api.nbp.pl/api"
SPREAD_PERCENT = 1.5  # our profit margin on top of NBP rates

# ============================================================
# In-memory storage
# ============================================================

users = {}          # user_id -> User
accounts = {}       # (user_id, currency_code) -> CurrencyAccount
transactions = []   # list of Transaction


# ============================================================
# Helpers
# ============================================================

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
        print(f"  NBP error: {e}")
        return None


def get_or_create_account(user_id, currency_code):
    """get currency account, create if doesn't exist"""
    key = (user_id, currency_code)
    if key not in accounts:
        accounts[key] = CurrencyAccount(
            user_id=user_id,
            currency_code=currency_code,
            balance=0.0,
        )
    return accounts[key]


# ============================================================
# The SOAP Service
# ============================================================

class ExchangeOfficeService(ServiceBase):
    """
    Currency Exchange Office - Full Implementation

    Spread: {spread}% on top of NBP rates
    """.format(spread=SPREAD_PERCENT)

    # --- user management ---

    @rpc(Unicode, Unicode, _returns=UserInfo)
    def register_user(ctx, username, password):
        """Create a new user account with 0 PLN balance"""
        print(f"  -> register_user('{username}')")

        for u in users.values():
            if u.username == username:
                raise ValueError(f"Username '{username}' already exists")

        user = User(
            username=username,
            password_hash=User.hash_password(password),
        )
        users[user.id] = user
        get_or_create_account(user.id, "PLN")

        print(f"     Created user id={user.id}")
        return UserInfo(
            user_id=user.id,
            username=user.username,
            created_at=user.created_at.isoformat(),
        )

    # --- account operations ---

    @rpc(Unicode, Float, _returns=Float)
    def deposit(ctx, user_id, amount):
        """Add PLN to user's account"""
        print(f"  -> deposit('{user_id}', {amount})")

        if user_id not in users:
            raise ValueError(f"User '{user_id}' not found")
        if amount <= 0:
            raise ValueError("Amount must be positive")

        acc = get_or_create_account(user_id, "PLN")
        acc.balance += amount
        print(f"     New PLN balance: {acc.balance:.2f}")
        return round(acc.balance, 2)

    @rpc(Unicode, _returns=Array(BalanceInfo))
    def get_balance(ctx, user_id):
        """Get all currency balances for a user"""
        print(f"  -> get_balance('{user_id}')")

        if user_id not in users:
            raise ValueError(f"User '{user_id}' not found")

        result = []
        for (uid, code), acc in sorted(accounts.items()):
            if uid == user_id:
                result.append(BalanceInfo(
                    currency_code=code,
                    balance=round(acc.balance, 2),
                ))

        if not result:
            result.append(BalanceInfo(currency_code="PLN", balance=0.0))

        return result

    # --- exchange rates ---

    @rpc(Unicode, _returns=ExchangeRateInfo)
    def get_rate(ctx, currency_code):
        """Get current mid rate from NBP Table A"""
        code = currency_code.upper().strip()
        print(f"  -> get_rate('{code}')")

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
        print(f"  -> get_buy_sell_rate('{code}')")

        data = fetch_nbp(f"exchangerates/rates/c/{code}/")
        if not data:
            raise ValueError(f"Currency '{code}' not in Table C")

        rate = data["rates"][0]
        return BuySellRateInfo(
            currency=data["currency"],
            code=data["code"],
            bid=rate["bid"],
            ask=rate["ask"],
            spread=round(rate["ask"] - rate["bid"], 4),
            date=rate["effectiveDate"],
        )

    # --- trading (FULLY IMPLEMENTED) ---

    @rpc(Unicode, Unicode, Float, _returns=TransactionResult)
    def buy_currency(ctx, user_id, currency_code, amount):
        """
        Buy foreign currency with PLN.

        Uses NBP Table C ask rate + our spread.
        If Table C is unavailable, falls back to Table A mid rate + spread.

        Args:
            user_id: user ID from register_user
            currency_code: ISO 4217 code (USD, EUR, etc.)
            amount: how much foreign currency to buy
        """
        code = currency_code.upper().strip()
        print(f"  -> buy_currency('{user_id}', '{code}', {amount})")

        # validate user
        if user_id not in users:
            raise ValueError(f"User '{user_id}' not found")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if code == "PLN":
            raise ValueError("Cannot buy PLN — deposit instead")

        # get rate: try Table C first, fall back to Table A
        data = fetch_nbp(f"exchangerates/rates/c/{code}/")
        if data:
            nbp_rate = data["rates"][0]["ask"]
            rate_source = "Table C ask"
        else:
            data = fetch_nbp(f"exchangerates/rates/a/{code}/")
            if not data:
                raise ValueError(f"Currency '{code}' not found in NBP")
            nbp_rate = data["rates"][0]["mid"]
            rate_source = "Table A mid"

        # apply our spread
        our_rate = nbp_rate * (1 + SPREAD_PERCENT / 100)
        cost_pln = round(amount * our_rate, 2)

        print(f"     NBP {rate_source}: {nbp_rate}")
        print(f"     Our rate (+{SPREAD_PERCENT}%): {our_rate:.4f}")
        print(f"     Cost: {cost_pln} PLN")

        # check balance
        pln_acc = get_or_create_account(user_id, "PLN")
        if pln_acc.balance < cost_pln:
            return TransactionResult(
                success="false",
                transaction_id="",
                message=f"Insufficient PLN. Need {cost_pln}, have {pln_acc.balance:.2f}",
                currency_code=code,
                amount=amount,
                rate=round(our_rate, 4),
                pln_amount=cost_pln,
                new_pln_balance=round(pln_acc.balance, 2),
                new_currency_balance=round(
                    get_or_create_account(user_id, code).balance, 2),
            )

        # execute trade
        pln_acc.balance -= cost_pln
        currency_acc = get_or_create_account(user_id, code)
        currency_acc.balance += amount

        # record transaction
        tx = Transaction(
            user_id=user_id,
            tx_type="BUY",
            currency_code=code,
            amount=amount,
            rate=round(our_rate, 4),
            pln_amount=cost_pln,
        )
        transactions.append(tx)

        print(f"     OK! PLN: {pln_acc.balance:.2f}, {code}: {currency_acc.balance:.2f}")

        return TransactionResult(
            success="true",
            transaction_id=tx.id,
            message=f"Bought {amount} {code} at {our_rate:.4f} PLN/{code}",
            currency_code=code,
            amount=amount,
            rate=round(our_rate, 4),
            pln_amount=cost_pln,
            new_pln_balance=round(pln_acc.balance, 2),
            new_currency_balance=round(currency_acc.balance, 2),
        )

    @rpc(Unicode, Unicode, Float, _returns=TransactionResult)
    def sell_currency(ctx, user_id, currency_code, amount):
        """
        Sell foreign currency for PLN.

        Uses NBP Table C bid rate - our spread.
        If Table C is unavailable, falls back to Table A mid rate - spread.

        Args:
            user_id: user ID from register_user
            currency_code: ISO 4217 code
            amount: how much foreign currency to sell
        """
        code = currency_code.upper().strip()
        print(f"  -> sell_currency('{user_id}', '{code}', {amount})")

        # validate
        if user_id not in users:
            raise ValueError(f"User '{user_id}' not found")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if code == "PLN":
            raise ValueError("Cannot sell PLN")

        # check currency balance
        currency_acc = get_or_create_account(user_id, code)
        if currency_acc.balance < amount:
            return TransactionResult(
                success="false",
                transaction_id="",
                message=f"Insufficient {code}. Have {currency_acc.balance:.2f}, "
                        f"want to sell {amount}",
                currency_code=code,
                amount=amount,
                rate=0.0,
                pln_amount=0.0,
                new_pln_balance=round(
                    get_or_create_account(user_id, "PLN").balance, 2),
                new_currency_balance=round(currency_acc.balance, 2),
            )

        # get rate: try Table C first, fall back to Table A
        data = fetch_nbp(f"exchangerates/rates/c/{code}/")
        if data:
            nbp_rate = data["rates"][0]["bid"]
            rate_source = "Table C bid"
        else:
            data = fetch_nbp(f"exchangerates/rates/a/{code}/")
            if not data:
                raise ValueError(f"Currency '{code}' not found in NBP")
            nbp_rate = data["rates"][0]["mid"]
            rate_source = "Table A mid"

        # apply our spread (subtract for selling)
        our_rate = nbp_rate * (1 - SPREAD_PERCENT / 100)
        revenue_pln = round(amount * our_rate, 2)

        print(f"     NBP {rate_source}: {nbp_rate}")
        print(f"     Our rate (-{SPREAD_PERCENT}%): {our_rate:.4f}")
        print(f"     Revenue: {revenue_pln} PLN")

        # execute trade
        currency_acc.balance -= amount
        pln_acc = get_or_create_account(user_id, "PLN")
        pln_acc.balance += revenue_pln

        # record transaction
        tx = Transaction(
            user_id=user_id,
            tx_type="SELL",
            currency_code=code,
            amount=amount,
            rate=round(our_rate, 4),
            pln_amount=revenue_pln,
        )
        transactions.append(tx)

        print(f"     OK! PLN: {pln_acc.balance:.2f}, {code}: {currency_acc.balance:.2f}")

        return TransactionResult(
            success="true",
            transaction_id=tx.id,
            message=f"Sold {amount} {code} at {our_rate:.4f} PLN/{code}",
            currency_code=code,
            amount=amount,
            rate=round(our_rate, 4),
            pln_amount=revenue_pln,
            new_pln_balance=round(pln_acc.balance, 2),
            new_currency_balance=round(currency_acc.balance, 2),
        )

    # --- history ---

    @rpc(Unicode, _returns=Array(TransactionInfo))
    def get_transaction_history(ctx, user_id):
        """Get all past transactions for a user"""
        print(f"  -> get_transaction_history('{user_id}')")

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


# ============================================================
# App setup
# ============================================================

application = Application(
    services=[ExchangeOfficeService],
    tns="lecture6.exchange.office",
    name="ExchangeOfficeWebService",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

wsgi_app = WsgiApplication(application)


if __name__ == "__main__":
    host, port = "localhost", 8000

    print(f"\nExchange Office Server (Full)")
    print(f"  URL:  http://{host}:{port}/")
    print(f"  WSDL: http://{host}:{port}/?wsdl")
    print(f"  Spread: {SPREAD_PERCENT}%")
    print(f"\n  Operations:")
    print(f"    User:    register_user, deposit, get_balance")
    print(f"    Rates:   get_rate, get_buy_sell_rate")
    print(f"    Trading: buy_currency, sell_currency")
    print(f"    History: get_transaction_history")
    print(f"\n  Ctrl+C to stop\n")

    server = make_server(host, port, wsgi_app)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
