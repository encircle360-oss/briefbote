from datetime import date
from decimal import Decimal
from unittest import TestCase

from briefbote.sales import order
from briefbote.sales.order import Delivery, Term

D = Decimal
DEC_1 = date(2026, 12, 1)
DEC_15 = date(2026, 12, 15)


class DeliveryTest(TestCase):
	def test_one_date_for_every_position_is_the_date_of_the_order(self):
		self.assertEqual(
			order.delivery(DEC_15, [DEC_1, DEC_1, None]), Delivery(order.SCHEDULED_DELIVERY, (DEC_1,), False)
		)

	def test_positions_due_on_different_days_print_their_span_and_each_its_day(self):
		self.assertEqual(
			order.delivery(DEC_1, [DEC_15, DEC_1]),
			Delivery(order.SCHEDULED_DELIVERIES, (DEC_1, DEC_15), True),
		)

	def test_without_dates_of_the_positions_the_order_gives_its_own(self):
		self.assertEqual(order.delivery(DEC_1, []), Delivery(order.SCHEDULED_DELIVERY, (DEC_1,), False))

	def test_a_period_of_service_stands_for_the_dates_of_delivery(self):
		self.assertEqual(
			order.delivery(DEC_1, [DEC_1], (DEC_1, DEC_15)),
			Delivery(order.SERVICE_PERIOD, (DEC_1, DEC_15), False),
		)

	def test_an_order_without_any_date_names_none(self):
		self.assertIsNone(order.delivery(None, [None]))


class QuotationsTest(TestCase):
	def test_the_quotations_of_the_positions_count_once_in_their_order(self):
		self.assertEqual(
			order.quotations(["AN-2", "", "AN-1", "AN-2", None]),
			["AN-2", "AN-1"],
		)


class PaymentTermsTest(TestCase):
	def test_one_term_prints_its_description_or_name(self):
		self.assertEqual(
			order.payment_terms([Term(D(100), "1.190,00 €", "15.12.2026", "Netto 14", "14 Tage netto")]),
			[(order.PAYMENT_TERM, ("14 Tage netto",))],
		)
		self.assertEqual(
			order.payment_terms([Term(D(100), "1.190,00 €", "15.12.2026", "Netto 14", "")]),
			[(order.PAYMENT_TERM, ("Netto 14",))],
		)

	def test_one_term_without_a_text_prints_nothing_rather_than_an_empty_label(self):
		self.assertEqual(order.payment_terms([Term(D(100), "1.190,00 €", "15.12.2026", "", "")]), [])
		self.assertEqual(order.payment_terms([]), [])

	def test_several_terms_print_each_amount_with_its_text_or_its_day(self):
		terms = [
			Term(D(30), "357,00 €", "01.12.2026", "Anzahlung", "Anzahlung bei Auftrag"),
			Term(D(70), "833,00 €", "15.01.2027", "", ""),
		]
		self.assertEqual(
			order.payment_terms(terms),
			[
				(order.PAYMENT_TERMS, ()),
				(order.TERM_TEXT, ("357,00 €", "Anzahlung bei Auftrag")),
				(order.TERM_DUE, ("833,00 €", "15.01.2027")),
			],
		)

	def test_no_text_of_an_order_confirmation_asks_for_a_transfer(self):
		for text in (order.TITLE, order.PAYMENT_TERM, order.PAYMENT_TERMS, order.TERM_TEXT, order.TERM_DUE):
			with self.subTest(text=text):
				self.assertNotIn("transfer", text.lower())
				self.assertNotIn("invoice", text.lower())
