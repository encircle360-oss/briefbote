from unittest import TestCase

from briefbote.layout import theme
from briefbote.layout.theme import Block, Placement


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


BLOCKS = {
	Block.COMPANY: ["Beispiel GmbH", "Musterweg 1"],
	Block.REGISTER: ["Sitz: Musterstadt"],
	Block.TAXES: ["USt-IdNr.: DE123456789"],
	Block.BANK: ["IBAN DE02 1203 0000 0000 2020 51"],
}


class FooterTest(TestCase):
	def test_without_a_layout_each_block_is_a_column_in_its_order(self):
		self.assertEqual(
			theme.arrange(BLOCKS, ()),
			[
				["Beispiel GmbH", "Musterweg 1"],
				["Sitz: Musterstadt"],
				["USt-IdNr.: DE123456789"],
				["IBAN DE02 1203 0000 0000 2020 51"],
			],
		)

	def test_a_layout_stacks_blocks_in_the_columns_it_names(self):
		layout = (
			Placement(1, Block.COMPANY),
			Placement(2, Block.REGISTER),
			Placement(2, Block.TAXES),
			Placement(3, Block.BANK),
		)
		self.assertEqual(
			theme.arrange(BLOCKS, layout),
			[
				["Beispiel GmbH", "Musterweg 1"],
				["Sitz: Musterstadt", "USt-IdNr.: DE123456789"],
				["IBAN DE02 1203 0000 0000 2020 51"],
			],
		)

	def test_columns_follow_their_numbers_and_empty_ones_drop_out(self):
		layout = (Placement(3, Block.COMPANY), Placement(1, Block.BANK), Placement(2, Block.REGISTER))
		blocks = {**BLOCKS, Block.REGISTER: []}
		self.assertEqual(
			theme.arrange(blocks, layout),
			[["IBAN DE02 1203 0000 0000 2020 51"], ["Beispiel GmbH", "Musterweg 1"]],
		)

	def test_a_block_left_out_of_the_layout_is_not_printed(self):
		self.assertEqual(
			theme.arrange(BLOCKS, (Placement(1, Block.BANK),)), [["IBAN DE02 1203 0000 0000 2020 51"]]
		)

	def test_a_block_is_read_from_its_name(self):
		self.assertIs(theme.block("Bank Accounts"), Block.BANK)
		with self.assertRaises(ValueError):
			theme.block("Wetter")


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
