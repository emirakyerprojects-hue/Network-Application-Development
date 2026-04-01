"""
Lecture 1 - Interoperability Demo

Shows why we need standardized formats like XML and JSON for web services.
Compares the same data as a Python dict, XML, and JSON to make the point
that language-specific formats don't work for cross-platform communication.
"""

import xml.etree.ElementTree as ET
import xml.dom.minidom
import json


def main():
    print("\nLecture 1 - Interoperability Demo")
    print("-" * 40)

    # the data we want to send
    method = "multiply"
    params = {"val1": 10, "val2": 5}
    result = params["val1"] * params["val2"]

    # --- 1. python dict ---
    print("\n1) Python dict (language-specific)")
    print(f"   Request:  {{'method': '{method}', 'params': {params}}}")
    print(f"   Response: {{'result': {result}}}")
    print("   Problem: only Python understands this format.")
    print("   A Java or C# app can't read it directly.")

    # --- 2. XML format ---
    print("\n2) XML (language-independent)")

    # build the SOAP-ish request
    req_env = ET.Element("soap:Envelope", {
        "xmlns:soap": "http://www.w3.org/2001/12/soap-envelope",
    })
    req_body = ET.SubElement(req_env, "soap:Body")
    req_method = ET.SubElement(req_body, f"m:{method}", {"xmlns:m": "demo"})
    for k, v in params.items():
        ET.SubElement(req_method, f"m:{k}").text = str(v)

    req_xml = ET.tostring(req_env, encoding="unicode")
    pretty_req = xml.dom.minidom.parseString(req_xml).toprettyxml(indent="  ")

    print("   Request:")
    for line in pretty_req.split("\n")[1:]:
        if line.strip():
            print(f"     {line}")

    # and the response
    resp_env = ET.Element("soap:Envelope", {
        "xmlns:soap": "http://www.w3.org/2001/12/soap-envelope",
    })
    resp_body = ET.SubElement(resp_env, "soap:Body")
    resp_m = ET.SubElement(resp_body, f"m:{method}Response", {"xmlns:m": "demo"})
    ET.SubElement(resp_m, "m:result").text = str(result)

    resp_xml = ET.tostring(resp_env, encoding="unicode")
    pretty_resp = xml.dom.minidom.parseString(resp_xml).toprettyxml(indent="  ")

    print("   Response:")
    for line in pretty_resp.split("\n")[1:]:
        if line.strip():
            print(f"     {line}")

    print("   -> every major language has an XML parser, so this works everywhere")

    # --- 3. JSON format ---
    print("\n3) JSON (language-independent)")

    json_req = {"method": method, "params": params}
    json_resp = {"method": f"{method}Response", "result": result}

    print(f"   Request:  {json.dumps(json_req)}")
    print(f"   Response: {json.dumps(json_resp)}")
    print("   -> also works everywhere, and it's shorter than XML")

    # --- comparison ---
    print("\n--- Size comparison ---")
    xml_size = len(req_xml.encode("utf-8"))
    json_size = len(json.dumps(json_req).encode("utf-8"))
    print(f"   XML:  {xml_size} bytes")
    print(f"   JSON: {json_size} bytes")
    print(f"   XML is {xml_size - json_size} bytes bigger "
          f"({(xml_size / json_size - 1) * 100:.0f}% overhead)")
    print()
    print("   XML is more verbose but supports namespaces and schemas,")
    print("   which is why SOAP uses it. JSON is simpler and used in REST.")
    print("   Both achieve the main goal: interoperability.")
    print()


if __name__ == "__main__":
    main()
