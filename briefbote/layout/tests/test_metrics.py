from decimal import Decimal
from unittest import TestCase

from briefbote.layout import metrics


class WidthTest(TestCase):
	def test_a_line_grows_with_its_text_and_its_size(self):
		short = metrics.width("Beispiel GmbH", Decimal(7))
		self.assertGreater(short, Decimal(15))
		self.assertLess(short, Decimal(25))
		self.assertAlmostEqual(metrics.width("Beispiel GmbH", Decimal(14)), short * 2, places=9)
		self.assertGreater(metrics.width("Beispiel GmbH · Musterweg 1", Decimal(7)), short)

	def test_a_character_the_font_lacks_counts_as_an_m(self):
		self.assertEqual(metrics.width("一", Decimal(7)), metrics.width("M", Decimal(7)))

	def test_nothing_has_no_width(self):
		self.assertEqual(metrics.width("", Decimal(7)), 0)
