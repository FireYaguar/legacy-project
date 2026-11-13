# test_shipping_fix.py
# Tests for shipping.py: behaviour of the public functions (regression)
# and removal of hardcoded credentials (CR-002).

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import shipping


# ---------- regression: behaviour must stay exactly as before ----------

def test_cost_standard_light_parcel():
    assert shipping.calculate_shipping_cost(0.5, 100, 1) == 45


def test_cost_standard_long_distance_surcharge():
    assert shipping.calculate_shipping_cost(1, 400, 1) == 60.5


def test_cost_express():
    assert shipping.calculate_shipping_cost(3, 100, 2) == 160


def test_cost_courier():
    assert shipping.calculate_shipping_cost(1, 20, 3) == 125


def test_cost_international_overweight():
    assert shipping.calculate_shipping_cost(4, 0, 4) == 600


def test_cost_fragile_surcharge():
    assert shipping.calculate_shipping_cost(0.5, 100, 1, is_fragile=True) == 58.5


def test_cost_unknown_method_is_zero():
    assert shipping.calculate_shipping_cost(1, 10, 9) == 0


def test_delivery_time_by_method():
    assert shipping.get_delivery_time(1, 50) == 1
    assert shipping.get_delivery_time(1, 350) == 3
    assert shipping.get_delivery_time(2, 1000) == 1
    assert shipping.get_delivery_time(3, 5) == 0
    assert shipping.get_delivery_time(4, 1) == 14
    assert shipping.get_delivery_time(9, 1) == -1


def test_create_shipment_standard():
    result = shipping.create_shipment(42, 1, "Kyiv, Khreshchatyk 1", 0.8)
    assert result["order_id"] == 42
    assert result["tracking"].startswith("TRK42")
    assert result["cost"] == 55
    assert result["estimated_days"] == 2
    assert result["carrier_response"]["success"] is True


def test_create_shipment_unknown_method():
    result = shipping.create_shipment(43, 9, "Lviv", 1)
    assert result["carrier_response"] == {"success": False, "error": "unknown method"}


def test_shipment_status():
    assert shipping.get_shipment_status("TRK123")["status"] == "in_transit"
    assert shipping.get_shipment_status("59000000000000")["status"] == "delivered"
    assert shipping.get_shipment_status("XYZ")["status"] == "unknown"


def test_cancel_shipment():
    assert shipping.cancel_shipment("") == (False, "no tracking number")
    assert shipping.cancel_shipment("TRK123") == (True, "cancelled (mock)")
