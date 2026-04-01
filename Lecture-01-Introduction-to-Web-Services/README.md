# Lecture 1 – Introduction to Web Services

Notes and examples from the first lecture.

## What are Web Services?

Basically a way for programs to talk to each other over a network. Unlike regular websites which serve HTML to humans, web services exchange structured data (usually XML) between applications. The whole point is machine-to-machine communication.

Main technologies in the classic Web Services stack:
- **SOAP** – the messaging protocol
- **WSDL** – describes what the service can do
- **UDDI** – registry for finding services (we didn't really use this one much)

## Web Services vs normal websites

| | Traditional Web | Web Services |
|---|---|---|
| Who uses it | People | Other programs |
| Format | HTML | XML/JSON |
| Purpose | Show stuff | Exchange data |

## SOA (Service-Oriented Architecture)

The idea is that instead of writing one big monolithic app, you break it into small independent services that talk to each other through standard interfaces. Each service does one thing and can be developed separately.

Key thing is **interoperability** – a Python app can call a .NET service, a Java client can talk to a PHP backend, etc. That's the whole reason we use standardized protocols.

## Examples

| File | What it does |
|------|-------------|
| `web_service_concepts.py` | Shows the difference between local calls and remote service calls |
| `soa_demo.py` | Simulates an SOA system with multiple services working together |
| `interoperability_demo.py` | Compares Python dict vs XML vs JSON to show why standard formats matter |

Run them with:
```bash
python examples/web_service_concepts.py
python examples/soa_demo.py
python examples/interoperability_demo.py
```

## Next

[Lecture 2 – SOAP Protocol](../Lecture-02-SOAP-Protocol/)
