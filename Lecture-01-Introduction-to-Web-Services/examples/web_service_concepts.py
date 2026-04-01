"""
Lecture 1 - Web Service Concepts

Shows the basic idea behind web services:
- difference between calling a function locally vs over the network
- how XML is used to make messages language-independent
- a simple HTTP service you can actually call

No extra libraries needed, just stdlib.
"""

import xml.etree.ElementTree as ET
import xml.dom.minidom
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.request
import json
import time


def multiply_local(a, b):
    """just a normal function"""
    return a * b


def part1_local_vs_remote():
    """shows why web services are different from normal function calls"""

    print("\n--- Part 1: Local Call vs Remote Service Call ---\n")

    result = multiply_local(3, 2)
    print(f"  Local:  multiply_local(3, 2) = {result}")
    print("  -> direct call, same process, only works in Python")

    print(f"\n  Remote: WebService.multiply(3, 2) = {result}")
    print("  -> params get serialized to XML, sent over HTTP,")
    print("     server processes it and sends back response")
    print("  -> any language can do this as long as it speaks HTTP + XML")


def part2_xml_message():
    """builds a simple SOAP-style XML request/response to show the format"""

    print("\n--- Part 2: XML Messages ---\n")

    # build request
    envelope = ET.Element("Envelope")
    body = ET.SubElement(envelope, "Body")
    method = ET.SubElement(body, "multiply")
    ET.SubElement(method, "val1").text = "3"
    ET.SubElement(method, "val2").text = "2"

    xml_str = ET.tostring(envelope, encoding="unicode")
    pretty = xml.dom.minidom.parseString(xml_str).toprettyxml(indent="  ")

    print("  Request XML:")
    for line in pretty.split("\n")[1:]:  # skip the <?xml?> declaration
        if line.strip():
            print(f"    {line}")

    # parse it back (this is what the server would do)
    root = ET.fromstring(xml_str)
    m = root.find(".//multiply")
    a = int(m.find("val1").text)
    b = int(m.find("val2").text)
    print(f"\n  Server reads: method=multiply, val1={a}, val2={b}")
    print(f"  Server computes: {a} * {b} = {a * b}")

    # build response
    resp_env = ET.Element("Envelope")
    resp_body = ET.SubElement(resp_env, "Body")
    resp_m = ET.SubElement(resp_body, "multiplyResponse")
    ET.SubElement(resp_m, "result").text = str(a * b)

    resp_xml = ET.tostring(resp_env, encoding="unicode")
    resp_pretty = xml.dom.minidom.parseString(resp_xml).toprettyxml(indent="  ")

    print("\n  Response XML:")
    for line in resp_pretty.split("\n")[1:]:
        if line.strip():
            print(f"    {line}")

    print("\n  Any language that can parse XML can read this -> interoperability")


# simple HTTP handler for part 3
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/multiply"):
            try:
                query = self.path.split("?")[1]
                params = dict(p.split("=") for p in query.split("&"))
                a, b = int(params["a"]), int(params["b"])
                result = {"method": "multiply", "result": a * b}

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            except Exception:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    # suppress the default logging, it's noisy
    def log_message(self, format, *args):
        pass


def part3_http_service():
    """starts a tiny HTTP service and calls it"""

    print("\n--- Part 3: Live HTTP Service ---\n")

    port = 9100
    server = HTTPServer(("localhost", port), SimpleHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.5)  # give it a moment to start

    print(f"  Server running on http://localhost:{port}")

    url = f"http://localhost:{port}/multiply?a=7&b=6"
    print(f"  Calling: GET {url}")

    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode())
            print(f"  Got back: {data}")
            print(f"  -> 7 * 6 = {data['result']}")
    finally:
        server.shutdown()
        print("  Server stopped.")

    print("\n  The client doesn't know how the server computes the result.")
    print("  It just knows: send two numbers, get an answer back.")


if __name__ == "__main__":
    print("\nLecture 1 - Web Service Concepts Demo")
    print("-" * 40)

    part1_local_vs_remote()
    part2_xml_message()
    part3_http_service()

    print("\n--- Takeaways ---")
    print("  1. Web services let programs talk over a network")
    print("  2. XML/JSON makes it language-independent")
    print("  3. Client only needs the interface, not the implementation")
    print("  4. This is the basis for SOAP, WSDL, etc.")
    print()
