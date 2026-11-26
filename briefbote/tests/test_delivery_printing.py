"""The print format Lieferschein on a site, for the delivery notes of print_documents_sales.py: the address the goods
go to, the order and the dates, serial numbers and batches, no prices unless the settings ask for them, the line for
the signature, the return, and HTML that loads nothing."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.translate import print_language

from briefbote.briefbote import sales
from briefbote.tests import print_documents as documents
from briefbote.tests import print_documents_sales as sales_documents
from briefbote.tests.print_proof import FETCHED, LINK, SCRIPT


class DeliveryPrintingTest(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		documents.run()
		sales_documents.run()

	def note(self, name: str) -> dict:
		with print_language("de"):
			return sales.briefbote_delivery_note(frappe.get_doc("Delivery Note", name))

	def letter(self, name: str) -> dict:
		with print_language("de"):
			return sales.briefbote_delivery_letter(frappe.get_doc("Delivery Note", name))

	def test_the_goods_go_to_the_shipping_address(self):
		self.assertEqual(
			self.letter("LS-2026-0001")["recipient"],
			["Kunde Muster AG", "Wareneingang Tor 3", "Industriestraße 40", "54329 Beispielstadt"],
		)
		self.assertEqual(self.letter("LS-2026-0002")["recipient"][0], "Kunde Muster AG")

	def test_the_note_names_its_date_the_day_of_delivery_and_the_orders(self):
		info = dict(self.note("LS-2026-0001")["info"])
		self.assertEqual((info["Datum"], info["Lieferdatum"]), ("23.11.2026", "23.11.2026"))
		self.assertEqual(info["Ihre Bestellung"], "B-4711 vom\u00a018.11.2026")
		self.assertEqual(info["Unser Auftrag"], "AB-2026-0001 vom\u00a020.11.2026")

	def test_serial_numbers_and_batches_stand_at_their_positions(self):
		positions = self.note("LS-2026-0001")["positions"]
		self.assertIn(
			"Seriennummern: TD200-26-00417, TD200-26-00418, TD200-26-00419", positions[0]["details"]
		)
		self.assertIn("Chargen: CH-2026-311 (16), CH-2026-327 (8)", positions[1]["details"])
		self.assertIn("Charge: CH-2026-102", positions[2]["details"])

	def test_without_the_setting_the_note_prints_no_prices_but_a_line_for_the_signature(self):
		note = self.note("LS-2026-0001")
		self.assertFalse(note["prices"])
		self.assertTrue(note["signature"])
		self.assertEqual(note["weight"], "Gesamtgewicht netto: 41,6 kg")

	def test_with_the_setting_the_note_prints_prices_and_no_signature(self):
		note = self.note("KL-2026-0001")
		self.assertTrue(note["prices"])
		self.assertFalse(note["signature"])
		self.assertEqual(note["totals"][-1][:2], ("Gesamtbetrag", "47,40 €"))

	def test_a_return_names_the_note_it_returns_and_counts_what_comes_back(self):
		"""ERPNext keeps the quantity of a return negative; on paper it is what comes back, under a title that says so."""
		note = self.note("LS-2026-0004")
		self.assertEqual(note["title"], "Rücklieferschein")
		self.assertEqual(
			note["subject"], "Rücklieferschein LS-2026-0004 zum Lieferschein LS-2026-0001 vom 23.11.2026"
		)
		self.assertEqual(dict(note["info"])["Lieferschein"], "LS-2026-0001 vom\u00a023.11.2026")
		self.assertEqual(note["positions"][0]["quantity"], "1")

	def test_a_draft_or_cancelled_note_asks_nobody_to_sign(self):
		for docstatus in (0, 2):
			with self.subTest(docstatus=docstatus), print_language("de"):
				doc = frappe.get_doc("Delivery Note", "LS-2026-0001")
				doc.docstatus = docstatus
				self.assertFalse(sales.briefbote_delivery_note(doc)["signature"])

	def test_the_columns_of_a_note_with_prices_are_measured(self):
		self.assertIn("amount", self.note("KL-2026-0001")["columns"])

	def test_the_print_format_renders_in_german_and_loads_nothing(self):
		with print_language("de"):
			html = frappe.get_print("Delivery Note", "LS-2026-0001", "Lieferschein", no_letterhead=0)
		self.assertIn("Lieferschein LS-2026-0001", html)
		self.assertNotIn("349,00", html)
		self.assertNotIn("Bitte überweisen", html)
		self.assertEqual(FETCHED.findall(LINK.sub("", SCRIPT.sub("", html))), [])
