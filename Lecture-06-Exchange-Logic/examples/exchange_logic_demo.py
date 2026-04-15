"""
Lecture 6 - Exchange Logic Demo

Shows how currency exchange calculations work without a server.
Demonstrates spread, margins, buy/sell pricing.

No dependencies needed, just run it.
"""


# exchange office spread (profit margin)
SPREAD_PERCENT = 1.5  # 1.5% on top of NBP rates


def calculate_buy_price(nbp_ask, spread_pct=SPREAD_PERCENT):
    """
    Price the client pays to BUY foreign currency.
    We take NBP ask rate and add our spread on top.
    """
    return nbp_ask * (1 + spread_pct / 100)


def calculate_sell_price(nbp_bid, spread_pct=SPREAD_PERCENT):
    """
    Price the client gets when SELLING foreign currency.
    We take NBP bid rate and subtract our spread.
    """
    return nbp_bid * (1 - spread_pct / 100)


def simulate_buy(pln_balance, currency_balance, amount, nbp_ask,
                 spread_pct=SPREAD_PERCENT):
    """
    Simulate buying foreign currency.

    Args:
        pln_balance: current PLN in account
        currency_balance: current foreign currency in account
        amount: how much foreign currency to buy
        nbp_ask: NBP ask rate (bank sells at this price)
        spread_pct: our profit margin percentage

    Returns: dict with transaction details
    """
    our_rate = calculate_buy_price(nbp_ask, spread_pct)
    cost_pln = amount * our_rate

    if pln_balance < cost_pln:
        return {
            "success": False,
            "reason": f"Not enough PLN. Need {cost_pln:.2f}, have {pln_balance:.2f}",
        }

    return {
        "success": True,
        "nbp_ask": nbp_ask,
        "our_rate": round(our_rate, 4),
        "amount": amount,
        "cost_pln": round(cost_pln, 2),
        "new_pln_balance": round(pln_balance - cost_pln, 2),
        "new_currency_balance": round(currency_balance + amount, 2),
        "office_profit_per_unit": round(our_rate - nbp_ask, 4),
        "office_total_profit": round((our_rate - nbp_ask) * amount, 2),
    }


def simulate_sell(pln_balance, currency_balance, amount, nbp_bid,
                  spread_pct=SPREAD_PERCENT):
    """
    Simulate selling foreign currency.

    Args:
        pln_balance: current PLN in account
        currency_balance: current foreign currency in account
        amount: how much foreign currency to sell
        nbp_bid: NBP bid rate (bank buys at this price)
        spread_pct: our profit margin percentage

    Returns: dict with transaction details
    """
    if currency_balance < amount:
        return {
            "success": False,
            "reason": f"Not enough currency. Have {currency_balance:.2f}, "
                      f"want to sell {amount:.2f}",
        }

    our_rate = calculate_sell_price(nbp_bid, spread_pct)
    revenue_pln = amount * our_rate

    return {
        "success": True,
        "nbp_bid": nbp_bid,
        "our_rate": round(our_rate, 4),
        "amount": amount,
        "revenue_pln": round(revenue_pln, 2),
        "new_pln_balance": round(pln_balance + revenue_pln, 2),
        "new_currency_balance": round(currency_balance - amount, 2),
        "office_profit_per_unit": round(nbp_bid - our_rate, 4),
        "office_total_profit": round((nbp_bid - our_rate) * amount, 2),
    }


def main():
    print("\nLecture 6 - Exchange Logic Demo")
    print("-" * 40)

    # sample NBP rates (Table C for USD)
    nbp_bid = 3.9950   # bank buys at this price
    nbp_ask = 4.0750   # bank sells at this price

    print(f"\n  NBP rates for USD:")
    print(f"    Bid (bank buys):  {nbp_bid} PLN/USD")
    print(f"    Ask (bank sells): {nbp_ask} PLN/USD")
    print(f"    NBP spread:       {nbp_ask - nbp_bid:.4f} PLN")

    # --- 1. our prices ---
    print(f"\n  Our exchange office rates (spread: {SPREAD_PERCENT}%):")
    our_buy = calculate_buy_price(nbp_ask)
    our_sell = calculate_sell_price(nbp_bid)
    print(f"    We sell USD at:  {our_buy:.4f} PLN (client buys)")
    print(f"    We buy USD at:   {our_sell:.4f} PLN (client sells)")
    print(f"    Our total spread: {our_buy - our_sell:.4f} PLN")
    print(f"    -> That's our profit per 1 USD traded")

    # --- 2. buy scenario ---
    print(f"\n  Scenario 1: Client buys 100 USD")
    print(f"    Starting balance: 5000 PLN, 0 USD")
    result = simulate_buy(
        pln_balance=5000.0,
        currency_balance=0.0,
        amount=100.0,
        nbp_ask=nbp_ask,
    )
    if result["success"]:
        print(f"    NBP ask:        {result['nbp_ask']} PLN/USD")
        print(f"    Our rate:       {result['our_rate']} PLN/USD")
        print(f"    Cost:           {result['cost_pln']} PLN")
        print(f"    New PLN:        {result['new_pln_balance']}")
        print(f"    New USD:        {result['new_currency_balance']}")
        print(f"    Office profit:  {result['office_total_profit']} PLN")

    # --- 3. sell scenario ---
    print(f"\n  Scenario 2: Client sells 50 USD")
    new_pln = result["new_pln_balance"]
    new_usd = result["new_currency_balance"]
    print(f"    Starting balance: {new_pln} PLN, {new_usd} USD")
    result2 = simulate_sell(
        pln_balance=new_pln,
        currency_balance=new_usd,
        amount=50.0,
        nbp_bid=nbp_bid,
    )
    if result2["success"]:
        print(f"    NBP bid:        {result2['nbp_bid']} PLN/USD")
        print(f"    Our rate:       {result2['our_rate']} PLN/USD")
        print(f"    Revenue:        {result2['revenue_pln']} PLN")
        print(f"    New PLN:        {result2['new_pln_balance']}")
        print(f"    New USD:        {result2['new_currency_balance']}")
        print(f"    Office profit:  {result2['office_total_profit']} PLN")

    # --- 4. insufficient funds ---
    print(f"\n  Scenario 3: Not enough PLN (try to buy 10000 USD)")
    result3 = simulate_buy(
        pln_balance=500.0,
        currency_balance=0.0,
        amount=10000.0,
        nbp_ask=nbp_ask,
    )
    print(f"    Success: {result3['success']}")
    print(f"    Reason: {result3['reason']}")

    # --- 5. multiple currencies ---
    print(f"\n  Scenario 4: Multiple currency trades")
    rates = {
        "EUR": {"bid": 4.3100, "ask": 4.3900},
        "GBP": {"bid": 5.0200, "ask": 5.1100},
        "CHF": {"bid": 4.5100, "ask": 4.5800},
    }

    pln = 10000.0
    balances = {}

    print(f"    Starting with {pln} PLN")
    for code, r in rates.items():
        buy = simulate_buy(pln, 0, 100, r["ask"])
        if buy["success"]:
            pln = buy["new_pln_balance"]
            balances[code] = buy["new_currency_balance"]
            print(f"    Buy 100 {code} @ {buy['our_rate']}: "
                  f"cost {buy['cost_pln']} PLN, "
                  f"remaining {pln} PLN")

    print(f"\n    Final portfolio:")
    print(f"      PLN: {pln}")
    for code, bal in balances.items():
        print(f"      {code}: {bal}")

    # --- 6. spread comparison ---
    print(f"\n  Spread comparison at different margins:")
    print(f"    {'Spread':>8}  {'Buy USD':>10}  {'Sell USD':>10}  {'Diff':>8}")
    print(f"    {'-'*8}  {'-'*10}  {'-'*10}  {'-'*8}")
    for pct in [0.5, 1.0, 1.5, 2.0, 3.0]:
        buy = calculate_buy_price(nbp_ask, pct)
        sell = calculate_sell_price(nbp_bid, pct)
        print(f"    {pct:>6.1f}%  {buy:>10.4f}  {sell:>10.4f}  {buy-sell:>8.4f}")

    print(f"\n--- Key points ---")
    print(f"  - Buy price = NBP ask + our spread (client pays MORE)")
    print(f"  - Sell price = NBP bid - our spread (client gets LESS)")
    print(f"  - Spread is how the exchange office profits")
    print(f"  - Always check sufficient balance before trading")
    print()


if __name__ == "__main__":
    main()
