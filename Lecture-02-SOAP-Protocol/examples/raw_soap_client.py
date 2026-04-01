"""
Lecture 2 - Raw SOAP Client

Sends SOAP XML manually using HTTP POST instead of using Zeep.
This shows what's actually going over the wire when you call a SOAP service.
Basically, this is what Zeep does behind the scenes.

Start soap_server.py first.

needs: pip install requests
"""

import requests
import xml.dom.minidom
import sys


def call_soap(url, method, namespace, params):
    """
    Manually build a SOAP request and send it via HTTP POST.
    Returns the request XML, response XML, and status code.
    """

    # build the XML by hand
    params_xml = "\n".join(
        f"        <tns:{k}>{v}</tns:{k}>" for k, v in params.items()
    )

    soap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap-env:Envelope
    xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:tns="{namespace}">
  <soap-env:Body>
    <tns:{method}>
{params_xml}
    </tns:{method}>
  </soap-env:Body>
</soap-env:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": f'"{namespace}/{method}"',
    }

    resp = requests.post(url, data=soap_xml, headers=headers)
    return soap_xml, resp.text, resp.status_code


def print_xml(xml_str, indent="      "):
    """pretty print xml"""
    try:
        pretty = xml.dom.minidom.parseString(xml_str).toprettyxml(indent="  ")
        for line in pretty.split("\n"):
            if line.strip():
                print(f"{indent}{line}")
    except Exception:
        print(f"{indent}{xml_str[:200]}")


def main():
    url = "http://localhost:8000/"
    ns = "lecture2.soap.demo"

    print("\nRaw SOAP Client (manual HTTP)")
    print("-" * 40)
    print("  Sending hand-crafted SOAP XML via HTTP POST\n")

    # test multiply
    print("  --- multiply(3, 2) ---")
    try:
        req, resp, status = call_soap(url, "multiply", ns, {"val1": 3, "val2": 2})
    except requests.ConnectionError:
        print("  Can't connect. Start soap_server.py first.")
        sys.exit(1)

    print("  Request sent:")
    print_xml(req)
    print(f"\n  HTTP {status}")
    print("  Response received:")
    print_xml(resp)

    # test add
    print("\n  --- add(15, 27) ---")
    req, resp, status = call_soap(url, "add", ns, {"val1": 15, "val2": 27})
    print("  Request:")
    print_xml(req)
    print(f"\n  HTTP {status}")
    print("  Response:")
    print_xml(resp)

    # test greet
    print("\n  --- greet('NetworkStudent') ---")
    req, resp, status = call_soap(url, "greet", ns, {"name": "NetworkStudent"})
    print("  Request:")
    print_xml(req)
    print(f"\n  HTTP {status}")
    print("  Response:")
    print_xml(resp)

    print("\n  What happens under the hood:")
    print("  1. Build XML with method name + params")
    print("  2. Set Content-Type to text/xml and add SOAPAction header")
    print("  3. HTTP POST to the service URL")
    print("  4. Server processes it and sends back XML response")
    print("  5. We parse the response")
    print("\n  Zeep does all of this automatically, but it's good to")
    print("  understand what's actually happening on the wire.")
    print()


if __name__ == "__main__":
    main()
