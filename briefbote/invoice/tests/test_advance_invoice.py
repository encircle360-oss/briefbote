from datetime import date
from unittest import TestCase

from briefbote.invoice import advance_invoice

ISSUED = date(2026, 11, 23)


class ExpectedTest(TestCase):
	"""UStAE 14.8 Abs. 4 Satz 3 to 5: the expected time or calendar month of the supply instead of its time, the agreed
	period or deadline, or that none is agreed yet."""

	def test_the_period_of_the_order_is_the_expected_period(self):
		period = (date(2027, 1, 1), date(2027, 12, 31))
		self.assertEqual(
			advance_invoice.expected(period, date(2027, 1, 1), [date(2027, 1, 1)]),
			(advance_invoice.EXPECTED_PERIOD, period),
		)

	def test_the_days_of_the_positions_give_the_expected_day_or_span(self):
		self.assertEqual(
			advance_invoice.expected(None, date(2027, 2, 1), [date(2027, 1, 29), date(2027, 1, 29), None]),
			(advance_invoice.EXPECTED_DATE, (date(2027, 1, 29),)),
		)
		self.assertEqual(
			advance_invoice.expected(None, None, [date(2027, 1, 29), date(2027, 1, 8)]),
			(advance_invoice.EXPECTED_PERIOD, (date(2027, 1, 8), date(2027, 1, 29))),
		)

	def test_the_day_of_the_order_counts_where_no_position_has_one(self):
		self.assertEqual(
			advance_invoice.expected(None, date(2027, 2, 1), [None]),
			(advance_invoice.EXPECTED_DATE, (date(2027, 2, 1),)),
		)

	def test_without_any_day_the_invoice_says_that_none_is_agreed(self):
		self.assertIsNone(advance_invoice.expected(None, None, []))
		self.assertEqual(advance_invoice.notices(None), [advance_invoice.ADVANCE, advance_invoice.NOT_AGREED])
		self.assertEqual(
			advance_invoice.notices((advance_invoice.EXPECTED_DATE, (date(2027, 1, 1),))),
			[advance_invoice.ADVANCE],
		)


class ReceiptTest(TestCase):
	"""§ 14 Abs. 4 Satz 1 Nr. 6 UStG: the time of receipt, where it is certain and not the day of the invoice."""

	def test_a_payment_received_before_the_invoice_names_its_day(self):
		self.assertEqual(advance_invoice.received(ISSUED, [date(2026, 11, 20)]), date(2026, 11, 20))

	def test_no_payment_one_on_the_day_or_after_it_or_two_name_no_day(self):
		for days in ([], [ISSUED], [date(2026, 11, 27)], [date(2026, 11, 20), date(2026, 11, 21)]):
			with self.subTest(days=days):
				self.assertIsNone(advance_invoice.received(ISSUED, days))


class FindingsTest(TestCase):
	def test_an_advance_invoice_without_a_number_of_its_own_is_incomplete(self):
		"""§ 14 Abs. 4 Satz 1 Nr. 4 UStG: printed from the Sales Order itself it has only the number of the order."""
		self.assertEqual(advance_invoice.findings(numbered=False), [advance_invoice.NO_NUMBER])
		self.assertEqual(advance_invoice.findings(numbered=True), [])


class PaymentTest(TestCase):
	def test_a_numbered_advance_invoice_asks_for_its_total(self):
		self.assertEqual(
			advance_invoice.request(numbered=True, asks=True, account=True), advance_invoice.REQUEST
		)

	def test_no_request_without_number_account_or_as_draft_or_cancelled(self):
		for numbered, asks, account in ((False, True, True), (True, False, True), (True, True, False)):
			with self.subTest(numbered=numbered, asks=asks, account=account):
				self.assertEqual(advance_invoice.request(numbered=numbered, asks=asks, account=account), "")


class SubjectTest(TestCase):
	def test_the_subject_names_the_invoice_and_the_order_it_bills_in_advance(self):
		"""UStAE 14.8 Abs. 1 Satz 1: the invoice shows that it bills an advance."""
		self.assertEqual(
			advance_invoice.subject("AZ-2026-0001", "AB-2026-0004"),
			(advance_invoice.SUBJECT, ("AZ-2026-0001", "AB-2026-0004")),
		)
		self.assertEqual(
			advance_invoice.subject("", "AB-2026-0004"),
			(advance_invoice.SUBJECT_UNNUMBERED, ("AB-2026-0004",)),
		)
