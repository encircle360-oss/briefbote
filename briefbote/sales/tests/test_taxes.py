from decimal import Decimal
from unittest import TestCase

from briefbote.invoice.taxes import Detail
from briefbote.sales import taxes

D = Decimal


class TaxBaseTest(TestCase):
	def test_a_line_of_a_german_template_takes_rate_and_base_from_the_positions_it_taxes(self):
		"""The German templates of ERPNext give each tax line the rate 0 and each position the rate of its item tax
		template; the line keeps as its own net amount every position whose template names its account, also at 0 %."""
		details = [
			Detail(item="i1", tax="t19", rate=D(19)),
			Detail(item="i1", tax="t7", rate=D(0)),
			Detail(item="i2", tax="t19", rate=D(0)),
			Detail(item="i2", tax="t7", rate=D(7)),
			Detail(item="i3", tax="t19", rate=D(19)),
		]
		nets = {"i1": D("100.00"), "i2": D("40.00"), "i3": D("10.00")}
		self.assertEqual(
			taxes.tax_base("t19", D(0), D("150.00"), details, nets), taxes.Base(D(19), D("110.00"))
		)
		self.assertEqual(taxes.tax_base("t7", D(0), D("150.00"), details, nets), taxes.Base(D(7), D("40.00")))

	def test_a_line_whose_positions_differ_in_rate_has_no_known_base(self):
		details = [Detail(item="i1", tax="t", rate=D(19)), Detail(item="i2", tax="t", rate=D(7))]
		self.assertIsNone(taxes.tax_base("t", D(0), D(0), details, {"i1": D(1), "i2": D(1)}))

	def test_a_line_that_taxes_no_position_has_no_known_base(self):
		details = [Detail(item="i1", tax="t", rate=D(0))]
		self.assertIsNone(taxes.tax_base("t", D(0), D(0), details, {"i1": D(1)}))

	def test_a_position_that_is_not_counted_adds_nothing_to_the_base(self):
		"""An alternative of a quotation has no tax detail, and a detail of a position that is not printed counts
		nowhere."""
		details = [Detail(item="i1", tax="t", rate=D(19)), Detail(item="gone", tax="t", rate=D(19))]
		self.assertEqual(taxes.tax_base("t", D(0), D(0), details, {"i1": D(5)}), taxes.Base(D(19), D(5)))

	def test_without_tax_details_a_line_keeps_its_own_rate_and_net_amount(self):
		self.assertEqual(taxes.tax_base("t", D(19), D("80.00"), [], {}), taxes.Base(D(19), D("80.00")))
		self.assertIsNone(taxes.tax_base("t", D(0), D("80.00"), [], {}))
