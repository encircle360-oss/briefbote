"""The proof of the documents of sales, dunning, payment and purchase as PDF, with the checks of print_proof.py: each
case with both PDF generators on its papers, within the time limits of the proof, with the mark of a draft or a
cancelled document checked on the text layer, painted on the page and again after the conversion to PDF/A. The
modules print_proof_sales.py, print_proof_dunning.py, print_proof_payment.py, print_proof_purchase.py and
print_proof_goods.py hold the cases.
"""

import dataclasses
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import frappe
from frappe.model.docstatus import DocStatus
from frappe.translate import print_language

from briefbote.briefbote import printing
from briefbote.layout import theme
from briefbote.proof import grid, raster
from briefbote.proof import pages as checks
from briefbote.tests.print_proof import (
	ENGINES,
	ENGLISH,
	GERMAN_WORDS,
	LAST_PAGE_LINES,
	LIGATURES,
	MARGINS,
	MARKS,
	TOOL_SECONDS,
	UNMARKED,
	Case,
	expectations,
	fonts,
	mark_painted,
	marked_as_pdfa,
	render_in_time,
)

# The frames of the letters whose recipient is not the address of the document: the goods go to the shipping
# address, also those of a packing slip and those that go back to a supplier, a payment has no address of its own,
# a request for quotation goes to the supplier it is printed for, a business letter has an address and a contact of
# its own.
FRAMES = {
	"Business Letter": "briefbote.briefbote.correspondence.briefbote_business_letter_frame",
	"Delivery Note": "briefbote.briefbote.sales.briefbote_delivery_letter",
	"Packing Slip": "briefbote.briefbote.sales.briefbote_packing_letter",
	"Payment Entry": "briefbote.briefbote.receipt.briefbote_payment_letter",
	"Purchase Receipt": "briefbote.briefbote.purchase.briefbote_return_letter",
	"Request for Quotation": "briefbote.briefbote.purchase.briefbote_request_letter",
}

type Expected = Callable[[object, Case, bool], checks.Expectations]

# A rule or line that must be visible is at least this dark (0 black, 255 white) at RULE_DPI: the light grey that
# wkhtmltopdf paints a thin line in is not.
RULE_GREY = 150
RULE_DPI = 150
# How far above its label a line to sign on stands, in millimetres.
RULE_BAND = 4


@dataclass(frozen=True)
class Layout:
	"""What a document of the proof must show beyond the checks of print_proof.py: amounts that end where the column
	they sum ends (head, label of the line), texts that never break over two lines, the least distance in millimetres
	of the head of its table from the line above, and the labels under lines to sign on, which must be painted."""

	aligned: tuple[tuple[str, str], ...] = ()
	one_line: tuple[str, ...] = ()
	space_above: tuple[str, float] | None = None
	rules_above: tuple[str, ...] = ()


def rules_painted(path: Path, pages, labels) -> list[str]:
	"""Each line to sign on above its label is painted dark enough to see, on every page that has the label."""
	pdftoppm = shutil.which("pdftoppm") or "pdftoppm"
	problems = []
	for number, page in enumerate(pages, start=1):
		words = [word for word in page.words if word.text in labels]
		if not words:
			continue
		root = path.parent / f"{path.stem}-rules-{number}"
		subprocess.run(  # noqa: S603 - Poppler on a PDF this run wrote
			[
				pdftoppm,
				"-r",
				str(RULE_DPI),
				"-gray",
				"-f",
				str(number),
				"-l",
				str(number),
				"-singlefile",
				str(path),
				str(root),
			],
			capture_output=True,
			check=True,
			timeout=TOOL_SECONDS,
		)
		pgm = path.parent / f"{root.name}.pgm"
		image = raster.read_pgm(pgm.read_bytes(), RULE_DPI)
		pgm.unlink()
		for word in words:
			grey = grid.darkest(image, grid.above(word, RULE_BAND))
			if grey > RULE_GREY:
				problems.append(
					f"Seite {number}: die Linie über „{word.text}“ ist kaum sichtbar (Grau {grey})"
				)
	return problems


def company_of(doc) -> str:
	"""The company of the document, or of the delivery note of a packing slip, which has none of its own."""
	if doc.get("company"):
		return doc.company
	return frappe.db.get_value("Delivery Note", doc.delivery_note, "company")


def letter_of(doc, own_paper: bool) -> dict:
	"""The frame the print format of the document sets."""
	frame = frappe.get_attr(FRAMES[doc.doctype]) if doc.doctype in FRAMES else printing.briefbote_letter
	return frame(doc, 0 if own_paper else 1)


def with_positions(doc, case: Case, own_paper: bool) -> checks.Expectations:
	"""The expectations of print_proof.py for a document with positions, with the address of its frame and the
	head of its own table."""
	return dataclasses.replace(
		expectations(doc, case, own_paper),
		address=tuple(letter_of(doc, own_paper)["recipient"]),
		**({"table_head": case.table_head} if case.table_head else {}),
	)


def listing(doc, case: Case, own_paper: bool) -> checks.Expectations:
	"""The expectations of a document without positions, whose table lists other documents and ends with its sum:
	a Mahnung, a Zahlungsbestätigung."""
	letter = letter_of(doc, own_paper)
	english = case.language == "en"
	return checks.Expectations(
		pages=case.pages,
		on_every_page=(
			f"{doc.name} · {'Page' if english else 'Seite'}" if case.docstatus is None else doc.name,
		),
		somewhere=(doc.name, *case.somewhere, *(case.particulars if own_paper else ())),
		nowhere=(
			*(GERMAN_WORDS if english else ENGLISH),
			*LIGATURES,
			*case.nowhere,
			*(() if case.docstatus is not None else UNMARKED),
		),
		page_label="Page {0} of {1}" if english else "Seite {0} von {1}",
		table_head=case.table_head,
		table_end=case.total,
		address=tuple(letter["recipient"]),
		window=letter["form"].recipient,
		margins=MARGINS,
		last_page_lines=LAST_PAGE_LINES,
		kept=case.kept,
	)


def proof(
	out: Path,
	stem: str,
	doc,
	case: Case,
	paper: str,
	engine: str,
	expected: Expected,
	layout: Layout = Layout(),
) -> tuple[list[str], int]:
	own_paper = paper == "eigenes-papier"
	try:
		pdf = render_in_time(doc, case.print_format, engine, own_paper, out / f"{stem}.html")
	except Exception as error:
		return [f"nicht gedruckt: {error}"], 0
	path = out / f"{stem}.pdf"
	path.write_bytes(pdf)
	pdftotext = shutil.which("pdftotext") or "pdftotext"
	words = subprocess.run(  # noqa: S603 - Poppler on a PDF this run wrote
		[pdftotext, "-bbox", str(path), "-"], capture_output=True, text=True, check=True, timeout=TOOL_SECONDS
	)
	(out / f"{stem}.bbox.html").write_text(words.stdout, encoding="utf-8")
	pages = checks.read_bbox(words.stdout)
	problems = checks.check(checks.without_mark(pages), expected(doc, case, own_paper))
	problems += fonts(path, theme.embeds(printing.settings(company_of(doc)).get("font")))
	bare = checks.without_mark(pages)
	for head, label in layout.aligned:
		problems += grid.aligned(bare, head, label)
	problems += grid.on_one_line(bare, layout.one_line)
	if layout.space_above:
		problems += grid.space_above(bare, *layout.space_above)
	if layout.rules_above:
		problems += rules_painted(path, bare, layout.rules_above)
	letter = letter_of(doc, own_paper)
	if letter["return_address"]:
		problems += [
			problem.replace("Anschrift", "Rücksendeangabe")
			for problem in checks.in_window(pages, tuple(letter["return_address"]), letter["form"].remarks)
		]
	if case.docstatus is not None:
		# wkhtmltopdf repeats no fixed element: there the mark across stands on the first page, the framed mark in the
		# foot and the word in the page line on every page.
		problems += checks.marked(
			pages, *MARKS[(case.language, case.docstatus)], across_every_page=engine == "chrome"
		)
		problems += mark_painted(path, pages if engine == "chrome" else pages[:1])
		problems += [f"PDF/A: {problem}" for problem in marked_as_pdfa(path, case, engine)]
	return problems, len(pages)


def run_cases(
	directory: str, cases, heading: str, expected: Expected, layouts: dict[str, Layout] | None = None
) -> None:
	"""Each case with both generators on its papers, as a draft or cancelled document where the case says so; the
	report in the directory, a failed run on any problem."""
	out = Path(directory)
	out.mkdir(parents=True, exist_ok=True)
	# Frappe prints a cancelled document only where the Print Settings allow it; a draft by default.
	frappe.db.set_single_value("Print Settings", {"allow_print_for_draft": 1, "allow_print_for_cancelled": 1})
	report, failed = [heading, ""], False
	for case in cases:
		doc = frappe.get_doc(case.doctype, case.name)
		if case.docstatus is not None:
			doc.docstatus = DocStatus(case.docstatus)
		if case.for_supplier:
			doc.update_supplier_part_no(case.for_supplier)
		name = f"{case.name}-{case.variant}" if case.variant else case.name
		for paper in case.papers:
			for engine in ENGINES:
				stem = f"{case.print_format.lower()}__{name}__{case.language}__{paper}__{engine}"
				with print_language(case.language):
					problems, count = proof(
						out,
						stem,
						doc,
						case,
						paper,
						engine,
						expected,
						(layouts or {}).get(case.name, Layout()),
					)
				failed = failed or bool(problems)
				report.append(f"- {stem}: {count} Seiten{'' if not problems else ', ' + '; '.join(problems)}")
	(out / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
	sys.stdout.write("\n".join(report) + "\n")
	if failed:
		raise SystemExit("Ausdrucke mit Problemen, siehe report.md")
