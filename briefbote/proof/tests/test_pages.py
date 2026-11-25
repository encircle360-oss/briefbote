from unittest import TestCase

from briefbote.layout.din5008 import Box
from briefbote.proof import pages as checks
from briefbote.proof.pages import MM, Expectations, Margins, Page, Word

A4 = (595.28, 841.89)


def word(text: str, x_mm: float, y_mm: float, width_mm: float = 10, height_mm: float = 3) -> Word:
	return Word(x_mm * MM, y_mm * MM, (x_mm + width_mm) * MM, (y_mm + height_mm) * MM, text)


def line(text: str, x_mm: float, y_mm: float, width_mm: float = 10) -> list[Word]:
	"""The words of a text side by side on one line, each width_mm wide with 1 mm between them."""
	return [
		word(part, x_mm + index * (width_mm + 1), y_mm, width_mm) for index, part in enumerate(text.split())
	]


def page(*words) -> Page:
	flat = []
	for item in words:
		flat.extend(item if isinstance(item, list) else [item])
	return Page(*A4, tuple(flat))


def numbered(pages: list[Page]) -> list[Page]:
	total = len(pages)
	return [
		Page(p.width, p.height, (*p.words, *line(f"Seite {n} von {total}", 160, 285, 6)))
		for n, p in enumerate(pages, start=1)
	]


BBOX = """<html><body><doc>
<page width="595.276000" height="841.890000">
<word xMin="70.866000" yMin="85.039000" xMax="120.500000" yMax="95.000000">Beispiel</word>
<word xMin="122.000000" yMin="85.039000" xMax="150.000000" yMax="95.000000">GmbH &amp; Co.</word>
</page>
<page width="595.276000" height="841.890000">
</page>
</doc></body></html>"""


class ReadTest(TestCase):
	def test_reads_the_words_and_their_boxes_of_every_page(self):
		pages = checks.read_bbox(BBOX)
		self.assertEqual(len(pages), 2)
		self.assertEqual([w.text for w in pages[0].words], ["Beispiel", "GmbH & Co."])
		self.assertAlmostEqual(pages[0].words[0].x0, 70.866)
		self.assertEqual(pages[1].words, ())

	def test_groups_words_into_lines_by_their_baseline(self):
		p = page(line("zwei Wörter", 25, 50), word("unten", 25, 60), word("fast", 80, 50.3))
		self.assertEqual(
			[checks.text_of(row) for row in checks.lines(p.words)], ["zwei Wörter fast", "unten"]
		)


class PageCheckTest(TestCase):
	def test_counts_the_pages(self):
		self.assertEqual(checks.page_count([page()] * 2, 1, 3), [])
		self.assertEqual(checks.page_count([page()] * 4, 1, 3), ["4 Seiten statt 1 bis 3"])

	def test_each_page_names_itself_of_how_many(self):
		self.assertEqual(checks.page_numbers(numbered([page(), page()])), [])
		self.assertEqual(
			checks.page_numbers([page(line("Seite 1 von 2", 160, 285)), page()]),
			["Seite 2: keine Seitenzahl „Seite 2 von 2“"],
		)

	def test_a_page_in_english_names_itself_in_english(self):
		pages = [page(line("Page 1 of 2", 160, 285)), page(line("Page 2 of 2", 160, 285))]
		self.assertEqual(checks.page_numbers(pages, "Page {0} of {1}"), [])
		self.assertEqual(len(checks.page_numbers(pages)), 2)

	def test_finds_a_text_missing_from_a_page(self):
		pages = [page(line("RE-2026-0001", 25, 280)), page()]
		self.assertEqual(checks.on_every_page(pages, ("RE-2026-0001",)), ["Seite 2: „RE-2026-0001“ fehlt"])

	def test_finds_a_word_beyond_the_margins(self):
		margins = Margins(top=10, bottom=10, left=20, right=15)
		inside = page(word("innen", 25, 50, 20))
		outside = page(word("links", 5, 50), word("rechts", 190, 50, 10))
		self.assertEqual(checks.bleed([inside], margins), [])
		self.assertEqual(
			checks.bleed([outside], margins),
			["Seite 1: „links“ läuft über den Rand", "Seite 1: „rechts“ läuft über den Rand"],
		)

	def test_finds_two_words_printed_over_each_other(self):
		self.assertEqual(checks.overprint([page(word("eins", 25, 50, 10), word("zwei", 36, 50))]), [])
		self.assertEqual(
			checks.overprint([page(word("eins", 25, 50, 10), word("zwei", 30, 50))]),
			["Seite 1: „eins“ und „zwei“ überdecken sich"],
		)

	def test_finds_a_last_page_with_almost_nothing_on_it(self):
		margins = Margins(top=10, bottom=20, left=20, right=15)
		full = page(*[word(f"z{n}", 25, 20 + 5 * n) for n in range(6)])
		self.assertEqual(checks.last_page([full], margins, 4), [])
		self.assertEqual(checks.last_page([full, full], margins, 4), [])
		self.assertEqual(
			checks.last_page([full, page(word("Gruß", 25, 20))], margins, 4),
			["letzte Seite mit nur 1 Zeilen"],
		)

	def test_finds_two_texts_that_must_stand_on_one_page_apart(self):
		pages = [page(line("Pos. 40", 25, 200)), page(line("Gesamtbetrag 100,00", 25, 30))]
		self.assertEqual(checks.together(pages, [("Pos. 40", "Pos. 40")]), [])
		self.assertEqual(
			checks.together(pages, [("Pos. 40", "Gesamtbetrag")]),
			["„Pos. 40“ auf Seite 1, „Gesamtbetrag“ auf Seite 2"],
		)
		self.assertEqual(
			checks.together(pages, [("Pos. 41", "Gesamtbetrag")]), ["„Pos. 41“ oder „Gesamtbetrag“ fehlt"]
		)

	def test_finds_a_text_missing_from_the_printout_and_one_that_must_not_be_there(self):
		pages = [page(line("Rechnung RE-1", 25, 100))]
		self.assertEqual(checks.somewhere(pages, ("Rechnung",)), [])
		self.assertEqual(checks.somewhere(pages, ("Gutschrift",)), ["„Gutschrift“ fehlt im Ausdruck"])
		self.assertEqual(checks.nowhere(pages, ("Invoice",)), [])
		self.assertEqual(checks.nowhere(pages, ("Rechnung",)), ["Seite 1: „Rechnung“ im Ausdruck"])

	def test_the_table_head_repeats_on_every_page_the_table_runs_over(self):
		head = "Pos. Bezeichnung Menge"
		pages = [
			page(line(head, 25, 110), line("1 Beratung", 25, 120)),
			page(line(head, 25, 20), line("2 Beratung", 25, 30)),
			page(line("Gesamtbetrag", 25, 30)),
		]
		self.assertEqual(checks.head_repeated(pages, head, "Gesamtbetrag"), [])
		pages[1] = page(line("2 Beratung", 25, 30))
		self.assertEqual(
			checks.head_repeated(pages, head, "Gesamtbetrag"),
			["Seite 2: Tabellenkopf „Pos. Bezeichnung Menge“ fehlt"],
		)
		self.assertEqual(
			checks.head_repeated(pages, "Artikel", "Gesamtbetrag"), ["Tabellenkopf „Artikel“ fehlt"]
		)
		self.assertEqual(checks.head_repeated(pages, head, "Endbetrag"), ["„Endbetrag“ fehlt"])

	def test_the_address_stands_inside_the_window(self):
		window = Box(left=20, top=62.7, width=85, height=27.3)
		address = ("Beispiel GmbH", "Musterweg 1", "12345 Musterstadt")
		inside = page(
			line("Beispiel GmbH", 25, 64), line("Musterweg 1", 25, 69), line("12345 Musterstadt", 25, 74)
		)
		self.assertEqual(checks.in_window([inside], address, window), [])
		low = page(
			line("Beispiel GmbH", 25, 82), line("Musterweg 1", 25, 88), line("12345 Musterstadt", 25, 94)
		)
		self.assertEqual(
			checks.in_window([low], address, window),
			[
				"Anschrift „Musterweg 1“ außerhalb des Fensters",
				"Anschrift „12345 Musterstadt“ außerhalb des Fensters",
			],
		)
		self.assertEqual(
			checks.in_window([page(line("Beispiel GmbH", 25, 64))], address, window),
			["Anschrift „Musterweg 1“ fehlt auf Seite 1", "Anschrift „12345 Musterstadt“ fehlt auf Seite 1"],
		)

	def test_a_wrapped_address_line_is_found_beside_the_information_block(self):
		"""The information block stands on the same lines as the address; its words do not break the address."""
		window = Box(left=20, top=62.7, width=85, height=27.3)
		p = page(
			line("Holzbau und Innenausbau", 25, 64),
			line("Rechnungsnummer RE-1", 125, 64),
			line("Beteiligungsgesellschaft mbH", 25, 68.3),
			line("Rechnungsdatum 20.11.2026", 125, 68.3),
		)
		self.assertEqual(
			checks.in_window([p], ("Holzbau und Innenausbau Beteiligungsgesellschaft mbH",), window), []
		)

	def test_an_address_line_is_found_where_its_words_follow_each_other(self):
		p = page(line("Musterweg 1 und mehr", 25, 64), line("Musterweg 1", 25, 70))
		found = checks.find_line(p, "Musterweg 1")
		self.assertEqual([w.text for w in found], ["Musterweg", "1"])
		self.assertIsNone(checks.find_line(p, "Musterweg 2"))
		self.assertIsNone(checks.find_line(p, "   "))

	def test_an_address_line_may_wrap_onto_the_next_line(self):
		p = page(line("Holzbau und Innenausbau", 25, 64), line("Beteiligungsgesellschaft mbH", 25, 68.3))
		found = checks.find_line(p, "Innenausbau Beteiligungsgesellschaft")
		self.assertEqual([w.text for w in found], ["Innenausbau", "Beteiligungsgesellschaft"])


class CheckTest(TestCase):
	def test_a_clean_printout_has_no_problem(self):
		head = "Pos. Bezeichnung"
		window = Box(left=20, top=62.7, width=85, height=27.3)
		first = page(
			line("Beispiel GmbH", 25, 64),
			line("Rechnung RE-1", 25, 100),
			line(head, 25, 110),
			line("1 Beratung", 25, 120),
			line("Gesamtbetrag 119,00", 25, 130),
			line("RE-1", 25, 280),
		)
		expected = Expectations(
			pages=(1, 1),
			on_every_page=("RE-1",),
			together=(("1 Beratung", "Gesamtbetrag"),),
			somewhere=("Rechnung",),
			nowhere=("Invoice",),
			table_head=head,
			table_end="Gesamtbetrag",
			address=("Beispiel GmbH",),
			window=window,
			margins=Margins(top=10, bottom=10, left=20, right=15),
		)
		self.assertEqual(checks.check(numbered([first]), expected), [])

	def test_a_printout_without_table_or_address_skips_those_checks(self):
		expected = Expectations(pages=(1, 2))
		self.assertEqual(checks.check(numbered([page(line("Brief", 25, 100))]), expected), [])


class SectionTest(TestCase):
	TITLE = "Leistungsnachweis zur Rechnung RE-1"

	def test_a_section_starts_on_a_page_after_the_text_it_follows_and_names_itself_on_each_of_its_pages(self):
		pages = [
			page(line("Gesamtbetrag 100,00", 25, 100)),
			page(line(self.TITLE, 25, 20)),
			page(line(self.TITLE, 25, 20)),
		]
		self.assertEqual(checks.section(pages, self.TITLE, "Gesamtbetrag"), [])

	def test_finds_a_section_on_the_page_of_the_text_it_follows(self):
		pages = [page(line("Gesamtbetrag 100,00", 25, 100), line(self.TITLE, 25, 150))]
		self.assertEqual(
			checks.section(pages, self.TITLE, "Gesamtbetrag"),
			[f"„{self.TITLE}“ beginnt nicht auf einer neuen Seite nach „Gesamtbetrag“"],
		)

	def test_finds_a_page_of_the_section_without_its_name(self):
		pages = [
			page(line("Gesamtbetrag", 25, 100)),
			page(line(self.TITLE, 25, 20)),
			page(line("Summe", 25, 20)),
		]
		self.assertEqual(
			checks.section(pages, self.TITLE, "Gesamtbetrag"), [f"Seite 3: „{self.TITLE}“ fehlt"]
		)

	def test_finds_a_missing_section(self):
		self.assertEqual(
			checks.section([page(line("Gesamtbetrag", 25, 100))], self.TITLE, "Gesamtbetrag"),
			[f"„{self.TITLE}“ oder „Gesamtbetrag“ fehlt"],
		)

	def test_check_runs_the_section_check_when_expected(self):
		pages = numbered([page(line("Gesamtbetrag", 25, 100), line(self.TITLE, 25, 150))])
		expected = Expectations(pages=(1, 2), section=self.TITLE, section_after="Gesamtbetrag")
		self.assertEqual(
			checks.check(pages, expected),
			[f"„{self.TITLE}“ beginnt nicht auf einer neuen Seite nach „Gesamtbetrag“"],
		)


class KeptTest(TestCase):
	def test_a_block_stands_whole_on_the_page_of_its_first_line(self):
		pages = [
			page(line("Eintrag 1", 25, 100)),
			page(
				line("Stunden je Person", 25, 20), line("Erika 76,00", 25, 30), line("Summe 194,75", 25, 40)
			),
		]
		self.assertEqual(checks.kept(pages, ("Stunden je Person", "Erika 76,00", "Summe 194,75")), [])

	def test_finds_a_block_torn_over_two_pages(self):
		pages = [
			page(line("Stunden je Person", 25, 250), line("Erika 76,00", 25, 255)),
			page(line("Summe 194,75", 25, 20)),
		]
		self.assertEqual(
			checks.kept(pages, ("Stunden je Person", "Erika 76,00", "Summe 194,75")),
			["„Summe 194,75“ nicht auf Seite 1 bei „Stunden je Person“"],
		)

	def test_finds_a_block_without_its_first_line(self):
		self.assertEqual(checks.kept([page()], ("Stunden je Person",)), ["„Stunden je Person“ fehlt"])

	def test_check_keeps_the_block_when_expected(self):
		pages = numbered(
			[page(line("Kopf", 25, 20)), page(line("Fuß", 25, 20), line("x", 25, 40), line("y", 25, 50))]
		)
		expected = Expectations(pages=(1, 2), kept=("Kopf", "Fuß"), last_page_lines=1)
		self.assertEqual(checks.check(pages, expected), ["„Fuß“ nicht auf Seite 1 bei „Kopf“"])


class LabelGapTest(TestCase):
	def page(self, *words):
		return [Page(595, 842, tuple(Word(x0, 100, x1, 108, text) for x0, x1, text in words))]

	def test_a_label_stands_before_its_value_with_room_between(self):
		mm = MM
		found = self.page((350, 400, "Ihre"), (402, 430, "Bestellung"), (430 + 4 * mm, 470, "B-4711"))
		self.assertEqual(checks.label_gaps(found, (("Ihre Bestellung", "B-4711"),), 3), [])

	def test_a_long_value_may_continue_on_the_next_line(self):
		found = [
			Page(
				*A4,
				(
					Word(350, 100, 390, 108, "Rechnung"),
					Word(440, 100, 500, 108, "RE-1"),
					Word(505, 100, 520, 108, "vom"),
					Word(440, 112, 500, 120, "20.11.2026"),
				),
			)
		]
		self.assertEqual(checks.label_gaps(found, (("Rechnung", "RE-1 vom 20.11.2026"),), 3), [])

	def test_a_label_that_touches_its_value_is_a_problem(self):
		found = self.page((350, 430, "Rechnungsnummer"), (431, 470, "97201-016"))
		self.assertEqual(
			checks.label_gaps(found, (("Rechnungsnummer", "97201-016"),), 3),
			["„Rechnungsnummer“ steht 0.4 mm vor „97201-016“, weniger als 3 mm"],
		)

	def test_a_label_without_its_value_is_a_problem(self):
		found = self.page((350, 430, "Rechnungsnummer"))
		self.assertEqual(
			checks.label_gaps(found, (("Rechnungsnummer", "RE-1"), ("Ihre Steuernummer", "")), 3),
			["„Rechnungsnummer RE-1“ fehlt im Informationsblock", "„Ihre Steuernummer“ ohne Wert"],
		)
		self.assertEqual(
			checks.label_gaps([], (("Datum", "1.1."),), 3), ["„Datum 1.1.“ fehlt im Informationsblock"]
		)
