from unittest import TestCase

from briefbote.invoice.document import Case
from briefbote.invoice.self_billing import PurchaseCase
from briefbote.setup import tax_cases


class SalesTest(TestCase):
	def test_the_templates_of_the_german_setup_of_erpnext_get_their_case(self):
		"""The titles of erpnext/setup/setup_wizard/data/country_wise_tax.json for Germany in ERPNext 16.60.0."""
		expected = {
			"Lieferung oder sonstige Leistung im Inland": Case.DOMESTIC,
			"Lieferung an Unternehmen in der EU": Case.INTRA_COMMUNITY_SUPPLY,
			"Sonstige Leistung an Unternehmen in der EU": Case.EU_SERVICE,
			"Lieferung oder sonstige Leistung an nicht-Unternehmen in der EU": Case.DOMESTIC,
			"Lieferung in Drittland": Case.EXPORT,
			"Sonstige Leistung an Unternehmen in Drittland": Case.NON_EU_SERVICE,
			"Sonstige Leistung an nicht-Unternehmen in Drittland": Case.DOMESTIC,
			"Bauleistungen nach § 13b UStG": Case.REVERSE_CHARGE,
		}
		for title, case in expected.items():
			with self.subTest(title=title):
				self.assertIs(tax_cases.sales_case(title), case)

	def test_a_template_the_rule_does_not_know_gets_no_case(self):
		self.assertIsNone(tax_cases.sales_case("Nullsteuersatz nach § 12 Abs. 3 UStG"))
		self.assertIsNone(tax_cases.sales_case("Steuerfrei Unterricht"))

	def test_the_title_is_read_without_the_abbreviation_of_the_company(self):
		self.assertEqual(tax_cases.title("Lieferung in Drittland - BSP", "BSP"), "Lieferung in Drittland")
		self.assertEqual(tax_cases.title("Lieferung in Drittland", "BSP"), "Lieferung in Drittland")


class PurchaseTest(TestCase):
	def test_the_domestic_purchase_templates_get_their_case(self):
		self.assertIs(tax_cases.purchase_case("Lieferung aus dem Inland"), PurchaseCase.DOMESTIC)
		self.assertIs(tax_cases.purchase_case("Sonstige Leistung aus dem Inland"), PurchaseCase.DOMESTIC)
		self.assertIs(tax_cases.purchase_case("Bauleistungen nach § 13b UStG"), PurchaseCase.REVERSE_CHARGE)

	def test_a_supplier_abroad_gets_no_case_since_a_gutschrift_for_him_follows_other_rules(self):
		for title in ("Lieferung aus der EU", "Sonstige Leistung aus der EU", "Lieferung aus Drittland"):
			with self.subTest(title=title):
				self.assertIsNone(tax_cases.purchase_case(title))
