"""The final invoice, the advance invoice and the proforma invoice on a site, for the documents of
print_documents_sales.py: the deduction of the advances with their tax (§ 14 Abs. 5 Satz 2 UStG), the remainder the
final invoice asks for, the particulars of the advance invoice, and a proforma that shows no tax and is no invoice."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.translate import print_language

from briefbote.briefbote import printing, sales
from briefbote.invoice import advances
from briefbote.tests import print_documents as documents
from briefbote.tests import print_documents_sales as sales_documents


class AdvancePrintingTest(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		documents.run()
		sales_documents.run()

	def invoice(self, name: str, language: str = "de") -> dict:
		with print_language(language):
			return printing.briefbote_invoice(frappe.get_doc("Sales Invoice", name))

	def copy(self, name: str):
		return frappe.get_doc("Proforma Invoice", name).get_sales_order_copy()

	def advance(self, name: str) -> dict:
		with print_language("de"):
			return sales.briefbote_advance_invoice(self.copy(name))

	def proforma(self, name: str) -> dict:
		with print_language("de"):
			return sales.briefbote_proforma(self.copy(name))

	def test_a_final_invoice_deducts_each_advance_with_its_consideration_and_tax(self):
		invoice = self.invoice("RE-2026-0401")
		self.assertEqual(invoice["title"], "Schlussrechnung")
		settlement = invoice["settlement"]
		self.assertEqual(
			settlement["rows"],
			[
				{
					"label": "Anzahlung vom 27.11.2026, Zahlung ZE-2026-0101, Anzahlungsrechnung AZ-2026-0001 vom 23.11.2026",
					"net": "3.600,00 €",
					"rate": "19 %",
					"tax": "684,00 €",
					"gross": "4.284,00 €",
				}
			],
		)
		self.assertEqual(settlement["after"], [("Verbleibender Restbetrag", "11.804,80 €", "total")])
		self.assertEqual(invoice["findings"], [])

	def test_a_final_invoice_asks_for_the_remainder_after_the_advances_with_their_tax(self):
		"""ERPNext allocates the advance without its tax and leaves 12.488,80 € open; the customer owes 11.804,80 €."""
		invoice = self.invoice("RE-2026-0401")
		self.assertIn("Bitte überweisen Sie 11.804,80 €", invoice["payment"][0])
		labels = [label for label, _amount, _style in invoice["totals"]]
		self.assertNotIn("Abzüglich erhaltener Anzahlungen", labels)
		self.assertEqual(labels[-1], "Gesamtbetrag")

	def test_an_advance_without_its_tax_is_deducted_whole_and_named_as_a_finding(self):
		invoice = self.invoice("RE-2026-0402")
		self.assertEqual(invoice["settlement"]["rows"][0]["net"], advances.UNKNOWN)
		self.assertEqual(invoice["settlement"]["rows"][0]["gross"], "2.000,00 €")
		self.assertIn(
			"Abzüglich erhaltener Zahlungen",
			[label for label, _amount, _style in invoice["settlement"]["after"]],
		)
		self.assertTrue(any("JV-2026-0101" in finding for finding in invoice["findings"]))

	def test_an_invoice_without_advances_stays_a_rechnung(self):
		invoice = self.invoice("RE-2026-0101")
		self.assertEqual(invoice["title"], "Rechnung")
		self.assertIsNone(invoice["settlement"])

	def test_an_advance_invoice_carries_the_number_and_date_of_its_proforma_and_the_tax_on_the_advance(self):
		advance = self.advance("AZ-2026-0001")
		info = dict(advance["info"])
		self.assertEqual(info["Rechnungsnummer"], "AZ-2026-0001")
		self.assertEqual(info["Rechnungsdatum"], "23.11.2026")
		self.assertEqual(info["Voraussichtliches Leistungsdatum"], "18.12.2026")
		self.assertEqual(info["Auftrag"], "AB-2026-0010 vom 20.11.2026")
		labels = {label: amount for label, amount, _style in advance["totals"]}
		self.assertEqual(labels["Umsatzsteuer 19 % auf 3.600,00 €"], "684,00 €")
		self.assertEqual(labels["Gesamtbetrag"], "4.284,00 €")
		self.assertEqual(advance["findings"], [])
		self.assertTrue(advance["hide_quantities"])
		self.assertEqual(
			advance["payment"],
			[
				"Bitte überweisen Sie 4.284,00 € auf das unten genannte Konto unter Angabe der Rechnungsnummer."
			],
		)

	def test_an_advance_invoice_printed_from_the_order_itself_has_no_number_and_asks_for_nothing(self):
		with print_language("de"):
			advance = sales.briefbote_advance_invoice(frappe.get_doc("Sales Order", "AB-2026-0010"))
		self.assertTrue(advance["findings"][0].startswith("Dieses Dokument hat keine eigene Rechnungsnummer"))
		self.assertEqual(advance["payment"], [])

	def test_a_proforma_shows_no_tax_amount_and_says_it_is_no_invoice(self):
		found = self.proforma("PRO-2026-0001")
		labels = [label for label, _amount, _style in found["totals"]]
		self.assertEqual(labels, ["Nettobetrag", "Gesamtbetrag einschließlich Umsatzsteuer"])
		self.assertFalse(found["show_rates"])
		self.assertTrue(found["payment"][0].startswith("Diese Proforma-Rechnung ist keine Rechnung"))
		self.assertEqual(dict(found["info"])["Proforma-Nr."], "PRO-2026-0001")
		self.assertNotIn("findings", found)
