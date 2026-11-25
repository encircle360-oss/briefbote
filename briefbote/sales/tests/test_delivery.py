from datetime import date
from decimal import Decimal
from unittest import TestCase

from briefbote.sales import delivery
from briefbote.sales.delivery import Batch

D = Decimal


class PricesTest(TestCase):
	def test_a_delivery_note_prints_prices_only_where_the_settings_ask_and_the_note_allows(self):
		self.assertFalse(delivery.prices(setting=False, without_amount=False))
		self.assertTrue(delivery.prices(setting=True, without_amount=False))
		self.assertFalse(delivery.prices(setting=True, without_amount=True))


class TitleTest(TestCase):
	def test_a_return_is_titled_as_such(self):
		self.assertEqual(delivery.title(False), delivery.TITLE)
		self.assertEqual(delivery.title(True), delivery.RETURN_TITLE)


class IdentifiersTest(TestCase):
	def test_serial_numbers_and_batches_print_as_lines_of_the_position(self):
		self.assertEqual(
			delivery.identifiers(["SN-2", "SN-1", "SN-2", ""], [Batch("CH-7", D(4)), Batch("CH-8", D(6))]),
			[
				(delivery.SERIAL_NUMBERS, ("SN-2, SN-1",)),
				(delivery.BATCHES, ("CH-7 (4), CH-8 (6)",)),
			],
		)

	def test_one_serial_number_and_one_batch_read_in_the_singular(self):
		self.assertEqual(
			delivery.identifiers(["SN-1"], [Batch("CH-7", D("2.5"))]),
			[(delivery.SERIAL_NUMBER, ("SN-1",)), (delivery.BATCH, ("CH-7",))],
		)

	def test_a_batch_named_twice_adds_its_quantities(self):
		self.assertEqual(
			delivery.identifiers([], [Batch("CH-7", D(1)), Batch("CH-7", D(2)), Batch("", D(5))]),
			[(delivery.BATCH, ("CH-7",))],
		)

	def test_a_position_without_any_prints_none(self):
		self.assertEqual(delivery.identifiers([], []), [])

	def test_the_serial_numbers_of_the_text_field_count_one_per_line(self):
		"""ERPNext keeps the serial numbers of a row without a bundle one per line (use_serial_batch_fields)."""
		self.assertEqual(delivery.split_serials("SN-1\nSN-2 \n\n"), ["SN-1", "SN-2"])
		self.assertEqual(delivery.split_serials(None), [])


class DatesTest(TestCase):
	def test_the_note_names_the_day_of_delivery_beside_its_own_date(self):
		"""UStAE 14.5 Abs. 16: an invoice may take the day of the supply from the delivery note it names only where the
		note states that day beside its own date."""
		day = date(2026, 11, 23)
		self.assertEqual(delivery.dates(day), [(delivery.DATE, day), (delivery.DELIVERY_DATE, day)])


class SignatureTest(TestCase):
	def test_only_a_submitted_note_asks_for_the_signature_of_the_recipient(self):
		self.assertTrue(delivery.asks_signature(setting=True, submitted=True))
		self.assertFalse(delivery.asks_signature(setting=True, submitted=False))
		self.assertFalse(delivery.asks_signature(setting=False, submitted=True))
