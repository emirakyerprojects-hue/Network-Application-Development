# Lecture 4 – NBP Exchange Rates

Notes and code from the lab about building a currency exchange rate service using the National Bank of Poland (NBP) API.

## NBP API

The NBP provides a free public API for currency exchange rates. No API key or authorization needed.

Base URL: `https://api.nbp.pl/api/`

### Table types

| Table | What it has | Use case |
|-------|-------------|----------|
| A | Mid (average) rates for ~33 currencies | General reference |
| B | Mid rates for less common currencies | Exotic currencies |
| C | Buy (bid) and sell (ask) rates | Actual trading |

Table C is the important one for an exchange office — it gives you the real buy/sell prices.

### Key endpoints

| What | Endpoint | Example |
|------|----------|---------|
| Current rate | `/exchangerates/rates/{table}/{code}/` | `/exchangerates/rates/a/USD/` |
| Rate on date | `/exchangerates/rates/{table}/{code}/{date}/` | `/exchangerates/rates/a/USD/2024-01-15/` |
| Last N rates | `/exchangerates/rates/{table}/{code}/last/{n}/` | `/exchangerates/rates/a/USD/last/10/` |
| Full table | `/exchangerates/tables/{table}/` | `/exchangerates/tables/a/` |

Add `?format=json` to get JSON instead of XML.

### Example response (Table A)

```json
{
  "table": "A",
  "currency": "US dollar",
  "code": "USD",
  "rates": [
    {
      "no": "073/A/NBP/2024",
      "effectiveDate": "2024-04-15",
      "mid": 4.0350
    }
  ]
}
```

### Example response (Table C — buy/sell)

```json
{
  "table": "C",
  "currency": "US dollar",
  "code": "USD",
  "rates": [
    {
      "no": "073/C/NBP/2024",
      "effectiveDate": "2024-04-15",
      "bid": 3.9950,
      "ask": 4.0750
    }
  ]
}
```

The difference between `bid` and `ask` is the bank's spread (profit margin).

## What we built

A SOAP service that wraps the NBP REST API. Instead of clients having to deal with REST/JSON, they can call our SOAP methods using standard WSDL.

## Code examples

| File | What it does |
|------|-------------|
| `nbp_api_demo.py` | Explores the NBP API directly — fetches rates, shows formats (no server) |
| `exchange_rate_server.py` | SOAP service that wraps NBP API |
| `exchange_rate_client.py` | Client that calls our SOAP service using Zeep |

### Running

```bash
# without server (just API exploration)
python examples/nbp_api_demo.py

# with server
python examples/exchange_rate_server.py    # terminal 1
python examples/exchange_rate_client.py    # terminal 2
```

## Previous

[Lecture 3 – WSDL](../Lecture-03-WSDL/)

## Next

[Lecture 5 – Project Architecture](../Lecture-05-Project-Architecture/)
