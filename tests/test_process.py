"""Тести для CR-015: валідація від'ємної суми/знижки у process.py."""
import unittest
from unittest import mock

import src.process as process
from src.process import get_discount, proc
from src.utils import calc


def make_order(order_id, user_id, amount, status="paid"):
    return {"id": order_id, "user_id": user_id, "amount": amount,
            "status": status, "date": "2024-03-01", "product_id": 10}


USERS = [
    {"id": 1, "name": "Regular", "role": 2},
    {"id": 2, "name": "Premium", "role": 3},
    {"id": 3, "name": "Guest", "role": 1},
]
PRODUCTS = [{"id": 10, "name": "Widget", "price": 150.0}]


class ProcTestBase(unittest.TestCase):
    """Підміняє get_data() і save(), щоб тести не залежали від DataManager."""

    def run_proc(self, orders):
        data = {"orders": orders, "users": USERS, "products": PRODUCTS}
        with mock.patch.object(process, "get_data", side_effect=lambda w: data[w]), \
                mock.patch.object(process, "save") as saved:
            result = proc()
        self.saved = saved
        return result


class TestGetDiscount(unittest.TestCase):
    def test_discount_zero_amount(self):
        self.assertEqual(get_discount(0, 3), 0)

    def test_discount_negative_amount(self):
        self.assertEqual(get_discount(-100, 3), 0)

    def test_discount_negative_large(self):
        self.assertEqual(get_discount(-5000, 3), 0)

    def test_discount_never_negative(self):
        for amount in (-1000, -1, 0, 1, 500, 501, 1000, 1001, 10000):
            with self.subTest(amount=amount):
                self.assertGreaterEqual(get_discount(amount, 3), 0)

    def test_discount_thresholds_unchanged(self):
        self.assertEqual(get_discount(500, 3), 0)
        self.assertEqual(get_discount(501, 3), 15.03)
        self.assertEqual(get_discount(1000, 3), 30.0)
        self.assertEqual(get_discount(1001, 3), 50.05)

    def test_discount_non_premium_role(self):
        self.assertEqual(get_discount(2000, 2), 0)


class TestCalcNegative(unittest.TestCase):
    def test_calc_negative(self):
        # calc() не валідує вхід, тому перевірка має бути у proc()
        self.assertEqual(calc(-50, 0.15), -7.5)


class TestNegativeAmount(ProcTestBase):
    def test_negative_regular(self):
        result = self.run_proc([make_order(1, 1, -50.0)])
        self.assertEqual(result["orders"], [])
        self.assertEqual(result["summary"]["processed"], 0)
        self.assertEqual(len(result["summary"]["errors"]), 1)
        self.assertEqual(result["summary"]["errors"][0]["order_id"], 1)

    def test_negative_premium(self):
        result = self.run_proc([make_order(2, 2, -100.0)])
        self.assertEqual(result["orders"], [])
        self.assertEqual(result["summary"]["errors"][0]["order_id"], 2)

    def test_negative_other_role(self):
        result = self.run_proc([make_order(3, 3, -10.0)])
        self.assertEqual(result["orders"], [])
        self.assertEqual(len(result["summary"]["errors"]), 1)

    def test_negative_keeps_revenue(self):
        orders = [make_order(1, 1, 200.0), make_order(2, 1, -50.0)]
        result = self.run_proc(orders)
        self.assertEqual(result["summary"]["total_revenue"], 160.0)
        self.assertEqual(result["summary"]["total_tax"], 40.0)
        self.assertEqual(result["summary"]["processed"], 1)

    def test_saved_net_not_negative(self):
        orders = [make_order(1, 1, -50.0), make_order(2, 2, -100.0),
                  make_order(3, 1, 80.0), make_order(4, 2, 1200.0)]
        result = self.run_proc(orders)
        for item in result["orders"]:
            self.assertGreaterEqual(item.get("net", 0), 0)
        saved_orders = self.saved.call_args_list[0][0][1]
        self.assertTrue(all(o.get("net", 0) >= 0 for o in saved_orders))

    def test_negative_pending_ignored(self):
        result = self.run_proc([make_order(5, 1, -20.0, status="pending")])
        self.assertEqual(result["summary"]["processed"], 0)
        self.assertEqual(result["summary"]["total_revenue"], 0)


class TestBoundary(ProcTestBase):
    def test_zero_amount_zero_net(self):
        result = self.run_proc([make_order(1, 1, 0.0)])
        self.assertEqual(result["summary"]["processed"], 1)
        self.assertEqual(result["orders"][0]["net"], 0)
        self.assertEqual(result["summary"]["errors"], [])

    def test_small_amount_processed(self):
        result = self.run_proc([make_order(1, 1, 0.01)])
        self.assertEqual(result["summary"]["processed"], 1)
        self.assertGreaterEqual(result["orders"][0]["net"], 0)

    def test_regular_unchanged(self):
        result = self.run_proc([make_order(1, 1, 500.0)])
        order = result["orders"][0]
        self.assertEqual((order["tax"], order["discount"], order["net"]),
                         (100.0, 0, 400.0))

    def test_premium_discount_unchanged(self):
        result = self.run_proc([make_order(2, 2, 1200.0)])
        order = result["orders"][0]
        self.assertEqual(order["discount"], 60.0)
        self.assertEqual(order["tax"], 180.0)
        self.assertEqual(order["net"], 960.0)

    def test_valid_order_saved(self):
        self.run_proc([make_order(1, 1, 100.0)])
        names = [c[0][0] for c in self.saved.call_args_list]
        self.assertEqual(names, ["processed_orders", "summary"])


if __name__ == "__main__":
    unittest.main()
