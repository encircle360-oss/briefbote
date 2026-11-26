"""The print format Geschäftsbrief on a site with erpnext_germany, for the letters of print_documents_letters.py. CI
runs the module after installing erpnext_germany; on a site without it the module skips."""

import unittest

import frappe
from frappe.tests import IntegrationTestCase
from frappe.translate import print_language

from briefbote.briefbote import correspondence
from briefbote.tests import print_documents_letters as letters
from briefbote.tests.print_proof import FETCHED, LINK, SCRIPT


class BusinessLetterPrintingTest(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("DocType", letters.DOCTYPE):
			raise unittest.SkipTest(
				"erpnext_germany is not installed; CI runs this module again after installing it"
			)
		letters.run()

	def letter(self, name: str, language: str = "de") -> dict:
		with print_language(language):
			return correspondence.briefbote_business_letter(frappe.get_doc(letters.DOCTYPE, name))

	def frame(self, name: str) -> dict:
		with print_language("de"):
			return correspondence.briefbote_business_letter_frame(frappe.get_doc(letters.DOCTYPE, name), 0)

	def test_a_person_in_a_company_stands_below_the_company(self):
		self.assertEqual(
			self.frame("GB-2026-0001")["recipient"],
			["Kunde Muster AG", "Erika Muster", "Hauptstraße 5", "54321 Beispielstadt"],
		)

	def test_a_private_person_is_the_first_line(self):
		self.assertEqual(
			self.frame("GB-2026-0003")["recipient"], ["Erika Beispiel", "Lindenweg 7", "23456 Musterdorf"]
		)

	def test_an_address_abroad_ends_with_the_country_in_capitals(self):
		self.assertEqual(
			self.frame("GB-2026-0004")["recipient"],
			[
				"Musterhandel Gesellschaft m.b.H.",
				"Max Beispielmann",
				"Ringstraße 1",
				"1010 Wien",
				"ÖSTERREICH",
			],
		)

	def test_a_letter_without_address_prints_no_window_but_a_finding(self):
		self.assertEqual(self.frame("GB-2026-0009")["recipient"], [])
		self.assertIn(
			"Der Brief hat keine Postanschrift des Empfängers: Wählen Sie eine Adresse mit Straße, Postleitzahl und Ort.",
			self.letter("GB-2026-0009")["findings"],
		)

	def test_the_information_block_names_the_reference_the_person_and_the_date_last(self):
		self.assertEqual(
			self.letter("GB-2026-0005")["info"],
			[
				("Unser Zeichen", "Ausgangsrechnung RE-2026-0101"),
				("Abteilung", "Vertrieb"),
				("Name", "Max Mustermann"),
				("Telefon", "+49 30 1234567"),
				("E-Mail", "max.mustermann"),
				("", "@beispiel.example"),
				("Datum", "26.11.2026"),
			],
		)

	def test_a_letter_without_a_person_names_only_the_date(self):
		self.assertEqual(self.letter("GB-2026-0008")["info"], [("Datum", "26.11.2026")])

	def test_subject_and_text_are_those_the_owning_app_rendered_and_are_not_rendered_again(self):
		found = self.letter("GB-2026-0005")
		self.assertEqual(found["subject"], "Ihre Rechnung RE-2026-0101")
		self.assertIn("Sehr geehrte Frau Muster,", found["body"])
		self.assertIn("{{ name }}", found["body"])

	def test_pasted_fonts_and_colours_do_not_print(self):
		body = self.letter("GB-2026-0007")["body"]
		for trace in ("font", "color", 'style="font', "Times", "Comic", "MsoNormal", "mso-", "<span"):
			with self.subTest(trace=trace):
				self.assertNotIn(trace, body)
		self.assertIn('<img class="bb-image" src="data:image/png;base64,', body)

	def test_an_empty_letter_is_a_finding_and_has_no_subject(self):
		found = self.letter("GB-2026-0008")
		self.assertEqual(found["subject"], "")
		self.assertEqual(found["findings"], ["Der Brief hat keinen Text."])

	def test_a_complete_letter_has_no_finding(self):
		self.assertEqual(self.letter("GB-2026-0001")["findings"], [])

	def test_the_page_line_names_the_recipient_and_the_date(self):
		self.assertEqual(
			self.letter("GB-2026-0001")["running_title"], "Brief an Kunde Muster AG vom\u00a026.11.2026"
		)
		self.assertEqual(
			self.letter("GB-2026-0006", "en")["running_title"],
			"Letter to Example Trading Inc. dated 26.11.2026",
		)

	def test_saving_a_letter_without_a_subject_warns(self):
		doc = frappe.get_doc(letters.DOCTYPE, "GB-2026-0008")
		frappe.clear_messages()
		with print_language("de"):
			correspondence.warn_without_subject(doc, "validate")
		self.assertTrue(any("keinen Betreff" in str(message) for message in frappe.get_message_log()))

	def test_the_print_format_renders_in_german_and_loads_nothing(self):
		with print_language("de"):
			html = frappe.get_print(letters.DOCTYPE, "GB-2026-0001", "Geschäftsbrief", no_letterhead=0)
		self.assertIn("Ihre Anfrage zur Wartung", html)
		self.assertIn("Unser Zeichen", self.render("GB-2026-0005"))
		self.assertEqual(FETCHED.findall(LINK.sub("", SCRIPT.sub("", html))), [])

	def render(self, name: str) -> str:
		with print_language("de"):
			return frappe.get_print(letters.DOCTYPE, name, "Geschäftsbrief", no_letterhead=0)
