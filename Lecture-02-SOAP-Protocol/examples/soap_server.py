"""
Lecture 2 - SOAP Server

A working SOAP web service using Spyne. Has a few arithmetic
operations and a greet method. The WSDL gets auto-generated at
http://localhost:8000/?wsdl

Start this before running the client scripts.

needs: pip install spyne lxml
"""

from spyne import Application, ServiceBase, rpc, Integer, Float, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server


class CalculatorService(ServiceBase):
    """our SOAP service - each @rpc method becomes a SOAP operation"""

    @rpc(Integer, Integer, _returns=Integer)
    def multiply(ctx, val1, val2):
        """the classic example from the lecture"""
        print(f"  -> multiply({val1}, {val2}) called")
        return val1 * val2

    @rpc(Integer, Integer, _returns=Integer)
    def add(ctx, val1, val2):
        print(f"  -> add({val1}, {val2}) called")
        return val1 + val2

    @rpc(Integer, Integer, _returns=Integer)
    def subtract(ctx, val1, val2):
        print(f"  -> subtract({val1}, {val2}) called")
        return val1 - val2

    @rpc(Integer, Integer, _returns=Float)
    def divide(ctx, val1, val2):
        print(f"  -> divide({val1}, {val2}) called")
        if val2 == 0:
            raise ValueError("Division by zero is not allowed")
        return val1 / val2

    @rpc(Unicode, _returns=Unicode)
    def greet(ctx, name):
        print(f"  -> greet('{name}') called")
        return f"Hello, {name}! Welcome to the SOAP Web Service."


# set up the Spyne application
application = Application(
    services=[CalculatorService],
    tns="lecture2.soap.demo",
    name="CalculatorWebService",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

wsgi_app = WsgiApplication(application)


if __name__ == "__main__":
    host, port = "localhost", 8000

    print(f"\nSOAP Server running")
    print(f"  URL:  http://{host}:{port}/")
    print(f"  WSDL: http://{host}:{port}/?wsdl")
    print(f"\n  Operations: multiply, add, subtract, divide, greet")
    print(f"  Ctrl+C to stop\n")

    server = make_server(host, port, wsgi_app)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
