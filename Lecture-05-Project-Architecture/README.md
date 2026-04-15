# Lecture 5 – Project Architecture

Designing the currency exchange office system. This lab focuses on planning the architecture before writing the full implementation.

## System overview

The exchange office system has three main parts:

```
┌─────────────┐     SOAP/WSDL     ┌──────────────────┐     HTTPS/JSON     ┌──────────┐
│   Client    │ ◄──────────────► │  Exchange Office  │ ◄────────────────► │  NBP API │
│   (WPF)     │                  │   Web Service     │                    │          │
└─────────────┘                  └──────────────────┘                    └──────────┘
                                        │
                                        │ (Lab 11+)
                                        ▼
                                  ┌──────────┐
                                  │ Database │
                                  └──────────┘
```

- **Web Service** (Labs 5-7): SOAP service with exchange logic, wraps NBP API
- **Client** (Labs 8-10): Application that talks to the service (optional, +1 grade)
- **Database** (Labs 11-12): Persistent storage for users/transactions (optional, +1 grade)

## Service interface design

These are the SOAP operations our exchange office will expose:

### User management
| Operation | Input | Output | Description |
|-----------|-------|--------|-------------|
| `register_user` | username, password | user_id | Create new account |
| `login` | username, password | session_token | Authenticate |

### Account operations
| Operation | Input | Output | Description |
|-----------|-------|--------|-------------|
| `deposit` | user_id, amount | new_balance | Add PLN to account |
| `get_balance` | user_id | balances[] | All currency balances |

### Exchange rates
| Operation | Input | Output | Description |
|-----------|-------|--------|-------------|
| `get_rate` | currency_code | rate info | Current mid rate from NBP |
| `get_buy_sell_rate` | currency_code | bid/ask | Buy/sell rates from NBP |

### Trading
| Operation | Input | Output | Description |
|-----------|-------|--------|-------------|
| `buy_currency` | user_id, code, amount | transaction | Buy foreign currency with PLN |
| `sell_currency` | user_id, code, amount | transaction | Sell foreign currency for PLN |
| `get_transaction_history` | user_id | transactions[] | Past trades |

## Data model

```
User
  - id: string (UUID)
  - username: string
  - password_hash: string
  - created_at: datetime

CurrencyAccount
  - user_id: string
  - currency_code: string (PLN, USD, EUR...)
  - balance: float

Transaction
  - id: string (UUID)
  - user_id: string
  - type: BUY | SELL
  - currency_code: string
  - amount: float
  - rate: float
  - pln_amount: float
  - timestamp: datetime
```

For now we store everything in memory (Python dicts). Database comes in Lab 11.

## Code examples

| File | What it does |
|------|-------------|
| `models.py` | Data class definitions (shared types) |
| `exchange_office_server.py` | Skeleton service with all operations defined |
| `exchange_office_client.py` | Client that connects and tests basic operations |

### Running

```bash
python examples/exchange_office_server.py    # terminal 1
python examples/exchange_office_client.py    # terminal 2
```

## Previous

[Lecture 4 – NBP Exchange Rates](../Lecture-04-NBP-Exchange-Rates/)

## Next

[Lecture 6 – Exchange Logic](../Lecture-06-Exchange-Logic/)
