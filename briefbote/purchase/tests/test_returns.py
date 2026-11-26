from decimal import Decimal
from unittest import TestCase

from briefbote.purchase import returns

D = Decimal


class ReturnTest(TestCase):
	def test_only_a_return_prints_as_one(self):
		"""A Purchase Receipt without is_return is the internal receipt of goods, no letter to the supplier."""
		self.assertEqual(returns.findings(True), [])
		self.assertEqual(returns.findings(False), [returns.NOT_A_RETURN])

	def test_the_quantity_that_goes_back_is_positive_with_what_was_rejected(self):
		"""ERPNext keeps a return negative, the accepted quantity in qty and the rejected one in rejected_qty
		(update_item in make_return_doc, erpnext/controllers/sales_and_purchase_return.py)."""
		self.assertEqual(returns.returned(D(-3), D(-2)), D(5))
		self.assertEqual(returns.returned(D(-3), D(0)), D(3))

	def test_the_rejected_share_is_named_only_where_there_is_one(self):
		self.assertEqual(returns.rejected_note(D(-3), D(0), False), None)
		self.assertEqual(returns.rejected_note(D(-3), D(-2), False), (returns.REJECTED_PART, (D(2),)))
		self.assertEqual(returns.rejected_note(D(0), D(-2), False), (returns.REJECTED, ()))

	def test_a_return_from_the_warehouse_of_rejected_goods_was_rejected_on_receipt(self):
		"""make_return_doc with return_against_rejected_qty puts the rejected quantity into qty and sets
		return_qty_from_rejected_warehouse."""
		self.assertEqual(returns.rejected_note(D(-4), D(0), True), (returns.REJECTED, ()))
		self.assertEqual(returns.rejected_note(D(0), D(0), True), None)

	def test_only_a_submitted_return_asks_for_the_confirmation_of_the_carrier(self):
		self.assertTrue(returns.asks_signature(submitted=True))
		self.assertFalse(returns.asks_signature(submitted=False))

	def test_the_title_is_that_of_a_return_shipment(self):
		self.assertEqual(returns.TITLE, "Return Shipment")
