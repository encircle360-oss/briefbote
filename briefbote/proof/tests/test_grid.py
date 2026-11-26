from unittest import TestCase

from briefbote.proof import grid
from briefbote.proof.pages import MM
from briefbote.proof.raster import Area, Raster
from briefbote.proof.tests.test_pages import line, page, word


class AlignedTest(TestCase):
	def test_an_amount_that_ends_where_its_column_ends_is_aligned(self):
		head = [word("Betrag", 120, 50, 15), word("Offen", 160, 50, 15)]
		total = [
			word("Offene", 25, 70, 15),
			word("Rechnungen", 41, 70, 20),
			word("4.760,00", 159, 70, 10),
			word("€", 171, 70, 4),
		]
		self.assertEqual(grid.aligned([page(head, total)], "Offen", "Offene Rechnungen"), [])

	def test_an_amount_under_another_column_is_found(self):
		head = [word("Betrag", 120, 50, 15), word("Offen", 160, 50, 15)]
		total = [
			word("Offene", 25, 70, 15),
			word("Rechnungen", 41, 70, 20),
			word("4.760,00", 120, 70, 10),
			word("€", 131, 70, 4),
		]
		problems = grid.aligned([page(head, total)], "Offen", "Offene Rechnungen")
		self.assertEqual(len(problems), 1)
		self.assertIn("„Offene Rechnungen“", problems[0])

	def test_the_column_is_the_rightmost_word_of_its_name(self):
		"""A label of the sums may bear the name of the column it sums, as „Angerechnet“ does."""
		head = [word("Betrag", 120, 50, 15), word("Angerechnet", 160, 50, 15)]
		total = [word("Angerechnet", 25, 70, 20), word("1,00", 166, 70, 5), word("€", 171, 70, 4)]
		self.assertEqual(grid.aligned([page(total, head)], "Angerechnet", "Angerechnet"), [])

	def test_a_page_without_the_head_or_the_label_is_not_judged(self):
		self.assertEqual(
			grid.aligned([page(line("Offene Rechnungen 1,00 €", 25, 70))], "Offen", "Offene Rechnungen"), []
		)
		self.assertEqual(grid.aligned([page(word("Offen", 160, 50, 15))], "Offen", "Offene Rechnungen"), [])


class OneLineTest(TestCase):
	def test_a_text_that_stands_on_one_line_is_found(self):
		pages = [page(line("Unser Auftrag AB-1 vom 26.11.2026", 125, 50))]
		self.assertEqual(grid.on_one_line(pages, ("vom 26.11.2026",)), [])

	def test_a_text_broken_over_two_lines_is_a_problem(self):
		pages = [page(line("Unser Auftrag AB-1 vom", 125, 50), line("26.11.2026", 156, 55))]
		self.assertEqual(
			grid.on_one_line(pages, ("vom 26.11.2026",)), ["„vom 26.11.2026“ steht auf keiner Zeile ganz"]
		)


class SpaceAboveTest(TestCase):
	def test_the_head_of_a_table_keeps_its_distance_from_the_line_above(self):
		pages = [page(line("Bitte überweisen Sie", 25, 60), line("Rechnung Datum", 25, 68))]
		self.assertEqual(grid.space_above(pages, "Rechnung Datum", 4), [])

	def test_a_head_that_sits_on_the_line_above_is_a_problem(self):
		pages = [page(line("Bitte überweisen Sie", 25, 60), line("Rechnung Datum", 25, 64))]
		self.assertEqual(
			grid.space_above(pages, "Rechnung Datum", 4),
			["„Rechnung Datum“ steht 1,0 mm unter der Zeile darüber, mindestens 4 mm"],
		)

	def test_a_head_at_the_top_of_a_page_or_missing_is_not_judged(self):
		self.assertEqual(grid.space_above([page(line("Rechnung Datum", 25, 64))], "Rechnung Datum", 4), [])
		self.assertEqual(grid.space_above([page(line("Etwas", 25, 64))], "Rechnung Datum", 4), [])


class DarkestTest(TestCase):
	def test_the_darkest_pixel_of_an_area(self):
		pixels = bytes([255] * 100)
		pixels = pixels[:55] + bytes([90]) + pixels[56:]
		image = Raster(10, 10, 25.4, pixels)
		self.assertEqual(grid.darkest(image, Area(0, 0, 10, 10)), 90)
		self.assertEqual(grid.darkest(image, Area(0, 0, 3, 3)), 255)
		self.assertEqual(grid.darkest(image, Area(20, 20, 30, 30)), 255)

	def test_the_area_above_a_word_in_millimetres(self):
		found = grid.above(word("Datum", 25, 100, 20), 4)
		self.assertEqual(
			(round(found.left, 3), round(found.top, 3), round(found.right, 3), round(found.bottom, 3)),
			(25, 96, 45, 100),
		)
		self.assertEqual(MM, 72 / 25.4)


class DateBreakTest(TestCase):
	"""„vom“ or „of“ and the date after it stand on one line, in a heading as in the information block."""

	def test_a_line_that_ends_with_vom_before_a_date_is_found(self):
		pages = [page(line("Rücksendung zu WE-2026-0001 vom", 25, 50), line("20.11.2026", 25, 56))]
		self.assertEqual(
			grid.date_breaks(pages), ["Seite 1: „vom“ am Ende einer Zeile, „20.11.2026“ auf der nächsten"]
		)

	def test_the_english_of_counts_alike(self):
		pages = [page(line("Return to Goods Receipt WE-1 of", 25, 50), line("20.11.2026", 25, 56))]
		self.assertEqual(len(grid.date_breaks(pages)), 1)

	def test_vom_with_its_date_on_the_next_line_or_before_a_word_is_none(self):
		pages = [
			page(
				line("Rücksendung zu WE-2026-0001", 25, 50),
				line("vom 20.11.2026", 25, 56),
				line("Die Steuernummer vom", 25, 62),
				line("Finanzamt", 25, 68),
			)
		]
		self.assertEqual(grid.date_breaks(pages), [])
