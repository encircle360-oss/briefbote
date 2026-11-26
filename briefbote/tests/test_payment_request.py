"""The request to pay an invoice on a site: an invoice that asks for a transfer but has no bank account to name is
incomplete and says so instead of asking, like the dunning letter."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.translate import print_language

from briefbote.briefbote import printing
from briefbote.tests import print_documents as documents

NO_BANK = "In den Einstellungen Geschäftspost ist kein Bankkonto gewählt; die Bitte um Überweisung kann nicht sagen, wohin."


class PaymentRequestTest(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		documents.run()

	def invoice(self, name: str) -> dict:
		with print_language("de"):
			return printing.briefbote_invoice(frappe.get_doc("Sales Invoice", name))

	def test_an_invoice_without_a_bank_account_asks_for_nothing_and_says_what_it_lacks(self):
		invoice = self.invoice("KB-2026-0001")
		self.assertEqual(invoice["payment"], [])
		self.assertIn(NO_BANK, invoice["findings"])

	def test_an_invoice_with_a_bank_account_asks_for_the_transfer_to_it(self):
		invoice = self.invoice("RE-2026-0101")
		self.assertTrue(invoice["payment"][0].startswith("Bitte überweisen Sie"))
		self.assertIn("Konto", invoice["payment"][0])
		self.assertNotIn(NO_BANK, invoice["findings"])

	def test_a_paid_or_draft_invoice_needs_no_account(self):
		doc = frappe.get_doc("Sales Invoice", "KB-2026-0001")
		doc.docstatus = 0
		with print_language("de"):
			self.assertNotIn(NO_BANK, printing.briefbote_invoice(doc)["findings"])
