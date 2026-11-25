"""The print format Bestellung on a site, for the purchase orders of print_documents_purchase.py."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.translate import print_language

from briefbote.briefbote import purchase
from briefbote.tests import print_documents as documents
from briefbote.tests import print_documents_purchase as purchase_documents
from briefbote.tests.print_proof import FETCHED, LINK, SCRIPT


class PurchasePrintingTest(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		documents.run()
		purchase_documents.run()

	def order(self, name: str) -> dict:
		with print_language("de"):
			return purchase.briefbote_purchase_order(frappe.get_doc("Purchase Order", name))

	def test_the_order_names_dates_delivery_address_and_tax_by_rate(self):
		found = self.order("BE-2026-0001")
		info = dict(found["info"])
		self.assertEqual((info["Bestellnummer"], info["Liefertermin"]), ("BE-2026-0001", "08.12.2026"))
		self.assertEqual(found["delivery_address"], ["Lager Süd", "Am Güterbahnhof 8", "12355 Musterstadt"])
		labels = [label for label, _amount, _style in found["totals"]]
		self.assertIn("Umsatzsteuer 19 % auf 768,00 €", labels)
		self.assertIn("Umsatzsteuer 7 % auf 98,00 €", labels)
		self.assertIn("Ihre Artikelnummer L-0001", found["positions"][0]["description"])
		self.assertEqual(
			found["payment"][-1], "Bitte bestätigen Sie uns diese Bestellung unter Angabe der Bestellnummer."
		)

	def test_an_order_under_section_13b_shows_no_tax(self):
		labels = [label for label, _amount, _style in self.order("BE-2026-0003")["totals"]]
		self.assertEqual(labels, ["Nettobetrag", "Gesamtbetrag"])

	def test_a_draft_or_cancelled_order_asks_for_no_confirmation(self):
		for docstatus in (0, 2):
			with self.subTest(docstatus=docstatus), print_language("de"):
				doc = frappe.get_doc("Purchase Order", "BE-2026-0001")
				doc.docstatus = docstatus
				self.assertEqual(
					purchase.briefbote_purchase_order(doc)["payment"], ["Zahlungsbedingungen: 30 Tage netto"]
				)

	def test_the_columns_are_measured_as_for_the_invoice(self):
		self.assertIn("amount", self.order("BE-2026-0001")["columns"])

	def test_the_print_format_renders_in_german_and_loads_nothing(self):
		with print_language("de"):
			html = frappe.get_print("Purchase Order", "BE-2026-0001", "Bestellung", no_letterhead=0)
		self.assertIn("Bestellung BE-2026-0001", html)
		self.assertEqual(FETCHED.findall(LINK.sub("", SCRIPT.sub("", html))), [])
