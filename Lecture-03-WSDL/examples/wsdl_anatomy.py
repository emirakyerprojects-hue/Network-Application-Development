"""
Lecture 3 - WSDL Anatomy

Builds a complete WSDL document element by element to understand
what each part does. No server needed - just constructs the XML.

Uses lxml because stdlib ElementTree doesn't handle namespace
prefixes properly (learned that the hard way).

needs: pip install lxml
"""

from lxml import etree


# namespaces used in WSDL
WSDL_NS = "http://schemas.xmlsoap.org/wsdl/"
SOAP_NS = "http://schemas.xmlsoap.org/wsdl/soap/"
XSD_NS = "http://www.w3.org/2001/XMLSchema"
TNS = "http://demo.lecture3.soap/"

NSMAP = {
    "wsdl": WSDL_NS,
    "soap": SOAP_NS,
    "xsd": XSD_NS,
    "tns": TNS,
}


def pp(element):
    """pretty print an lxml element"""
    return etree.tostring(element, pretty_print=True, encoding="unicode")


def main():
    print("\nLecture 3 - WSDL Document Anatomy")
    print("-" * 40)
    print("  Building a WSDL for: CalculatorService (multiply, add)\n")

    # --- 1. root element ---
    print("1) <definitions> - root element")
    print("   Contains all the other WSDL elements.\n")

    definitions = etree.Element(
        f"{{{WSDL_NS}}}definitions",
        nsmap=NSMAP,
        attrib={"targetNamespace": TNS, "name": "CalculatorService"},
    )

    # --- 2. types ---
    print("2) <types> - data type definitions")
    print("   Uses XML Schema to define request/response structures.\n")

    types = etree.SubElement(definitions, f"{{{WSDL_NS}}}types")
    schema = etree.SubElement(types, f"{{{XSD_NS}}}schema",
                              attrib={"targetNamespace": TNS})

    # helper to add a request/response type
    # got tired of writing this out manually for each one
    def add_type(name, fields):
        elem = etree.SubElement(schema, f"{{{XSD_NS}}}element",
                                attrib={"name": name})
        ct = etree.SubElement(elem, f"{{{XSD_NS}}}complexType")
        seq = etree.SubElement(ct, f"{{{XSD_NS}}}sequence")
        for field_name, field_type in fields:
            etree.SubElement(seq, f"{{{XSD_NS}}}element",
                             attrib={"name": field_name, "type": f"xsd:{field_type}"})

    add_type("multiplyRequest", [("val1", "int"), ("val2", "int")])
    add_type("multiplyResponse", [("result", "int")])
    add_type("addRequest", [("val1", "int"), ("val2", "int")])
    add_type("addResponse", [("result", "int")])

    print(pp(types))

    # --- 3. messages ---
    print("3) <message> - input/output definitions")
    print("   Each operation needs a request and response message.\n")

    for name, element in [("multiplyRequest", "tns:multiplyRequest"),
                          ("multiplyResponse", "tns:multiplyResponse"),
                          ("addRequest", "tns:addRequest"),
                          ("addResponse", "tns:addResponse")]:
        msg = etree.SubElement(definitions, f"{{{WSDL_NS}}}message",
                               attrib={"name": name})
        etree.SubElement(msg, f"{{{WSDL_NS}}}part",
                         attrib={"name": "parameters", "element": element})

    # just show the first one as an example
    msgs = definitions.findall(f"{{{WSDL_NS}}}message")
    print(pp(msgs[0]))
    print(pp(msgs[1]))

    # --- 4. portType (the interface) ---
    print("4) <portType> - available operations")
    print("   This is like an interface in Java/C#.\n")

    port_type = etree.SubElement(definitions, f"{{{WSDL_NS}}}portType",
                                 attrib={"name": "CalculatorPortType"})

    for op_name in ["multiply", "add"]:
        op = etree.SubElement(port_type, f"{{{WSDL_NS}}}operation",
                              attrib={"name": op_name})
        etree.SubElement(op, f"{{{WSDL_NS}}}input",
                         attrib={"message": f"tns:{op_name}Request"})
        etree.SubElement(op, f"{{{WSDL_NS}}}output",
                         attrib={"message": f"tns:{op_name}Response"})

    print(pp(port_type))

    # --- 5. binding ---
    print("5) <binding> - protocol details")
    print("   Connects the abstract interface to actual SOAP over HTTP.\n")

    binding = etree.SubElement(definitions, f"{{{WSDL_NS}}}binding",
                               attrib={"name": "CalculatorBinding",
                                       "type": "tns:CalculatorPortType"})
    etree.SubElement(binding, f"{{{SOAP_NS}}}binding",
                     attrib={"style": "document",
                             "transport": "http://schemas.xmlsoap.org/soap/http"})

    for op_name in ["multiply", "add"]:
        op = etree.SubElement(binding, f"{{{WSDL_NS}}}operation",
                              attrib={"name": op_name})
        etree.SubElement(op, f"{{{SOAP_NS}}}operation",
                         attrib={"soapAction": f"{TNS}{op_name}"})
        inp = etree.SubElement(op, f"{{{WSDL_NS}}}input")
        etree.SubElement(inp, f"{{{SOAP_NS}}}body", attrib={"use": "literal"})
        out = etree.SubElement(op, f"{{{WSDL_NS}}}output")
        etree.SubElement(out, f"{{{SOAP_NS}}}body", attrib={"use": "literal"})

    print(pp(binding))

    # --- 6. service (endpoint) ---
    print("6) <service> - where the service lives")

    service = etree.SubElement(definitions, f"{{{WSDL_NS}}}service",
                               attrib={"name": "CalculatorService"})
    port = etree.SubElement(service, f"{{{WSDL_NS}}}port",
                            attrib={"name": "CalculatorPort",
                                    "binding": "tns:CalculatorBinding"})
    etree.SubElement(port, f"{{{SOAP_NS}}}address",
                     attrib={"location": "http://localhost:8000/"})

    print(pp(service))

    # --- full document ---
    print("\n--- Complete WSDL ---")
    print(pp(definitions))

    print("Summary:")
    print("  types     -> what the data looks like")
    print("  message   -> input/output for each operation")
    print("  portType  -> what operations exist (the interface)")
    print("  binding   -> how to communicate (SOAP/HTTP)")
    print("  service   -> where to find it (URL)")
    print()


if __name__ == "__main__":
    main()
