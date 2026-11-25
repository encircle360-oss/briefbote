from unittest import TestCase

from briefbote.invoice import document, self_billing
from briefbote.invoice.document import Kind
from briefbote.invoice.self_billing import PurchaseCase


class TitleTest(TestCase):
	def test_every_title_carries_the_word_gutschrift(self):
		"""§ 14 Abs. 4 Satz 1 Nr. 10 UStG; the German of each title is checked in test_translations."""
		self.assertEqual(
			self_billing.TITLES,
			{
				Kind.INVOICE: "Self-Billing Invoice",
				Kind.CORRECTION: "Correction of the Self-Billing Invoice",
				Kind.CANCELLATION: "Cancellation of the Self-Billing Invoice",
				Kind.CREDIT: "Correction of the Self-Billing Invoice",
			},
		)


class CaseTest(TestCase):
	def test_a_case_is_read_from_its_name_and_none_is_a_supply_taxable_in_germany(self):
		self.assertIs(self_billing.case(None), PurchaseCase.DOMESTIC)
		self.assertIs(self_billing.case("Reverse charge in Germany"), PurchaseCase.REVERSE_CHARGE)
		with self.assertRaises(ValueError):
			self_billing.case("Lieferung nach Mars")

	def test_only_a_supply_taxable_in_germany_shows_tax(self):
		self.assertEqual(
			{case for case in PurchaseCase if self_billing.charges_tax(case)}, {PurchaseCase.DOMESTIC}
		)


class NoticeTest(TestCase):
	def test_says_first_that_the_recipient_settles_by_self_billing(self):
		self.assertEqual(self_billing.notices(PurchaseCase.DOMESTIC), [(self_billing.SELF_BILLING, ())])

	def test_each_case_without_tax_says_why(self):
		self.assertEqual(
			self_billing.notices(PurchaseCase.REVERSE_CHARGE),
			[(self_billing.SELF_BILLING, ()), (document.REVERSE_CHARGE, ())],
		)
		self.assertEqual(
			self_billing.notices(PurchaseCase.SMALL_BUSINESS),
			[(self_billing.SELF_BILLING, ()), (document.SMALL_BUSINESS, ())],
		)
		self.assertEqual(
			self_billing.notices(PurchaseCase.EXEMPT, "§ 4 Nr. 11 UStG"),
			[(self_billing.SELF_BILLING, ()), (document.EXEMPT, ("§ 4 Nr. 11 UStG",))],
		)
		self.assertEqual(self_billing.notices(PurchaseCase.EXEMPT), [(self_billing.SELF_BILLING, ())])


class TaxIdTest(TestCase):
	def test_a_number_that_starts_with_the_code_of_a_country_is_a_vat_id(self):
		"""§ 14 Abs. 4 Satz 1 Nr. 2 UStG: the Steuernummer or the USt-IdNr. of the supplier, named as what it is."""
		self.assertEqual(self_billing.tax_id_label("DE111111111"), self_billing.VAT_ID)
		self.assertEqual(self_billing.tax_id_label(" atu12345678"), self_billing.VAT_ID)
		self.assertEqual(self_billing.tax_id_label("21/815/08150"), self_billing.TAX_NUMBER)
		self.assertEqual(self_billing.tax_id_label("2181508150"), self_billing.TAX_NUMBER)
		self.assertEqual(self_billing.tax_id_label(""), self_billing.TAX_NUMBER)
