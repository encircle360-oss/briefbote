from dataclasses import replace
from unittest import TestCase

from briefbote.setup import check
from briefbote.setup.check import Company, Finding

COMPLETE = Company(
	name="Beispiel GmbH",
	has_settings=True,
	blank_paper=True,
	logo=True,
	address=True,
	registered_office=True,
	register=True,
	management=True,
	vat_id=True,
	tax_number=True,
	bank_accounts=1,
	unmapped_sales=(),
	unmapped_purchase=(),
)


class CheckTest(TestCase):
	def test_a_complete_company_lacks_nothing(self):
		self.assertEqual(check.findings(COMPLETE), [])

	def test_advance_invoices_switched_on_point_to_the_warnings_of_their_page(self):
		"""docs/anzahlungsrechnung.md: the VAT of an advance twice in the books of ERPNext, no e-invoice."""
		self.assertEqual(
			check.findings(replace(COMPLETE, advance_invoices=True)),
			[Finding(check.INFO, check.ADVANCE_INVOICES, ())],
		)

	def test_without_settings_the_company_prints_with_the_defaults(self):
		company = Company(name="Beispiel GmbH", has_settings=False)
		self.assertIn(Finding(check.ERROR, check.NO_SETTINGS, ("Beispiel GmbH",)), check.findings(company))

	def test_names_each_missing_particular_of_the_company(self):
		company = Company(
			name="Beispiel GmbH",
			has_settings=True,
			blank_paper=True,
			logo=False,
			address=False,
			registered_office=False,
			register=False,
			management=False,
			vat_id=False,
			tax_number=False,
			bank_accounts=0,
			unmapped_sales=("Nullsteuersatz nach § 12 Abs. 3 UStG - BSP",),
			unmapped_purchase=("Lieferung aus der EU - BSP",),
		)
		self.assertEqual(
			check.findings(company),
			[
				Finding(check.ERROR, check.NO_ADDRESS, ()),
				Finding(check.ERROR, check.NO_TAX_ID, ()),
				Finding(check.WARNING, check.NO_REGISTERED_OFFICE, ()),
				Finding(check.WARNING, check.NO_REGISTER, ()),
				Finding(check.WARNING, check.NO_MANAGEMENT, ()),
				Finding(check.WARNING, check.NO_BANK, ()),
				Finding(check.INFO, check.NO_LOGO, ()),
				Finding(check.WARNING, check.UNMAPPED_SALES, ("Nullsteuersatz nach § 12 Abs. 3 UStG - BSP",)),
				Finding(check.INFO, check.UNMAPPED_PURCHASE, ("Lieferung aus der EU - BSP",)),
			],
		)

	def test_on_pre_printed_paper_the_paper_carries_logo_and_particulars(self):
		company = Company(
			name="Beispiel GmbH",
			has_settings=True,
			blank_paper=False,
			address=True,
			vat_id=True,
		)
		self.assertEqual(check.findings(company), [Finding(check.WARNING, check.NO_BANK, ())])

	def test_one_of_steuernummer_and_vat_id_is_enough(self):
		self.assertEqual(check.findings(replace(COMPLETE, vat_id=False)), [])


class LetterheadCheckTest(TestCase):
	def test_a_logo_that_cannot_be_read_or_has_no_size_is_a_warning(self):
		found = check.findings(replace(COMPLETE, logo_readable=False))
		self.assertEqual(found, [Finding(check.WARNING, check.LOGO_UNREADABLE, ())])

	def test_a_logo_on_pre_printed_paper_does_not_print(self):
		self.assertEqual(check.findings(replace(COMPLETE, blank_paper=False, logo_readable=False)), [])

	def test_particulars_that_need_more_than_four_lines_in_a_block_of_the_foot_are_a_warning(self):
		found = check.findings(
			replace(COMPLETE, foot_overflows=(("Register and Management", "5", "English"),))
		)
		self.assertEqual(
			found, [Finding(check.WARNING, check.FOOT_TOO_LONG, ("Register and Management", "5", "English"))]
		)

	def test_pre_printed_paper_has_no_foot_to_fit(self):
		found = check.findings(
			replace(
				COMPLETE, blank_paper=False, foot_overflows=(("Register and Management", "5", "English"),)
			)
		)
		self.assertNotIn(check.FOOT_TOO_LONG, [finding.text for finding in found])

	def test_a_return_address_that_does_not_fit_the_remarks_zone_is_a_warning(self):
		found = check.findings(replace(COMPLETE, return_address_fits=False))
		self.assertEqual(found, [Finding(check.WARNING, check.RETURN_ADDRESS_TOO_LONG, ())])
