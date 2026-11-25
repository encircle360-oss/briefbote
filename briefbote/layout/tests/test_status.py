from unittest import TestCase

from briefbote.layout import status


class StatusTest(TestCase):
	def test_a_draft_and_a_cancelled_document_carry_their_mark(self):
		self.assertEqual(status.of(True, 0), status.DRAFT)
		self.assertEqual(status.of(True, 2), status.CANCELLED)

	def test_a_submitted_document_carries_none(self):
		self.assertIsNone(status.of(True, 1))

	def test_a_document_that_is_never_submitted_carries_none(self):
		"""A DocType that is not submittable stays at docstatus 0; it has no draft."""
		self.assertIsNone(status.of(False, 0))

	def test_neither_draft_nor_cancelled_asks_for_payment(self):
		self.assertFalse(status.asks_for_payment(status.DRAFT))
		self.assertFalse(status.asks_for_payment(status.CANCELLED))
		self.assertTrue(status.asks_for_payment(None))

	def test_each_mark_has_its_word_for_the_page_and_for_the_page_line(self):
		self.assertEqual((status.DRAFT.mark, status.DRAFT.label), ("DRAFT", "Draft"))
		self.assertEqual((status.CANCELLED.mark, status.CANCELLED.label), ("CANCELLED", "Cancelled"))


class RepeatedTest(TestCase):
	def test_one_mark_for_each_page_of_a_document_laid_out_as_one_long_page(self):
		"""wkhtmltopdf lays a document out as one long page and cuts it into pages of the height of the sheet less
		its margins: 297 - 12 - 36 = 249 mm."""
		tops = status.repeated_tops(page=297, top=12, bottom=36, pages=3, offset=100)
		self.assertEqual(tops, [100, 349, 598])
