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
