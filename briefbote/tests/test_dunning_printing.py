"""The print format Mahnung on a site, for the Dunnings of print_documents_dunning.py: title and text by level, the
deadline, the open invoices, the interest and the lump sum only where they are lawful, a finding instead of a claim
where ERPNext booked more, the base rates of the settings and the check that warns without them."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.translate import print_language

from briefbote.briefbote import dunning, setup
from briefbote.dunning import interest
from briefbote.tests import print_documents as documents
from briefbote.tests import print_documents_dunning as dunning_documents
from briefbote.tests.print_proof import FETCHED, LINK, SCRIPT


class DunningPrintingTest(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		documents.run()
		dunning_documents.run()

	def letter(self, name: str) -> dict:
		with print_language("de"):
			return dunning.briefbote_dunning(frappe.get_doc("Dunning", name))

	def test_new_settings_hold_the_published_base_rates(self):
		config = frappe.new_doc("Business Document Settings", company=documents.SMALL_COMPANY)
		config.run_method("before_insert")
		self.assertEqual(
			[(row.valid_from, row.rate) for row in config.base_rates],
			[(row.valid_from, float(row.rate)) for row in interest.PUBLISHED],
		)

	def test_a_payment_reminder_asks_for_payment_without_interest_or_fee(self):
		letter = self.letter("MZ-2026-0001")
		self.assertEqual(letter["title"], "Zahlungserinnerung")
		self.assertEqual(letter["findings"], [])
		self.assertEqual([label for label, _amount, _style in letter["totals"]], ["Offene Rechnungen"])
		self.assertIn("bis zum 20.11.2026", letter["text"])
		self.assertIn(
			"Zahlungen, die bis zum 10.11.2026 eingegangen sind, sind berücksichtigt.", letter["closing"]
		)

	def test_a_mahnung_to_a_business_claims_lawful_interest_and_the_lump_sum(self):
		letter = self.letter("MZ-2026-0002")
		self.assertEqual(letter["title"], "Mahnung")
		labels = [label for label, _amount, _style in letter["totals"]]
		self.assertEqual(
			labels,
			[
				"Offene Rechnungen",
				"Verzugszinsen (§ 288 BGB) bis 25.11.2026",
				"Pauschale (§ 288 Abs. 5 BGB)",
				"Gesamtbetrag",
			],
		)
		rows = {row["invoice"]: row for row in letter["rows"]}
		self.assertEqual(rows["RE-2026-0202"]["open"], "1.880,00 €")
		self.assertEqual(rows["RE-2026-0202"]["paid"], "500,00 €")
		self.assertEqual(rows["RE-2026-0201"]["days"], "191")

	def test_a_mahnung_to_a_consumer_claims_no_lump_sum(self):
		labels = [label for label, _amount, _style in self.letter("MZ-2026-0003")["totals"]]
		self.assertNotIn("Pauschale (§ 288 Abs. 5 BGB)", labels)
		self.assertIn("Verzugszinsen (§ 288 BGB) bis 25.11.2026", labels)

	def test_interest_above_the_lawful_maximum_prints_a_finding_and_no_claim(self):
		letter = self.letter("MZ-2026-0005")
		self.assertEqual(letter["title"], "2. Mahnung")
		self.assertEqual(len(letter["findings"]), 1)
		self.assertIn("übersteigt", letter["findings"][0])
		self.assertEqual([label for label, _amount, _style in letter["totals"]], ["Offene Rechnungen"])
		self.assertEqual((letter["text"], letter["bank"]), ("", ""))

	def test_the_last_level_reads_as_the_final_reminder(self):
		self.assertEqual(self.letter("MZ-2026-0006")["title"], "Letzte Mahnung")

	def test_the_check_warns_where_no_base_rate_covers_today(self):
		frappe.db.delete("Business Document Base Rate", {"parent": documents.SMALL_COMPANY})
		messages = [finding["message"] for finding in setup.check(documents.SMALL_COMPANY)]
		self.assertTrue(any("Basiszinssatz" in message for message in messages), messages)

	def test_the_print_format_renders_in_german_and_loads_nothing(self):
		with print_language("de"):
			html = frappe.get_print("Dunning", "MZ-2026-0002", "Mahnung", no_letterhead=0)
		self.assertIn("Mahnung MZ-2026-0002", html)
		self.assertNotIn("Rechnungsnummer", html)
		self.assertEqual(FETCHED.findall(LINK.sub("", SCRIPT.sub("", html))), [])
