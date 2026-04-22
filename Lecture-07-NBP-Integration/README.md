# Lecture 7 – NBP API Integration

Full integration of the NBP API into the exchange office system. This builds on
the architecture (Lecture 5) and exchange logic (Lecture 6) to create a
production-style service with caching, retries, multi-currency support, and
historical rate queries.

## What's new compared to Lecture 6

| Feature | Lecture 6 | Lecture 7 |
|---------|-----------|-----------|
| NBP calls | Direct, one at a time | Cached with TTL |
| Error handling | Basic try/except | Retry with backoff |
| Rate queries | Single currency only | Multi-currency + date ranges |
| Historical rates | Not available | Full history support |
| Rate caching | None | In-memory cache (configurable TTL) |
| Gold prices | Not available | Supported |
| Rate trends | Not available | Min/max/avg analysis |

## Architecture

```
┌─────────────┐     SOAP/WSDL     ┌──────────────────────────────────┐
│   Client    │ ◄──────────────►  │   Exchange Office Web Service    │
│   (Zeep)    │                   │                                  │
└─────────────┘                   │  ┌────────────────────────────┐  │
                                  │  │  NbpApiClient (new!)       │  │
                                  │  │  - caching layer           │  │
                                  │  │  - retry logic             │  │
                                  │  │  - rate history            │  │
                                  │  │  - multi-currency queries  │  │
                                  │  └────────────┬───────────────┘  │
                                  │               │                  │
                                  └───────────────┼──────────────────┘
                                                  │ HTTPS/JSON
                                                  ▼
                                           ┌──────────┐
                                           │  NBP API │
                                           └──────────┘
```

## NbpApiClient

The key addition in this lab is a dedicated `NbpApiClient` class that handles
all communication with the NBP API:

- **Caching**: Rates are cached for a configurable TTL (default 5 minutes).
  This avoids hitting the API on every SOAP call.
- **Retry logic**: Failed requests are retried up to 3 times with exponential
  backoff.
- **Batch queries**: Fetch rates for multiple currencies in a single method call.
- **Historical data**: Query rates for date ranges, get last N rates, compute
  min/max/avg statistics.
- **Gold prices**: Fetch current and historical gold prices from NBP.

## New service operations

| Operation | Input | Output | Description |
|-----------|-------|--------|-------------|
| `get_multiple_rates` | currency codes (comma-separated) | rate list | Rates for several currencies at once |
| `get_rate_for_date` | code, date | rate info | Historical rate for a specific date |
| `get_rate_history` | code, last_n | rate list | Last N rates for a currency |
| `get_rate_date_range` | code, start, end | rate list | Rates between two dates |
| `get_rate_statistics` | code, last_n | statistics | Min/max/avg/trend analysis |
| `get_gold_price` | — | gold price | Current gold price from NBP |
| `get_available_currencies` | — | currency list | All currencies in NBP Table A |

These are **on top of** all the operations from Lectures 5-6 (register, deposit,
buy/sell, get_balance, etc.).

## Code examples

| File | What it does |
|------|-------------|
| `nbp_client.py` | The `NbpApiClient` class — caching, retries, batch queries |
| `exchange_office_server.py` | Full exchange office service with NBP integration |
| `exchange_office_client.py` | Client demonstrating all new features |
| `nbp_integration_demo.py` | Standalone demo of the NBP client (no server needed) |

### Running

```bash
# standalone NBP client demo (no server needed)
python examples/nbp_integration_demo.py

# full service
python examples/exchange_office_server.py    # terminal 1
python examples/exchange_office_client.py    # terminal 2
```

## Key points

- **Always cache API responses** — external APIs can be slow or rate-limited
- **Implement retries** — network calls fail, be prepared
- **Separate the API client** — don't mix HTTP logic with business logic
- **Handle weekends/holidays** — NBP doesn't publish rates every day

## Previous

[Lecture 6 – Exchange Logic](../Lecture-06-Exchange-Logic/)
