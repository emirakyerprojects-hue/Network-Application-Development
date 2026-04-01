# Lecture 2 – SOAP Protocol

Notes and code from the second lecture about SOAP.

## What is SOAP?

SOAP = Simple Object Access Protocol. It's an XML-based protocol for exchanging data between applications. The main thing is that it's platform and language independent — a Python client can talk to a Java server as long as both understand SOAP.

## Message structure

Every SOAP message has this basic layout:

```
Envelope (required)
  Header (optional - for auth, metadata etc)
  Body (required - the actual data)
    Fault (optional - error info)
```

## Communication styles

- **RPC style**: you call a specific method with parameters, like a remote function call. Always synchronous.
- **Document style**: you send an XML document. More flexible, can be async.

## The multiply example from class

Request:
```xml
<soap:Body>
  <m:multiply>
    <m:val1>3</m:val1>
    <m:val2>2</m:val2>
  </m:multiply>
</soap:Body>
```

Response:
```xml
<soap:Body>
  <m:multiplyResponse>
    <m:result>6</m:result>
  </m:multiplyResponse>
</soap:Body>
```

Pretty straightforward — you wrap the method call in XML and send it over HTTP.

## Code examples

| File | What it does |
|------|-------------|
| `soap_server.py` | SOAP server with multiply, add, subtract, divide, greet |
| `soap_client.py` | Client that calls the server using Zeep |
| `soap_message_anatomy.py` | Builds and parses SOAP messages step by step (no server needed) |
| `raw_soap_client.py` | Sends raw SOAP XML over HTTP to see what's happening under the hood |

### Running it

```bash
# start the server first
python examples/soap_server.py

# then in another terminal
python examples/soap_client.py
python examples/raw_soap_client.py
```

The anatomy script works without a server:
```bash
python examples/soap_message_anatomy.py
```

## Pros and cons

Pros: standardized, interoperable, well-defined error handling with Faults

Cons: XML is verbose (lots of overhead), more complex than REST, harder to debug

## Next

[Lecture 3 - WSDL](../Lecture-03-WSDL/)
