from datetime import date
from unittest import TestCase

from briefbote.sales import proforma


class NoInvoiceTest(TestCase):
	def test_a_proforma_says_it_is_no_invoice_and_gives_no_right_to_deduct_input_tax(self):
		"""§ 14 Abs. 1 Satz 1 and § 15 Abs. 1 Satz 1 Nr. 1 UStG."""
		self.assertIn("not an invoice", proforma.NOT_AN_INVOICE)
		self.assertIn("input tax", proforma.NOT_AN_INVOICE)
		self.assertEqual(proforma.closing(asks=True), [proforma.NOT_AN_INVOICE, proforma.INVOICE_FOLLOWS])

	def test_a_draft_or_cancelled_proforma_still_says_it_is_no_invoice_but_announces_nothing(self):
		self.assertEqual(proforma.closing(asks=False), [proforma.NOT_AN_INVOICE])


class TotalTest(TestCase):
	"""UStAE 14c.2 Abs. 1 Satz 6: tax is shown separately once it is named as an amount of money and marked as tax.
	The proforma names no tax amount and no rate, only the price with tax."""

	def test_with_vat_the_total_says_it_includes_it(self):
		self.assertEqual(proforma.total_label(charges_tax=True), proforma.TOTAL_WITH_VAT)

	def test_without_vat_the_total_is_the_total(self):
		self.assertEqual(proforma.total_label(charges_tax=False), proforma.TOTAL)


class NumberTest(TestCase):
	def test_a_proforma_of_erpnext_names_its_number_and_the_order(self):
		self.assertEqual(
			proforma.reference("PRO-2026-0001", date(2026, 11, 23), "AB-2026-0001", date(2026, 11, 20)),
			(("PRO-2026-0001", date(2026, 11, 23)), ("AB-2026-0001", date(2026, 11, 20))),
		)

	def test_printed_from_the_order_it_has_the_number_and_day_of_the_order(self):
		self.assertEqual(
			proforma.reference("", None, "AB-2026-0001", date(2026, 11, 20)),
			(None, ("AB-2026-0001", date(2026, 11, 20))),
		)
