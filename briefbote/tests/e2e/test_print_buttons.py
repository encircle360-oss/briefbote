"""What a user gets who prints a document of Briefbote from the print view of the desk, by the buttons he sees.

„PDF“ downloads what the PDF generator of Frappe makes, which the proof of the printouts checks. „Drucken“ must give
the same document: the PDF of the generator, with its pages, „Seite n von N“ and the head of the table on each, not
the preview of the browser sliced into sheets. Who prints the page /printview with the browser's own print command
gets the fallback of the print stylesheet, which numbers the pages as well. The preview on the screen shows no page
line, which only a PDF can fill.
"""

import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote

from briefbote.proof import pages as checks

INVOICE_HEAD = "Pos. Bezeichnung Menge Einheit Einzelpreis USt. Betrag"
ANNEX_HEAD = "Datum Person Tätigkeit Projekt und Aufgabe Stunden"
DOCUMENTS = {
	# 40 positions at two rates over several pages.
	"RE-2026-0102": (INVOICE_HEAD, "Gesamtbetrag"),
	# An invoice with its Leistungsnachweis after it.
	"RE-2026-0114": (ANNEX_HEAD, "Summe der Stunden"),
}
DOWNLOAD = "frappe.utils.print_format.download_pdf"
PREVIEW = ".preview-beta-wrapper iframe"


def words(path: Path) -> list[checks.Page]:
	pdftotext = shutil.which("pdftotext") or "pdftotext"
	result = subprocess.run(  # noqa: S603 - Poppler on a PDF this test wrote
		[pdftotext, "-bbox", str(path), "-"], capture_output=True, text=True, check=True
	)
	return checks.read_bbox(result.stdout)


def compact(page: checks.Page) -> str:
	"""The text of a page without spaces: the headless Chromium of Playwright spaces some letters so that Poppler
	splits a word in two, „Leist ungspaket“."""
	return "".join(word.text for line in checks.lines(page.words) for word in line)


def problems_of(pages: list[checks.Page], name: str) -> list[str]:
	"""Each page names itself „Seite n von N“ with the document, and the head of the table stands on every page from
	the first to the one with the end of the table."""
	head, end = ("".join(text.split()) for text in DOCUMENTS[name])
	texts = [compact(page) for page in pages]
	found = [] if len(pages) > 1 else [f"{len(pages)} Seite statt mehrerer"]
	for number, text in enumerate(texts, start=1):
		if f"{name}·Seite{number}von{len(pages)}" not in text:
			found.append(f"Seite {number}: keine Seitenzeile „{name} · Seite {number} von {len(pages)}“")
	first = next((number for number, text in enumerate(texts, start=1) if head in text), None)
	last = next((number for number, text in enumerate(texts, start=1) if end in text), None)
	if first is None or last is None:
		return [*found, "Tabellenkopf oder Ende der Tabelle fehlt"]
	# The page that ends the table may hold only the block that is kept together, without the head.
	found += [
		f"Seite {number}: Tabellenkopf fehlt"
		for number in range(first, last)
		if head not in texts[number - 1]
	]
	return found


def open_print_view(page, name: str) -> None:
	"""The print view of the invoice with its default print format, Rechnung, once the preview shows it."""
	page.goto(f"/desk/print/Sales%20Invoice/{quote(name)}")
	page.frame_locator(PREVIEW).locator(".bb-subject").wait_for()


def test_print_prints_the_generated_pdf_of_the_invoice(page, output):
	opened: list[str] = []
	page.context.on("page", lambda popup: opened.append(popup.url))
	for name in DOCUMENTS:
		open_print_view(page, name)
		with page.expect_response(lambda response: DOWNLOAD in response.url) as answer:
			page.locator(".page-actions .primary-action").click()
		assert answer.value.ok, answer.value.status
		path = output / f"drucken__{name}.pdf"
		path.write_bytes(answer.value.body())
		problems = problems_of(words(path), name)
		assert not problems, f"{name}: " + "; ".join(problems)
		assert not opened, "Drucken opened a window instead of printing the PDF"


def test_the_browser_prints_the_page_with_numbered_pages(page, output):
	"""The fallback: the page /printview printed by Chromium itself, as Ctrl+P on it does."""
	for name in DOCUMENTS:
		page.goto(
			f"/printview?doctype=Sales%20Invoice&name={quote(name)}&format=Rechnung&no_letterhead=0&settings=%7B%7D"
			"&_lang=de"
		)
		page.locator(".bb-subject").wait_for()
		page.emulate_media(media="print")
		path = output / f"browser__{name}.pdf"
		path.write_bytes(page.pdf(prefer_css_page_size=True, print_background=True))
		problems = problems_of(words(path), name)
		assert not problems, f"{name}: " + "; ".join(problems)


def test_the_preview_shows_no_empty_page_line(page):
	open_print_view(page, "RE-2026-0102")
	assert not page.frame_locator(PREVIEW).locator(".bb-pageline").is_visible()


def test_the_preview_shows_the_letterhead_and_the_particulars(page):
	"""What a user looks at before printing: the logo and the particulars of the company, as on paper."""
	open_print_view(page, "RE-2026-0102")
	preview = page.frame_locator(PREVIEW)
	assert preview.locator(".bb-brand img").is_visible()
	assert preview.locator(".bb-particulars").get_by_text("Amtsgericht Musterstadt").is_visible()
