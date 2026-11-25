"""The fonts of the printouts, read without a bench: what scripts/build_fonts.py promises of them.

A font may replace letters by other glyphs through its OpenType features; a print format once printed „№“ for „Nr.“
that way. The subset keeps no feature that replaces a sequence of letters, and none of its substitutions yields the
numero sign. Its digits are of one width, so that amounts line up. The bench of the CI has no fontTools; there the
tests are skipped, the job without bench runs them.
"""

from pathlib import Path
from unittest import TestCase, skipUnless

try:
	from fontTools.ttLib import TTFont
except ImportError:  # pragma: no cover - the bench has no fontTools
	TTFont = None

FONTS = Path(__file__).resolve().parents[1] / "public" / "fonts"
NAMES = ("Inter-Regular.ttf", "Inter-SemiBold.ttf")
NUMERO = 0x2116
LIGATURE_FEATURES = {"liga", "dlig", "hlig", "ordn", "calt", "rlig", "frac"}


@skipUnless(TTFont, "fontTools is not installed")
class FontTest(TestCase):
	def fonts(self):
		return [(name, TTFont(FONTS / name)) for name in NAMES]

	def test_keeps_no_feature_that_replaces_letters_by_a_ligature(self):
		for name, font in self.fonts():
			with self.subTest(font=name):
				features = {record.FeatureTag for record in font["GSUB"].table.FeatureList.FeatureRecord}
				self.assertEqual(sorted(features & LIGATURE_FEATURES), [])

	def test_no_substitution_yields_the_numero_sign(self):
		for name, font in self.fonts():
			numero = font.getBestCmap().get(NUMERO)
			with self.subTest(font=name):
				for lookup in font["GSUB"].table.LookupList.Lookup:
					for table in lookup.SubTable:
						table = getattr(table, "ExtSubTable", table)
						targets = set(getattr(table, "mapping", {}).values())
						targets |= {
							ligature.LigGlyph
							for ligatures in getattr(table, "ligatures", {}).values()
							for ligature in ligatures
						}
						self.assertNotIn(numero, targets)

	def test_every_digit_has_the_same_width(self):
		for name, font in self.fonts():
			with self.subTest(font=name):
				cmap, metrics = font.getBestCmap(), font["hmtx"]
				self.assertEqual(len({metrics[cmap[ord(digit)]][0] for digit in "0123456789"}), 1)

	def test_the_licence_comes_with_the_fonts(self):
		self.assertIn("SIL OPEN FONT LICENSE Version 1.1", (FONTS / "OFL.txt").read_text(encoding="utf-8"))


@skipUnless(TTFont, "fontTools is not installed")
class WidthsTest(TestCase):
	def test_the_table_of_widths_is_that_of_the_regular_font(self):
		import json
		import sys

		sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
		import build_fonts

		table = json.loads(
			(FONTS.parents[1] / "layout" / "inter_regular_widths.json").read_text(encoding="utf-8")
		)
		self.assertEqual(table, build_fonts.widths(TTFont(FONTS / "Inter-Regular.ttf")))


@skipUnless(TTFont, "fontTools is not installed")
class CapitalsTest(TestCase):
	def test_the_outlines_of_the_capitals_are_those_of_the_semibold_font(self):
		import json
		import sys

		sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
		import build_fonts

		table = json.loads(
			(FONTS.parents[1] / "layout" / "inter_semibold_capitals.json").read_text(encoding="utf-8")
		)
		self.assertEqual(table, build_fonts.capitals(TTFont(FONTS / "Inter-SemiBold.ttf")))
