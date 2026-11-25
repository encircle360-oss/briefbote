from unittest import TestCase

from briefbote.invoice.self_billing import PurchaseCase
from briefbote.purchase import order


class TaxTest(TestCase):
	def test_only_a_supply_taxable_in_germany_shows_the_tax_of_the_supplier(self):
		"""A purchase template of § 13b UStG books the tax as added and deducted again; it is the tax of the company,
		which the order does not show."""
		self.assertTrue(order.shows_tax(PurchaseCase.DOMESTIC))
		for case in (PurchaseCase.REVERSE_CHARGE, PurchaseCase.SMALL_BUSINESS, PurchaseCase.EXEMPT):
			with self.subTest(case=case):
				self.assertFalse(order.shows_tax(case))


class ConfirmationTest(TestCase):
	def test_only_a_submitted_order_asks_the_supplier_to_confirm_it(self):
		self.assertEqual(order.closing(submitted=True), [order.CONFIRM])
		self.assertEqual(order.closing(submitted=False), [])

	def test_the_title_is_that_of_a_purchase_order(self):
		self.assertEqual(order.TITLE, "Purchase Order")
