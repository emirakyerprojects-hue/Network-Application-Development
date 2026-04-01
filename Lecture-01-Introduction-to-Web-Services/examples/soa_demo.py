"""
Lecture 1 - SOA Demo

Simulates a Service-Oriented Architecture for an e-commerce system.
Four independent services work together to process orders.

In a real system these would run on different servers and communicate
over the network, but here they just call each other directly to
show the idea.
"""

from dataclasses import dataclass
from typing import Optional


# --- Product Service ---
# handles product catalog, nothing else

@dataclass
class Product:
    id: str
    name: str
    base_price: float
    category: str


class ProductService:
    def __init__(self):
        # some sample products
        self._catalog = {
            "P001": Product("P001", "Wireless Mouse", 29.99, "Electronics"),
            "P002": Product("P002", "Mechanical Keyboard", 89.99, "Electronics"),
            "P003": Product("P003", "USB-C Hub", 49.99, "Accessories"),
            "P004": Product("P004", "Monitor Stand", 39.99, "Furniture"),
        }

    def get_product(self, product_id: str) -> Optional[Product]:
        return self._catalog.get(product_id)

    def list_products(self) -> list[Product]:
        return list(self._catalog.values())


# --- Pricing Service ---
# figures out discounts and final prices

class PricingService:
    # different discount rates per category
    DISCOUNT_RULES = {
        "Electronics": 0.10,
        "Accessories": 0.05,
        "Furniture": 0.0,
    }

    def calculate_price(self, base_price, category, quantity):
        discount_rate = self.DISCOUNT_RULES.get(category, 0.0)
        subtotal = base_price * quantity
        discount = subtotal * discount_rate
        final = subtotal - discount

        return {
            "base_price": base_price,
            "quantity": quantity,
            "subtotal": subtotal,
            "discount_rate": f"{discount_rate:.0%}",
            "discount_amount": discount,
            "final_price": final,
        }


# --- Inventory Service ---
# tracks whats in stock

class InventoryService:
    def __init__(self):
        self._stock = {
            "P001": 150,
            "P002": 42,
            "P003": 0,   # out of stock
            "P004": 85,
        }

    def check_availability(self, product_id, quantity):
        stock = self._stock.get(product_id, 0)
        return {
            "product_id": product_id,
            "requested": quantity,
            "in_stock": stock,
            "available": stock >= quantity,
        }

    def reserve_stock(self, product_id, quantity):
        if self._stock.get(product_id, 0) >= quantity:
            self._stock[product_id] -= quantity
            return True
        return False


# --- Order Service ---
# this one orchestrates everything, calls the other services

class OrderService:
    def __init__(self, product_svc, pricing_svc, inventory_svc):
        self._product_svc = product_svc
        self._pricing_svc = pricing_svc
        self._inventory_svc = inventory_svc
        self._order_counter = 0

    def place_order(self, product_id, quantity):
        print(f"\n  Processing order: {product_id} x {quantity}")
        print(f"  {'-' * 40}")

        # step 1 - look up the product
        print("  [1] Product Service -> lookup...")
        product = self._product_svc.get_product(product_id)
        if not product:
            print(f"      FAIL: product '{product_id}' not found")
            return {"status": "FAILED", "reason": "Product not found"}
        print(f"      OK: {product.name} (${product.base_price:.2f})")

        # step 2 - check if we have enough in stock
        print("  [2] Inventory Service -> check stock...")
        avail = self._inventory_svc.check_availability(product_id, quantity)
        if not avail["available"]:
            print(f"      FAIL: need {quantity}, only {avail['in_stock']} left")
            return {"status": "FAILED", "reason": "Out of stock"}
        print(f"      OK: {avail['in_stock']} in stock")

        # step 3 - calculate price
        print("  [3] Pricing Service -> calculate...")
        pricing = self._pricing_svc.calculate_price(
            product.base_price, product.category, quantity
        )
        print(f"      Subtotal: ${pricing['subtotal']:.2f} "
              f"(discount: {pricing['discount_rate']})")
        print(f"      Final: ${pricing['final_price']:.2f}")

        # step 4 - reserve stock
        print("  [4] Inventory Service -> reserve...")
        if not self._inventory_svc.reserve_stock(product_id, quantity):
            print("      FAIL: couldn't reserve")
            return {"status": "FAILED", "reason": "Reservation failed"}
        print("      OK: reserved")

        self._order_counter += 1
        order_id = f"ORD-{self._order_counter:04d}"
        print(f"\n  Order {order_id} confirmed! "
              f"{product.name} x{quantity} = ${pricing['final_price']:.2f}")

        return {
            "status": "CONFIRMED",
            "order_id": order_id,
            "product": product.name,
            "quantity": quantity,
            "total": pricing["final_price"],
        }


if __name__ == "__main__":
    print("\nLecture 1 - SOA Demo")
    print("-" * 40)

    print("""
  Simulating 4 independent services:
  - Product Service   (catalog)
  - Pricing Service   (discounts)
  - Inventory Service (stock)
  - Order Service     (orchestrator)
    """)

    # set up all services
    product_svc = ProductService()
    pricing_svc = PricingService()
    inventory_svc = InventoryService()
    order_svc = OrderService(product_svc, pricing_svc, inventory_svc)

    # try a few scenarios
    print("  Scenario 1: normal order")
    order_svc.place_order("P001", 2)

    print("\n  Scenario 2: product doesn't exist")
    order_svc.place_order("P999", 1)

    print("\n  Scenario 3: out of stock")
    order_svc.place_order("P003", 1)

    print("\n  Scenario 4: another normal order")
    order_svc.place_order("P002", 3)

    print("\n--- Key points ---")
    print("  - each service handles one thing")
    print("  - they communicate through defined interfaces")
    print("  - you can swap out a service without breaking the others")
    print("  - in practice this would be over SOAP/REST, not direct calls")
    print()
