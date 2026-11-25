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


class SvgTest(TestCase):
	def test_the_mark_is_the_word_in_paths_rotated_about_the_middle(self):
		drawn = status.svg("Entwurf", 210, 249)
		self.assertTrue(drawn.startswith('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 210 249"'))
		self.assertEqual(drawn.count("<path "), 7)
		self.assertIn("rotate(-40 105.0 124.5)", drawn)
		self.assertIn('fill-opacity="0.14"', drawn)
		self.assertNotIn("<text", drawn)

	def test_a_letter_without_an_outline_leaves_its_room(self):
		self.assertEqual(status.svg("A-B", 210, 249).count("<path "), 2)
