"""
Lecture 5 - Data Models

Shared data classes and Spyne ComplexModel definitions for the
exchange office system.

These define the structure of data exchanged between client and server
via SOAP. They also show up in the auto-generated WSDL.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid
import hashlib

from spyne import ComplexModel, Unicode, Float, DateTime, Array


# ============================================================
# Plain Python data classes (used internally by the server)
# ============================================================

@dataclass
class User:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    username: str = ""
    password_hash: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        return self.password_hash == self.hash_password(password)


@dataclass
class CurrencyAccount:
    user_id: str = ""
    currency_code: str = "PLN"
    balance: float = 0.0


@dataclass
class Transaction:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    user_id: str = ""
    tx_type: str = ""         # BUY or SELL
    currency_code: str = ""
    amount: float = 0.0       # amount of foreign currency
    rate: float = 0.0         # exchange rate used
    pln_amount: float = 0.0   # total PLN involved
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================
# Spyne ComplexModel types (used in SOAP interface)
# These define how the data looks in the WSDL
# ============================================================

class UserInfo(ComplexModel):
    """user info returned by the service (no password)"""
    user_id = Unicode
    username = Unicode
    created_at = Unicode


class BalanceInfo(ComplexModel):
    """single currency balance"""
    currency_code = Unicode
    balance = Float


class TransactionInfo(ComplexModel):
    """single transaction record"""
    transaction_id = Unicode
    tx_type = Unicode
    currency_code = Unicode
    amount = Float
    rate = Float
    pln_amount = Float
    timestamp = Unicode


class TransactionResult(ComplexModel):
    """result of a buy/sell operation"""
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
    """exchange rate from NBP"""
    currency = Unicode
    code = Unicode
    mid = Float
    date = Unicode


class BuySellRateInfo(ComplexModel):
    """buy/sell rate from NBP Table C"""
    currency = Unicode
    code = Unicode
    bid = Float
    ask = Float
    spread = Float
    date = Unicode
