"""The print format Rechnung on a site: the frame of the letter, the kind of each document of the proof, its notices
and the HTML it renders, in German; the settings that refuse what does not belong to the company; the block
Über Briefbote."""

import json

import frappe
from frappe.desk.desktop import get_desktop_page
from frappe.tests import IntegrationTestCase
from frappe.translate import print_language

from briefbote.briefbote import about, about_block, printing, setup
from briefbote.setup import check as checks
from briefbote.tests import print_documents as documents
from briefbote.tests.print_proof import FETCHED, LINK, SCRIPT

KINDS = {
	"RE-2026-0101": "invoice",
	"RE-2026-0109": "correction",
	"RE-2026-0110": "cancellation",
	"RE-2026-0111": "credit",
}


class PrintingTest(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		documents.run()

	def invoice(self, name: str):
		return frappe.get_doc("Sales Invoice", name)

	def test_each_return_prints_as_the_kind_of_document_it_is(self):
		for name, kind in KINDS.items():
			with self.subTest(invoice=name), print_language("de"):
				self.assertEqual(printing.briefbote_invoice(self.invoice(name))["kind"], kind)

	def test_the_letter_takes_form_paper_and_particulars_from_the_settings(self):
		with print_language("de"):
			letter = printing.briefbote_letter(self.invoice("RE-2026-0101"))
			plain = printing.briefbote_letter(self.invoice("RE-2026-0101"), no_letterhead=1)
			small = printing.briefbote_letter(self.invoice("KB-2026-0001"))
		self.assertEqual(letter["form"].name, "B")
		self.assertEqual(small["form"].name, "A")
		self.assertTrue(letter["own_paper"])
		self.assertTrue(letter["logo"]["src"].startswith("data:image/svg+xml;base64,"))
		self.assertEqual((letter["logo"]["width"], letter["logo"]["height"]), (67.5, 18.0))
		self.assertEqual(letter["return_address"], ("Beispiel GmbH · Musterweg 1 · 12345 Musterstadt",))
		self.assertEqual(letter["recipient"], ["Kunde Muster AG", "Hauptstraße 5", "54321 Beispielstadt"])
		self.assertEqual(len(letter["footer"]), 3)
		self.assertIn("IBAN DE02 1203 0000 0000 2020 51", letter["footer"][2])
		self.assertIn("Amtsgericht Musterstadt, HRB 99999", letter["footer"][1])
		self.assertIn("USt-IdNr.: DE123456789", letter["footer"][1])
		self.assertEqual(
			(letter["accent"], letter["logo_side"], small["logo_side"]), ("#0B6E99", "right", "left")
		)
		self.assertEqual(small["fonts"], "")
		self.assertEqual((plain["footer"], plain["logo"], plain["own_paper"]), ([], {}, False))

	def test_an_eu_service_names_both_vat_ids_and_the_reverse_charge(self):
		with print_language("de"):
			invoice = printing.briefbote_invoice(self.invoice("RE-2026-0103"))
		info = dict(invoice["info"])
		self.assertEqual((info["Ihre USt-IdNr."], info["Unsere USt-IdNr."]), ("ATU87654321", "DE123456789"))
		self.assertTrue(invoice["notices"][0].startswith("Steuerschuldnerschaft des Leistungsempfängers"))

	def test_a_small_business_charges_no_vat_and_says_so(self):
		with print_language("de"):
			invoice = printing.briefbote_invoice(self.invoice("KB-2026-0001"))
		self.assertIn("Gemäß § 19 UStG wird keine Umsatzsteuer berechnet", invoice["notices"][0])
		self.assertEqual(
			[label for label, _amount, _style in invoice["totals"] if "Umsatzsteuer" in label], []
		)

	def test_the_print_format_renders_in_german_and_loads_nothing(self):
		with print_language("de"):
			html = frappe.get_print("Sales Invoice", "RE-2026-0101", "Rechnung", no_letterhead=0)
		for text in (
			"Rechnung RE-2026-0101",
			"Umsatzsteuer 19 % auf",
			"Leistungszeitraum",
			"Kunde Muster AG",
		):
			with self.subTest(text=text):
				self.assertIn(text, html)
		self.assertEqual(FETCHED.findall(LINK.sub("", SCRIPT.sub("", html))), [])

	def test_positions_with_two_rates_show_each_rate_and_the_untaxed_ones_their_line(self):
		with print_language("de"):
			mixed = printing.briefbote_invoice(self.invoice("RE-2026-0102"))
			untaxed = printing.briefbote_invoice(self.invoice("RE-2026-0113"))
			single = printing.briefbote_invoice(self.invoice("RE-2026-0101"))
		self.assertTrue(mixed["show_rates"])
		self.assertEqual({row["tax_rate"] for row in mixed["positions"]}, {"7 %", "19 %"})
		self.assertFalse(single["show_rates"])
		self.assertIn("Entgelt ohne Umsatzsteuer", [label for label, _amount, _style in untaxed["totals"]])

	def german_invoice(self, discount: float = 0, inclusive: bool = False, sign: int = 1):
		"""An invoice as ERPNext computes it with its German tax templates: tax lines at rate 0 and the rate of each
		position from its item tax template (erpnext/controllers/taxes_and_totals.py), with the tax details ERPNext
		writes from that computation on saving."""
		from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals

		doc = frappe.new_doc("Sales Invoice")
		doc.update(
			{
				"company": documents.COMPANY,
				"customer": documents.CUSTOMERS["inland"].name,
				"customer_name": documents.CUSTOMERS["inland"].name,
				"customer_address": f"{documents.CUSTOMERS['inland'].name}-Billing",
				"posting_date": documents.POSTING,
				"due_date": documents.POSTING,
				"currency": "EUR",
				"conversion_rate": 1,
				"is_return": int(sign < 0),
				"taxes_and_charges": f"Lieferung oder sonstige Leistung im Inland - {documents.ABBR}",
				"additional_discount_percentage": discount,
				"apply_discount_on": "Net Total",
				"disable_rounded_total": 1,
			}
		)
		for index, (qty, rate, tax) in enumerate(((3, 119.0, 19), (2, 53.5, 7), (1, 10.0, 19)), start=1):
			doc.append(
				"items",
				{
					"name": f"german-item-{index}",
					"item_name": f"Position {index}",
					"qty": qty * sign,
					"rate": rate,
					"uom": "Stück",
					"conversion_factor": 1,
					"item_tax_template": f"Umsatzsteuer {tax} % - {documents.ABBR}",
				},
			)
		for index, (rate, account) in enumerate(documents.GERMAN_ACCOUNTS.items(), start=1):
			doc.append(
				"taxes",
				{
					"name": f"german-tax-{index}",
					"charge_type": "On Net Total",
					"account_head": f"{account} - {documents.ABBR}",
					"description": f"Umsatzsteuer {rate} %",
					"rate": 0,
					"included_in_print_rate": int(inclusive),
				},
			)
		calculate_taxes_and_totals(doc)
		for row in doc.get("_item_wise_tax_details"):
			doc.append(
				"item_wise_tax_details",
				{
					"item_row": row.item.name,
					"tax_row": row.tax.name,
					"rate": row.rate,
					"amount": row.amount,
					"taxable_amount": row.taxable_amount,
				},
			)
		return doc

	def test_the_tax_lines_of_the_german_templates_name_their_rate_and_base(self):
		"""§ 14 Abs. 4 Satz 1 Nr. 8 UStG. The tax lines of the German templates have rate 0 and the net amount of
		every position; the base of each rate is the net amount of its positions."""
		for discount, inclusive, sign in ((0, False, 1), (10, False, 1), (0, True, 1), (0, False, -1)):
			doc = self.german_invoice(discount, inclusive, sign)
			bases = {19: 0.0, 7: 0.0}
			for item in doc.items:
				bases[19 if "19" in item.item_tax_template else 7] += item.net_amount
			with self.subTest(discount=discount, inclusive=inclusive, sign=sign), print_language("de"):
				labels = [label for label, _amount, _style in printing.briefbote_invoice(doc)["totals"]]
				for rate, base in bases.items():
					amount = frappe.format(base, {"fieldtype": "Currency", "options": "currency"}, doc)
					self.assertIn(f"Umsatzsteuer {rate} % auf {amount}", labels)

	def test_only_an_invoice_asks_for_payment_and_prints_the_terms(self):
		with print_language("de"):
			for name in ("RE-2026-0109", "RE-2026-0110", "RE-2026-0111"):
				with self.subTest(document=name):
					printed = printing.briefbote_invoice(self.invoice(name))
					self.assertEqual((printed["payment"], printed["terms"]), ([], ""))

	def test_a_self_billing_invoice_carries_the_word_gutschrift_and_the_number_of_the_supplier(self):
		with print_language("de"):
			printed = printing.briefbote_self_billing(frappe.get_doc("Purchase Invoice", "GS-2026-0001"))
			reverse = printing.briefbote_self_billing(frappe.get_doc("Purchase Invoice", "GS-2026-0002"))
		self.assertEqual(printed["title"], "Gutschrift")
		self.assertIn(("Ihre Steuernummer", "21/815/08150"), printed["info"])
		self.assertTrue(any(label.startswith("Umsatzsteuer 19 % auf") for label, _a, _s in printed["totals"]))
		self.assertFalse(any("Umsatzsteuer" in label for label, _a, _s in reverse["totals"]))

	def test_the_settings_refuse_a_bank_account_of_another_company(self):
		frappe.get_doc(
			{
				"doctype": "Bank Account",
				"name": "Fremdes Konto - Beispielbank",
				"account_name": "Fremdes Konto",
				"bank": "Beispielbank",
				"company": documents.SMALL_COMPANY,
				"is_company_account": 1,
				"iban": "DE02120300000000202051",
			}
		).db_insert()
		settings = frappe.get_doc("Business Document Settings", documents.COMPANY)
		settings.append("bank_accounts", {"bank_account": "Fremdes Konto - Beispielbank"})
		with self.assertRaises(frappe.ValidationError):
			settings.save(ignore_permissions=True)


class SetupTest(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		documents.run()

	def test_the_company_of_the_proof_lacks_nothing(self):
		self.assertEqual(setup.check(documents.COMPANY), [])

	def test_the_check_names_what_a_company_lacks(self):
		frappe.local.lang = "de"
		try:
			messages = [finding["message"] for finding in setup.check(documents.SMALL_COMPANY)]
		finally:
			frappe.local.lang = "en"
		self.assertIn("Registergericht und Registernummer fehlen.", messages)
		self.assertIn("Kein Bankkonto gewählt; Rechnungen bitten ohne Konto um Zahlung.", messages)

	def test_the_check_warns_of_a_logo_without_a_size(self):
		"""A file that is no image, such as the page a broken upload left, has no size; the letterhead would show
		nothing."""
		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "briefbote-proof-no-logo.svg",
				"content": "<html><body>not found</body></html>",
				"is_private": 0,
			}
		).insert(ignore_permissions=True)
		settings = frappe.get_doc("Business Document Settings", documents.COMPANY)
		settings.logo = "/files/briefbote-proof-no-logo.svg"
		settings.save(ignore_permissions=True)
		try:
			levels = {finding["message"]: finding["level"] for finding in setup.check(documents.COMPANY)}
			with print_language("de"):
				letter = printing.briefbote_letter(self.invoice_of(documents.COMPANY))
		finally:
			frappe.db.rollback()
			frappe.clear_document_cache("Business Document Settings", documents.COMPANY)
		self.assertEqual(levels, {checks.LOGO_UNREADABLE: "warning"})
		self.assertEqual(letter["logo"], {})

	def invoice_of(self, company: str):
		return frappe.get_doc("Sales Invoice", {"company": company, "docstatus": 1})

	def test_the_long_name_of_a_company_takes_a_line_of_its_own_in_the_return_address(self):
		with print_language("de"):
			letter = printing.briefbote_letter(frappe.get_doc("Sales Invoice", "HB-2026-0001"))
		self.assertEqual(
			letter["return_address"],
			(documents.LONG_COMPANY, "Industriestraße 123, Gebäude C · 12355 Musterstadt-Nord"),
		)
		messages = [finding["message"] for finding in setup.check(documents.LONG_COMPANY)]
		self.assertNotIn(checks.RETURN_ADDRESS_TOO_LONG, messages)

	def test_the_rule_gave_the_templates_of_the_erpnext_setup_their_case(self):
		settings = frappe.get_doc("Business Document Settings", documents.COMPANY)
		cases = {row.taxes_and_charges: row.tax_case for row in settings.tax_cases}
		self.assertEqual(cases[f"Lieferung in Drittland - {documents.ABBR}"], "Export")
		self.assertEqual(setup.apply_tax_cases(documents.COMPANY), {"sales": [], "purchase": []})


class AboutBlockTest(IntegrationTestCase):
	def test_the_endpoint_speaks_the_language_of_the_user(self):
		frappe.local.lang = "de"
		try:
			markup = about_block.render()
		finally:
			frappe.local.lang = "en"
		self.assertIn("Briefbote ersetzt keine rechtliche oder steuerliche Beratung.", markup)

	def test_the_block_is_installed_and_the_workspace_shows_it(self):
		block = frappe.get_doc("Custom HTML Block", about.BLOCK)
		self.assertEqual((block.private, block.roles), (0, []))
		page = get_desktop_page(json.dumps({"name": "Geschäftspost", "title": "Geschäftspost", "public": 1}))
		self.assertIn(about.BLOCK, [item.label for item in page["custom_blocks"]["items"]])
