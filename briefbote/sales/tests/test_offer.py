from datetime import date
from decimal import Decimal
from unittest import TestCase

from briefbote.sales import offer
from briefbote.sales.offer import Line, Role, Row

D = Decimal


class LinesTest(TestCase):
	def test_an_alternative_stands_in_for_the_position_before_it(self):
		"""ERPNext keeps an alternative right after the position it may replace and leaves it out of the totals
		(set_has_alternative_item and filter_rows of ERPNext 16)."""
		rows = [
			Row("r1", 1),
			Row("r2", 2),
			Row("r3", 3, alternative=True),
			Row("r4", 4, alternative=True),
			Row("r5", 5),
		]
		self.assertEqual(
			offer.lines(rows),
			[
				Line("r1", Role.POSITION),
				Line("r2", Role.POSITION),
				Line("r3", Role.ALTERNATIVE, 2),
				Line("r4", Role.ALTERNATIVE, 2),
				Line("r5", Role.POSITION),
			],
		)

	def test_an_alternative_at_the_top_stands_in_for_no_position(self):
		self.assertEqual(offer.lines([Row("r1", 1, alternative=True)]), [Line("r1", Role.ALTERNATIVE)])

	def test_a_position_without_a_quantity_offers_a_unit_price(self):
		"""Selling Settings allow a quotation with a quantity of 0 (allow_zero_qty_in_quotation): a price for each
		unit, billed by the quantity actually supplied."""
		self.assertEqual(offer.lines([Row("r1", 1, quantity=D(0))]), [Line("r1", Role.UNIT_PRICE)])

	def test_only_a_position_counts_toward_the_totals(self):
		self.assertTrue(Line("r", Role.POSITION).counts)
		self.assertFalse(Line("r", Role.ALTERNATIVE, 1).counts)
		self.assertFalse(Line("r", Role.UNIT_PRICE).counts)

	def test_an_alternative_or_a_unit_price_says_that_the_total_leaves_it_out(self):
		self.assertEqual(offer.note(Line("r", Role.ALTERNATIVE, 2)), (offer.ALTERNATIVE, (2,)))
		self.assertEqual(offer.note(Line("r", Role.ALTERNATIVE)), (offer.ALTERNATIVE_ALONE, ()))
		self.assertEqual(offer.note(Line("r", Role.UNIT_PRICE)), (offer.UNIT_PRICE, ()))
		self.assertIsNone(offer.note(Line("r", Role.POSITION)))
		for text in (offer.ALTERNATIVE, offer.ALTERNATIVE_ALONE, offer.UNIT_PRICE):
			with self.subTest(text=text):
				self.assertIn("not included in the total", text)


class ClosingTest(TestCase):
	def test_a_quotation_with_a_deadline_names_it_for_validity_and_acceptance(self):
		"""§ 148 BGB: an offer with a deadline can only be accepted within it."""
		self.assertEqual(
			offer.closing(date(2026, 12, 18)), [(offer.VALID_UNTIL_ACCEPT, (date(2026, 12, 18),))]
		)

	def test_a_quotation_without_a_deadline_asks_for_acceptance_without_one(self):
		"""§ 147 Abs. 2 BGB: without a deadline the offer stands as long as an answer may be expected; no date is
		printed that the quotation does not have."""
		self.assertEqual(offer.closing(None), [(offer.ACCEPT, ())])
		self.assertNotIn("{0}", offer.ACCEPT)

	def test_no_text_of_a_quotation_asks_for_payment_or_calls_it_an_invoice(self):
		for text in (
			offer.TITLE,
			offer.VALID_UNTIL_ACCEPT,
			offer.ACCEPT,
			offer.UNIT_PRICE,
			offer.ALTERNATIVE,
		):
			with self.subTest(text=text):
				self.assertNotIn("invoice", text.lower())
				self.assertNotIn("transfer", text.lower())
