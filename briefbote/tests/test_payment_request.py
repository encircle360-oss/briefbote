"""The request to pay an invoice on a site: an invoice that asks for a transfer but has no bank account to name is
incomplete and says so instead of asking."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.translate import print_language

from briefbote.briefbote import printing
from briefbote.tests import print_documents as documents


class PaymentRequestTest(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		documents.run()

	def test_an_invoice_without_a_bank_account_asks_for_nothing_and_says_what_it_lacks(self):
		with print_language("de"):
			invoice = printing.briefbote_invoice(frappe.get_doc("Sales Invoice", "KB-2026-0001"))
		self.assertEqual(invoice["payment"], [])
		self.assertIn(
			"In den Einstellungen Geschäftspost ist kein Bankkonto gewählt; die Bitte um Überweisung kann nicht sagen, wohin.",
			invoice["findings"],
		)

	def test_an_invoice_with_a_bank_account_asks_for_the_transfer(self):
		with print_language("de"):
			invoice = printing.briefbote_invoice(frappe.get_doc("Sales Invoice", "RE-2026-0101"))
		self.assertTrue(invoice["payment"][0].startswith("Bitte überweisen Sie"))
		self.assertEqual(invoice["findings"], [])
