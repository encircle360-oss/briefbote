from unittest import TestCase

from briefbote.layout import din5008


class FormTest(TestCase):
	def test_form_b_puts_the_address_field_45_mm_from_the_top(self):
		form = din5008.FORMS["B"]
		self.assertEqual(
			(form.address.left, form.address.top, form.address.width, form.address.height), (20, 45, 85, 45)
		)
		self.assertEqual(form.letterhead_height, 45)
		self.assertEqual((form.information.left, form.information.top), (125, 50))
		self.assertEqual(form.fold_marks, (105, 210))

	def test_form_a_puts_the_address_field_27_mm_from_the_top(self):
		form = din5008.FORMS["A"]
		self.assertEqual(
			(form.address.left, form.address.top, form.address.width, form.address.height), (20, 27, 85, 45)
		)
		self.assertEqual(form.letterhead_height, 27)
		self.assertEqual((form.information.left, form.information.top), (125, 32))
		self.assertEqual(form.fold_marks, (87, 192))

	def test_the_address_field_has_five_lines_for_remarks_above_six_for_the_address(self):
		for name, form in din5008.FORMS.items():
			with self.subTest(form=name):
				self.assertEqual(form.remarks.top, form.address.top)
				self.assertEqual(form.remarks.height, din5008.REMARK_ZONE_HEIGHT)
				self.assertEqual(form.recipient.top, form.address.top + din5008.REMARK_ZONE_HEIGHT)
				self.assertEqual(form.recipient.bottom, form.address.bottom)
				self.assertEqual(form.recipient.height, din5008.ADDRESS_ZONE_HEIGHT)
				self.assertAlmostEqual(din5008.REMARK_ZONE_HEIGHT + din5008.ADDRESS_ZONE_HEIGHT, 45)

	def test_both_forms_share_the_punch_mark_and_the_text_margins(self):
		self.assertEqual(din5008.PUNCH_MARK, 148.5)
		self.assertEqual(din5008.PAGE, (210, 297))
		self.assertEqual((din5008.MARGIN_LEFT, din5008.MARGIN_RIGHT), (25, 20))
		self.assertEqual(din5008.TEXT_WIDTH, 165)

	def test_the_address_text_starts_where_the_body_text_starts(self):
		for name, form in din5008.FORMS.items():
			with self.subTest(form=name):
				self.assertEqual(form.address.left + din5008.ADDRESS_INSET, din5008.MARGIN_LEFT)

	def test_a_rectangle_knows_its_edges_and_what_lies_inside(self):
		box = din5008.Box(left=20, top=45, width=85, height=45)
		self.assertEqual((box.right, box.bottom), (105, 90))
		self.assertTrue(box.holds(20, 45, 105, 90))
		self.assertTrue(box.holds(30, 60, 80, 70))
		self.assertFalse(box.holds(19, 60, 80, 70))
		self.assertFalse(box.holds(30, 60, 106, 70))
		self.assertFalse(box.holds(30, 44, 80, 70))
		self.assertFalse(box.holds(30, 60, 80, 91))

	def test_a_rectangle_holds_what_reaches_over_its_edge_by_less_than_the_tolerance(self):
		box = din5008.Box(left=20, top=45, width=85, height=45)
		self.assertTrue(box.holds(19.8, 44.8, 105.2, 90.2, tolerance=0.3))
		self.assertFalse(box.holds(19.6, 50, 80, 70, tolerance=0.3))

	def test_a_form_is_named_by_its_letter_and_an_unknown_one_falls_back_to_form_b(self):
		self.assertIs(din5008.form("A"), din5008.FORMS["A"])
		self.assertIs(din5008.form("B"), din5008.FORMS["B"])
		self.assertIs(din5008.form(None), din5008.FORMS["B"])
		self.assertIs(din5008.form("Form A"), din5008.FORMS["A"])
