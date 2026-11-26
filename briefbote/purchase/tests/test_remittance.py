from decimal import Decimal
from unittest import TestCase

from briefbote.purchase import remittance


class AdvisesTest(TestCase):
	def test_only_a_submitted_payment_to_a_supplier_is_advised(self):
		"""An advice tells the supplier of a payment that was made; a draft or a cancelled payment was not."""
		self.assertTrue(remittance.advises("Pay", "Supplier", 1))
		self.assertFalse(remittance.advises("Pay", "Supplier", 0))
		self.assertFalse(remittance.advises("Pay", "Supplier", 2))
		self.assertFalse(remittance.advises("Receive", "Customer", 1))
		self.assertFalse(remittance.advises("Pay", "Employee", 1))
		self.assertFalse(remittance.advises("Internal Transfer", "", 1))


class DirectionTest(TestCase):
	def test_only_a_payment_to_a_supplier_has_invoices_to_advise(self):
		"""A payment received or one to another party lists nothing the supplier could match."""
		self.assertTrue(remittance.to_supplier("Pay", "Supplier"))
		self.assertFalse(remittance.to_supplier("Receive", "Customer"))
		self.assertFalse(remittance.to_supplier("Pay", "Employee"))


class TextTest(TestCase):
	def test_a_payment_by_bank_was_transferred_any_other_paid(self):
		self.assertEqual(remittance.text("Bank"), remittance.TRANSFERRED)
		self.assertEqual(remittance.total_label("Bank"), remittance.TRANSFERRED_TOTAL)
		for mode_type in ("Cash", "General", "Phone", ""):
			with self.subTest(mode_type=mode_type):
				self.assertEqual(remittance.text(mode_type), remittance.PAID)
				self.assertEqual(remittance.total_label(mode_type), remittance.PAID_TOTAL)

	def test_the_text_names_day_and_amount(self):
		for text in (remittance.TRANSFERRED, remittance.PAID):
			with self.subTest(text=text):
				self.assertEqual(text.count("{"), 2)

	def test_no_text_asks_for_anything(self):
		for text in (remittance.TITLE, remittance.TRANSFERRED, remittance.PAID, remittance.NOT_ADVISED):
			with self.subTest(text=text):
				self.assertNotIn("please", text.lower())


class DiscountTest(TestCase):
	def test_the_column_of_the_cash_discount_shows_only_where_a_discount_was_taken(self):
		self.assertTrue(remittance.shows_discount([Decimal(0), Decimal("23.80")]))
		self.assertFalse(remittance.shows_discount([Decimal(0), Decimal(0)]))
		self.assertFalse(remittance.shows_discount([]))


class BillNumberTest(TestCase):
	def test_an_invoice_of_the_supplier_without_its_number_is_a_finding(self):
		"""The supplier finds the invoices it is paid for by its own numbers."""
		rows = [
			("Purchase Invoice", "ER-2026-0001", "4711"),
			("Purchase Invoice", "ER-2026-0002", ""),
			("Purchase Order", "BE-2026-0001", ""),
			("Journal Entry", "BU-2026-0001", ""),
		]
		self.assertEqual(remittance.without_bill_number(rows), ["ER-2026-0002"])


class AccountTest(TestCase):
	def test_the_account_paid_from_is_printed_only_as_the_foot_shows_it(self):
		"""The advice tells no more about the company's accounts than its foot already does."""
		shown = ("DE02120300000000202051",)
		self.assertEqual(
			remittance.own_account("DE02 1203 0000 0000 2020 51", shown), "DE02120300000000202051"
		)
		self.assertEqual(remittance.own_account("DE00123456780000000000", shown), "")
		self.assertEqual(remittance.own_account("", shown), "")
		self.assertEqual(remittance.own_account("DE02120300000000202051", ()), "")
