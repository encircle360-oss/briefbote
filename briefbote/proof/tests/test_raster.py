from unittest import TestCase

from briefbote.proof import raster
from briefbote.proof.raster import Area

# 25.4 dots per inch: one pixel is one millimetre.
DPI = 25.4


def pgm(width: int, height: int, dark: set[tuple[int, int]], comment: bool = False) -> bytes:
	pixels = bytes(0 if (x, y) in dark else 255 for y in range(height) for x in range(width))
	head = b"P5\n" + (b"# made by a test\n" if comment else b"") + f"{width} {height}\n255\n".encode()
	return head + pixels


class RasterTest(TestCase):
	def test_the_painted_rectangle_of_an_area(self):
		image = raster.read_pgm(pgm(20, 10, {(3, 2), (7, 5), (15, 1)}, comment=True), DPI)
		self.assertEqual(raster.painted(image, Area(0, 0, 10, 10)), Area(3, 2, 8, 6))
		self.assertEqual(raster.painted(image, Area(0, 0, 20, 10)), Area(3, 1, 16, 6))

	def test_a_blank_area_has_none(self):
		image = raster.read_pgm(pgm(20, 10, {(15, 1)}), DPI)
		self.assertIsNone(raster.painted(image, Area(0, 0, 10, 10)))

	def test_an_area_beyond_the_page_ends_at_its_edge(self):
		image = raster.read_pgm(pgm(4, 4, {(3, 3)}), DPI)
		self.assertEqual(raster.painted(image, Area(-5, -5, 50, 50)), Area(3, 3, 4, 4))

	def test_an_area_knows_its_size(self):
		self.assertEqual((Area(1, 2, 4, 8).width, Area(1, 2, 4, 8).height), (3, 6))

	def test_an_empty_or_cut_off_image_is_an_error_not_a_loop(self):
		for data in (b"", b"P5", b"P5\n10 10\n255\n" + b"\xff" * 5):
			with self.subTest(data=data[:12]), self.assertRaises(ValueError):
				raster.read_pgm(data, DPI)

	def test_only_a_binary_greyscale_image_reads(self):
		with self.assertRaises(ValueError):
			raster.read_pgm(b"P6\n1 1\n255\n\x00\x00\x00", DPI)
		with self.assertRaises(ValueError):
			raster.read_pgm(b"P5\n1 1\n65535\n\x00\x00", DPI)


class ShareTest(TestCase):
	def test_the_share_of_pixels_in_a_grey_range(self):
		image = raster.Raster(4, 1, DPI, bytes([0, 200, 220, 255]))
		self.assertEqual(raster.share(image, Area(0, 0, 4, 1), 180, 240), 0.5)

	def test_an_area_beyond_the_image_has_no_share(self):
		image = raster.Raster(1, 1, DPI, bytes([200]))
		self.assertEqual(raster.share(image, Area(5, 5, 9, 9), 180, 240), 0)


class RuleTest(TestCase):
	def test_the_first_row_that_runs_across_the_area(self):
		dark = {(x, 6) for x in range(2, 18)} | {(3, 2), (4, 2)}
		image = raster.read_pgm(pgm(20, 10, dark), DPI)
		self.assertEqual(raster.rule(image, Area(0, 0, 20, 10)), 6)

	def test_an_area_without_a_rule_has_none(self):
		image = raster.read_pgm(pgm(20, 10, {(3, 2)}), DPI)
		self.assertIsNone(raster.rule(image, Area(0, 0, 20, 10)))

	def test_the_lowest_painted_row(self):
		image = raster.read_pgm(pgm(20, 10, {(3, 2), (8, 7)}), DPI)
		self.assertEqual(raster.lowest(image, Area(0, 0, 20, 10)), 8)
		self.assertIsNone(raster.lowest(image, Area(10, 0, 20, 10)))

	def test_the_bands_of_painted_rows(self):
		dark = {(3, 1), (3, 2), (5, 5), (9, 8), (9, 9)}
		image = raster.read_pgm(pgm(20, 12, dark), DPI)
		self.assertEqual(raster.bands(image, Area(0, 0, 20, 12)), [(1, 3), (5, 6), (8, 10)])
		self.assertEqual(raster.bands(image, Area(10, 0, 20, 12)), [])


class StrokesTest(TestCase):
	def test_a_stroke_at_each_height_and_no_other(self):
		dark = {(x, 4) for x in range(1, 4)} | {(x, 9) for x in range(1, 6)}
		image = raster.read_pgm(pgm(10, 14, dark), DPI)
		self.assertEqual(raster.strokes(image, Area(0, 0, 10, 14), (4.5, 9.3), 0.6), ((), ()))

	def test_a_height_without_a_stroke_and_a_stroke_at_no_height(self):
		image = raster.read_pgm(pgm(10, 14, {(2, 4), (2, 12)}), DPI)
		self.assertEqual(raster.strokes(image, Area(0, 0, 10, 14), (4.5, 9.0), 0.6), ((9.0,), (12,)))

	def test_no_heights_ask_for_a_blank_strip(self):
		self.assertEqual(
			raster.strokes(raster.read_pgm(pgm(4, 4, set()), DPI), Area(0, 0, 4, 4), (), 0.6), ((), ())
		)
		image = raster.read_pgm(pgm(4, 4, {(1, 2)}), DPI)
		self.assertEqual(raster.strokes(image, Area(0, 0, 4, 4), (), 0.6), ((), (2,)))
