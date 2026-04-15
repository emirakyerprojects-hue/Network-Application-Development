# Lecture 3 – WSDL

Notes and code from the lecture on WSDL (Web Services Description Language).

## What is WSDL?

WSDL is basically an XML file that describes everything about a web service — what operations it has, what parameters they take, what protocol to use, and where the service lives. It's like a contract between the client and server.

The key idea: the client doesn't need to know anything about the implementation. It just reads the WSDL and knows exactly how to call the service.

## WSDL structure

A WSDL document has these main parts:

- `<types>` – data type definitions (using XML Schema)
- `<message>` – defines input/output data for each operation
- `<portType>` – the operations themselves (basically the interface)
- `<binding>` – how the communication works (SOAP, HTTP, etc.)
- `<service>` – the actual URL where the service is hosted

Or as the professor put it: **WSDL = interface + protocol + location**

## Why it matters

The biggest advantage is **automatic client generation**. Tools like Zeep (Python) or svcutil (C#) can read a WSDL and generate all the code you need to call the service. You never have to write XML by hand.

Flow:
1. Client downloads the WSDL
2. Tool generates a proxy class
3. You call methods on the proxy like normal functions
4. The proxy handles all the SOAP XML stuff

## Code examples

| File | What it does |
|------|-------------|
| `wsdl_anatomy.py` | Builds a WSDL document from scratch to understand the structure (no server) |
| `wsdl_server.py` | SOAP server that auto-generates a WSDL |
| `wsdl_client.py` | Client that reads WSDL and generates proxy automatically |
| `wsdl_inspector.py` | Fetches and analyzes any WSDL document |

### Running

```bash
# without server (just WSDL structure)
python examples/wsdl_anatomy.py

# with server
python examples/wsdl_server.py          # terminal 1
python examples/wsdl_client.py          # terminal 2
python examples/wsdl_inspector.py       # terminal 2
```

You can also open http://localhost:8000/?wsdl in a browser to see the raw WSDL XML.

## Previous

[Lecture 2 – SOAP](../Lecture-02-SOAP-Protocol/)

## Next

[Lecture 4 – NBP Exchange Rates](../Lecture-04-NBP-Exchange-Rates/)
