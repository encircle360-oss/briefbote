from decimal import Decimal
from unittest import TestCase

from briefbote.sales import packing
from briefbote.sales.packing import Slip

D = Decimal
NONE = Decimal(0)


def slip(first, last, net=NONE, gross=NONE, unit="kg", name="PK-1", submitted=True):
	return Slip(name, first, last, net, unit, gross, unit, submitted)


class SlipsTest(TestCase):
	"""ERPNext packs one delivery note into several Packing Slips, each for its packages from_case_no to to_case_no
	(erpnext/stock/doctype/packing_slip/packing_slip.py)."""

	def test_a_submitted_slip_lists_every_submitted_slip_of_its_delivery_by_package(self):
		printed = slip(3, 4, name="PK-2")
		others = [slip(1, 2, name="PK-1"), printed, slip(5, 5, name="PK-3")]
		self.assertEqual([found.name for found in packing.listed(printed, others)], ["PK-1", "PK-2", "PK-3"])

	def test_a_draft_or_cancelled_slip_lists_only_itself(self):
		draft = slip(3, 3, name="PK-9", submitted=False)
		self.assertEqual(packing.listed(draft, [slip(1, 2, name="PK-1")]), [draft])

	def test_a_slip_missing_from_the_others_is_listed_once(self):
		printed = slip(2, 2, name="PK-2")
		self.assertEqual(
			packing.listed(printed, [slip(1, 1, name="PK-1")]), [slip(1, 1, name="PK-1"), printed]
		)

	def test_the_packages_read_as_their_numbers(self):
		self.assertEqual(packing.label(slip(1, 1)), (packing.PACKAGE, (1,)))
		self.assertEqual(packing.label(slip(2, 4)), (packing.PACKAGES, (2, 4)))
		self.assertEqual(packing.label(slip(2, 0)), (packing.PACKAGE, (2,)))

	def test_the_list_names_the_packages_it_covers(self):
		self.assertEqual(packing.covered([slip(1, 2), slip(3, 5)]), (packing.PACKAGES, (1, 5)))
		self.assertEqual(packing.covered([slip(4, 4)]), (packing.PACKAGE, (4,)))

	def test_the_packages_are_counted_over_their_ranges(self):
		self.assertEqual(packing.count([slip(1, 2), slip(3, 5)]), 5)


class WeightTest(TestCase):
	def test_the_weight_of_a_slip_in_its_unit(self):
		self.assertEqual(packing.weight(D("12.50"), "kg"), "12,5 kg")
		self.assertEqual(packing.weight(D(0), "kg"), "")
		self.assertEqual(packing.weight(D(3), ""), "")

	def test_the_totals_add_up_the_slips_of_one_unit(self):
		slips = [slip(1, 1, D("10.5"), D(12)), slip(2, 3, D(20), D("22.5"))]
		self.assertEqual(packing.totals(slips), (D("30.5"), "kg", D("34.5"), "kg"))

	def test_a_total_needs_every_slip_weighed_in_one_unit(self):
		mixed = [slip(1, 1, D(10), D(12)), Slip("PK-2", 2, 2, D(1), "t", D(1), "t", True)]
		self.assertEqual(packing.totals(mixed), (None, "", None, ""))
		unweighed = [slip(1, 1, D(10), D(12)), slip(2, 2)]
		self.assertEqual(packing.totals(unweighed), (None, "", None, ""))

	def test_the_title_is_that_of_a_packing_list(self):
		self.assertEqual(packing.TITLE, "Packing List")
