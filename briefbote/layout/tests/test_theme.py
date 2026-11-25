from unittest import TestCase

from briefbote.layout import theme


class ColourTest(TestCase):
	def test_an_accent_is_a_hex_colour(self):
		self.assertEqual(theme.colour("#1caee5"), "#1CAEE5")
		self.assertEqual(theme.colour(" #1CAEE5 "), "#1CAEE5")
		self.assertEqual(theme.colour("#abc"), "#AABBCC")

	def test_anything_else_falls_back_to_black_so_that_no_css_slips_into_the_sheet(self):
		for value in (None, "", "red", "#12345", "#1CAEE5; } body { display: none", "url(x)"):
			with self.subTest(value=value):
				self.assertEqual(theme.colour(value), theme.BLACK)


class LogoTest(TestCase):
	def test_the_logo_stands_right_unless_left_is_chosen(self):
		self.assertEqual(theme.logo_side("Left"), "left")
		self.assertEqual(theme.logo_side("Right"), "right")
		self.assertEqual(theme.logo_side(None), "right")
		self.assertEqual(theme.logo_side("Middle"), "right")

	def test_the_height_of_the_logo_keeps_within_the_letterhead(self):
		self.assertEqual(theme.logo_height(18, letterhead=45, top=12), 18)
		self.assertEqual(theme.logo_height(40, letterhead=45, top=12), 29)
		self.assertEqual(theme.logo_height(None, letterhead=45, top=12), theme.LOGO_HEIGHT)
		self.assertEqual(theme.logo_height(0, letterhead=27, top=12), 11)
		self.assertEqual(theme.logo_height(3, letterhead=45, top=12), theme.LOGO_MINIMUM)


class FontTest(TestCase):
	def test_the_embedded_font_comes_first_and_the_system_stack_alone_where_chosen(self):
		self.assertTrue(theme.font_stack(theme.EMBEDDED).startswith('"Inter Tabular", '))
		self.assertFalse(theme.font_stack(theme.SYSTEM).startswith('"Inter'))
		self.assertTrue(theme.font_stack(None).startswith('"Inter Tabular"'))
		self.assertTrue(theme.embeds(theme.EMBEDDED))
		self.assertFalse(theme.embeds(theme.SYSTEM))


class TextColourTest(TestCase):
	"""Small text in the accent colour stays readable: WCAG 2.2 asks for a contrast of 4.5:1 against the paper."""

	def test_contrast_against_white(self):
		self.assertAlmostEqual(theme.contrast("#FFFFFF"), 1.0)
		self.assertAlmostEqual(theme.contrast("#000000"), 21.0)
		self.assertAlmostEqual(theme.contrast("#0B6E99"), 5.67, places=2)

	def test_a_dark_accent_is_its_own_text_colour(self):
		self.assertEqual(theme.text_colour("#0B6E99"), "#0B6E99")
		self.assertEqual(theme.text_colour("#111111"), "#111111")

	def test_a_light_accent_gives_small_text_a_darker_shade_of_its_hue(self):
		for accent in ("#1CAEE5", "#FFD400", "#7FA7C9", "#FFFFFF"):
			with self.subTest(accent=accent):
				text = theme.text_colour(accent)
				self.assertNotEqual(text, accent)
				self.assertGreaterEqual(theme.contrast(text), theme.READABLE)
		red, green, blue = (int(theme.text_colour("#1CAEE5")[i : i + 2], 16) for i in (1, 3, 5))
		self.assertLess(red, green)
		self.assertLess(green, blue)
