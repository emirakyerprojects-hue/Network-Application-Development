"""
Lecture 3 - WSDL Server

Same idea as the Lecture 2 server but with some extras to show
more WSDL features - like a complex return type.

WSDL gets generated automatically at http://localhost:8000/?wsdl

needs: pip install spyne lxml
"""

from spyne import (
    Application, ServiceBase, rpc,
    Integer, Float, Unicode, ComplexModel,
)
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server


# a complex type - this shows up in the WSDL <types> section
class OperationResult(ComplexModel):
    """returns more detail about the calculation"""
    operation = Unicode
    val1 = Integer
    val2 = Integer
    result = Float
    description = Unicode


class CalculatorService(ServiceBase):

    @rpc(Integer, Integer, _returns=Integer, _out_variable_name="result")
    def multiply(ctx, val1, val2):
        return val1 * val2

    @rpc(Integer, Integer, _returns=Integer, _out_variable_name="result")
    def add(ctx, val1, val2):
        return val1 + val2

    @rpc(Integer, Integer, _returns=Integer, _out_variable_name="result")
    def subtract(ctx, val1, val2):
        return val1 - val2

    @rpc(Integer, Integer, _returns=OperationResult)
    def multiply_detailed(ctx, val1, val2):
        """returns a complex type instead of just an int"""
        r = val1 * val2
        return OperationResult(
            operation="multiply",
            val1=val1, val2=val2,
            result=r,
            description=f"{val1} x {val2} = {r}",
        )

    @rpc(_returns=Unicode)
    def get_service_info(ctx):
        return "CalculatorService v1.0 - Lecture 3 WSDL Demo"


application = Application(
    services=[CalculatorService],
    tns="http://lecture3.wsdl.demo/",
    name="CalculatorWebService",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

wsgi_app = WsgiApplication(application)


if __name__ == "__main__":
    host, port = "localhost", 8000

    print(f"\nWSDL Server running")
    print(f"  URL:  http://{host}:{port}/")
    print(f"  WSDL: http://{host}:{port}/?wsdl")
    print(f"\n  Try opening the WSDL URL in your browser")
    print(f"  Ctrl+C to stop\n")

    server = make_server(host, port, wsgi_app)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
