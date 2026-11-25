"""Checks of a printout as PDF, on the words and their boxes that `pdftotext -bbox` of Poppler reads from each page.

A print format can look right in the preview of the browser and still break on paper: an address that slips out of
the window of the envelope, a table whose head is missing on the second page, totals torn from their positions, an
amount cut off at the edge, a last page with one line. These checks find what can be found without eyes. The module
imports no Frappe; the proof in CI (briefbote/tests/print_proof.py) renders the printouts and hands their words to it.
"""

import html
import itertools
import re
from dataclasses import dataclass, field

from briefbote.layout.din5008 import Box

# 1 mm in PDF points.
MM = 72 / 25.4
# Words whose baselines differ by less than this many points stand on the same line.
SAME_LINE = 2.0
# Two words on a line may touch; overlapping by more than this many points, one is printed over the other.
OVERPRINT = 0.8
# How far a word may reach into the margin before it counts as cut off or bleeding, in points.
BLEED = 1.0
# How far a word of the address may reach over the edge of the window, in millimetres.
WINDOW_TOLERANCE = 0.3

PAGE = re.compile(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', re.DOTALL)
WORD = re.compile(
	r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', re.DOTALL
)


@dataclass(frozen=True, slots=True)
class Word:
	x0: float
	y0: float
	x1: float
	y1: float
	text: str


@dataclass(frozen=True, slots=True)
class Page:
	width: float
	height: float
	words: tuple[Word, ...]


@dataclass(frozen=True, slots=True)
class Margins:
	"""The margins of the body of a page in millimetres; the running foot stands in the bottom one."""

	top: float
	bottom: float
	left: float
	right: float


@dataclass(frozen=True)
class Expectations:
	"""What a printout must hold: its pages, the texts on every page, the pairs of texts that must stand on the same
	page, the least number of lines of the body of a last page, texts it must hold somewhere, such as its mandatory
	particulars, and texts it must not hold anywhere; the head of its table, repeated on every page up to the text
	that ends the table; the lines of the address, inside the window of the envelope on the first page."""

	pages: tuple[int, int]
	on_every_page: tuple[str, ...] = ()
	together: tuple[tuple[str, str], ...] = ()
	last_page_lines: int = 4
	somewhere: tuple[str, ...] = ()
	nowhere: tuple[str, ...] = ()
	table_head: str = ""
	table_end: str = ""
	address: tuple[str, ...] = ()
	window: Box | None = None
	margins: Margins = field(default_factory=lambda: Margins(top=10, bottom=10, left=5, right=5))


def read_bbox(xhtml: str) -> list[Page]:
	"""The pages of the output of `pdftotext -bbox` with their words."""
	pages = []
	for width, height, content in PAGE.findall(xhtml):
		words = tuple(
			Word(float(x0), float(y0), float(x1), float(y1), html.unescape(text).strip())
			for x0, y0, x1, y1, text in WORD.findall(content)
		)
		pages.append(Page(float(width), float(height), words))
	return pages


def lines(words) -> list[list[Word]]:
	"""The words grouped into lines by their baseline, top to bottom, each line left to right."""
	result: list[list[Word]] = []
	for word in sorted(words, key=lambda word: (word.y1, word.x0)):
		if result and abs(result[-1][0].y1 - word.y1) < SAME_LINE:
			result[-1].append(word)
		else:
			result.append([word])
	return [sorted(line, key=lambda word: word.x0) for line in result]


def text_of(line) -> str:
	return " ".join(word.text for word in line)


def body(page: Page, margins: Margins) -> list[Word]:
	"""The words between the top margin and the running foot."""
	top, bottom = margins.top * MM, page.height - margins.bottom * MM
	return [word for word in page.words if word.y0 >= top - BLEED and word.y1 <= bottom + BLEED]


def page_text(page: Page) -> str:
	return " ".join(text_of(line) for line in lines(page.words))


def page_count(pages, low: int, high: int) -> list[str]:
	if low <= len(pages) <= high:
		return []
	return [f"{len(pages)} Seiten statt {low} bis {high}"]


def page_numbers(pages) -> list[str]:
	"""Each page names itself as „Seite n von N“."""
	total = len(pages)
	return [
		f"Seite {number}: keine Seitenzahl „Seite {number} von {total}“"
		for number, page in enumerate(pages, start=1)
		if f"Seite {number} von {total}" not in page_text(page)
	]


def on_every_page(pages, texts) -> list[str]:
	return [
		f"Seite {number}: „{text}“ fehlt"
		for number, page in enumerate(pages, start=1)
		for text in texts
		if " ".join(text.split()) not in page_text(page)
	]


def bleed(pages, margins: Margins) -> list[str]:
	"""No word starts left of the left margin or ends right of the right margin, where the paper or a printer cuts it."""
	problems = []
	for number, page in enumerate(pages, start=1):
		left, right = margins.left * MM - BLEED, page.width - margins.right * MM + BLEED
		problems += [
			f"Seite {number}: „{word.text}“ läuft über den Rand"
			for word in page.words
			if word.x0 < left or word.x1 > right
		]
	return problems


def overprint(pages) -> list[str]:
	"""No word on a line overlaps the next one, as an amount that runs into the text beside it does."""
	problems = []
	for number, page in enumerate(pages, start=1):
		for line in lines(page.words):
			problems += [
				f"Seite {number}: „{first.text}“ und „{second.text}“ überdecken sich"
				for first, second in itertools.pairwise(line)
				if second.x0 < first.x1 - OVERPRINT
			]
	return problems


def last_page(pages, margins: Margins, least: int) -> list[str]:
	"""A printout of more than one page does not end on a page with almost nothing on it."""
	if len(pages) < 2:
		return []
	count = len(lines(body(pages[-1], margins)))
	return [] if count >= least else [f"letzte Seite mit nur {count} Zeilen"]


def first_page_of(pages, text: str) -> int | None:
	wanted = " ".join(text.split())
	for number, page in enumerate(pages, start=1):
		if wanted in page_text(page):
			return number
	return None


def together(pages, pairs) -> list[str]:
	"""Each pair of texts, such as the last position and the total of the table, stands on the same page."""
	problems = []
	for first, second in pairs:
		one, other = first_page_of(pages, first), first_page_of(pages, second)
		if one is None or other is None:
			problems.append(f"„{first}“ oder „{second}“ fehlt")
		elif one != other:
			problems.append(f"„{first}“ auf Seite {one}, „{second}“ auf Seite {other}")
	return problems


def somewhere(pages, texts) -> list[str]:
	"""Each text stands on some page, such as a mandatory particular or a text in the language of the printout."""
	return [f"„{text}“ fehlt im Ausdruck" for text in texts if first_page_of(pages, text) is None]


def nowhere(pages, texts) -> list[str]:
	"""No text stands on any page as whole words, such as a word of the source language a missing translation falls
	back to."""
	return [
		f"Seite {number}: „{text}“ im Ausdruck"
		for text in texts
		for number, page in enumerate(pages, start=1)
		if f" {' '.join(text.split())} " in f" {page_text(page)} "
	]


def head_repeated(pages, head: str, end: str) -> list[str]:
	"""The head of a table stands on every page from the one it starts on to the one with the text that ends it."""
	start, stop = first_page_of(pages, head), first_page_of(pages, end)
	if start is None:
		return [f"Tabellenkopf „{head}“ fehlt"]
	if stop is None:
		return [f"„{end}“ fehlt"]
	return [
		f"Seite {number}: Tabellenkopf „{head}“ fehlt"
		for number in range(start + 1, stop)
		if " ".join(head.split()) not in page_text(pages[number - 1])
	]


def find_line(page: Page, text: str) -> list[Word] | None:
	"""The words of the page that read as the text, word by word in reading order, the first such run top to bottom;
	a run may wrap onto the next line, as a long name does in the address field."""
	wanted = text.split()
	if not wanted:
		return None
	words = [word for line in lines(page.words) for word in line]
	texts = [word.text for word in words]
	for start in range(len(texts) - len(wanted) + 1):
		if texts[start : start + len(wanted)] == wanted:
			return words[start : start + len(wanted)]
	return None


def in_window(pages, address, window: Box) -> list[str]:
	"""Each line of the address stands on the first page inside the window of the envelope."""
	problems = []
	for text in address:
		words = find_line(pages[0], text)
		if words is None:
			problems.append(f"Anschrift „{text}“ fehlt auf Seite 1")
			continue
		left, top = min(word.x0 for word in words) / MM, min(word.y0 for word in words) / MM
		right, bottom = max(word.x1 for word in words) / MM, max(word.y1 for word in words) / MM
		if not window.holds(left, top, right, bottom, WINDOW_TOLERANCE):
			problems.append(f"Anschrift „{text}“ außerhalb des Fensters")
	return problems


def check(pages, expected: Expectations) -> list[str]:
	"""Every problem of a printout, empty when it is clean."""
	margins = expected.margins
	problems = [
		*page_count(pages, *expected.pages),
		*page_numbers(pages),
		*on_every_page(pages, expected.on_every_page),
		*bleed(pages, margins),
		*overprint(pages),
		*last_page(pages, margins, expected.last_page_lines),
		*together(pages, expected.together),
		*somewhere(pages, expected.somewhere),
		*nowhere(pages, expected.nowhere),
	]
	if expected.table_head:
		problems += head_repeated(pages, expected.table_head, expected.table_end)
	if expected.window is not None:
		problems += in_window(pages, expected.address, expected.window)
	return problems
