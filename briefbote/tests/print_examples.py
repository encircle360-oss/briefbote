"""The examples of the README and of the pages of docs/: one printout of each print format and three that show more
than a plain page, printed from the documents and settings of the proof with the Chromium-based generator on blank
paper, as PDF and one page of it as PNG:

	bench --site <site> execute briefbote.tests.print_examples.run --kwargs "{'directory': '<directory>'}"

The directory receives docs/bilder/beispiele/<name>.png and docs/beispiele/<name>.pdf, as they stand in the
repository, and report.md. The run then compares them with the files of the repository and fails where one is missing
or differs: in its number of pages, in the words of its pages or in its picture. The Chromium of the runner changes
with its updates and draws the edges of letters a little differently each time, so the picture is compared coarsely,
in cells of CELL pixels, where a moved column or line shows and the edges of letters do not. To bring the files of the
repository up to date, unpack the artifact beispiele of the CI into the root of the repository.

The proof sets the dates of its documents, so a second run prints the same pages.
"""

import io
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import frappe
from frappe.model.docstatus import DocStatus
from frappe.translate import print_language
from PIL import Image, ImageChops, ImageStat

from briefbote.tests import print_documents as documents
from briefbote.tests import (
	print_proof,
	print_proof_dunning,
	print_proof_payment,
	print_proof_purchase,
	print_proof_sales,
)
from briefbote.tests.print_proof import TOOL_SECONDS, Case, render_in_time, settings_of

ENGINE = "chrome"
# About 115 dpi: an A4 page 951 pixels wide, legible when opened at full size.
DPI = 115
# Colours of a page after quantisation: the accent, the greys of text and lines and the edges of letters.
COLOURS = 64
PICTURES = Path("docs/bilder/beispiele")
PDFS = Path("docs/beispiele")
# The coarse comparison of two pictures: the mean of their difference in cells of CELL pixels, in grey levels, and
# the largest difference of one cell.
CELL = 8
MEAN_DIFFERENCE = 1.5
CELL_DIFFERENCE = 40


@dataclass(frozen=True)
class Example:
	"""A printout of the examples: its file name, the case of the proof it prints and the page it shows."""

	name: str
	cases: tuple[Case, ...]
	document: str
	print_format: str
	language: str = "de"
	variant: str = ""
	page: int = 1

	def case(self) -> Case:
		for case in self.cases:
			if (case.name, case.print_format, case.language, case.variant) == (
				self.document,
				self.print_format,
				self.language,
				self.variant,
			):
				return case
		raise LookupError(f"Kein Fall des Nachweises für {self.name}")


EXAMPLES = (
	Example("rechnung", print_proof.CASES, documents.EXAMPLE_INVOICE, "Rechnung"),
	Example("gutschrift", print_proof.CASES, "GS-2026-0001", "Gutschrift"),
	Example("leistungsnachweis", print_proof.CASES, "RE-2026-0114", "Leistungsnachweis"),
	Example("angebot", print_proof_sales.CASES, "AN-2026-0001", "Angebot"),
	Example("auftragsbestaetigung", print_proof_sales.CASES, "AB-2026-0001", "Auftragsbestätigung"),
	Example("lieferschein", print_proof_sales.CASES, "LS-2026-0001", "Lieferschein"),
	Example("mahnung", print_proof_dunning.CASES, "MZ-2026-0002", "Mahnung"),
	Example("zahlungsbestaetigung", print_proof_payment.CASES, "ZE-2026-0001", "Zahlungsbestätigung"),
	Example("quittung", print_proof_payment.CASES, "ZE-2026-0002", "Quittung"),
	Example("bestellung", print_proof_purchase.CASES, "BE-2026-0001", "Bestellung"),
	Example("rechnung-entwurf", print_proof.CASES, "RE-2026-0102", "Rechnung", variant="entwurf"),
	Example("rechnung-mehrseitig", print_proof.CASES, "RE-2026-0102", "Rechnung", page=2),
	Example("rechnung-englisch", print_proof.CASES, "RE-2026-0103", "Rechnung", language="en"),
)


def run(directory: str) -> None:
	out = Path(directory)
	for folder in (PICTURES, PDFS):
		(out / folder).mkdir(parents=True, exist_ok=True)
	# Frappe prints a draft only where the Print Settings allow it.
	frappe.db.set_single_value("Print Settings", "allow_print_for_draft", 1)
	repository = Path(frappe.get_app_path("briefbote")).parent
	report, failed = ["# Beispiele", ""], False
	for example in EXAMPLES:
		pdf, picture = print_example(example, out)
		problems = differences(repository, out, pdf, picture)
		failed = failed or bool(problems)
		report.append(f"- {example.name}: {'; '.join(problems) if problems else 'unverändert'}")
	(out / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
	sys.stdout.write("\n".join(report) + "\n")
	if failed:
		raise SystemExit(
			"Die Beispiele im Repository sind nicht die, die der Generator druckt; das Artifact beispiele hat die neuen."
		)


def print_example(example: Example, out: Path) -> tuple[Path, Path]:
	"""The PDF of the example and the picture of its page, in the directory as in the repository."""
	case = example.case()
	doc = frappe.get_doc(case.doctype, case.name)
	if case.docstatus is not None:
		doc.docstatus = DocStatus(case.docstatus)
	with print_language(case.language), settings_of(doc.company, case.settings):
		content = render_in_time(doc, case.print_format, ENGINE, True, out / f"{example.name}.html")
	pdf = PDFS / f"{example.name}.pdf"
	(out / pdf).write_bytes(content)
	picture = PICTURES / f"{example.name}.png"
	(out / picture).write_bytes(png(out / pdf, example.page))
	return pdf, picture


def png(pdf: Path, page: int) -> bytes:
	"""The page of the PDF at DPI, in COLOURS colours without dithering, so that a page of text stays small and its
	letters sharp."""
	pdftoppm = shutil.which("pdftoppm") or "pdftoppm"
	root = pdf.with_suffix("")
	subprocess.run(  # noqa: S603 - Poppler on a PDF this run wrote
		[
			pdftoppm,
			"-r",
			str(DPI),
			"-f",
			str(page),
			"-l",
			str(page),
			"-png",
			"-singlefile",
			str(pdf),
			str(root),
		],
		check=True,
		timeout=TOOL_SECONDS,
	)
	raster = root.with_suffix(".png")
	with Image.open(raster) as image:
		reduced = image.convert("RGB").quantize(
			COLOURS, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE
		)
	raster.unlink()
	buffer = io.BytesIO()
	reduced.save(buffer, format="PNG", optimize=True)
	return buffer.getvalue()


def differences(repository: Path, out: Path, pdf: Path, picture: Path) -> list[str]:
	"""What sets the printout of this run apart from the one in the repository: its absence, its number of pages, the
	words of its pages, its picture."""
	committed_pdf, committed_picture = repository / pdf, repository / picture
	if not committed_pdf.exists() or not committed_picture.exists():
		return ["fehlt im Repository"]
	new, old = words(out / pdf), words(committed_pdf)
	if len(new) != len(old):
		return [f"{len(new)} statt {len(old)} Seiten"]
	problems = [
		f"Seite {index}: andere Wörter"
		for index, (one, other) in enumerate(zip(new, old, strict=True), 1)
		if one != other
	]
	difference = coarse_difference(out / picture, committed_picture)
	if difference is None:
		problems.append("Bild in anderer Größe")
	elif difference[0] > MEAN_DIFFERENCE or difference[1] > CELL_DIFFERENCE:
		problems.append(f"Bild weicht ab (Mittel {difference[0]:.2f}, größte Zelle {difference[1]})")
	return problems


def words(pdf: Path) -> list[str]:
	"""The words of each page of the PDF, in the order Poppler reads them."""
	pdftotext = shutil.which("pdftotext") or "pdftotext"
	text = subprocess.run(  # noqa: S603 - Poppler on a PDF of the repository or of this run
		[pdftotext, str(pdf), "-"], capture_output=True, text=True, check=True, timeout=TOOL_SECONDS
	).stdout
	return [" ".join(page.split()) for page in text.split("\f")[:-1]]


def coarse_difference(first: Path, second: Path) -> tuple[float, int] | None:
	"""The mean and the largest difference of the two pictures in cells of CELL pixels, in grey levels; None where
	they differ in size."""
	images = [Image.open(path).convert("L") for path in (first, second)]
	if images[0].size != images[1].size:
		return None
	width, height = images[0].size
	cells = (max(1, width // CELL), max(1, height // CELL))
	small = [image.resize(cells, Image.Resampling.BOX) for image in images]
	difference = ImageChops.difference(*small)
	return ImageStat.Stat(difference).mean[0], difference.getextrema()[1]
