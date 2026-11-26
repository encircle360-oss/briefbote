"""The proof of the print format Geschäftsbrief as PDF, for CI on a site with erpnext_germany: the letters of
print_documents_letters.py with both PDF generators, checked page by page with the checks of print_proof.py, and
measured on the pages rendered as images: the text stays in its type area and above the foot, a pasted letter prints
in the size and colour of the letter, an image stays within the width of the text.

	bench --site <site> execute briefbote.tests.print_proof_letters.run --kwargs "{'directory': '<directory>'}"
"""

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import frappe
from frappe.model.docstatus import DocStatus
from frappe.translate import print_language

from briefbote.briefbote import correspondence
from briefbote.proof import pages as checks
from briefbote.proof import raster
from briefbote.tests.print_proof import (
	ENGINES,
	ENGLISH,
	ENGLISH_PARTICULARS,
	GERMAN_WORDS,
	LAST_PAGE_LINES,
	LIGATURES,
	MARGINS,
	TOOL_SECONDS,
	UNMARKED,
	Case,
)
from briefbote.tests.proof_runner import proof

LETTER = {"doctype": "Business Letter", "print_format": "Geschäftsbrief"}
CLOSING = ("Mit freundlichen Grüßen", "Max Mustermann")
SECTIONS = ("1. Ausgangslage", "2. Vorgehen", "3. Leistungen im Einzelnen", "4. Termine", "5. Zusammenarbeit")
# Words a letter that prints an empty or missing subject would hold.
NO_SUBJECT = ("Betreff",)
INCOMPLETE = "Dieser Brief ist unvollständig"
# The text ends where the foot begins, 36 mm above the lower edge of the sheet (style.html), in millimetres.
TEXT_BOTTOM = 297 - 36 + 0.5
# Beside the type area, 25 mm from the left and 10 mm from the right edge, nothing is painted but the fold and punch
# marks at 4 to 11 mm; a pixel darker than INK is a letter or a line.
BESIDE = (raster.Area(12, 12, 24.4, TEXT_BOTTOM), raster.Area(200.6, 12, 210, TEXT_BOTTOM))
INK = 160
RASTER_DPI = 100
# A pasted letter prints in the colour of the text: no pixel of its body is coloured more than this, the difference
# between the strongest and the weakest of red, green and blue.
COLOURED = 60
# The words of a letter set in one size: their height differs by no more than this, in millimetres.
SIZE_TOLERANCE = 0.3


@dataclass(frozen=True)
class LetterCase(Case):
	"""A letter of the proof: beyond a Case, the pairs of texts on one page, such as a heading and the start of its
	text, and the words that must print in the size of a reference word."""

	together: tuple[tuple[str, str], ...] = ()
	sized: tuple[str, ...] = ()
	plain: bool = False


def german(name: str, pages=(1, 1), **fields) -> LetterCase:
	return LetterCase(name, pages, "", **LETTER, **fields)


CASES = (
	german(
		"GB-2026-0001",
		somewhere=("Ihre Anfrage zur Wartung", "Name Max Mustermann", "Sehr geehrte Frau Muster,", *CLOSING),
		nowhere=(INCOMPLETE,),
		kept=CLOSING,
		papers=("eigenes-papier", "briefpapier"),
	),
	german(
		"GB-2026-0002",
		pages=(3, 3),
		somewhere=(
			"1. Ausgangslage",
			"5. Zusammenarbeit",
			"Gespräche mit den Fachbereichen",
			"Nr. Leistung Umfang",
		),
		nowhere=(INCOMPLETE,),
		kept=("Wir freuen uns auf Ihre Rückmeldung.", *CLOSING),
		together=tuple((title, f"Zu Abschnitt {number}:") for number, title in enumerate(SECTIONS, start=1)),
	),
	german("GB-2026-0003", somewhere=("Erika Beispiel", "Ihr Termin am 3. Dezember"), nowhere=(INCOMPLETE,)),
	german("GB-2026-0004", somewhere=("ÖSTERREICH", "Max Beispielmann"), nowhere=(INCOMPLETE,)),
	german(
		"GB-2026-0005",
		somewhere=(
			"Ihre Rechnung RE-2026-0101",
			"Unser Zeichen",
			"Unser Zeichen Ausgangsrechnung",
			"RE-2026-0101",
			"{{ name }}",
			"Sehr geehrte Frau Muster,",
		),
		nowhere=(INCOMPLETE,),
	),
	LetterCase(
		"GB-2026-0006",
		(1, 1),
		"",
		somewhere=("Your enquiry", "UNITED STATES", "Name Max Mustermann", "Date", "Kind regards"),
		nowhere=("Datum", "Brief an"),
		language="en",
		particulars=ENGLISH_PARTICULARS,
		**LETTER,
	),
	german(
		"GB-2026-0007",
		somewhere=(
			"Rote Schrift in großer Schrift",
			"Gelb hinterlegt und riesig.",
			"Blau in einer Serifenschrift.",
		),
		nowhere=(INCOMPLETE,),
		sized=("Rote", "Gelb", "Blau", "Sehr", "letzter"),
		plain=True,
	),
	german("GB-2026-0008", somewhere=(INCOMPLETE, "Der Brief hat keinen Text."), nowhere=NO_SUBJECT),
	german(
		"GB-2026-0009",
		somewhere=(INCOMPLETE, "Der Brief hat keine Postanschrift des Empfängers"),
		nowhere=("Beispiel Handels KG",),
	),
	german(
		"GB-2026-0001",
		somewhere=("Ihre Anfrage zur Wartung", *CLOSING),
		kept=CLOSING,
		variant="entwurf",
		docstatus=0,
	),
	german(
		"GB-2026-0002",
		pages=(3, 3),
		somewhere=("5. Zusammenarbeit", *CLOSING),
		kept=("Wir freuen uns auf Ihre Rückmeldung.", *CLOSING),
		variant="storniert",
		docstatus=2,
	),
)


def expected(doc, case: LetterCase, own_paper: bool) -> checks.Expectations:
	english = case.language == "en"
	frame = correspondence.briefbote_business_letter_frame(doc, 0 if own_paper else 1)
	title = correspondence.briefbote_business_letter(doc)["running_title"]
	return checks.Expectations(
		pages=case.pages,
		on_every_page=(f"{title} · {'Page' if english else 'Seite'}" if case.docstatus is None else title,),
		together=case.together,
		somewhere=(*case.somewhere, *(case.particulars if own_paper else ())),
		nowhere=(
			*(GERMAN_WORDS if english else ENGLISH),
			*LIGATURES,
			*case.nowhere,
			*(() if case.docstatus is not None else UNMARKED),
		),
		page_label="Page {0} of {1}" if english else "Seite {0} von {1}",
		address=tuple(frame["recipient"]),
		window=frame["form"].recipient,
		margins=MARGINS,
		last_page_lines=LAST_PAGE_LINES,
		kept=case.kept,
	)


def _render(path: Path, page: int, colour: bool) -> Path:
	pdftoppm = shutil.which("pdftoppm") or "pdftoppm"
	root = path.parent / f"{path.stem}-letter-{page}"
	subprocess.run(  # noqa: S603 - Poppler on a PDF this run wrote
		[
			pdftoppm,
			"-r",
			str(RASTER_DPI),
			*(() if colour else ("-gray",)),
			"-f",
			str(page),
			"-l",
			str(page),
			"-singlefile",
			str(path),
			str(root),
		],
		capture_output=True,
		check=True,
		timeout=TOOL_SECONDS,
	)
	return path.parent / f"{root.name}.{'ppm' if colour else 'pgm'}"


def _box(image: raster.Raster, area: raster.Area) -> tuple[int, int, int, int]:
	scale = image.dpi / raster.INCH_MM
	return (
		max(int(area.left * scale), 0),
		max(int(area.top * scale), 0),
		min(int(area.right * scale), image.width),
		min(int(area.bottom * scale), image.height),
	)


def beside_the_text(path: Path, pages) -> list[str]:
	"""Nothing is painted left or right of the type area, measured on each page as an image."""
	problems = []
	for number in range(1, len(pages) + 1):
		pgm = _render(path, number, colour=False)
		image = raster.read_pgm(pgm.read_bytes(), RASTER_DPI)
		pgm.unlink()
		for area in BESIDE:
			left, top, right, bottom = _box(image, area)
			dark = sum(
				value < INK
				for y in range(top, bottom)
				for value in image.pixels[y * image.width + left : y * image.width + right]
			)
			if dark:
				problems.append(
					f"Seite {number}: {dark} Pixel außerhalb des Textbereichs ({area.left:g} bis {area.right:g} mm)"
				)
	return problems


def above_the_foot(pages, foot: set[str]) -> list[str]:
	"""Every word of the body ends above the foot: below TEXT_BOTTOM stand only the words of the foot, with the page
	numbers and the separators of its page line."""
	foot = foot | {"·"} | {str(number) for number in range(1, len(pages) + 1)}
	return [
		f"Seite {number}: „{word.text}“ reicht in den Fuß"
		for number, page in enumerate(pages, start=1)
		for word in page.words
		if word.y1 / checks.MM > TEXT_BOTTOM and word.text not in foot
	]


def foot_words(doc, case: LetterCase, own_paper: bool) -> set[str]:
	frame = correspondence.briefbote_business_letter_frame(doc, 0 if own_paper else 1)
	title = correspondence.briefbote_business_letter(doc)["running_title"]
	texts = [title, "Seite von Page of", frame["status_label"], frame["mark"]]
	texts += [line for block in frame["footer"] for line in block]
	return {word for text in texts for word in text.replace("\u00a0", " ").split()} | set(
		re.findall(r"\d+", " ".join(texts))
	)


def read_ppm(data: bytes) -> tuple[int, int, bytes]:
	head = re.match(rb"P6\s+(\d+)\s+(\d+)\s+255\s", data)
	if not head:
		raise ValueError("not a binary PPM with 8 bits a channel")
	return int(head.group(1)), int(head.group(2)), data[head.end() :]


def in_the_colour_of_the_text(path: Path, pages) -> list[str]:
	"""The body of a pasted letter is black or grey: no pixel below the subject is coloured."""
	problems = []
	for number in range(1, len(pages) + 1):
		ppm = _render(path, number, colour=True)
		width, height, pixels = read_ppm(ppm.read_bytes())
		ppm.unlink()
		scale = RASTER_DPI / raster.INCH_MM
		top, bottom = int(110 * scale), min(int(TEXT_BOTTOM * scale), height)
		left, right = int(25 * scale), int(200 * scale)
		strongest = 0
		for y in range(top, bottom):
			row = pixels[(y * width + left) * 3 : (y * width + right) * 3]
			for index in range(0, len(row), 3):
				red, green, blue = row[index], row[index + 1], row[index + 2]
				strongest = max(strongest, max(red, green, blue) - min(red, green, blue))
		if strongest > COLOURED:
			problems.append(f"Seite {number}: farbiger Text im Brief (Sättigung {strongest})")
	return problems


def in_one_size(pages, words: tuple[str, ...]) -> list[str]:
	"""The words print in one size: the height of each, read from the layer of text, is that of the first."""
	heights = {}
	for page in pages:
		for word in page.words:
			if word.text in words and word.text not in heights:
				heights[word.text] = (word.y1 - word.y0) / checks.MM
	missing = [word for word in words if word not in heights]
	if missing:
		return [f"„{word}“ fehlt" for word in missing]
	reference = heights[words[0]]
	return [
		f"„{word}“ ist {height:.2f} mm hoch statt {reference:.2f} mm wie „{words[0]}“"
		for word, height in heights.items()
		if abs(height - reference) > SIZE_TOLERANCE
	]


def run(directory: str) -> None:
	if not frappe.db.exists("DocType", "Business Letter"):
		raise SystemExit(
			"Der Nachweis des Geschäftsbriefs braucht erpnext_germany mit dem DocType Business Letter."
		)
	out = Path(directory)
	out.mkdir(parents=True, exist_ok=True)
	frappe.db.set_single_value("Print Settings", {"allow_print_for_draft": 1, "allow_print_for_cancelled": 1})
	report, failed = ["# Geschäftsbriefe als PDF", ""], False
	for case in CASES:
		doc = frappe.get_doc(case.doctype, case.name)
		if case.docstatus is not None:
			doc.docstatus = DocStatus(case.docstatus)
		name = f"{case.name}-{case.variant}" if case.variant else case.name
		for paper in case.papers:
			for engine in ENGINES:
				stem = f"geschäftsbrief__{name}__{case.language}__{paper}__{engine}"
				own_paper = paper == "eigenes-papier"
				with print_language(case.language):
					problems, count = proof(out, stem, doc, case, paper, engine, expected)
					path = out / f"{stem}.pdf"
					if path.exists():
						pages = checks.without_mark(
							checks.read_bbox((out / f"{stem}.bbox.html").read_text(encoding="utf-8"))
						)
						problems += above_the_foot(pages, foot_words(doc, case, own_paper))
						if case.docstatus is None:
							problems += beside_the_text(path, pages)
						if case.plain:
							problems += in_the_colour_of_the_text(path, pages)
						if case.sized:
							problems += in_one_size(pages, case.sized)
				failed = failed or bool(problems)
				report.append(f"- {stem}: {count} Seiten{'' if not problems else ', ' + '; '.join(problems)}")
	(out / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
	sys.stdout.write("\n".join(report) + "\n")
	if failed:
		raise SystemExit("Ausdrucke mit Problemen, siehe report.md")
