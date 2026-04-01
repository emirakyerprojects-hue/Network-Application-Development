"""
Lecture 3 - WSDL Client

Shows the main advantage of WSDL: automatic client generation.
Zeep reads the WSDL and creates a proxy so you can call methods
like they're local functions. No XML needed on our side.

Also shows how to peek at the raw SOAP messages being sent.

Start wsdl_server.py first.

needs: pip install zeep lxml
"""

from zeep import Client
from zeep.plugins import HistoryPlugin
from lxml import etree
import sys


def main():
    wsdl = "http://localhost:8000/?wsdl"

    print("\nWSDL Client - Auto-Generated Proxy")
    print("-" * 40)

    # step 1: connect and let zeep generate the proxy
    print(f"  Reading WSDL from {wsdl}...")
    try:
        client = Client(wsdl)
    except Exception as e:
        print(f"  Failed: {e}")
        print("  -> start wsdl_server.py first")
        sys.exit(1)
    print("  Proxy generated!\n")

    # step 2: see what services/operations the WSDL describes
    print("  Services found in WSDL:")
    for svc_name, svc in client.wsdl.services.items():
        print(f"    {svc_name}")
        for port_name, port in svc.ports.items():
            print(f"      port: {port_name}")
            for op_name in port.binding._operations:
                print(f"        - {op_name}")
    print()

    # step 3: call methods like they're local
    # this is the whole point of WSDL + auto-generation
    print("  Calling methods (just like local functions):\n")

    r = client.service.multiply(val1=3, val2=2)
    print(f"    multiply(3, 2) = {r}  (type: {type(r).__name__})")

    r = client.service.add(val1=15, val2=27)
    print(f"    add(15, 27) = {r}")

    r = client.service.subtract(val1=100, val2=37)
    print(f"    subtract(100, 37) = {r}")

    # complex return type
    r = client.service.multiply_detailed(val1=7, val2=6)
    print(f"    multiply_detailed(7, 6):")
    print(f"      operation: {r.operation}")
    print(f"      result: {r.result}")
    print(f"      description: {r.description}")

    r = client.service.get_service_info()
    print(f"    get_service_info() = {r}")

    # step 4: look at what's actually being sent over the wire
    # (using zeep's history plugin)
    print("\n  Peeking at raw SOAP messages:")
    print("  " + "-" * 30)

    history = HistoryPlugin()
    client2 = Client(wsdl, plugins=[history])
    client2.service.multiply(val1=10, val2=5)

    # the actual XML that was sent
    sent = etree.tostring(history.last_sent["envelope"],
                          pretty_print=True, encoding="unicode")
    print("  Request XML:")
    for line in sent.strip().split("\n"):
        print(f"    {line}")

    # and what came back
    received = etree.tostring(history.last_received["envelope"],
                              pretty_print=True, encoding="unicode")
    print("\n  Response XML:")
    for line in received.strip().split("\n"):
        print(f"    {line}")

    print("\n  The proxy handles all of this automatically.")
    print("  We just call multiply(10, 5) and get 50 back.")
    print("  WSDL makes this possible by describing the interface.\n")


if __name__ == "__main__":
    main()
