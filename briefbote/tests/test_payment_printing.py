"""The print formats Zahlungsbestätigung and Quittung on a site, for the payments of print_documents_payment.py: what
was received, for which invoices, what is not yet applied, and that only a submitted receipt from a customer is
confirmed."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.translate import print_language

from briefbote.briefbote import receipt
from briefbote.tests import print_documents as documents
from briefbote.tests import print_documents_dunning as dunning_documents
from briefbote.tests import print_documents_payment as payment_documents
from briefbote.tests.print_proof import FETCHED, LINK, SCRIPT


class PaymentPrintingTest(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		documents.run()
		dunning_documents.run()
		payment_documents.run()

	def payment(self, name: str, as_receipt: bool = False) -> dict:
		with print_language("de"):
			return receipt.briefbote_payment(frappe.get_doc("Payment Entry", name), as_receipt)

	def test_the_confirmation_lists_the_invoices_and_what_is_not_applied(self):
		found = self.payment("ZE-2026-0001")
		self.assertEqual(found["title"], "Zahlungsbestätigung")
		self.assertEqual([row["name"] for row in found["rows"]], ["RE-2026-0202", "RE-2026-0203"])
		self.assertEqual(found["rows"][0]["applied"], "1.880,00 €")
		self.assertIn("25,00 €", found["unallocated"])
		self.assertEqual(dict(found["info"])["Zahlungsweg"], "Überweisung")
		self.assertEqual(dict(found["info"])["Referenz"], "SEPA-2026-11-26-0042 vom\u00a026.11.2026")
		self.assertTrue(found["text"].startswith("Ihre Zahlung über 2.500,00 € vom 26.11.2026"))

	def test_the_receipt_acknowledges_amount_payer_and_day_and_asks_for_a_signature(self):
		found = self.payment("ZE-2026-0002", as_receipt=True)
		self.assertEqual(found["title"], "Quittung")
		self.assertEqual(
			found["text"], "Den Betrag von 476,00 € haben wir am 26.11.2026 von Erika Beispiel erhalten."
		)
		self.assertTrue(found["signature"])

	def test_the_letter_goes_to_the_address_of_the_customer(self):
		"""A Payment Entry has no address of its own; the letter takes the primary address of the customer."""
		with print_language("de"):
			frame = receipt.briefbote_payment_letter(frappe.get_doc("Payment Entry", "ZE-2026-0002"))
		self.assertEqual(frame["recipient"], ["Erika Beispiel", "Lindenweg 7", "23456 Musterdorf"])

	def test_a_deduction_stands_between_payment_and_applied_amount(self):
		with print_language("en"):
			found = receipt.briefbote_payment(frappe.get_doc("Payment Entry", "ZE-2026-0003"))
		self.assertEqual(
			[label for label, _amount, _style in found["totals"]],
			["Payment received", "Bankgebühren", "Applied"],
		)

	def test_a_payment_to_a_supplier_is_confirmed_by_nobody(self):
		found = self.payment("ZA-2026-0001")
		self.assertEqual(len(found["findings"]), 1)
		self.assertEqual((found["text"], found["signature"]), ("", False))

	def test_a_draft_or_cancelled_payment_is_confirmed_by_nobody(self):
		for docstatus in (0, 2):
			with self.subTest(docstatus=docstatus), print_language("de"):
				doc = frappe.get_doc("Payment Entry", "ZE-2026-0002")
				doc.docstatus = docstatus
				found = receipt.briefbote_payment(doc, as_receipt=True)
				self.assertEqual((found["text"], found["signature"], found["unallocated"]), ("", False, ""))
				self.assertEqual(found["findings_title"], "Dieses Dokument bestätigt nichts:")

	def test_the_print_formats_render_in_german_and_load_nothing(self):
		for print_format in ("Zahlungsbestätigung", "Quittung"):
			with self.subTest(print_format=print_format), print_language("de"):
				html = frappe.get_print("Payment Entry", "ZE-2026-0001", print_format, no_letterhead=0)
				self.assertIn(f"{print_format} ZE-2026-0001", html)
				self.assertNotIn("Bitte überweisen", html)
				self.assertEqual(FETCHED.findall(LINK.sub("", SCRIPT.sub("", html))), [])
