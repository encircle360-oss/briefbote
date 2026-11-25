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


def problems_of(pages: list[checks.Page], name: str) -> list[str]:
	head, end = DOCUMENTS[name]
	found = checks.page_numbers(pages)
	found += checks.on_every_page(pages, (f"{name} · Seite",))
	found += checks.head_repeated(pages, head, end)
	if len(pages) < 2:
		found.append(f"{len(pages)} Seite statt mehrerer")
	return found


def open_print_view(page, name: str) -> None:
	"""The print view of the invoice with its default print format, Rechnung, once the preview shows it."""
	page.goto(f"/desk/print/Sales%20Invoice/{quote(name)}")
	page.frame_locator(PREVIEW).locator(".bb-subject").wait_for()


def test_print_prints_the_generated_pdf_of_the_invoice(page, output):
	for name in DOCUMENTS:
		open_print_view(page, name)
		opened = []
		page.context.on("page", opened.append)
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
