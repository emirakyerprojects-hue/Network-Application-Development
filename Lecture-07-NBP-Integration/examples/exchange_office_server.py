"""
Lecture 7 - Exchange Office Server (Full NBP Integration)

Complete exchange office SOAP service with enhanced NBP API integration.
Builds on Lecture 6 with:
- NbpApiClient for cached, retry-enabled API calls
- Multi-currency rate queries
- Historical rate and date-range queries
- Rate statistics (min/max/avg/trend)
- Gold price support
- List of all available currencies

WSDL: http://localhost:8000/?wsdl

needs: pip install spyne lxml requests
"""

import sys
import os
from datetime import datetime

# add parent dirs for imports
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

# import our NBP client
from nbp_client import NbpApiClient

# reuse models from Lecture 5
try:
    from models import (
        User, CurrencyAccount, Transaction,
        UserInfo, BalanceInfo, TransactionInfo, TransactionResult,
        ExchangeRateInfo, BuySellRateInfo,
    )
except ImportError:
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
# New ComplexModel types for Lecture 7
# ============================================================

from spyne import ComplexModel as CM

class RateHistoryEntry(CM):
    """single historical rate entry"""
    date = Unicode
    mid = Float

class RateStatistics(CM):
    """rate statistics over a period"""
    code = Unicode
    period_days = Integer
    min_rate = Float
    max_rate = Float
    avg_rate = Float
    current_rate = Float
    first_rate = Float
    change = Float
    change_pct = Float
    trend = Unicode
    start_date = Unicode
    end_date = Unicode

class GoldPrice(CM):
    """gold price from NBP"""
    price = Float
    date = Unicode

class CurrencyListItem(CM):
    """currency info item"""
    code = Unicode
    name = Unicode

class CacheStats(CM):
    """cache statistics"""
    api_calls = Integer
    cache_hits = Integer
    cached_entries = Integer
    hit_rate = Unicode

class EffectiveRate(CM):
    """our exchange office effective buy/sell rate"""
    code = Unicode
    source = Unicode
    our_buy_rate = Float
    our_sell_rate = Float
    our_spread = Float
    spread_pct = Float
    date = Unicode

class DateRangeRate(CM):
    """rate entry for a date range query"""
    date = Unicode
    mid = Float


# ============================================================
# Configuration
# ============================================================

SPREAD_PERCENT = 1.5   # our profit margin
CACHE_TTL = 300        # 5 minutes cache

# ============================================================
# In-memory storage
# ============================================================

users = {}          # user_id -> User
accounts = {}       # (user_id, currency_code) -> CurrencyAccount
transactions = []   # list of Transaction

# ============================================================
# NBP API Client (shared instance)
# ============================================================

nbp = NbpApiClient(cache_ttl=CACHE_TTL, max_retries=3, timeout=10)


# ============================================================
# Helpers
# ============================================================

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
    Currency Exchange Office - Full NBP Integration (Lecture 7)

    Features:
    - User registration and PLN deposits
    - Live exchange rates from NBP API (cached)
    - Buy/sell foreign currency with spread
    - Multi-currency rate queries
    - Historical rates and date ranges
    - Rate statistics and trend analysis
    - Gold price support
    - Transaction history

    Spread: {spread}%
    Cache TTL: {ttl}s
    """.format(spread=SPREAD_PERCENT, ttl=CACHE_TTL)

    # --------------------------------------------------------
    # User management (same as Lecture 6)
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Account operations (same as Lecture 6)
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Exchange rates - ENHANCED with NbpApiClient
    # --------------------------------------------------------

    @rpc(Unicode, _returns=ExchangeRateInfo)
    def get_rate(ctx, currency_code):
        """Get current mid rate from NBP Table A (cached)"""
        code = currency_code.upper().strip()
        print(f"  -> get_rate('{code}')")

        rate = nbp.get_mid_rate(code)
        if not rate:
            raise ValueError(f"Currency '{code}' not found")

        return ExchangeRateInfo(
            currency=rate["currency"],
            code=rate["code"],
            mid=rate["mid"],
            date=rate["date"],
        )

    @rpc(Unicode, _returns=BuySellRateInfo)
    def get_buy_sell_rate(ctx, currency_code):
        """Get buy/sell rate from NBP Table C (cached)"""
        code = currency_code.upper().strip()
        print(f"  -> get_buy_sell_rate('{code}')")

        rate = nbp.get_buy_sell_rate(code)
        if not rate:
            raise ValueError(f"Currency '{code}' not in Table C")

        return BuySellRateInfo(
            currency=rate["currency"],
            code=rate["code"],
            bid=rate["bid"],
            ask=rate["ask"],
            spread=rate["spread"],
            date=rate["date"],
        )

    # --------------------------------------------------------
    # NEW: Multi-currency rates
    # --------------------------------------------------------

    @rpc(Unicode, _returns=Array(ExchangeRateInfo))
    def get_multiple_rates(ctx, currency_codes):
        """
        Get mid rates for multiple currencies at once.

        Args:
            currency_codes: comma-separated currency codes (e.g. "USD,EUR,GBP")
        """
        codes = [c.strip().upper() for c in currency_codes.split(",")]
        print(f"  -> get_multiple_rates({codes})")

        rates = nbp.get_multiple_mid_rates(codes)
        return [
            ExchangeRateInfo(
                currency=r["currency"],
                code=r["code"],
                mid=r["mid"],
                date=r["date"],
            )
            for r in rates
        ]

    # --------------------------------------------------------
    # NEW: Effective rates (our buy/sell with spread)
    # --------------------------------------------------------

    @rpc(Unicode, _returns=EffectiveRate)
    def get_effective_rate(ctx, currency_code):
        """
        Get our exchange office buy/sell rates (with spread applied).
        Uses Table C if available, falls back to Table A.
        """
        code = currency_code.upper().strip()
        print(f"  -> get_effective_rate('{code}')")

        rate = nbp.get_effective_rate(code, spread_pct=SPREAD_PERCENT)
        if not rate:
            raise ValueError(f"Currency '{code}' not found")

        return EffectiveRate(
            code=rate["code"],
            source=rate["source"],
            our_buy_rate=rate["our_buy_rate"],
            our_sell_rate=rate["our_sell_rate"],
            our_spread=rate["our_spread"],
            spread_pct=rate["spread_pct"],
            date=rate["date"],
        )

    # --------------------------------------------------------
    # NEW: Historical rates
    # --------------------------------------------------------

    @rpc(Unicode, Unicode, _returns=ExchangeRateInfo)
    def get_rate_for_date(ctx, currency_code, date):
        """
        Get exchange rate for a specific date.

        Args:
            currency_code: ISO 4217 code
            date: YYYY-MM-DD format
        """
        code = currency_code.upper().strip()
        print(f"  -> get_rate_for_date('{code}', '{date}')")

        rate = nbp.get_rate_for_date(code, date)
        if not rate:
            raise ValueError(
                f"No rate for '{code}' on {date}. "
                "Could be a weekend or holiday."
            )

        return ExchangeRateInfo(
            currency=rate["currency"],
            code=rate["code"],
            mid=rate.get("mid", 0.0),
            date=rate["date"],
        )

    @rpc(Unicode, Integer, _returns=Array(RateHistoryEntry))
    def get_rate_history(ctx, currency_code, last_n):
        """
        Get last N exchange rates for a currency.

        Args:
            currency_code: ISO 4217 code
            last_n: number of recent rates (max 255)
        """
        code = currency_code.upper().strip()
        n = min(last_n or 10, 255)
        print(f"  -> get_rate_history('{code}', {n})")

        history = nbp.get_rate_history(code, last_n=n)
        return [
            RateHistoryEntry(date=r["date"], mid=r["mid"])
            for r in history
        ]

    @rpc(Unicode, Unicode, Unicode, _returns=Array(DateRangeRate))
    def get_rate_date_range(ctx, currency_code, start_date, end_date):
        """
        Get exchange rates for a date range.

        Args:
            currency_code: ISO 4217 code
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD
        """
        code = currency_code.upper().strip()
        print(f"  -> get_rate_date_range('{code}', {start_date} to {end_date})")

        rates = nbp.get_rate_date_range(code, start_date, end_date)
        return [
            DateRangeRate(date=r["date"], mid=r["mid"])
            for r in rates
        ]

    # --------------------------------------------------------
    # NEW: Rate statistics
    # --------------------------------------------------------

    @rpc(Unicode, Integer, _returns=RateStatistics)
    def get_rate_statistics(ctx, currency_code, last_n):
        """
        Get rate statistics (min, max, avg, trend) for last N rates.

        Args:
            currency_code: ISO 4217 code
            last_n: number of rates to analyze (default 30)
        """
        code = currency_code.upper().strip()
        n = last_n or 30
        print(f"  -> get_rate_statistics('{code}', {n})")

        stats = nbp.get_rate_statistics(code, last_n=n)
        if not stats:
            raise ValueError(f"Could not fetch statistics for '{code}'")

        return RateStatistics(
            code=stats["code"],
            period_days=stats["period_days"],
            min_rate=stats["min"],
            max_rate=stats["max"],
            avg_rate=stats["avg"],
            current_rate=stats["current"],
            first_rate=stats["first"],
            change=stats["change"],
            change_pct=stats["change_pct"],
            trend=stats["trend"],
            start_date=stats["start_date"],
            end_date=stats["end_date"],
        )

    # --------------------------------------------------------
    # NEW: Gold prices
    # --------------------------------------------------------

    @rpc(_returns=GoldPrice)
    def get_gold_price(ctx):
        """Get current gold price from NBP (PLN per gram)"""
        print("  -> get_gold_price()")

        gold = nbp.get_gold_price()
        if not gold:
            raise ValueError("Could not fetch gold price")

        return GoldPrice(
            price=gold["price"],
            date=gold["date"],
        )

    @rpc(Integer, _returns=Array(GoldPrice))
    def get_gold_price_history(ctx, last_n):
        """Get last N gold prices"""
        n = min(last_n or 10, 255)
        print(f"  -> get_gold_price_history({n})")

        history = nbp.get_gold_price_history(last_n=n)
        return [
            GoldPrice(price=g["price"], date=g["date"])
            for g in history
        ]

    # --------------------------------------------------------
    # NEW: Available currencies
    # --------------------------------------------------------

    @rpc(_returns=Array(CurrencyListItem))
    def get_available_currencies(ctx):
        """List all currencies available in NBP Table A"""
        print("  -> get_available_currencies()")

        currencies = nbp.get_available_currencies()
        return [
            CurrencyListItem(code=c["code"], name=c["name"])
            for c in currencies
        ]

    # --------------------------------------------------------
    # NEW: Cache management
    # --------------------------------------------------------

    @rpc(_returns=CacheStats)
    def get_cache_stats(ctx):
        """Get NBP API cache statistics"""
        print("  -> get_cache_stats()")
        stats = nbp.get_cache_stats()
        return CacheStats(
            api_calls=stats["api_calls"],
            cache_hits=stats["cache_hits"],
            cached_entries=stats["cached_entries"],
            hit_rate=stats["hit_rate"],
        )

    @rpc(_returns=Unicode)
    def clear_cache(ctx):
        """Clear the NBP rate cache"""
        print("  -> clear_cache()")
        nbp.clear_cache()
        return "Cache cleared"

    # --------------------------------------------------------
    # Trading (from Lecture 6, now using NbpApiClient)
    # --------------------------------------------------------

    @rpc(Unicode, Unicode, Float, _returns=TransactionResult)
    def buy_currency(ctx, user_id, currency_code, amount):
        """
        Buy foreign currency with PLN.
        Uses NbpApiClient for cached rate lookups.
        """
        code = currency_code.upper().strip()
        print(f"  -> buy_currency('{user_id}', '{code}', {amount})")

        if user_id not in users:
            raise ValueError(f"User '{user_id}' not found")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if code == "PLN":
            raise ValueError("Cannot buy PLN — deposit instead")

        # get effective rate using NbpApiClient
        eff = nbp.get_effective_rate(code, spread_pct=SPREAD_PERCENT)
        if not eff:
            raise ValueError(f"Currency '{code}' not found in NBP")

        our_rate = eff["our_buy_rate"]
        cost_pln = round(amount * our_rate, 2)

        print(f"     Source: {eff['source']}, Rate: {our_rate}")
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
            message=f"Bought {amount} {code} at {our_rate:.4f} PLN/{code} ({eff['source']})",
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
        Uses NbpApiClient for cached rate lookups.
        """
        code = currency_code.upper().strip()
        print(f"  -> sell_currency('{user_id}', '{code}', {amount})")

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

        # get effective rate using NbpApiClient
        eff = nbp.get_effective_rate(code, spread_pct=SPREAD_PERCENT)
        if not eff:
            raise ValueError(f"Currency '{code}' not found in NBP")

        our_rate = eff["our_sell_rate"]
        revenue_pln = round(amount * our_rate, 2)

        print(f"     Source: {eff['source']}, Rate: {our_rate}")
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
            message=f"Sold {amount} {code} at {our_rate:.4f} PLN/{code} ({eff['source']})",
            currency_code=code,
            amount=amount,
            rate=round(our_rate, 4),
            pln_amount=revenue_pln,
            new_pln_balance=round(pln_acc.balance, 2),
            new_currency_balance=round(currency_acc.balance, 2),
        )

    # --------------------------------------------------------
    # Transaction history (same as Lecture 6)
    # --------------------------------------------------------

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
    tns="lecture7.exchange.office",
    name="ExchangeOfficeWebService",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

wsgi_app = WsgiApplication(application)


if __name__ == "__main__":
    host, port = "localhost", 8000

    print(f"\nExchange Office Server (Lecture 7 - Full NBP Integration)")
    print(f"  URL:  http://{host}:{port}/")
    print(f"  WSDL: http://{host}:{port}/?wsdl")
    print(f"  Spread: {SPREAD_PERCENT}%")
    print(f"  Cache TTL: {CACHE_TTL}s")
    print(f"\n  Operations:")
    print(f"    User:       register_user, deposit, get_balance")
    print(f"    Rates:      get_rate, get_buy_sell_rate, get_multiple_rates")
    print(f"    Effective:  get_effective_rate")
    print(f"    History:    get_rate_for_date, get_rate_history, get_rate_date_range")
    print(f"    Stats:      get_rate_statistics")
    print(f"    Gold:       get_gold_price, get_gold_price_history")
    print(f"    Currencies: get_available_currencies")
    print(f"    Trading:    buy_currency, sell_currency")
    print(f"    History:    get_transaction_history")
    print(f"    Cache:      get_cache_stats, clear_cache")
    print(f"\n  Ctrl+C to stop\n")

    server = make_server(host, port, wsgi_app)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
