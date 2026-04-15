# Lecture 6 – Exchange Logic

Implementation of the actual currency exchange (buy/sell) logic.

## How currency exchange works

When you go to a real exchange office:

1. **Buying foreign currency** (e.g. buying USD):
   - You give PLN to the office
   - Office gives you USD
   - Rate used: **ask** price (higher — you pay more)
   - Plus office adds its own **spread** (profit margin)

2. **Selling foreign currency** (e.g. selling USD):
   - You give USD to the office
   - Office gives you PLN
   - Rate used: **bid** price (lower — you get less)
   - Office also takes a spread here

## The spread

The spread is how exchange offices make money. Example:

```
NBP bid (bank buys):  3.9950 PLN/USD
NBP ask (bank sells): 4.0750 PLN/USD
NBP spread:           0.0800 PLN

Our office spread:    1.5% on top of NBP rates
Our buy price:        4.0750 * 1.015 = 4.1361 PLN/USD  (client pays more)
Our sell price:       3.9950 * 0.985 = 3.9351 PLN/USD  (client gets less)
```

## Transaction flow

### Buy 100 USD:
```
1. Client has 5000 PLN
2. Get NBP ask rate: 4.0750
3. Apply spread (+1.5%): 4.0750 * 1.015 = 4.1361
4. Cost: 100 * 4.1361 = 413.61 PLN
5. Check: 5000 >= 413.61 ✓
6. Deduct: 5000 - 413.61 = 4586.39 PLN
7. Add: 0 + 100 = 100.00 USD
8. Record transaction
```

### Sell 50 USD:
```
1. Client has 100 USD
2. Get NBP bid rate: 3.9950
3. Apply spread (-1.5%): 3.9950 * 0.985 = 3.9351
4. Revenue: 50 * 3.9351 = 196.76 PLN
5. Deduct: 100 - 50 = 50.00 USD
6. Add: 4586.39 + 196.76 = 4783.15 PLN
7. Record transaction
```

## Code examples

| File | What it does |
|------|-------------|
| `exchange_logic_demo.py` | Standalone demo of exchange calculations (no server) |
| `exchange_office_server.py` | Full exchange office service with working buy/sell |
| `exchange_office_client.py` | Client demonstrating the complete flow |

### Running

```bash
# standalone (no server needed)
python examples/exchange_logic_demo.py

# full service
python examples/exchange_office_server.py    # terminal 1
python examples/exchange_office_client.py    # terminal 2
```

## Previous

[Lecture 5 – Project Architecture](../Lecture-05-Project-Architecture/)
