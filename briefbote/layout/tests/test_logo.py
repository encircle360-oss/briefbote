import base64
from decimal import Decimal
from unittest import TestCase

from briefbote.layout import logo

# 300 x 60 and 60 x 120 pixels.
JPEG = base64.b64decode(
	"/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGB"
	"YUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAA8"
	"ASwDAREAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAj/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAf/xA"
	"AUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCYlNTcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
	"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
	"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
	"AAAAAAAAAAAAAAAAAAAAAAB//9k="
)
PNG = base64.b64decode(
	"iVBORw0KGgoAAAANSUhEUgAAADwAAAB4CAIAAAAhVwZfAAAAgklEQVR4nO3OAQkAIBAAMZvYyD62N4b3MFiArX3uOOv7QDpMWlo6QFpaOkBaWj"
	"pAWlo6QFpaOkBaWjpAWlo6QFpaOkBaWjpAWlo6QFpaOkBaWjpAWlo6QFpaOkBaWjpAWlo6QFpaOkBaWjpAWlo6QFpaOkBaWjpAWlo6QFpaOmBk"
	"+gHEw0Y4ci4fwwAAAABJRU5ErkJggg=="
)
EXPORTED_SVG = b"""<?xml version="1.0" encoding="utf-8"?>
<!-- Generator: a drawing program -->
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
\t viewBox="34 36 532 228" enable-background="new 34 36 532 228" xml:space="preserve">
<path fill="#1CAEE5" d="M34 36h532v228H34z"/>
</svg>
"""


class SizeTest(TestCase):
	def test_png_and_jpeg_tell_their_pixels(self):
		self.assertEqual(logo.size(PNG), (Decimal(60), Decimal(120)))
		self.assertEqual(logo.size(JPEG), (Decimal(300), Decimal(60)))

	def test_an_svg_without_width_and_height_takes_its_view_box(self):
		self.assertEqual(logo.size(EXPORTED_SVG), (Decimal(532), Decimal(228)))

	def test_an_svg_with_width_and_height_takes_them_in_any_unit(self):
		self.assertEqual(
			logo.size(b'<svg xmlns="http://www.w3.org/2000/svg" width="240" height="64"/>'),
			(Decimal(240), Decimal(64)),
		)
		self.assertEqual(
			logo.size(b'<svg width="60mm" height="15.5mm" viewBox="0 0 1 1"/>'),
			(Decimal(60), Decimal("15.5")),
		)
		self.assertEqual(
			logo.size(b'<svg width="100%" height="100%" viewBox="0,0,400,100"/>'),
			(Decimal(400), Decimal(100)),
		)

	def test_what_has_no_usable_size_is_none(self):
		for content in (
			b"",
			b"GIF89a",
			b"<svg xmlns='http://www.w3.org/2000/svg'><path d='M0 0'/></svg>",
			b'<svg viewBox="0 0 0 10"/>',
			b'<svg viewBox="0 0 a b"/>',
			b"\xff\xd8" + b"\x00" * 12,
			b"\x89PNG\r\n\x1a\n" + b"\x00" * 8,
			b"\xff\xd8\xff\xd9",
			b"<html><body>not found</body></html>",
		):
			with self.subTest(content=content[:20]):
				self.assertIsNone(logo.size(content))


class CleanTest(TestCase):
	def test_an_exported_svg_loses_prolog_comment_and_doctype_and_gains_its_size(self):
		cleaned = logo.clean_svg(EXPORTED_SVG)
		self.assertTrue(cleaned.startswith(b"<svg "))
		self.assertNotIn(b"DOCTYPE", cleaned)
		self.assertNotIn(b"<!--", cleaned)
		self.assertIn(b' width="532" height="228"', cleaned)
		self.assertEqual(logo.size(cleaned), (Decimal(532), Decimal(228)))

	def test_what_is_no_svg_or_has_no_view_box_stays_as_it_is(self):
		self.assertEqual(logo.clean_svg(PNG), PNG)
		self.assertEqual(logo.clean_svg(b"<?xml?><svg><path/></svg>"), b"<svg><path/></svg>")

	def test_an_svg_with_its_size_keeps_it(self):
		svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="240" height="64"><rect/></svg>'
		self.assertEqual(logo.clean_svg(svg), svg)


class BoxTest(TestCase):
	def test_a_logo_takes_its_height_and_the_width_of_its_proportions(self):
		self.assertEqual(
			logo.box((Decimal(532), Decimal(228)), Decimal(24), Decimal(75)), (Decimal("56.0"), Decimal(24))
		)

	def test_a_wide_logo_never_grows_beyond_its_width_and_shrinks_in_height(self):
		self.assertEqual(
			logo.box((Decimal(1000), Decimal(100)), Decimal(24), Decimal(75)), (Decimal(75), Decimal("7.5"))
		)

	def test_a_tall_logo_keeps_its_height(self):
		self.assertEqual(
			logo.box((Decimal(60), Decimal(120)), Decimal(24), Decimal(75)), (Decimal("12.0"), Decimal(24))
		)
