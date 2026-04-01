"""
Lecture 2 - SOAP Message Anatomy

Builds and parses SOAP messages manually to understand the structure.
Doesn't need a running server - just shows how the XML looks.
"""

import xml.etree.ElementTree as ET
import xml.dom.minidom


SOAP_NS = "http://www.w3.org/2003/05/soap-envelope"
DEMO_NS = "demo"


def pretty(xml_str):
    """helper to pretty-print XML"""
    return xml.dom.minidom.parseString(xml_str).toprettyxml(indent="  ")


def print_xml(xml_str, indent="    "):
    """prints formatted XML with indentation"""
    for line in pretty(xml_str).split("\n")[1:]:
        if line.strip():
            print(f"{indent}{line}")


def build_request(method, params):
    """builds a SOAP request envelope"""
    env = ET.Element("soap:Envelope", {
        "xmlns:soap": SOAP_NS,
        "soap:encodingStyle": "http://www.w3.org/2003/05/soap-encoding",
    })
    body = ET.SubElement(env, "soap:Body", {"xmlns:m": DEMO_NS})
    m = ET.SubElement(body, f"m:{method}")
    for k, v in params.items():
        ET.SubElement(m, f"m:{k}").text = str(v)
    return ET.tostring(env, encoding="unicode")


def build_response(method, result):
    """builds a SOAP response envelope"""
    env = ET.Element("soap:Envelope", {
        "xmlns:soap": SOAP_NS,
        "soap:encodingStyle": "http://www.w3.org/2003/05/soap-encoding",
    })
    body = ET.SubElement(env, "soap:Body", {"xmlns:m": DEMO_NS})
    resp = ET.SubElement(body, f"m:{method}Response")
    ET.SubElement(resp, "m:result").text = str(result)
    return ET.tostring(env, encoding="unicode")


def build_fault(code, message, detail=""):
    """builds a SOAP fault message (for errors)"""
    env = ET.Element("soap:Envelope", {"xmlns:soap": SOAP_NS})
    body = ET.SubElement(env, "soap:Body")
    fault = ET.SubElement(body, "soap:Fault")
    ET.SubElement(fault, "faultcode").text = code
    ET.SubElement(fault, "faultstring").text = message
    if detail:
        ET.SubElement(fault, "detail").text = detail
    return ET.tostring(env, encoding="unicode")


def build_with_header(method, params, token=""):
    """builds a SOAP message that also has a Header (for auth etc)"""
    env = ET.Element("soap:Envelope", {"xmlns:soap": SOAP_NS})
    if token:
        header = ET.SubElement(env, "soap:Header")
        auth = ET.SubElement(header, "m:Authentication", {"xmlns:m": DEMO_NS})
        ET.SubElement(auth, "m:Token").text = token
    body = ET.SubElement(env, "soap:Body", {"xmlns:m": DEMO_NS})
    m = ET.SubElement(body, f"m:{method}")
    for k, v in params.items():
        ET.SubElement(m, f"m:{k}").text = str(v)
    return ET.tostring(env, encoding="unicode")


def main():
    print("\nLecture 2 - SOAP Message Anatomy")
    print("-" * 40)

    # 1. basic request
    print("\n1) SOAP Request - multiply(3, 2)")
    req = build_request("multiply", {"val1": 3, "val2": 2})
    print_xml(req)
    print("    -> Envelope > Body > method name + parameters")

    # 2. response
    print("\n2) SOAP Response")
    resp = build_response("multiply", 6)
    print_xml(resp)
    print("    -> same structure, but with the result instead")

    # 3. message with header
    print("\n3) SOAP with Header (authentication)")
    msg = build_with_header("multiply", {"val1": 10, "val2": 5},
                            token="Bearer abc123")
    print_xml(msg)
    print("    -> Header section is optional, used for metadata like auth tokens")

    # 4. fault (error)
    print("\n4) SOAP Fault (error response)")
    fault = build_fault("soap:Server", "Division by zero",
                        "Cannot divide by zero in the divide operation")
    print_xml(fault)
    print("    -> faultcode and faultstring tell the client what went wrong")

    # 5. parsing a message
    print("\n5) Parsing a SOAP request")
    incoming = build_request("multiply", {"val1": 10, "val2": 5})
    root = ET.fromstring(incoming)

    # find the method element
    for elem in root.iter():
        if "multiply" in elem.tag:
            method_elem = elem
            break

    print(f"    Method: {method_elem.tag}")
    for param in method_elem:
        name = param.tag.split(":")[-1]  # strip namespace prefix
        print(f"    Param: {name} = {param.text}")

    # 6. show full request/response cycle
    print("\n6) Request/Response cycle")
    ops = [
        ("multiply", {"val1": 3, "val2": 2}, lambda p: p["val1"] * p["val2"]),
        ("add", {"val1": 15, "val2": 27}, lambda p: p["val1"] + p["val2"]),
        ("subtract", {"val1": 100, "val2": 37}, lambda p: p["val1"] - p["val2"]),
    ]
    for method, params, fn in ops:
        result = fn(params)
        args = ", ".join(f"{k}={v}" for k, v in params.items())
        print(f"    {method}({args}) -> SOAP request -> server -> result={result}")

    print("\n  Summary:")
    print("    Envelope (required) - wraps everything")
    print("    Header (optional)   - metadata like auth")
    print("    Body (required)     - the actual method call or response")
    print("    Fault (optional)    - error details")
    print()


if __name__ == "__main__":
    main()
