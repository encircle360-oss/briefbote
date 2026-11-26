"""The print format Zahlungsavis on a site, for the payments of print_documents_remittance.py: what was paid, for which
invoices of the supplier by its own numbers, the cash discount, and that only a submitted payment to a supplier is
advised."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.translate import print_language

from briefbote.briefbote import receipt
from briefbote.tests import print_documents as documents
from briefbote.tests import print_documents_dunning as dunning_documents
from briefbote.tests import print_documents_payment as payment_documents
from briefbote.tests import print_documents_remittance as remittance_documents
from briefbote.tests.print_proof import FETCHED, LINK, SCRIPT


class RemittancePrintingTest(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		documents.run()
		dunning_documents.run()
		payment_documents.run()
		remittance_documents.run()

	def advice(self, name: str, language: str = "de") -> dict:
		with print_language(language):
			return receipt.briefbote_remittance(frappe.get_doc("Payment Entry", name))

	def test_the_advice_names_the_invoices_by_the_number_of_the_supplier_first(self):
		found = self.advice("ZA-2026-0002")
		self.assertEqual(found["title"], "Zahlungsavis")
		self.assertEqual(
			[(row["bill_no"], row["bill_date"], row["name"]) for row in found["rows"]],
			[("RG-2026-1187", "02.11.2026", "ER-2026-0101"), ("RG-2026-1203", "09.11.2026", "ER-2026-0102")],
		)
		self.assertEqual([column["key"] for column in found["columns"]][:3], ["bill_no", "bill_date", "name"])
		self.assertEqual(found["findings"], [])

	def test_the_cash_discount_stands_with_its_invoice_and_between_settled_and_transferred(self):
		found = self.advice("ZA-2026-0002")
		self.assertEqual(found["rows"][0]["discount"], "47,60 €")
		self.assertEqual(found["rows"][1]["discount"], "")
		self.assertEqual(
			found["totals"],
			[
				("Ausgeglichen", "2.975,00 €", "sum"),
				("Erhaltene Skonti", "-47,60 €", ""),
				("Überwiesen", "2.927,40 €", "total"),
			],
		)
		self.assertEqual(
			found["text"],
			"Wir haben am 27.11.2026 den Betrag von 2.927,40 € überwiesen und wie folgt verrechnet.",
		)

	def test_the_account_paid_from_shows_as_the_foot_shows_it(self):
		info = dict(self.advice("ZA-2026-0002")["info"])
		self.assertEqual(info["Unser Konto"], "DE02 1203 0000 0000 2020 51")
		self.assertNotIn("Lieferantennummer", info)

	def test_without_a_discount_the_advice_has_no_column_for_it(self):
		found = self.advice("ZA-2026-0003", "en")
		self.assertNotIn("discount", [column["key"] for column in found["columns"]])
		self.assertTrue(found["text"].startswith("On 27.11.2026 we paid the amount of"))
		self.assertIn(("Not applied to an invoice", "100,00 €", ""), found["totals"])
		self.assertEqual(dict(found["info"])["Supplier No."], "L-0007")
		self.assertNotIn("Our account", dict(found["info"]))

	def test_an_invoice_without_the_number_of_the_supplier_is_a_finding(self):
		found = self.advice("ZA-2026-0005")
		self.assertEqual(found["findings_title"], "Diesem Zahlungsavis fehlt etwas:")
		self.assertEqual(
			found["findings"], ["Die Rechnung ER-2026-0105 trägt keine Rechnungsnummer des Lieferanten."]
		)
		self.assertTrue(found["text"])

	def test_the_letter_goes_to_the_address_of_the_supplier(self):
		with print_language("de"):
			frame = receipt.briefbote_payment_letter(frappe.get_doc("Payment Entry", "ZA-2026-0002"))
		self.assertEqual(frame["recipient"], ["Muster Trockenbau GmbH", "Industrieweg 9", "34569 Baustadt"])

	def test_a_receipt_from_a_customer_is_advised_by_nobody(self):
		found = self.advice("ZE-2026-0001")
		self.assertEqual(found["findings_title"], "Dieses Dokument meldet keine Zahlung:")
		self.assertEqual(found["text"], "")
		self.assertEqual((found["rows"], found["totals"]), ([], []))

	def test_a_draft_or_cancelled_payment_is_advised_by_nobody(self):
		for docstatus in (0, 2):
			with self.subTest(docstatus=docstatus), print_language("de"):
				doc = frappe.get_doc("Payment Entry", "ZA-2026-0002")
				doc.docstatus = docstatus
				found = receipt.briefbote_remittance(doc)
				self.assertEqual(found["text"], "")
				self.assertEqual(found["findings_title"], "Dieses Dokument meldet keine Zahlung:")

	def test_the_confirmation_of_a_payment_to_a_supplier_still_confirms_nothing(self):
		with print_language("de"):
			found = receipt.briefbote_payment(frappe.get_doc("Payment Entry", "ZA-2026-0002"))
		self.assertEqual(found["findings_title"], "Dieses Dokument bestätigt nichts:")
		self.assertEqual(found["text"], "")
		self.assertEqual((found["rows"], found["totals"]), ([], []))

	def test_the_print_format_renders_in_german_and_loads_nothing(self):
		with print_language("de"):
			html = frappe.get_print("Payment Entry", "ZA-2026-0002", "Zahlungsavis", no_letterhead=0)
		self.assertIn("Zahlungsavis ZA-2026-0002", html)
		self.assertNotIn("Bitte überweisen", html)
		self.assertEqual(FETCHED.findall(LINK.sub("", SCRIPT.sub("", html))), [])
