"""
Lecture 4 - Exchange Rate SOAP Server

A SOAP web service that wraps the NBP API. Clients call our SOAP methods
instead of dealing with REST/JSON directly.

This is what the professor asked for: a service that accepts a currency
code and returns the exchange rate from NBP.

WSDL: http://localhost:8000/?wsdl

needs: pip install spyne lxml requests
"""

from spyne import (
    Application, ServiceBase, rpc,
    Unicode, Float, ComplexModel, Array, Integer,
)
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server
import requests


NBP_BASE = "https://api.nbp.pl/api"


# --- complex types for structured responses ---

class ExchangeRate(ComplexModel):
    """mid rate from Table A"""
    currency = Unicode
    code = Unicode
    mid = Float
    date = Unicode
    table_no = Unicode


class BuySellRate(ComplexModel):
    """buy/sell rate from Table C"""
    currency = Unicode
    code = Unicode
    bid = Float
    ask = Float
    spread = Float
    date = Unicode


class CurrencyInfo(ComplexModel):
    """basic currency info"""
    code = Unicode
    name = Unicode


class RateHistory(ComplexModel):
    """single historical rate entry"""
    date = Unicode
    mid = Float


# --- helper to call NBP ---

def fetch_nbp(endpoint):
    """call NBP API and return JSON or None"""
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


# --- the SOAP service ---

class ExchangeRateService(ServiceBase):
    """SOAP service wrapping the NBP REST API"""

    @rpc(Unicode, _returns=ExchangeRate)
    def get_rate(ctx, currency_code):
        """
        Get the current mid exchange rate for a currency.
        Uses NBP Table A.

        Args:
            currency_code: ISO 4217 code (e.g. USD, EUR, GBP)
        """
        code = currency_code.upper().strip()
        print(f"  -> get_rate('{code}') called")

        data = fetch_nbp(f"exchangerates/rates/a/{code}/")
        if not data:
            raise ValueError(f"Currency '{code}' not found or NBP unavailable")

        rate = data["rates"][0]
        return ExchangeRate(
            currency=data["currency"],
            code=data["code"],
            mid=rate["mid"],
            date=rate["effectiveDate"],
            table_no=rate["no"],
        )

    @rpc(Unicode, _returns=BuySellRate)
    def get_buy_sell_rate(ctx, currency_code):
        """
        Get the buy (bid) and sell (ask) rates.
        Uses NBP Table C — this is what exchange offices use.

        Args:
            currency_code: ISO 4217 code
        """
        code = currency_code.upper().strip()
        print(f"  -> get_buy_sell_rate('{code}') called")

        data = fetch_nbp(f"exchangerates/rates/c/{code}/")
        if not data:
            raise ValueError(
                f"Currency '{code}' not found in Table C. "
                "Table C only has major currencies."
            )

        rate = data["rates"][0]
        return BuySellRate(
            currency=data["currency"],
            code=data["code"],
            bid=rate["bid"],
            ask=rate["ask"],
            spread=round(rate["ask"] - rate["bid"], 4),
            date=rate["effectiveDate"],
        )

    @rpc(Unicode, Unicode, _returns=ExchangeRate)
    def get_rate_by_date(ctx, currency_code, date):
        """
        Get exchange rate for a specific date.

        Args:
            currency_code: ISO 4217 code
            date: date string in YYYY-MM-DD format
        """
        code = currency_code.upper().strip()
        print(f"  -> get_rate_by_date('{code}', '{date}') called")

        data = fetch_nbp(f"exchangerates/rates/a/{code}/{date}/")
        if not data:
            raise ValueError(
                f"No rate found for '{code}' on {date}. "
                "Date might be a weekend/holiday."
            )

        rate = data["rates"][0]
        return ExchangeRate(
            currency=data["currency"],
            code=data["code"],
            mid=rate["mid"],
            date=rate["effectiveDate"],
            table_no=rate["no"],
        )

    @rpc(Unicode, Integer, _returns=Array(RateHistory))
    def get_rate_history(ctx, currency_code, last_n):
        """
        Get last N exchange rates for a currency.

        Args:
            currency_code: ISO 4217 code
            last_n: number of recent rates to fetch (max 255)
        """
        code = currency_code.upper().strip()
        n = min(last_n or 10, 255)
        print(f"  -> get_rate_history('{code}', {n}) called")

        data = fetch_nbp(f"exchangerates/rates/a/{code}/last/{n}/")
        if not data:
            raise ValueError(f"Could not fetch history for '{code}'")

        return [
            RateHistory(date=r["effectiveDate"], mid=r["mid"])
            for r in data["rates"]
        ]

    @rpc(_returns=Array(CurrencyInfo))
    def get_supported_currencies(ctx):
        """
        List all currencies available in NBP Table A.
        """
        print("  -> get_supported_currencies() called")

        data = fetch_nbp("exchangerates/tables/a/")
        if not data:
            raise ValueError("Could not fetch currency table from NBP")

        return [
            CurrencyInfo(code=r["code"], name=r["currency"])
            for r in data[0]["rates"]
        ]


# --- app setup ---

application = Application(
    services=[ExchangeRateService],
    tns="lecture4.nbp.exchange",
    name="ExchangeRateWebService",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

wsgi_app = WsgiApplication(application)


if __name__ == "__main__":
    host, port = "localhost", 8000

    print(f"\nExchange Rate SOAP Server")
    print(f"  URL:  http://{host}:{port}/")
    print(f"  WSDL: http://{host}:{port}/?wsdl")
    print(f"\n  Operations:")
    print(f"    - get_rate(currency_code)")
    print(f"    - get_buy_sell_rate(currency_code)")
    print(f"    - get_rate_by_date(currency_code, date)")
    print(f"    - get_rate_history(currency_code, last_n)")
    print(f"    - get_supported_currencies()")
    print(f"\n  Ctrl+C to stop\n")

    server = make_server(host, port, wsgi_app)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
