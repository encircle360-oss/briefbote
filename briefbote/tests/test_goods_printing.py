"""The print formats Anfrage, Lieferantenrücksendung and Packliste on a site, for the documents of
print_documents_goods.py: whom each letter goes to, what it states, what it asks for, and HTML that loads nothing."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.translate import print_language

from briefbote.briefbote import purchase, sales
from briefbote.tests import print_documents as documents
from briefbote.tests import print_documents_goods as goods
from briefbote.tests import print_documents_purchase as purchase_documents
from briefbote.tests import print_documents_sales as sales_documents
from briefbote.tests.print_proof import FETCHED, LINK, SCRIPT

SUPPLIER = "Muster Trockenbau GmbH"
OTHER_SUPPLIER = "Grafikbüro Klein"


class GoodsPrintingTest(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		documents.run()
		sales_documents.run()
		purchase_documents.run()
		goods.run()

	def request(self, name: str, supplier: str | None = None):
		"""The request as ERPNext prints it: for the supplier chosen in its dialog, else for the first of its list
		(get_pdf and before_print in erpnext/buying/doctype/request_for_quotation/request_for_quotation.py)."""
		doc = frappe.get_doc("Request for Quotation", name)
		if supplier:
			doc.update_supplier_part_no(supplier)
		else:
			doc.run_method("before_print", {})
		with print_language("de"):
			return purchase.briefbote_request_letter(doc), purchase.briefbote_request_for_quotation(doc)

	def test_the_request_goes_to_the_first_supplier_unless_one_is_chosen(self):
		letter, found = self.request("AF-2026-0001")
		self.assertEqual(letter["recipient"][:2], [SUPPLIER, "Max Bauer"])
		self.assertEqual(found["findings"], [])
		self.assertEqual(self.request("AF-2026-0001", OTHER_SUPPLIER)[0]["recipient"][0], OTHER_SUPPLIER)

	def test_the_request_names_our_and_the_suppliers_item_numbers_and_the_required_dates(self):
		_letter, found = self.request("AF-2026-0001")
		first = found["positions"][0]
		self.assertIn("Unsere Artikelnummer GK-125", first["description"])
		self.assertIn("Ihre Artikelnummer MT-4711", first["description"])
		self.assertEqual(first["period"], "Benötigt bis 08.12.2026")
		self.assertEqual(dict(found["info"])["Benötigt bis"], "08.12.2026")
		self.assertNotIn(
			"Ihre Artikelnummer",
			self.request("AF-2026-0001", OTHER_SUPPLIER)[1]["positions"][0]["description"],
		)

	def test_the_request_asks_for_what_it_has_data_for_and_names_the_delivery_address(self):
		_letter, found = self.request("AF-2026-0001")
		self.assertEqual(
			found["payment"],
			[
				"Bitte nennen Sie in Ihrem Angebot den Preis je Einheit jeder Position.",
				"Bitte nennen Sie auch, ob Sie zu den genannten Terminen liefern können.",
				"Bitte bieten Sie auf der Grundlage der Lieferbedingung FCA Baustadt an.",
				"Lieferanschrift: Lager Süd, Am Güterbahnhof 8, 12355 Musterstadt",
			],
		)
		self.assertIn("bitten wir um Ihr Angebot", found["intro"])

	def test_a_request_without_suppliers_addresses_nobody(self):
		letter, found = self.request("AF-2026-0004")
		self.assertEqual((letter["recipient"], letter["return_address"]), ([], ()))
		self.assertEqual(
			found["findings"],
			[
				"Die Anfrage nennt keinen Lieferanten. ERPNext druckt sie für einen Lieferanten aus ihrer Liste der Lieferanten."
			],
		)

	def test_a_draft_request_asks_nothing(self):
		doc = frappe.get_doc("Request for Quotation", "AF-2026-0001")
		doc.run_method("before_print", {})
		doc.docstatus = 0
		with print_language("de"):
			found = purchase.briefbote_request_for_quotation(doc)
		self.assertEqual(
			found["payment"], ["Lieferanschrift: Lager Süd, Am Güterbahnhof 8, 12355 Musterstadt"]
		)
		self.assertEqual(found["intro"], "")

	def receipt(self, name: str):
		doc = frappe.get_doc("Purchase Receipt", name)
		with print_language("de"):
			return purchase.briefbote_return_letter(doc), purchase.briefbote_purchase_return(doc)

	def test_the_return_goes_to_the_dispatch_address_of_the_supplier(self):
		letter, found = self.receipt("RS-2026-0001")
		self.assertEqual(
			letter["recipient"],
			["Muster Trockenbau GmbH", "Warenannahme Halle 2", "Industrieweg 11", "34569 Baustadt"],
		)
		info = dict(found["info"])
		self.assertEqual(info["Unser Wareneingang"], "WE-2026-0001 vom\u00a020.11.2026")
		self.assertEqual(info["Ihr Lieferschein"], "LF-88231")
		self.assertEqual(info["Frachtführer"], "Spedition Beispiel KG")
		self.assertEqual(
			found["subject"], "Rücksendung RS-2026-0001 zu unserem Wareneingang WE-2026-0001 vom 20.11.2026"
		)

	def test_the_return_counts_what_goes_back_and_names_the_rejected_share(self):
		_letter, found = self.receipt("RS-2026-0001")
		first, second = found["positions"]
		self.assertEqual((first["quantity"], second["quantity"]), ("2", "10"))
		self.assertIn("Seriennummern: BS18-26-1041, BS18-26-1042", first["details"])
		self.assertIn("Davon beim Wareneingang abgelehnt: 4", second["details"])
		self.assertNotIn("abgelehnt", first["description"])
		self.assertEqual(found["weight"], "Gesamtgewicht netto: 38,5 kg")
		self.assertTrue(found["signature"])
		self.assertEqual(
			found["payment"], ["Abholanschrift: Lager Süd, Am Güterbahnhof 8, 12355 Musterstadt"]
		)

	def test_a_receipt_that_is_no_return_prints_a_finding_and_no_letter(self):
		letter, _found = self.receipt("WE-2026-0001")
		self.assertEqual((letter["recipient"], letter["return_address"]), ([], ()))
		self.assertEqual(
			self.receipt("WE-2026-0001")[1]["findings"],
			[
				"Dieser Wareneingang ist keine Rücksendung; das Druckformat Lieferantenrücksendung druckt nur eine Rücksendung an den Lieferanten."
			],
		)

	def test_a_cancelled_return_asks_nobody_to_sign(self):
		doc = frappe.get_doc("Purchase Receipt", "RS-2026-0001")
		doc.docstatus = 2
		with print_language("de"):
			self.assertFalse(purchase.briefbote_purchase_return(doc)["signature"])

	def packing(self, name: str, docstatus: int | None = None):
		doc = frappe.get_doc("Packing Slip", name)
		if docstatus is not None:
			doc.docstatus = docstatus
		with print_language("de"):
			return sales.briefbote_packing_letter(doc), sales.briefbote_packing_slip(doc)

	def test_the_packing_list_covers_every_submitted_slip_of_the_delivery(self):
		letter, found = self.packing("PK-2026-0002")
		self.assertEqual(letter["recipient"][1], "Wareneingang Tor 3")
		self.assertEqual(found["subject"], "Packliste: Packstücke 1 bis 3 zum Lieferschein LS-2026-0001")
		self.assertEqual(
			[row["number"] for row in found["positions"]], ["1", "2\N{EN DASH}3", "2\N{EN DASH}3"]
		)
		self.assertEqual(
			found["packages"],
			[("Packstück 1", "12,6 kg", "14,2 kg"), ("Packstücke 2 bis 3", "29 kg", "31,5 kg")],
		)
		self.assertEqual(found["package_totals"], [("Gesamt", "41,6 kg", "45,7 kg")])
		self.assertEqual(dict(found["info"])["Packstücke"], "3")

	def test_a_draft_slip_lists_only_itself_under_its_mark(self):
		letter, found = self.packing("PK-2026-0002", docstatus=0)
		self.assertEqual(letter["mark"], "ENTWURF")
		self.assertEqual(found["subject"], "Packliste: Packstücke 2 bis 3 zum Lieferschein LS-2026-0001")
		self.assertEqual(found["packages"], [])
		self.assertEqual(found["weight"], "Nettogewicht 29 kg · Bruttogewicht 31,5 kg")

	def test_the_print_formats_render_in_german_and_load_nothing(self):
		for doctype, name, print_format, text in (
			("Request for Quotation", "AF-2026-0001", "Anfrage", "Anfrage AF-2026-0001"),
			("Purchase Receipt", "RS-2026-0001", "Lieferantenrücksendung", "Rücksendung RS-2026-0001"),
			("Packing Slip", "PK-2026-0001", "Packliste", "Packliste: Packstücke 1 bis 3"),
		):
			with self.subTest(print_format=print_format), print_language("de"):
				html = frappe.get_print(doctype, name, print_format, no_letterhead=0)
				self.assertIn(text, html)
				self.assertNotIn("Bitte überweisen", html)
				self.assertEqual(FETCHED.findall(LINK.sub("", SCRIPT.sub("", html))), [])
