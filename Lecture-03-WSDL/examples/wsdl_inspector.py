"""
Lecture 3 - WSDL Inspector

Fetches a WSDL document and shows what's in it: services, operations,
types, namespaces. Works with the local demo server or any public WSDL.

Usage:
  python wsdl_inspector.py                        # local server
  python wsdl_inspector.py http://example.com?wsdl  # any WSDL

Start wsdl_server.py first (if using default URL).

needs: pip install zeep lxml requests
"""

from zeep import Client
from lxml import etree
import requests
import sys


def main():
    # use command line arg if provided, otherwise default to local server
    wsdl_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/?wsdl"

    print(f"\nWSDL Inspector")
    print(f"-" * 40)
    print(f"  URL: {wsdl_url}\n")

    # fetch the raw XML first
    try:
        resp = requests.get(wsdl_url)
        resp.raise_for_status()
    except requests.ConnectionError:
        print(f"  Can't connect to {wsdl_url}")
        print("  Make sure the server is running.")
        sys.exit(1)

    # show the raw WSDL (first 50 lines, otherwise it's too much)
    print("1) Raw WSDL XML (first 50 lines):")
    root = etree.fromstring(resp.content)
    xml_pretty = etree.tostring(root, pretty_print=True, encoding="unicode")
    lines = xml_pretty.split("\n")
    for i, line in enumerate(lines[:50]):
        print(f"   {i+1:3d}| {line}")
    if len(lines) > 50:
        print(f"   ... ({len(lines) - 50} more lines)")
    print(f"\n   Total size: {len(resp.content)} bytes, {len(lines)} lines")

    # parse with zeep for structured info
    try:
        client = Client(wsdl_url)
    except Exception as e:
        print(f"\n  Zeep couldn't parse it: {e}")
        return

    # services
    print("\n2) Services:")
    for svc_name, svc in client.wsdl.services.items():
        print(f"   {svc_name}")
        for port_name, port in svc.ports.items():
            print(f"     port: {port_name} (binding: {port.binding.name.localname})")

    # operations - the most useful part
    print("\n3) Operations:")
    for svc in client.wsdl.services.values():
        for port in svc.ports.values():
            for op_name, op in port.binding._operations.items():
                print(f"   - {op_name}")
                # try to show input/output info
                if hasattr(op, 'abstract') and op.abstract:
                    abstract = op.abstract
                    if hasattr(abstract, 'input_message') and abstract.input_message:
                        msg = abstract.input_message
                        if hasattr(msg, 'parts'):
                            for pname, part in msg.parts.items():
                                print(f"       input:  {pname} ({part.element})")
                    if hasattr(abstract, 'output_message') and abstract.output_message:
                        msg = abstract.output_message
                        if hasattr(msg, 'parts'):
                            for pname, part in msg.parts.items():
                                print(f"       output: {pname} ({part.element})")

    # types (if any custom ones exist)
    print("\n4) Custom types:")
    found_types = False
    if hasattr(client.wsdl, 'types') and client.wsdl.types:
        if hasattr(client.wsdl.types, '_schemas'):
            for prefix, schema in client.wsdl.types._schemas.items():
                if hasattr(schema, 'types'):
                    for type_name, type_def in schema.types.items():
                        found_types = True
                        print(f"   {type_name}")
                        if hasattr(type_def, 'elements'):
                            for elem_name, elem in type_def.elements:
                                etype = getattr(elem.type, 'name', '?')
                                print(f"     .{elem_name}: {etype}")
    if not found_types:
        print("   (none found)")

    # namespaces
    print("\n5) Namespaces:")
    for prefix, uri in root.nsmap.items():
        prefix_str = prefix if prefix else "(default)"
        print(f"   {prefix_str:>10} -> {uri}")

    # summary
    num_ops = sum(
        len(port.binding._operations)
        for svc in client.wsdl.services.values()
        for port in svc.ports.values()
    )
    print(f"\n  Total: {len(client.wsdl.services)} service(s), {num_ops} operation(s)")
    print()


if __name__ == "__main__":
    main()
