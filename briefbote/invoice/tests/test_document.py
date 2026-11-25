from datetime import date
from decimal import Decimal
from unittest import TestCase

from briefbote.invoice import document
from briefbote.invoice.document import Case, Kind


class KindTest(TestCase):
	def test_an_invoice_that_is_no_return_is_an_invoice(self):
		self.assertIs(document.kind_of(False, "", Decimal("119.00"), None), Kind.INVOICE)

	def test_a_return_against_an_invoice_that_reverses_it_in_full_is_a_cancellation(self):
		self.assertIs(
			document.kind_of(True, "RE-1", Decimal("-119.00"), Decimal("119.00")), Kind.CANCELLATION
		)

	def test_a_return_against_an_invoice_for_part_of_it_is_a_correction(self):
		self.assertIs(document.kind_of(True, "RE-1", Decimal("-50.00"), Decimal("119.00")), Kind.CORRECTION)

	def test_a_return_against_an_invoice_whose_amount_is_unknown_is_a_correction(self):
		self.assertIs(document.kind_of(True, "RE-1", Decimal("-119.00"), None), Kind.CORRECTION)

	def test_a_return_without_an_invoice_is_a_commercial_credit(self):
		self.assertIs(document.kind_of(True, "", Decimal("-20.00"), None), Kind.CREDIT)

	def test_no_kind_is_titled_gutschrift_alone_which_is_the_word_for_self_billing(self):
		self.assertEqual(
			{kind: document.TITLES[kind] for kind in Kind},
			{
				Kind.INVOICE: "Invoice",
				Kind.CANCELLATION: "Cancellation Invoice",
				Kind.CORRECTION: "Invoice Correction",
				Kind.CREDIT: "Commercial Credit Note",
			},
		)


class CaseTest(TestCase):
	def test_a_case_is_read_from_its_name_and_none_is_a_domestic_taxable_supply(self):
		self.assertIs(document.case("Intra-Community supply"), Case.INTRA_COMMUNITY_SUPPLY)
		self.assertIs(document.case(None), Case.DOMESTIC)
		self.assertIs(document.case(""), Case.DOMESTIC)
		with self.assertRaises(ValueError):
			document.case("Lieferung nach Mars")

	def test_the_eu_cases_name_both_vat_ids(self):
		both = {case for case in Case if document.needs_both_vat_ids(case, small_business=False)}
		self.assertEqual(both, {Case.INTRA_COMMUNITY_SUPPLY, Case.EU_SERVICE})

	def test_a_small_business_names_no_vat_id_of_the_recipient(self):
		self.assertFalse(document.needs_both_vat_ids(Case.INTRA_COMMUNITY_SUPPLY, small_business=True))

	def test_a_case_without_german_tax_shows_none(self):
		self.assertEqual(
			{case for case in Case if document.charges_tax(case, small_business=False)}, {Case.DOMESTIC}
		)
		self.assertFalse(document.charges_tax(Case.DOMESTIC, small_business=True))


class NoticeTest(TestCase):
	def test_a_domestic_taxable_supply_needs_no_notice(self):
		self.assertEqual(document.notices(Kind.INVOICE, Case.DOMESTIC), [])

	def test_each_case_without_german_tax_says_why(self):
		expected = {
			Case.INTRA_COMMUNITY_SUPPLY: [(document.INTRA_COMMUNITY_SUPPLY, ())],
			Case.EU_SERVICE: [(document.EU_SERVICE, ())],
			Case.REVERSE_CHARGE: [(document.REVERSE_CHARGE, ())],
			Case.EXPORT: [(document.EXPORT, ())],
			Case.NON_EU_SERVICE: [(document.NON_EU_SERVICE, ())],
		}
		for case, notices in expected.items():
			with self.subTest(case=case):
				self.assertEqual(document.notices(Kind.INVOICE, case), notices)

	def test_the_reverse_charge_notices_carry_the_words_of_the_law(self):
		for text in (document.EU_SERVICE, document.REVERSE_CHARGE):
			with self.subTest(text=text):
				self.assertIn("Reverse charge", text)
		self.assertIn("Section 13b UStG", document.REVERSE_CHARGE)
		self.assertIn("Section 3a(2) UStG", document.EU_SERVICE)

	def test_an_exempt_supply_names_its_reason(self):
		self.assertEqual(
			document.notices(Kind.INVOICE, Case.EXEMPT, exemption_reason="Section 4 No. 14 UStG"),
			[(document.EXEMPT, ("Section 4 No. 14 UStG",))],
		)

	def test_an_exempt_supply_without_a_reason_has_no_notice_and_the_proof_finds_it(self):
		self.assertEqual(document.notices(Kind.INVOICE, Case.EXEMPT), [])

	def test_a_small_business_says_so_whatever_the_case(self):
		self.assertEqual(
			document.notices(Kind.INVOICE, Case.EXPORT, small_business=True), [(document.SMALL_BUSINESS, ())]
		)

	def test_a_commercial_credit_says_that_it_is_no_self_billing_invoice(self):
		self.assertEqual(document.notices(Kind.CREDIT, Case.DOMESTIC), [(document.COMMERCIAL_CREDIT, ())])
		self.assertEqual(
			document.notices(Kind.CREDIT, Case.EXPORT),
			[(document.COMMERCIAL_CREDIT, ()), (document.EXPORT, ())],
		)


class ServiceTest(TestCase):
	def test_the_period_of_the_invoice_comes_first(self):
		service = document.service(
			posting_date=date(2026, 11, 30),
			from_date=date(2026, 11, 1),
			to_date=date(2026, 11, 30),
			item_periods=[(date(2026, 10, 1), date(2026, 10, 31))],
			delivery_dates=[date(2026, 11, 3)],
		)
		self.assertEqual(service, (document.SERVICE_PERIOD, (date(2026, 11, 1), date(2026, 11, 30))))

	def test_without_one_the_periods_of_the_items_span_the_service(self):
		service = document.service(
			posting_date=date(2026, 11, 30),
			item_periods=[(date(2026, 10, 1), date(2026, 10, 31)), (date(2026, 11, 1), date(2026, 11, 15))],
		)
		self.assertEqual(service, (document.SERVICE_PERIOD, (date(2026, 10, 1), date(2026, 11, 15))))

	def test_without_periods_the_day_of_one_delivery_is_the_delivery_date(self):
		service = document.service(posting_date=date(2026, 11, 30), delivery_dates=[date(2026, 11, 3)] * 2)
		self.assertEqual(service, (document.DELIVERY_DATE, (date(2026, 11, 3),)))

	def test_several_deliveries_span_a_delivery_period(self):
		service = document.service(
			posting_date=date(2026, 11, 30), delivery_dates=[date(2026, 11, 13), date(2026, 11, 3)]
		)
		self.assertEqual(service, (document.DELIVERY_PERIOD, (date(2026, 11, 3), date(2026, 11, 13))))

	def test_without_any_the_date_of_the_invoice_is_named_as_the_date_of_the_service(self):
		"""UStAE 14.5 Abs. 16: the date must be stated even where it is that of the invoice."""
		service = document.service(posting_date=date(2026, 11, 30))
		self.assertEqual(service, (document.SERVICE_DATE, (date(2026, 11, 30),)))

	def test_an_invoice_period_needs_both_ends(self):
		service = document.service(posting_date=date(2026, 11, 30), from_date=date(2026, 11, 1))
		self.assertEqual(service, (document.SERVICE_DATE, (date(2026, 11, 30),)))

	def test_items_without_a_full_period_do_not_count(self):
		service = document.service(
			posting_date=date(2026, 11, 30), item_periods=[(date(2026, 11, 1), None), (None, None)]
		)
		self.assertEqual(service, (document.SERVICE_DATE, (date(2026, 11, 30),)))


class ConsumerTest(TestCase):
	def test_tells_a_consumer_when_he_defaults_without_a_reminder(self):
		"""§ 286 Abs. 3 Satz 1 BGB: against a consumer only where the invoice points it out."""
		self.assertIn("30 days", document.CONSUMER_DEFAULT)
		self.assertIn("Section 286(3) BGB", document.CONSUMER_DEFAULT)
