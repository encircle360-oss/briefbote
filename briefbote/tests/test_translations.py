"""Every text of the printouts and of the desk reads in German, read from the files without a bench.

A printout takes its texts in the language of its document: the English source in the code, the German in
briefbote/translations/de.csv. The texts of the printouts carry the context Briefbote there, so that a short text
such as „Amount“ reads on paper as Briefbote translates it and the desk of ERPNext keeps its own German.
"""

import csv
import json
import re
from pathlib import Path
from unittest import TestCase

from briefbote.invoice import completeness, document, self_billing
from briefbote.layout import letter
from briefbote.setup import check

APP = Path(__file__).resolve().parents[1]
TRANSLATIONS = APP / "translations" / "de.csv"
PRINTING = APP / "briefbote" / "printing.py"
ANNEX = APP / "briefbote" / "annex.py"
TEMPLATES = [*(APP / "templates").rglob("*.html"), *(APP / "briefbote" / "print_format").rglob("*.html")]
DOCTYPES = (APP / "briefbote" / "doctype").glob("*/*.json")
CONTEXT = "Briefbote"
PRINTING_TEXT = re.compile(r'\bt\(\s*"((?:[^"\\]|\\.)+)"')
TEMPLATE_TEXT = re.compile(r'_\("((?:[^"\\]|\\.)+)", context="Briefbote"\)')
FOOTER_TEXTS = (
	"Phone {0}",
	"Registered Office: {0}",
	"Managing Directors:",
	"Managing Director:",
	"Executive Board:",
	"Chair of the Supervisory Board: {0}",
	"VAT ID: {0}",
	"Tax Number: {0}",
)


def rows() -> list[list[str]]:
	with TRANSLATIONS.open(encoding="utf-8", newline="") as file:
		return list(csv.reader(file))


def printout_german() -> dict[str, str]:
	return {row[0]: row[1] for row in rows() if len(row) == 3 and row[2] == CONTEXT}


def desk_german() -> dict[str, str]:
	return {row[0]: row[1] for row in rows() if len(row) == 2 or not row[2]}


class PrintoutTextsTest(TestCase):
	def test_every_text_of_the_print_module_reads_in_german(self):
		texts = {
			text
			for path in (PRINTING, ANNEX)
			for text in PRINTING_TEXT.findall(path.read_text(encoding="utf-8"))
		}
		self.assertTrue(texts)
		self.assertEqual(sorted(texts - printout_german().keys()), [])

	def test_every_text_of_the_templates_reads_in_german(self):
		texts = {
			text for path in TEMPLATES for text in TEMPLATE_TEXT.findall(path.read_text(encoding="utf-8"))
		}
		self.assertTrue(texts)
		self.assertEqual(sorted(texts - printout_german().keys()), [])

	def test_the_templates_translate_only_with_the_context_of_briefbote(self):
		for path in TEMPLATES:
			with self.subTest(template=path.name):
				source = path.read_text(encoding="utf-8")
				self.assertEqual(len(re.findall(r"\b_\(", source)), len(TEMPLATE_TEXT.findall(source)))

	def test_every_title_notice_and_label_of_an_invoice_reads_in_german(self):
		texts = {
			*document.TITLES.values(),
			document.INTRA_COMMUNITY_SUPPLY,
			document.EU_SERVICE,
			document.REVERSE_CHARGE,
			document.EXPORT,
			document.NON_EU_SERVICE,
			document.EXEMPT,
			document.SMALL_BUSINESS,
			document.COMMERCIAL_CREDIT,
			document.CONSUMER_DEFAULT,
			document.SERVICE_PERIOD,
			document.SERVICE_DATE,
			document.DELIVERY_DATE,
			document.DELIVERY_PERIOD,
		}
		self.assertEqual(sorted(texts - printout_german().keys()), [])

	def test_every_finding_of_an_incomplete_document_reads_in_german(self):
		self.assertEqual(sorted(set(completeness.TEXTS) - printout_german().keys()), [])

	def test_every_text_of_the_footer_reads_in_german(self):
		source = Path(letter.__file__).read_text(encoding="utf-8")
		for text in FOOTER_TEXTS:
			with self.subTest(text=text):
				self.assertIn(f'"{text}"', source)
		self.assertEqual(sorted(set(FOOTER_TEXTS) - printout_german().keys()), [])

	def test_every_title_and_notice_of_a_self_billing_invoice_reads_in_german_with_the_word_gutschrift(self):
		"""§ 14 Abs. 4 Satz 1 Nr. 10 UStG."""
		german = printout_german()
		for title in self_billing.TITLES.values():
			with self.subTest(title=title):
				self.assertIn("Gutschrift", german[title])
		self.assertIn(self_billing.SELF_BILLING, german)

	def test_no_title_but_that_of_self_billing_is_gutschrift_alone(self):
		"""UStAE 14.3 Abs. 2 Satz 5: the cancellation or correction of an invoice is no Gutschrift."""
		titles = {printout_german()[title] for title in document.TITLES.values()}
		self.assertEqual(
			titles, {"Rechnung", "Stornorechnung", "Rechnungskorrektur", "Kaufmännische Gutschrift"}
		)

	def test_the_reverse_charge_notices_carry_the_term_of_the_law(self):
		"""§ 14a Abs. 1 and 5 UStG: „Steuerschuldnerschaft des Leistungsempfängers“."""
		for text in (document.EU_SERVICE, document.REVERSE_CHARGE):
			with self.subTest(text=text):
				self.assertIn("Steuerschuldnerschaft des Leistungsempfängers", printout_german()[text])

	def test_a_text_and_its_german_name_the_same_placeholders(self):
		for source, german in printout_german().items():
			with self.subTest(text=source):
				self.assertEqual(sorted(re.findall(r"\{\d\}", source)), sorted(re.findall(r"\{\d\}", german)))

	def test_no_text_starts_or_ends_with_a_space_which_the_lookup_strips(self):
		self.assertEqual([row[0] for row in rows() if row[0] != row[0].strip()], [])


class DeskTextsTest(TestCase):
	def test_every_label_description_and_option_of_the_settings_reads_in_german(self):
		known = {
			"Company",
			"Bank Account",
			"Bank Accounts",
			"Taxes",
			"Logo",
			"Sales Taxes and Charges Template",
			"Purchase Taxes and Charges Template",
			"Font",
			"Footer",
			"Column",
			"Block",
			"Right",
			"Left",
			"Name",
			"None",
		}
		texts = set()
		for path in DOCTYPES:
			definition = json.loads(path.read_text(encoding="utf-8"))
			texts.add(definition["name"])
			for field in definition["fields"]:
				texts.update(filter(None, (field.get("label"), field.get("description"))))
				if field["fieldtype"] == "Select":
					texts.update(filter(None, field["options"].split("\n")))
		texts -= known | {"A", "B"}
		self.assertEqual(sorted(texts - desk_german().keys()), [])

	def test_every_finding_of_the_check_reads_in_german(self):
		self.assertEqual(sorted(set(check.TEXTS) - desk_german().keys()), [])

	def test_every_text_of_the_scripts_of_the_desk_reads_in_german(self):
		texts = {
			text
			for path in (APP / "public" / "js").glob("*.js")
			for text in re.findall(r'__\("((?:[^"\\]|\\.)+)"\)', path.read_text(encoding="utf-8"))
		}
		self.assertTrue(texts)
		self.assertEqual(sorted(texts - desk_german().keys()), [])

	def test_the_tax_cases_read_in_german(self):
		cases = {case.value for case in document.Case} | {case.value for case in self_billing.PurchaseCase}
		self.assertEqual(sorted(cases - desk_german().keys()), [])

	def test_the_field_of_the_purchase_invoice_reads_in_german(self):
		for field in json.loads((APP / "fixtures" / "custom_field.json").read_text(encoding="utf-8")):
			with self.subTest(field=field["fieldname"]):
				self.assertIn(field["label"], desk_german())
				self.assertIn(field["description"], desk_german())
