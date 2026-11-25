"""The proof of the print format Mahnung as PDF, for CI: the Dunnings of print_documents_dunning.py with both PDF
generators, on blank and on pre-printed paper, checked page by page with the checks of print_proof.py:

	bench --site <site> execute briefbote.tests.print_proof_dunning.run --kwargs "{'directory': '<directory>'}"

A Dunning has no positions; its table is that of the open invoices, which ends with their sum.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import frappe
from frappe.translate import print_language

from briefbote.briefbote import printing
from briefbote.layout import theme
from briefbote.proof import pages as checks
from briefbote.tests.print_proof import (
	ENGINES,
	ENGLISH,
	ENGLISH_PARTICULARS,
	GERMAN_WORDS,
	LAST_PAGE_LINES,
	LIGATURES,
	MARGINS,
	Case,
	fonts,
	render,
)
from briefbote.tests.print_proof_sales import letter_of

HEAD = "Rechnung Datum Fällig am Betrag Bezahlt Offen Tage"
HEAD_EN = "Invoice Date Due Date Amount Paid Open Days"
OPEN = "Offene Rechnungen"
NO_INVOICE = ("Rechnungsnummer", "Rechnungsdatum", "Leistungsdatum")
NO_CHARGES = ("Verzugszinsen", "Pauschale")
DUNNING = {"doctype": "Dunning", "print_format": "Mahnung", "table_head": HEAD}

CASES = (
	Case(
		"MZ-2026-0001",
		(1, 1),
		OPEN,
		(
			"Zahlungserinnerung MZ-2026-0001",
			"RE-2026-0202",
			"RE-2026-0203",
			"bis zum 20.11.2026",
			"Zahlungen, die bis zum 10.11.2026 eingegangen sind, sind berücksichtigt.",
			"DE02 1203 0000 0000 2020 51",
		),
		(*NO_INVOICE, *NO_CHARGES),
		papers=("eigenes-papier", "briefpapier"),
		kept=(OPEN,),
		**DUNNING,
	),
	Case(
		"MZ-2026-0002",
		(1, 2),
		"Gesamtbetrag",
		(
			"Mahnung MZ-2026-0002",
			"Verzugszinsen (§ 288 BGB) bis 25.11.2026",
			"Pauschale (§ 288 Abs. 5 BGB)",
			"1.880,00 €",
			"500,00 €",
			"191",
		),
		NO_INVOICE,
		papers=("eigenes-papier", "briefpapier"),
		kept=(OPEN, "Gesamtbetrag"),
		**DUNNING,
	),
	Case(
		"MZ-2026-0003",
		(1, 1),
		"Gesamtbetrag",
		("Mahnung MZ-2026-0003", "Verzugszinsen (§ 288 BGB)"),
		(*NO_INVOICE, "Pauschale"),
		kept=(OPEN, "Gesamtbetrag"),
		**DUNNING,
	),
	Case(
		"MZ-2026-0005",
		(1, 1),
		OPEN,
		("2. Mahnung MZ-2026-0005", "übersteigen"),
		(*NO_INVOICE, "Verzugszinsen (§ 288 BGB) bis", "Pauschale (", "Bitte überweisen", "Bankverbindung"),
		kept=(OPEN,),
		**DUNNING,
	),
	Case(
		"MZ-2026-0006",
		(2, 8),
		OPEN,
		("Letzte Mahnung MZ-2026-0006", "RE-2026-0340", "spätestens"),
		(*NO_INVOICE, *NO_CHARGES),
		kept=(OPEN,),
		**DUNNING,
	),
	Case(
		"MZ-2026-0007",
		(1, 1),
		"Open invoices",
		("Reminder MZ-2026-0007", "RE-2026-0205", "Payments received by 25.11.2026 are taken into account."),
		("Default interest", "Lump sum"),
		language="en",
		particulars=ENGLISH_PARTICULARS,
		kept=("Open invoices",),
		doctype="Dunning",
		print_format="Mahnung",
		table_head=HEAD_EN,
	),
)


def expectations(doc, case: Case, own_paper: bool) -> checks.Expectations:
	letter = letter_of(doc, own_paper)
	english = case.language == "en"
	return checks.Expectations(
		pages=case.pages,
		on_every_page=(f"{doc.name} · {'Page' if english else 'Seite'}",),
		somewhere=(doc.name, *case.somewhere, *(case.particulars if own_paper else ())),
		nowhere=(*(GERMAN_WORDS if english else ENGLISH), *LIGATURES, *case.nowhere),
		page_label="Page {0} of {1}" if english else "Seite {0} von {1}",
		table_head=case.table_head,
		table_end=case.total,
		address=tuple(letter["recipient"]),
		window=letter["form"].recipient,
		margins=MARGINS,
		last_page_lines=LAST_PAGE_LINES,
		kept=case.kept,
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
	letter = letter_of(doc, own_paper)
	if letter["return_address"]:
		problems += [
			problem.replace("Anschrift", "Rücksendeangabe")
			for problem in checks.in_window(pages, tuple(letter["return_address"]), letter["form"].remarks)
		]
	return problems, len(pages)


def run(directory: str) -> None:
	run_cases(Path(directory), CASES, "# Mahnungen als PDF")


def run_cases(out: Path, cases, heading: str) -> None:
	"""Each case with both generators on its papers, the report in the directory, a failed run on any problem."""
	out.mkdir(parents=True, exist_ok=True)
	report, failed = [heading, ""], False
	for case in cases:
		doc = frappe.get_doc(case.doctype, case.name)
		for paper in case.papers:
			for engine in ENGINES:
				stem = f"{case.print_format.lower()}__{case.name}__{case.language}__{paper}__{engine}"
				with print_language(case.language):
					problems, count = proof(out, stem, doc, case, paper, engine)
				failed = failed or bool(problems)
				report.append(f"- {stem}: {count} Seiten{'' if not problems else ', ' + '; '.join(problems)}")
	(out / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
	sys.stdout.write("\n".join(report) + "\n")
	if failed:
		raise SystemExit("Ausdrucke mit Problemen, siehe report.md")
