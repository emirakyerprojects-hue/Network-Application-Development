"""
Lecture 7 - NBP API Client

A dedicated client class for the National Bank of Poland API.
Adds caching, retry logic, and convenience methods on top of raw HTTP calls.

Features:
- In-memory cache with configurable TTL
- Automatic retry with exponential backoff
- Single and multi-currency rate fetching
- Historical rates (date ranges, last N)
- Rate statistics (min, max, avg, trend)
- Gold price support
- Table A (mid rates) and Table C (bid/ask rates)

needs: pip install requests
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Optional


class NbpApiClient:
    """
    Client for the NBP (National Bank of Poland) exchange rate API.

    Usage:
        client = NbpApiClient(cache_ttl=300)
        rate = client.get_mid_rate("USD")
        rates = client.get_multiple_mid_rates(["USD", "EUR", "GBP"])
        history = client.get_rate_history("EUR", last_n=30)
    """

    BASE_URL = "https://api.nbp.pl/api"

    def __init__(self, cache_ttl=300, max_retries=3, timeout=10):
        """
        Args:
            cache_ttl: cache time-to-live in seconds (default 5 min)
            max_retries: number of retries on failure
            timeout: HTTP request timeout in seconds
        """
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries
        self.timeout = timeout

        # cache: key -> (timestamp, data)
        self._cache = {}

        # stats
        self.api_calls = 0
        self.cache_hits = 0

    # ================================================================
    # Internal helpers
    # ================================================================

    def _cache_key(self, endpoint):
        """create a cache key from the endpoint"""
        return endpoint.lower().strip("/")

    def _get_cached(self, endpoint):
        """return cached data if still valid, else None"""
        key = self._cache_key(endpoint)
        if key in self._cache:
            ts, data = self._cache[key]
            if time.time() - ts < self.cache_ttl:
                self.cache_hits += 1
                return data
            else:
                del self._cache[key]
        return None

    def _set_cached(self, endpoint, data):
        """store data in cache"""
        key = self._cache_key(endpoint)
        self._cache[key] = (time.time(), data)

    def _fetch(self, endpoint, use_cache=True):
        """
        Fetch data from NBP API with caching and retry.

        Returns the parsed JSON or None if not found (404).
        Raises RuntimeError on persistent failure.
        """
        # check cache first
        if use_cache:
            cached = self._get_cached(endpoint)
            if cached is not None:
                return cached

        url = f"{self.BASE_URL}/{endpoint}"
        if "?" in url:
            url += "&format=json"
        else:
            url += "?format=json"

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                self.api_calls += 1
                resp = requests.get(url, timeout=self.timeout)

                if resp.status_code == 404:
                    return None

                resp.raise_for_status()
                data = resp.json()

                # cache successful response
                if use_cache:
                    self._set_cached(endpoint, data)

                return data

            except requests.RequestException as e:
                last_error = e
                if attempt < self.max_retries:
                    wait = 0.5 * (2 ** (attempt - 1))  # 0.5s, 1s, 2s
                    print(f"  [NBP] Retry {attempt}/{self.max_retries} "
                          f"after {wait}s: {e}")
                    time.sleep(wait)

        print(f"  [NBP] All {self.max_retries} attempts failed: {last_error}")
        return None

    def clear_cache(self):
        """clear the entire cache"""
        self._cache.clear()

    def get_cache_stats(self):
        """return cache statistics"""
        return {
            "api_calls": self.api_calls,
            "cache_hits": self.cache_hits,
            "cached_entries": len(self._cache),
            "hit_rate": (
                f"{self.cache_hits / (self.api_calls + self.cache_hits) * 100:.1f}%"
                if (self.api_calls + self.cache_hits) > 0 else "N/A"
            ),
        }

    # ================================================================
    # Mid rates (Table A)
    # ================================================================

    def get_mid_rate(self, currency_code):
        """
        Get current mid exchange rate from Table A.

        Returns: dict with keys: currency, code, mid, date, table_no
                 or None if currency not found
        """
        code = currency_code.upper().strip()
        data = self._fetch(f"exchangerates/rates/a/{code}/")
        if not data:
            return None

        rate = data["rates"][0]
        return {
            "currency": data["currency"],
            "code": data["code"],
            "mid": rate["mid"],
            "date": rate["effectiveDate"],
            "table_no": rate["no"],
        }

    def get_multiple_mid_rates(self, currency_codes):
        """
        Get mid rates for multiple currencies at once.

        Returns: list of rate dicts (skips currencies that are not found)
        """
        results = []
        for code in currency_codes:
            rate = self.get_mid_rate(code)
            if rate:
                results.append(rate)
        return results

    def get_full_table(self, table="a"):
        """
        Get the complete exchange rate table.

        Returns: list of rate dicts with all currencies in the table
        """
        data = self._fetch(f"exchangerates/tables/{table}/")
        if not data:
            return None

        table_data = data[0]
        return {
            "table": table_data["table"],
            "no": table_data["no"],
            "date": table_data["effectiveDate"],
            "rates": table_data["rates"],
        }

    # ================================================================
    # Buy/Sell rates (Table C)
    # ================================================================

    def get_buy_sell_rate(self, currency_code):
        """
        Get buy/sell (bid/ask) rate from Table C.

        Returns: dict with keys: currency, code, bid, ask, spread, date
                 or None if not available
        """
        code = currency_code.upper().strip()
        data = self._fetch(f"exchangerates/rates/c/{code}/")
        if not data:
            return None

        rate = data["rates"][0]
        return {
            "currency": data["currency"],
            "code": data["code"],
            "bid": rate["bid"],
            "ask": rate["ask"],
            "spread": round(rate["ask"] - rate["bid"], 4),
            "date": rate["effectiveDate"],
        }

    def get_effective_rate(self, currency_code, spread_pct=1.5):
        """
        Get our exchange office effective buy/sell rates.

        Tries Table C first (bid/ask), falls back to Table A (mid).
        Applies our spread on top.

        Returns: dict with our_buy_rate, our_sell_rate, source, etc.
        """
        code = currency_code.upper().strip()

        # try Table C first
        tc = self.get_buy_sell_rate(code)
        if tc:
            our_buy = tc["ask"] * (1 + spread_pct / 100)
            our_sell = tc["bid"] * (1 - spread_pct / 100)
            return {
                "code": code,
                "source": "Table C",
                "nbp_bid": tc["bid"],
                "nbp_ask": tc["ask"],
                "our_buy_rate": round(our_buy, 4),
                "our_sell_rate": round(our_sell, 4),
                "our_spread": round(our_buy - our_sell, 4),
                "spread_pct": spread_pct,
                "date": tc["date"],
            }

        # fall back to Table A
        ta = self.get_mid_rate(code)
        if ta:
            our_buy = ta["mid"] * (1 + spread_pct / 100)
            our_sell = ta["mid"] * (1 - spread_pct / 100)
            return {
                "code": code,
                "source": "Table A",
                "nbp_mid": ta["mid"],
                "our_buy_rate": round(our_buy, 4),
                "our_sell_rate": round(our_sell, 4),
                "our_spread": round(our_buy - our_sell, 4),
                "spread_pct": spread_pct,
                "date": ta["date"],
            }

        return None

    # ================================================================
    # Historical rates
    # ================================================================

    def get_rate_for_date(self, currency_code, date_str, table="a"):
        """
        Get exchange rate for a specific date.

        Args:
            currency_code: ISO 4217 code
            date_str: date in YYYY-MM-DD format
            table: 'a' for mid rates, 'c' for bid/ask

        Returns: rate dict or None (weekends/holidays return 404)
        """
        code = currency_code.upper().strip()
        data = self._fetch(
            f"exchangerates/rates/{table}/{code}/{date_str}/",
            use_cache=True,
        )
        if not data:
            return None

        rate = data["rates"][0]
        result = {
            "currency": data["currency"],
            "code": data["code"],
            "date": rate["effectiveDate"],
        }
        if table.lower() == "c":
            result["bid"] = rate["bid"]
            result["ask"] = rate["ask"]
        else:
            result["mid"] = rate["mid"]

        return result

    def get_rate_history(self, currency_code, last_n=10, table="a"):
        """
        Get last N exchange rates for a currency.

        Args:
            currency_code: ISO 4217 code
            last_n: number of recent rates (max 255)
            table: 'a' or 'c'

        Returns: list of rate dicts ordered by date
        """
        code = currency_code.upper().strip()
        n = min(last_n, 255)
        data = self._fetch(
            f"exchangerates/rates/{table}/{code}/last/{n}/",
            use_cache=(n <= 10),  # only cache small queries
        )
        if not data:
            return []

        results = []
        for r in data["rates"]:
            entry = {"date": r["effectiveDate"]}
            if table.lower() == "c":
                entry["bid"] = r["bid"]
                entry["ask"] = r["ask"]
            else:
                entry["mid"] = r["mid"]
            results.append(entry)

        return results

    def get_rate_date_range(self, currency_code, start_date, end_date,
                            table="a"):
        """
        Get exchange rates for a date range.

        Args:
            currency_code: ISO 4217 code
            start_date: start date YYYY-MM-DD
            end_date: end date YYYY-MM-DD
            table: 'a' or 'c'

        Returns: list of rate dicts
        """
        code = currency_code.upper().strip()
        data = self._fetch(
            f"exchangerates/rates/{table}/{code}/{start_date}/{end_date}/",
            use_cache=True,
        )
        if not data:
            return []

        results = []
        for r in data["rates"]:
            entry = {"date": r["effectiveDate"]}
            if table.lower() == "c":
                entry["bid"] = r["bid"]
                entry["ask"] = r["ask"]
            else:
                entry["mid"] = r["mid"]
            results.append(entry)

        return results

    def get_rate_statistics(self, currency_code, last_n=30):
        """
        Compute statistics for the last N rates.

        Returns: dict with min, max, avg, current, change, trend
        """
        rates = self.get_rate_history(currency_code, last_n=last_n)
        if not rates:
            return None

        mids = [r["mid"] for r in rates]
        current = mids[-1]
        previous = mids[0]

        return {
            "code": currency_code.upper(),
            "period_days": len(mids),
            "min": round(min(mids), 4),
            "max": round(max(mids), 4),
            "avg": round(sum(mids) / len(mids), 4),
            "current": current,
            "first": previous,
            "change": round(current - previous, 4),
            "change_pct": round((current - previous) / previous * 100, 2),
            "trend": "↑" if current > previous else
                     "↓" if current < previous else "→",
            "start_date": rates[0]["date"],
            "end_date": rates[-1]["date"],
        }

    # ================================================================
    # Gold prices
    # ================================================================

    def get_gold_price(self):
        """
        Get current gold price from NBP (PLN per gram).

        Returns: dict with price and date, or None
        """
        data = self._fetch("cenyzlota/")
        if not data:
            return None

        return {
            "price": data[0]["cena"],
            "date": data[0]["data"],
        }

    def get_gold_price_history(self, last_n=10):
        """
        Get last N gold prices.

        Returns: list of dicts with price and date
        """
        data = self._fetch(f"cenyzlota/last/{last_n}/", use_cache=False)
        if not data:
            return []

        return [
            {"price": entry["cena"], "date": entry["data"]}
            for entry in data
        ]

    # ================================================================
    # Utility
    # ================================================================

    def get_available_currencies(self, table="a"):
        """
        List all currencies available in a given table.

        Returns: list of dicts with code and name
        """
        data = self._fetch(f"exchangerates/tables/{table}/")
        if not data:
            return []

        return [
            {"code": r["code"], "name": r["currency"]}
            for r in data[0]["rates"]
        ]

    def is_currency_supported(self, currency_code, table="a"):
        """Check if a currency exists in the given table."""
        currencies = self.get_available_currencies(table)
        code = currency_code.upper().strip()
        return any(c["code"] == code for c in currencies)
