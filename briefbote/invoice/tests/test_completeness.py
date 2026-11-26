from unittest import TestCase

from briefbote.invoice import completeness
from briefbote.invoice.completeness import Facts


class MissingTest(TestCase):
	def test_a_complete_invoice_lacks_nothing(self):
		self.assertEqual(completeness.missing(Facts()), [])
		self.assertEqual(completeness.missing(Facts(taxable=True, charges_tax=True)), [])

	def test_each_missing_particular_has_its_finding(self):
		cases = {
			Facts(recipient_address=False): completeness.RECIPIENT_ADDRESS,
			Facts(issuer_tax_id=False): completeness.OWN_TAX_ID,
			Facts(issuer_tax_id=False, self_billing=True): completeness.SUPPLIER_TAX_ID,
			Facts(service_date=False): completeness.SERVICE_DATE,
			Facts(taxable=True, charges_tax=False): completeness.NO_TAX,
			Facts(bases_known=False): completeness.TAX_BASE,
			Facts(needs_both_vat_ids=True, recipient_vat_id=False): completeness.RECIPIENT_VAT_ID,
			Facts(needs_both_vat_ids=True, own_vat_id=False): completeness.OWN_VAT_ID,
		}
		for facts, text in cases.items():
			with self.subTest(text=text):
				self.assertEqual(completeness.missing(facts), [text])

	def test_a_taxable_supply_without_tax_but_with_its_reason_lacks_nothing(self):
		self.assertEqual(completeness.missing(Facts(taxable=True, charges_tax=False, states_reason=True)), [])

	def test_an_invoice_of_at_most_250_euros_needs_no_recipient_number_or_date(self):
		"""§ 33 UStDV, but not in the cases of § 14a UStG (§ 33 Satz 3 UStDV)."""
		facts = Facts(small_amount=True, recipient_address=False, issuer_tax_id=False, service_date=False)
		self.assertEqual(completeness.missing(facts), [])
		self.assertEqual(
			completeness.missing(Facts(small_amount=True, recipient_address=False, needs_both_vat_ids=True)),
			[completeness.RECIPIENT_ADDRESS],
		)
		self.assertEqual(
			completeness.missing(Facts(small_amount=True, taxable=True, charges_tax=False)),
			[completeness.NO_TAX],
		)

	def test_a_commercial_credit_is_no_invoice(self):
		self.assertEqual(
			completeness.missing(Facts(credit=True, recipient_address=False, issuer_tax_id=False)), []
		)

	def test_the_findings_follow_the_order_of_the_law(self):
		facts = Facts(recipient_address=False, issuer_tax_id=False, service_date=False, bases_known=False)
		self.assertEqual(
			completeness.missing(facts),
			[
				completeness.RECIPIENT_ADDRESS,
				completeness.OWN_TAX_ID,
				completeness.SERVICE_DATE,
				completeness.TAX_BASE,
			],
		)


class SelfBillingRolesTest(TestCase):
	def test_a_gutschrift_names_the_supplier_as_the_party_whose_particulars_are_missing(self):
		"""§ 14 Abs. 2 Satz 5 UStG: the recipient of the supply issues the Gutschrift; it is addressed to the supplier,
		the leistender Unternehmer, whose address and number it must carry."""
		found = completeness.missing(Facts(self_billing=True, recipient_address=False, issuer_tax_id=False))
		self.assertEqual(found, [completeness.SUPPLIER_ADDRESS, completeness.SUPPLIER_TAX_ID])
		self.assertIn("supplier", completeness.SUPPLIER_ADDRESS)
		self.assertNotIn("recipient", completeness.SUPPLIER_ADDRESS)

	def test_an_invoice_names_its_recipient(self):
		self.assertEqual(
			completeness.missing(Facts(recipient_address=False)), [completeness.RECIPIENT_ADDRESS]
		)

	def test_no_finding_of_a_gutschrift_calls_the_supplier_the_recipient(self):
		every = completeness.missing(
			Facts(
				self_billing=True,
				recipient_address=False,
				issuer_tax_id=False,
				service_date=False,
				taxable=True,
				charges_tax=False,
				bases_known=False,
			)
		)
		self.assertEqual([text for text in every if "recipient" in text.lower()], [])
