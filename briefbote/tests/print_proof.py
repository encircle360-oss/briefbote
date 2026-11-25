"""The proof of the print formats as PDF, for CI: every print format of the app, in German, with both PDF generators
Frappe offers, wkhtmltopdf and the Chromium-based one, for the documents of print_documents.py, on blank paper and on
pre-printed letter paper, then checked page by page (briefbote/proof/pages.py):

	bench --site <site> execute briefbote.tests.print_proof.run --kwargs "{'directory': '<directory>'}"

The step of the CI makes the URL of the site unreachable: a print format must load nothing. wkhtmltopdf gets the HTML
without the link to Frappe's print bundle, which Frappe adds to every print format and which Briefbote does not need;
any other address in the HTML fails the printout. The directory receives the PDFs, the words of their pages
(pdftotext -bbox) and report.md with the pages and the problems of each; the run fails when one has a problem.
"""

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import frappe
from frappe.translate import print_language
from frappe.utils.pdf import get_pdf

from briefbote.briefbote import printing
from briefbote.invoice import taxes
from briefbote.layout import theme
from briefbote.proof import pages as checks

LANGUAGE = "de"
ENGINES = ("wkhtmltopdf", "chrome")
TABLE_HEAD = "Pos. Bezeichnung Menge Einheit Einzelpreis Betrag"
TABLE_HEAD_WITH_RATE = "Pos. Bezeichnung Menge Einheit Einzelpreis USt. Betrag"
# Words only a printout that falls back to the English source holds.
ENGLISH = ("Invoice", "Amount", "Page", "Quantity", "Description", "Reverse charge:", "Total Amount")
# What a font that replaces letters by ligatures prints for „Nr.“.
LIGATURES = ("№",)
# The margins of the body: the information block reaches to 10 mm from the right edge, the fold marks carry no text.
MARGINS = checks.Margins(top=10, bottom=8, left=20, right=10)
LINK = re.compile(r'<link[^>]*rel="stylesheet"[^>]*>')
SCRIPT = re.compile(r"<script[^>]*\bsrc=[^>]*>\s*</script>")
# What makes a browser fetch something: a source, a stylesheet, a CSS address or import; data URLs fetch nothing.
FETCHED = re.compile(
	r"""\bsrc=["'](?!data:)[^"']+|<link\b[^>]*>|url\((?!data:)[^)]*\)|@import[^;]*""", re.IGNORECASE
)

# The particulars every invoice of the company Beispiel GmbH holds (§ 14 Abs. 4 Satz 1 Nr. 1 to 3 UStG, § 35a GmbHG).
# The columns of the footer stand side by side, so each particular is checked by words that stay on one line.
COMPANY_PARTICULARS = (
	"Beispiel GmbH",
	"Musterweg 1",
	"12345 Musterstadt",
	"USt-IdNr.: DE123456789",
	"12/345/67890",
	"Sitz: Musterstadt",
	"Amtsgericht Musterstadt,",
	"HRB 99999",
	"Geschäftsführer:",
	"Erika Mustermann",
	"Max Mustermann",
	"DE02 1203 0000 0000 2020 51",
)
RATE_19 = "Umsatzsteuer 19 % auf"


@dataclass(frozen=True)
class Case:
	"""A document of the proof: how many pages it may take, what it must hold and must not hold, and its total."""

	name: str
	pages: tuple[int, int]
	total: str
	somewhere: tuple[str, ...] = ()
	nowhere: tuple[str, ...] = ()
	papers: tuple[str, ...] = ("eigenes-papier",)
	particulars: tuple[str, ...] = COMPANY_PARTICULARS
	doctype: str = "Sales Invoice"
	print_format: str = "Rechnung"
	section: str = ""
	section_after: str = ""
	table_head: str = ""


CASES = (
	Case(
		"RE-2026-0101",
		(1, 1),
		"Gesamtbetrag",
		(
			"Rechnung RE-2026-0101",
			"Rechnungsdatum",
			"Leistungszeitraum",
			"01.11.2026 bis 30.11.2026",
			RATE_19,
			"Ihre Bestellung",
			"Fällig am",
			"Bitte überweisen Sie",
		),
		papers=("eigenes-papier", "briefpapier"),
	),
	Case(
		"RE-2026-0102",
		(2, 8),
		"Gesamtbetrag",
		("Rechnung RE-2026-0102", RATE_19, "Umsatzsteuer 7 % auf", "Leistungspaket 40"),
		papers=("eigenes-papier", "briefpapier"),
	),
	Case(
		"RE-2026-0103",
		(1, 2),
		"Gesamtbetrag",
		(
			"Steuerschuldnerschaft des Leistungsempfängers",
			"Reverse Charge",
			"Ihre USt-IdNr.",
			"ATU87654321",
			"Unsere USt-IdNr.",
			"DE123456789",
			"ÖSTERREICH",
		),
		(RATE_19,),
	),
	Case(
		"RE-2026-0104",
		(1, 1),
		"Gesamtbetrag",
		(
			"Steuerfreie innergemeinschaftliche Lieferung",
			"Ihre USt-IdNr.",
			"ATU12345678",
			"Unsere USt-IdNr.",
			"Leistungsdatum",
		),
		(RATE_19,),
	),
	Case(
		"RE-2026-0105",
		(1, 1),
		"Gesamtbetrag",
		(
			"Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge, § 13b UStG)",
			"05.10.2026 bis 13.11.2026",
		),
		(RATE_19, "Umsatzsteuer"),
	),
	Case("RE-2026-0106", (1, 1), "Gesamtbetrag", ("Steuerfreie Ausfuhrlieferung",), (RATE_19,)),
	Case(
		"RE-2026-0107",
		(1, 1),
		"Gesamtbetrag",
		("Im Inland nicht steuerbare Leistung",),
		(RATE_19, "steuerfrei"),
	),
	Case(
		"RE-2026-0108",
		(1, 1),
		"Gesamtbetrag",
		("Steuerfreie Leistung: § 4 Nr. 21 UStG (Unterrichtsleistungen)",),
		(RATE_19,),
	),
	Case(
		"RE-2026-0109",
		(1, 1),
		"Korrekturbetrag",
		(
			"Rechnungskorrektur RE-2026-0109 zur Rechnung RE-2026-0101 vom 20.11.2026",
			"RE-2026-0101 vom 20.11.2026",
			RATE_19,
		),
		("Fällig am", "Bitte überweisen Sie"),
	),
	Case(
		"RE-2026-0110",
		(1, 1),
		"Stornierter Betrag",
		("Stornorechnung RE-2026-0110 zur Rechnung RE-2026-0101 vom 20.11.2026",),
		("Fällig am", "Bitte überweisen Sie"),
	),
	Case(
		"RE-2026-0111",
		(1, 1),
		"Gutgeschriebener Betrag",
		("Kaufmännische Gutschrift RE-2026-0111", "keine Gutschrift im Sinne des § 14 Abs. 2 Satz 5 UStG"),
		("Fällig am",),
	),
	Case(
		"RE-2026-0112",
		(1, 1),
		"Gesamtbetrag",
		(
			"kommen Sie auch ohne Mahnung in Verzug (§ 286 Abs. 3 BGB)",
			"2 % Skonto bei Zahlung bis zum 27.11.2026",
		),
	),
	Case(
		"KB-2026-0001",
		(1, 1),
		"Gesamtbetrag",
		(
			"Gemäß § 19 UStG wird keine Umsatzsteuer berechnet",
			"Kleinbetrieb Beispiel",
			"Steuernummer: 98/765/43210",
		),
		("Umsatzsteuer 19 %",),
		particulars=(),
	),
	Case(
		"RE-2026-0113",
		(1, 1),
		"Gesamtbetrag",
		("Entgelt ohne Umsatzsteuer", "38,00 €", "Umsatzsteuer 19 % auf 876,00 €", "USt.", "0 %"),
	),
	Case(
		"GS-2026-0001",
		(1, 1),
		"Gesamtbetrag",
		(
			"Gutschrift GS-2026-0001",
			"Ihre Steuernummer 21/815/08150",
			"Umsatzsteuer 19 % auf 1.540,00 €",
			"Gutschriftsverfahren (§ 14 Abs. 2 Satz 5 UStG)",
			"überweisen wir",
		),
		("Vorsteuer",),
		doctype="Purchase Invoice",
		print_format="Gutschrift",
	),
	Case(
		"GS-2026-0002",
		(1, 1),
		"Gesamtbetrag",
		(
			"Gutschrift GS-2026-0002",
			"Steuerschuldnerschaft des Leistungsempfängers",
			"Ihre USt-IdNr. DE111111111",
		),
		("Vorsteuer", "Umsatzsteuer 19 %", "Umsatzsteuer 13b"),
		doctype="Purchase Invoice",
		print_format="Gutschrift",
	),
	Case(
		"GS-2026-0003",
		(1, 1),
		"Gesamtbetrag",
		(
			"Gutschrift GS-2026-0003",
			"Gemäß § 19 UStG wird keine Umsatzsteuer berechnet",
			"Ihre Steuernummer 31/999/00001",
		),
		("Vorsteuer", "Umsatzsteuer 19 %"),
		doctype="Purchase Invoice",
		print_format="Gutschrift",
	),
	Case(
		"GS-2026-0004",
		(1, 1),
		"Korrekturbetrag",
		("Korrektur der Gutschrift GS-2026-0004 zur Gutschrift GS-2026-0001 vom 20.11.2026",),
		("Vorsteuer", "überweisen wir"),
		doctype="Purchase Invoice",
		print_format="Gutschrift",
	),
	Case(
		"RE-2026-0114",
		(3, 8),
		"Summe der Stunden",
		(
			"Gesamtbetrag",
			"Anlage: Leistungsnachweis mit 194,75 Stunden.",
			"102,00",
			"Stunden je Projekt",
			"Stunden je Person",
			"Erika Mustermann",
			"Dr. Anna Beispiel",
			"Abgerechnet in Position 1, 2",
		),
		section="Leistungsnachweis zur Rechnung RE-2026-0114 vom 20.11.2026",
		section_after="Gesamtbetrag",
		table_head="Datum Person Tätigkeit Projekt und Aufgabe Stunden",
	),
	Case(
		"RE-2026-0114",
		(2, 6),
		"Summe der Stunden",
		(
			"Leistungsnachweis zur Rechnung RE-2026-0114 vom 20.11.2026",
			"Abgerechnet in Position 1, 2",
			"194,75",
		),
		("Gesamtbetrag", "Anlage: Leistungsnachweis"),
		print_format="Leistungsnachweis",
		table_head="Datum Person Tätigkeit Projekt und Aufgabe Stunden",
	),
)


def run(directory: str) -> None:
	"""Every printout in German, the language of the documents: German texts run longer than their English source,
	and the checks of margins and page breaks are only worth what the texts they measure are."""
	with print_language(LANGUAGE):
		if printing.t("Total Amount") == "Total Amount":
			raise SystemExit(
				"Die deutschen Übersetzungen von Briefbote fehlen, die Ausdrucke wären englisch."
			)
		proof_all(Path(directory))


def proof_all(out: Path) -> None:
	out.mkdir(parents=True, exist_ok=True)
	report, failed = ["# Ausdrucke als PDF", ""], False
	for case in CASES:
		doc = frappe.get_doc(case.doctype, case.name)
		for paper in case.papers:
			for engine in ENGINES:
				stem = f"{case.print_format.lower()}__{case.name}__{paper}__{engine}"
				problems, count = proof(out, stem, doc, case, paper, engine)
				failed = failed or bool(problems)
				report.append(f"- {stem}: {count} Seiten{'' if not problems else ', ' + '; '.join(problems)}")
	(out / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
	sys.stdout.write("\n".join(report) + "\n")
	if failed:
		raise SystemExit("Ausdrucke mit Problemen, siehe report.md")


def expectations(doc, case: Case, own_paper: bool) -> checks.Expectations:
	letter = printing.briefbote_letter(doc, 0 if own_paper else 1)
	form = letter["form"]
	positions = doc.items
	head = case.table_head or (
		TABLE_HEAD_WITH_RATE if taxes.shows_rates(printing.position_rates(doc)) else TABLE_HEAD
	)
	return checks.Expectations(
		pages=case.pages,
		on_every_page=(f"{doc.name} · Seite",),
		together=() if case.table_head else ((" ".join(positions[-1].item_name.split()[:2]), case.total),),
		somewhere=(
			doc.name,
			*case.somewhere,
			*(case.particulars if own_paper else ()),
		),
		nowhere=(*ENGLISH, *LIGATURES, *case.nowhere),
		table_head=head,
		table_end=case.total,
		address=tuple(letter["recipient"]),
		window=form.recipient,
		margins=MARGINS,
		last_page_lines=3,
		section=case.section,
		section_after=case.section_after,
	)


def proof(out: Path, stem: str, doc, case: Case, paper: str, engine: str) -> tuple[list[str], int]:
	own_paper = paper == "eigenes-papier"
	try:
		pdf = render(doc, case.print_format, engine, own_paper, out / f"{stem}.html")
	except Exception as error:
		return [f"nicht gedruckt: {error}"], 0
	path = out / f"{stem}.pdf"
	path.write_bytes(pdf)
	pdftotext = shutil.which("pdftotext") or "pdftotext"
	words = subprocess.run(  # noqa: S603 - Poppler on a PDF this run wrote
		[pdftotext, "-bbox", str(path), "-"], capture_output=True, text=True, check=True
	)
	(out / f"{stem}.bbox.html").write_text(words.stdout, encoding="utf-8")
	pages = checks.read_bbox(words.stdout)
	problems = checks.check(pages, expectations(doc, case, own_paper))
	problems += fonts(path, theme.embeds(printing.settings(doc.company).get("font")))
	problems += hours_billed(doc)
	letter = printing.briefbote_letter(doc, 0 if own_paper else 1)
	if letter["return_address"]:
		problems += [
			problem.replace("Anschrift", "Rücksendeangabe")
			for problem in checks.in_window(pages, (letter["return_address"],), letter["form"].remarks)
		]
	return problems, len(pages)


def hours_billed(doc) -> list[str]:
	"""The hours of the timesheets of an invoice equal the quantity of its positions in the unit of time."""
	if doc.doctype != "Sales Invoice" or not doc.get("timesheets"):
		return []
	unit = printing.settings(doc.company).get("time_unit")
	hours = sum(Decimal(str(row.billing_hours)) for row in doc.timesheets)
	billed = sum(Decimal(str(row.qty)) for row in doc.items if (row.uom or row.stock_uom) == unit)
	return (
		[]
		if abs(hours - billed) < Decimal("0.01")
		else [f"{hours} Stunden im Nachweis, {billed} abgerechnet"]
	)


def fonts(path: Path, embedded: bool) -> list[str]:
	"""The PDF sets its text in the embedded Inter and in no font of the system, or, where the theme of the company
	asks for the font of the system, in no Inter."""
	pdffonts = shutil.which("pdffonts") or "pdffonts"
	listed = subprocess.run(  # noqa: S603 - Poppler on a PDF this run wrote
		[pdffonts, str(path)], capture_output=True, text=True, check=True
	).stdout.splitlines()[2:]
	names = sorted({line.split()[0].split("+")[-1] for line in listed if line.strip()})
	if not embedded:
		return [
			f"Schrift {name} statt der Schrift des Systems" for name in names if name.startswith("Inter-")
		]
	others = [name for name in names if not name.startswith("Inter-")]
	return [f"Schrift {name} statt Inter" for name in others] if others or not names else []


def render(doc, print_format: str, engine: str, own_paper: bool, keep: Path | None = None) -> bytes:
	"""The PDF of a document with one of the engines of Frappe. The Chromium-based one takes the assets of the bench
	from disk. wkhtmltopdf would fetch Frappe's print bundle from the URL of the site, which the step of the CI makes
	unreachable; it gets the HTML without that link and fails on any other address the print format would load."""
	no_letterhead = 0 if own_paper else 1
	if engine == "chrome":
		return frappe.get_print(
			doc.doctype,
			doc.name,
			print_format,
			doc=doc,
			no_letterhead=no_letterhead,
			as_pdf=True,
			pdf_generator="chrome",
		)
	html = frappe.get_print(
		doc.doctype, doc.name, print_format, doc=doc, no_letterhead=no_letterhead, pdf_generator="wkhtmltopdf"
	)
	html = LINK.sub("", SCRIPT.sub("", html))
	if keep:
		keep.write_text(html, encoding="utf-8")
	if fetched := FETCHED.findall(html):
		raise ValueError(f"lädt aus dem Netz: {fetched[:3]}")
	return get_pdf(html)
