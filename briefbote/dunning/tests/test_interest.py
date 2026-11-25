from datetime import date
from decimal import Decimal
from unittest import TestCase

from briefbote.dunning import interest
from briefbote.dunning.interest import BaseRate

D = Decimal
RATES = (
	BaseRate(date(2026, 1, 1), D("1.27")),
	BaseRate(date(2026, 7, 1), D("1.52")),
)


class BaseRateTest(TestCase):
	def test_the_rate_of_a_day_is_that_of_the_latest_row_before_it(self):
		self.assertEqual(interest.rate_on(RATES, date(2026, 6, 30)), D("1.27"))
		self.assertEqual(interest.rate_on(RATES, date(2026, 7, 1)), D("1.52"))
		self.assertIsNone(interest.rate_on(RATES, date(2025, 12, 31)))

	def test_a_table_covers_a_period_only_when_it_holds_the_rate_of_its_last_half_year(self):
		"""§ 247 Abs. 1 Satz 2 BGB: the base rate changes on 1 January and 1 July; a rate for a later half-year is
		known only once the Bundesbank publishes it."""
		self.assertTrue(interest.covers(RATES, date(2026, 1, 1), date(2026, 12, 31)))
		self.assertFalse(interest.covers(RATES, date(2026, 3, 1), date(2027, 1, 5)))
		self.assertFalse(interest.covers(RATES, date(2025, 12, 1), date(2026, 2, 1)))
		self.assertFalse(interest.covers((), date(2026, 3, 1), date(2026, 3, 2)))

	def test_the_published_rates_start_each_on_a_first_of_january_or_july(self):
		self.assertTrue(interest.PUBLISHED)
		for row in interest.PUBLISHED:
			with self.subTest(row=row):
				self.assertEqual((row.valid_from.day, row.valid_from.month in (1, 7)), (1, True))
		self.assertEqual(interest.PUBLISHED[-1], BaseRate(date(2026, 7, 1), D("1.52")))


class DefaultTest(TestCase):
	def test_a_reminder_after_the_due_date_puts_the_debtor_in_default_from_the_next_day(self):
		"""§ 286 Abs. 1 Satz 1 BGB."""
		self.assertEqual(
			interest.default_start(
				due=date(2026, 11, 3),
				issued=date(2026, 10, 20),
				consumer=True,
				notice=False,
				reminders=(date(2026, 11, 10),),
			),
			date(2026, 11, 11),
		)

	def test_a_reminder_on_or_before_the_due_date_counts_for_nothing(self):
		self.assertIsNone(
			interest.default_start(
				due=date(2026, 11, 3),
				issued=date(2026, 10, 20),
				consumer=True,
				notice=False,
				reminders=(date(2026, 11, 3),),
			)
		)

	def test_a_business_is_in_default_thirty_days_after_due_date_and_receipt(self):
		"""§ 286 Abs. 3 Satz 1 BGB, the day of the event not counted (§ 187 Abs. 1 BGB), the period ending with its
		last day (§ 188 Abs. 1 BGB): due on 18.05., the 30th day is 17.06., default from 18.06."""
		self.assertEqual(
			interest.default_start(
				due=date(2026, 5, 18), issued=date(2026, 5, 4), consumer=False, notice=False, reminders=()
			),
			date(2026, 6, 18),
		)

	def test_the_thirty_days_run_from_the_later_of_due_date_and_invoice(self):
		self.assertEqual(
			interest.default_start(
				due=date(2026, 5, 1), issued=date(2026, 5, 18), consumer=False, notice=False, reminders=()
			),
			date(2026, 6, 18),
		)

	def test_a_period_ending_on_a_weekend_ends_on_the_next_working_day(self):
		"""§ 193 BGB: the 30th day after 6.11.2026 is Sunday 6.12., so the period ends on Monday 7.12. and default
		begins on 8.12."""
		self.assertEqual(
			interest.default_start(
				due=date(2026, 11, 6), issued=date(2026, 11, 1), consumer=False, notice=False, reminders=()
			),
			date(2026, 12, 8),
		)

	def test_a_consumer_falls_into_default_by_the_thirty_days_only_where_the_invoice_said_so(self):
		"""§ 286 Abs. 3 Satz 1 Halbsatz 2 BGB."""
		kwargs = {"due": date(2026, 5, 18), "issued": date(2026, 5, 4), "consumer": True, "reminders": ()}
		self.assertIsNone(interest.default_start(notice=False, **kwargs))
		self.assertEqual(interest.default_start(notice=True, **kwargs), date(2026, 6, 18))

	def test_the_earlier_of_reminder_and_thirty_days_counts(self):
		self.assertEqual(
			interest.default_start(
				due=date(2026, 5, 18),
				issued=date(2026, 5, 4),
				consumer=False,
				notice=False,
				reminders=(date(2026, 7, 1), date(2026, 5, 25)),
			),
			date(2026, 5, 26),
		)


class InterestTest(TestCase):
	def test_a_business_owes_nine_points_above_the_base_rate_split_at_each_half_year(self):
		"""§ 288 Abs. 2 BGB: 1.000 € from 18.06. to 25.11.2026: 13 days at 10,27 % and 148 days at 10,52 %."""
		found = interest.lawful(D("1000"), date(2026, 6, 18), date(2026, 11, 25), RATES, consumer=False)
		expected = D("1000") * (D("10.27") * 13 + D("10.52") * 148) / 100 / 365
		self.assertEqual(found, expected)

	def test_a_consumer_owes_five_points_above_the_base_rate(self):
		"""§ 288 Abs. 1 Satz 2 BGB."""
		found = interest.lawful(D("365"), date(2026, 7, 1), date(2026, 7, 10), RATES, consumer=True)
		self.assertEqual(found, D("365") * D("6.52") * 10 / 100 / 365)

	def test_no_default_and_no_days_owe_nothing(self):
		self.assertEqual(interest.lawful(D(100), None, date(2026, 7, 10), RATES, consumer=False), D(0))
		self.assertEqual(
			interest.lawful(D(100), date(2026, 7, 11), date(2026, 7, 10), RATES, consumer=False), D(0)
		)

	def test_without_the_rate_of_every_day_the_interest_is_not_known(self):
		self.assertIsNone(
			interest.lawful(D(100), date(2025, 12, 1), date(2026, 1, 10), RATES, consumer=False)
		)
		self.assertIsNone(
			interest.lawful(D(100), date(2026, 12, 1), date(2027, 1, 10), RATES, consumer=False)
		)


class LumpSumTest(TestCase):
	def test_forty_euro_per_claim_in_default_and_only_from_a_business(self):
		"""§ 288 Abs. 5 Satz 1 BGB."""
		self.assertEqual(interest.lump_sum(consumer=False, in_default=2), D(80))
		self.assertEqual(interest.lump_sum(consumer=False, in_default=0), D(0))
		self.assertEqual(interest.lump_sum(consumer=True, in_default=2), D(0))
