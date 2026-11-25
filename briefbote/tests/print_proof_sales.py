"""The proof of the print formats of sales as PDF, for CI: Angebot and Auftragsbestätigung for the documents of
print_documents_sales.py, with both PDF generators, on blank and on pre-printed paper, checked page by page with the
checks of print_proof.py:

	bench --site <site> execute briefbote.tests.print_proof_sales.run --kwargs "{'directory': '<directory>'}"

Neither document is an invoice: none may ask for a transfer or carry the particulars of an invoice.
"""

import dataclasses
import shutil
import subprocess
import sys
from pathlib import Path

import frappe
from frappe.translate import print_language

from briefbote.briefbote import printing
from briefbote.layout import theme
from briefbote.proof import pages as checks
from briefbote.tests.print_proof import ENGINES, ENGLISH_PARTICULARS, Case, expectations, fonts, render

NO_INVOICE = ("Rechnungsdatum", "Rechnungsnummer", "Bitte überweisen", "Fällig am", "Leistungsdatum")
NO_INVOICE_EN = ("Invoice Date", "Invoice No.", "Please transfer", "Due Date")
QUOTATION = {"doctype": "Quotation", "print_format": "Angebot"}
ORDER = {"doctype": "Sales Order", "print_format": "Auftragsbestätigung"}

CASES = (
	Case(
		"AN-2026-0001",
		(1, 1),
		"Gesamtbetrag",
		(
			"Angebot AN-2026-0001",
			"Gültig bis 18.12.2026",
			"Alternative zu Position 2, nicht im Gesamtbetrag enthalten.",
			"Umsatzsteuer 19 % auf 4.780,00 €",
			"Umsatzsteuer 7 % auf 119,70 €",
			"Dieses Angebot gilt bis zum 18.12.2026.",
			"Zahlungsbedingungen: 14 Tage netto",
			"Allgemeinen Geschäftsbedingungen",
		),
		NO_INVOICE,
		papers=("eigenes-papier", "briefpapier"),
		**QUOTATION,
	),
	Case(
		"AN-2026-0002",
		(2, 8),
		"Gesamtbetrag",
		("Angebot AN-2026-0002", "Modul 36", "Umsatzsteuer 7 % auf", "USt."),
		NO_INVOICE,
		papers=("eigenes-papier", "briefpapier"),
		**QUOTATION,
	),
	Case(
		"AN-2026-0003",
		(1, 1),
		"Gesamtbetrag",
		("Zur Annahme", "Preis je Einheit"),
		(*NO_INVOICE, "Gültig bis", "18.12.2026"),
		**QUOTATION,
	),
	Case(
		"KA-2026-0001",
		(1, 1),
		"Gesamtbetrag",
		("Gemäß § 19 UStG wird keine Umsatzsteuer berechnet", "Gültig bis 31.01.2027"),
		(*NO_INVOICE, "Umsatzsteuer 19 %"),
		particulars=(),
		**QUOTATION,
	),
	Case(
		"AN-2026-0004",
		(1, 2),
		"Total Amount",
		(
			"Quotation AN-2026-0004",
			"Valid Until",
			"Reverse charge: the recipient of the service is liable for the tax.",
		),
		(*NO_INVOICE_EN, "VAT 19 %"),
		language="en",
		particulars=ENGLISH_PARTICULARS,
		**QUOTATION,
	),
	Case(
		"AB-2026-0001",
		(1, 1),
		"Gesamtbetrag",
		(
			"Auftragsbestätigung AB-2026-0001",
			"Unser Angebot AN-2026-0001",
			"Ihre Bestellung B-4711 vom 18.11.2026",
			"Liefertermin 15.12.2026",
			"Anzahlung bei Auftragserteilung",
			"Die Rechnung erhalten Sie gesondert.",
		),
		NO_INVOICE,
		papers=("eigenes-papier", "briefpapier"),
		**ORDER,
	),
	Case(
		"AB-2026-0002",
		(2, 8),
		"Gesamtbetrag",
		(
			"Liefertermine",
			"01.12.2026 bis 22.12.2026",
			"Liefertermin 08.12.2026",
			"Regal 29, Lagerregal verzinkt",
		),
		NO_INVOICE,
		**ORDER,
	),
	Case(
		"AB-2026-0003",
		(1, 1),
		"Total Amount",
		("Order Confirmation AB-2026-0003", "Service Period", "Payment terms: Monatlich im Voraus"),
		NO_INVOICE_EN,
		language="en",
		particulars=ENGLISH_PARTICULARS,
		**ORDER,
	),
)


def run(directory: str) -> None:
	with print_language("de"):
		if printing.t("Quotation") == "Quotation":
			raise SystemExit(
				"Die deutschen Übersetzungen von Briefbote fehlen, die Ausdrucke wären englisch."
			)
	out = Path(directory)
	out.mkdir(parents=True, exist_ok=True)
	report, failed = ["# Ausdrucke des Verkaufs als PDF", ""], False
	for case in CASES:
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


def letter_of(doc, own_paper: bool) -> dict:
	"""The frame the print format sets."""
	return printing.briefbote_letter(doc, 0 if own_paper else 1)


def proof(out: Path, stem: str, doc, case: Case, paper: str, engine: str) -> tuple[list[str], int]:
	"""The proof of print_proof.py without the checks that read an invoice, with the address of the frame of the
	document and the head of its own table."""
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
	letter = letter_of(doc, own_paper)
	expected = dataclasses.replace(
		expectations(doc, case, own_paper),
		address=tuple(letter["recipient"]),
		**({"table_head": case.table_head} if case.table_head else {}),
	)
	problems = checks.check(pages, expected)
	problems += fonts(path, theme.embeds(printing.settings(doc.company).get("font")))
	if letter["return_address"]:
		problems += [
			problem.replace("Anschrift", "Rücksendeangabe")
			for problem in checks.in_window(pages, tuple(letter["return_address"]), letter["form"].remarks)
		]
	return problems, len(pages)
