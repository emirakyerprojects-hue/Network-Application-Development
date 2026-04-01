"""
Lecture 2 - SOAP Client

Calls the SOAP server using Zeep. Zeep reads the WSDL and generates
a proxy so you can call remote methods like normal Python functions.

Start soap_server.py first!

needs: pip install zeep
"""

from zeep import Client
from zeep.exceptions import Fault
import sys


def main():
    wsdl = "http://localhost:8000/?wsdl"

    print("\nSOAP Client (using Zeep)")
    print("-" * 40)

    # connect to the service
    print(f"  Connecting to {wsdl}...")
    try:
        client = Client(wsdl)
        print("  Connected!\n")
    except Exception as e:
        print(f"  Failed: {e}")
        print("  -> make sure soap_server.py is running")
        sys.exit(1)

    # list what operations are available
    print("  Available operations:")
    for svc in client.wsdl.services.values():
        for port in svc.ports.values():
            for op in port.binding._operations.values():
                print(f"    - {op.name}")
    print()

    # call multiply (the example from class)
    print("  multiply(3, 2) =", client.service.multiply(val1=3, val2=2))
    print("  multiply(10, 5) =", client.service.multiply(val1=10, val2=5))
    print("  add(15, 27) =", client.service.add(val1=15, val2=27))
    print("  subtract(100, 37) =", client.service.subtract(val1=100, val2=37))

    result = client.service.divide(val1=22, val2=7)
    print(f"  divide(22, 7) = {result:.6f}")

    print(f"  greet('Student') = {client.service.greet(name='Student')}")

    # test error handling - division by zero should return a SOAP Fault
    print("\n  Testing error handling (divide by zero):")
    try:
        client.service.divide(val1=10, val2=0)
    except Fault as f:
        print(f"  Got SOAP Fault: {f.message}")
        print("  -> server returned an error through the SOAP Fault mechanism")

    print("\n  Behind the scenes, Zeep:")
    print("  - reads the WSDL to know what methods exist")
    print("  - builds SOAP XML for each call")
    print("  - sends it via HTTP POST")
    print("  - parses the XML response back into Python types")
    print()


if __name__ == "__main__":
    main()
