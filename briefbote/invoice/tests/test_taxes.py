from decimal import Decimal
from unittest import TestCase

from briefbote.invoice import taxes
from briefbote.invoice.taxes import Detail

D = Decimal


class PositionRatesTest(TestCase):
	def test_each_position_takes_the_rates_of_its_tax_details(self):
		details = [
			Detail(item="i1", tax="t19", rate=D(19)),
			Detail(item="i2", tax="t7", rate=D(7)),
			Detail(item="i2", tax="t19", rate=D(0)),
			Detail(item="removed", tax="t19", rate=D(19)),
		]
		rates = taxes.position_rates(["i1", "i2", "i3"], details, single_rate=None)
		self.assertEqual(rates, {"i1": D(19), "i2": D(7), "i3": D(0)})

	def test_without_tax_details_every_position_takes_the_one_rate_of_the_invoice(self):
		self.assertEqual(
			taxes.position_rates(["i1", "i2"], [], single_rate=D(19)), {"i1": D(19), "i2": D(19)}
		)

	def test_without_tax_details_and_without_a_single_rate_no_rate_is_known(self):
		self.assertEqual(taxes.position_rates(["i1"], [], single_rate=None), {})

	def test_the_rate_column_shows_where_the_positions_differ(self):
		self.assertTrue(taxes.shows_rates({"i1": D(19), "i2": D(7)}))
		self.assertTrue(taxes.shows_rates({"i1": D(19), "i2": D(0)}))
		self.assertFalse(taxes.shows_rates({"i1": D(19), "i2": D(19)}))
		self.assertFalse(taxes.shows_rates({}))

	def test_the_positions_without_tax_add_up_to_their_own_line(self):
		"""§ 14 Abs. 4 Satz 1 Nr. 7 UStG: the consideration broken down by rates and exemptions."""
		nets = {"i1": D("100.00"), "i2": D("50.00"), "i3": D("25.50")}
		rates = {"i1": D(19), "i2": D(0), "i3": D(0)}
		self.assertEqual(taxes.untaxed(nets, rates), D("75.50"))
		self.assertEqual(taxes.untaxed(nets, {"i1": D(19), "i2": D(19), "i3": D(19)}), D(0))
		self.assertEqual(taxes.untaxed(nets, {}), D(0))

	def test_a_single_rate_is_the_one_rate_all_tax_lines_share(self):
		self.assertEqual(taxes.single_rate([D(19)]), D(19))
		self.assertEqual(taxes.single_rate([D(19), D(19)]), D(19))
		self.assertIsNone(taxes.single_rate([D(19), D(7)]))
		self.assertIsNone(taxes.single_rate([]))

	def test_a_rate_reads_without_trailing_zeros(self):
		self.assertEqual(taxes.percent(D("19.000")), "19")
		self.assertEqual(taxes.percent(D("7.5")), "7,5")
		self.assertEqual(taxes.percent(D(0)), "0")


NETS = {"i1": D("100.00"), "i2": D("50.00"), "i3": D("25.50")}


class TaxBaseTest(TestCase):
	"""§ 14 Abs. 4 Satz 1 Nr. 8 UStG: each tax line names its rate and the consideration it is charged on."""

	def test_the_base_of_a_tax_line_are_the_positions_its_details_tax(self):
		"""The German templates of ERPNext: tax lines with rate 0, the rate from the item tax template of each
		position, which names every tax account, its own with its rate and the others with 0."""
		details = [
			Detail(item="i1", tax="t19", rate=D(19)),
			Detail(item="i1", tax="t7", rate=D(0)),
			Detail(item="i2", tax="t19", rate=D(0)),
			Detail(item="i2", tax="t7", rate=D(7)),
			Detail(item="i3", tax="t19", rate=D(19)),
			Detail(item="i3", tax="t7", rate=D(0)),
		]
		self.assertEqual(
			taxes.tax_base("t19", D(0), D("175.50"), details, NETS), taxes.Base(D(19), D("125.50"))
		)
		self.assertEqual(taxes.tax_base("t7", D(0), D("175.50"), details, NETS), taxes.Base(D(7), D("50.00")))

	def test_a_position_removed_from_the_invoice_adds_nothing(self):
		details = [Detail(item="i1", tax="t19", rate=D(19)), Detail(item="gone", tax="t19", rate=D(19))]
		self.assertEqual(taxes.tax_base("t19", D(19), D(0), details, NETS), taxes.Base(D(19), D("100.00")))

	def test_without_details_the_tax_line_keeps_its_rate_and_net_amount(self):
		self.assertEqual(taxes.tax_base("t19", D(19), D("175.50"), [], NETS), taxes.Base(D(19), D("175.50")))

	def test_a_base_that_cannot_be_known_is_none(self):
		# No details and no rate on the line.
		self.assertIsNone(taxes.tax_base("t19", D(0), D("175.50"), [], NETS))
		# Details, but none taxes a position on this line.
		details = [Detail(item="i1", tax="t19", rate=D(0)), Detail(item="i1", tax="t7", rate=D(7))]
		self.assertIsNone(taxes.tax_base("t19", D(0), D(0), details, NETS))
		# One line that charges two rates.
		details = [Detail(item="i1", tax="t", rate=D(19)), Detail(item="i2", tax="t", rate=D(7))]
		self.assertIsNone(taxes.tax_base("t", D(0), D(0), details, NETS))
