"""The print formats Angebot and Auftragsbestätigung on a site, for the documents of print_documents_sales.py: what
counts toward the total of a quotation, the tax by rate and base from a German template, validity and acceptance,
the references, dates and payment terms of an order confirmation, and HTML that loads nothing."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.translate import print_language

from briefbote.briefbote import sales
from briefbote.tests import print_documents as documents
from briefbote.tests import print_documents_sales as sales_documents
from briefbote.tests.print_proof import FETCHED, LINK, SCRIPT


class SalesPrintingTest(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		documents.run()
		sales_documents.run()

	def quotation(self, name: str) -> dict:
		with print_language("de"):
			return sales.briefbote_quotation(frappe.get_doc("Quotation", name))

	def order(self, name: str) -> dict:
		with print_language("de"):
			return sales.briefbote_sales_order(frappe.get_doc("Sales Order", name))

	def test_an_alternative_says_whom_it_replaces_and_stays_out_of_the_total(self):
		quotation = self.quotation("AN-2026-0001")
		alternative = quotation["positions"][2]
		self.assertIn(
			"Alternative zu Position 2, nicht im Gesamtbetrag enthalten.", alternative["description"]
		)
		self.assertEqual(alternative["tax_rate"], "")
		totals = {label: amount for label, amount, _style in quotation["totals"]}
		self.assertEqual(totals["Nettobetrag"], "4.899,70 €")
		self.assertEqual(totals["Gesamtbetrag"], "5.816,28 €")

	def test_each_tax_line_of_the_german_template_names_its_rate_and_base(self):
		labels = [label for label, _amount, _style in self.quotation("AN-2026-0001")["totals"]]
		self.assertIn("Umsatzsteuer 19 % auf 4.780,00 €", labels)
		self.assertIn("Umsatzsteuer 7 % auf 119,70 €", labels)
		self.assertTrue(self.quotation("AN-2026-0001")["show_rates"])

	def test_quotation_and_confirmation_name_the_vat_id_of_the_customer_as_the_invoice_does(self):
		"""The rule of the invoice: the customer's USt-IdNr. whenever it is known, and ours beside it where § 14a UStG
		asks for both."""
		self.assertEqual(dict(self.quotation("AN-2026-0001")["info"])["Ihre USt-IdNr."], "DE987654321")
		self.assertEqual(dict(self.order("AB-2026-0001")["info"])["Ihre USt-IdNr."], "DE987654321")
		with print_language("de"):
			eu = dict(sales.briefbote_quotation(frappe.get_doc("Quotation", "AN-2026-0004"))["info"])
		self.assertEqual((eu["Ihre USt-IdNr."], eu["Unsere USt-IdNr."]), ("ATU87654321", "DE123456789"))

	def test_validity_and_acceptance_name_the_deadline_of_the_quotation(self):
		quotation = self.quotation("AN-2026-0001")
		self.assertIn(("Gültig bis", "18.12.2026"), quotation["info"])
		self.assertIn("Dieses Angebot gilt bis zum 18.12.2026.", " ".join(quotation["payment"]))
		self.assertIn("Zahlungsbedingungen: 14 Tage netto", quotation["payment"])

	def test_a_quotation_without_a_deadline_prints_no_empty_label(self):
		quotation = self.quotation("AN-2026-0003")
		self.assertNotIn("Gültig bis", dict(quotation["info"]))
		self.assertTrue(quotation["payment"][-1].startswith("Zur Annahme"))
		unit_price = quotation["positions"][1]
		self.assertEqual((unit_price["quantity"], unit_price["amount"]), ("", ""))
		self.assertIn("nicht im Gesamtbetrag enthalten", unit_price["description"])

	def test_the_order_confirmation_names_quotation_order_dates_and_terms(self):
		confirmation = self.order("AB-2026-0001")
		info = dict(confirmation["info"])
		self.assertEqual(info["Unser Angebot"], "AN-2026-0001 vom\u00a016.11.2026")
		self.assertEqual(info["Ihre Bestellung"], "B-4711 vom\u00a018.11.2026")
		self.assertEqual(info["Liefertermin"], "15.12.2026")
		self.assertEqual(
			confirmation["payment"][:3],
			[
				"Zahlungsbedingungen:",
				"1.744,88 €: Anzahlung bei Auftragserteilung",
				"4.071,40 €: Rest 14 Tage nach Abnahme",
			],
		)
		self.assertEqual(confirmation["payment"][-1], "Die Rechnung erhalten Sie gesondert.")

	def test_positions_due_on_different_days_name_each_its_day(self):
		confirmation = self.order("AB-2026-0002")
		self.assertEqual(dict(confirmation["info"])["Liefertermine"], "01.12.2026 bis 22.12.2026")
		self.assertEqual(confirmation["positions"][1]["period"], "Liefertermin 08.12.2026")

	def test_a_draft_or_cancelled_document_asks_for_nothing(self):
		"""briefbote/layout/status.py: a draft or cancelled printout carries its mark and no call to action."""
		for docstatus in (0, 2):
			with self.subTest(docstatus=docstatus), print_language("de"):
				quotation = frappe.get_doc("Quotation", "AN-2026-0001")
				quotation.docstatus = docstatus
				confirmation = frappe.get_doc("Sales Order", "AB-2026-0001")
				confirmation.docstatus = docstatus
				self.assertEqual(
					sales.briefbote_quotation(quotation)["payment"], ["Zahlungsbedingungen: 14 Tage netto"]
				)
				self.assertNotIn(
					"Die Rechnung erhalten Sie gesondert.",
					sales.briefbote_sales_order(confirmation)["payment"],
				)

	def test_the_columns_are_measured_as_for_the_invoice(self):
		quotation = self.quotation("AN-2026-0001")
		self.assertEqual(
			set(quotation["columns"])
			>= {"number", "description", "quantity", "unit", "rate", "tax", "amount"},
			True,
		)

	def test_the_print_formats_render_in_german_and_load_nothing(self):
		for doctype, name, print_format, title in (
			("Quotation", "AN-2026-0001", "Angebot", "Angebot AN-2026-0001"),
			("Sales Order", "AB-2026-0001", "Auftragsbestätigung", "Auftragsbestätigung AB-2026-0001"),
		):
			with self.subTest(print_format=print_format), print_language("de"):
				html = frappe.get_print(doctype, name, print_format, no_letterhead=0)
				self.assertIn(title, html)
				self.assertNotIn("Bitte überweisen", html)
				self.assertNotIn("Rechnungsnummer", html)
				self.assertEqual(FETCHED.findall(LINK.sub("", SCRIPT.sub("", html))), [])
