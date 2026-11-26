"""The proof of the print formats as PDF, for CI: every print format of the app, in German, with both PDF generators
Frappe offers, wkhtmltopdf and the Chromium-based one, for the documents of print_documents.py, on blank paper and on
pre-printed letter paper, then checked page by page (briefbote/proof/pages.py):

	bench --site <site> execute briefbote.tests.print_proof.run --kwargs "{'directory': '<directory>'}"

The step of the CI makes the URL of the site unreachable: a print format must load nothing. wkhtmltopdf gets the HTML
without the link to Frappe's print bundle, which Frappe adds to every print format and which Briefbote does not need;
any other address in the HTML fails the printout. The directory receives the PDFs, the words of their pages
(pdftotext -bbox) and report.md with the pages and the problems of each; the run fails when one has a problem.
"""

import itertools
import re
import shutil
import signal
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import frappe
from frappe.model.docstatus import DocStatus
from frappe.translate import print_language
from frappe.utils.pdf import get_pdf

from briefbote.briefbote import printing
from briefbote.invoice import taxes
from briefbote.layout import din5008, letter, logo, theme
from briefbote.proof import pages as checks
from briefbote.proof import raster
from briefbote.tests import print_documents as documents

LANGUAGE = "de"
ENGINES = ("wkhtmltopdf", "chrome")
TABLE_HEAD = "Pos. Bezeichnung Menge Einheit Einzelpreis Betrag"
TABLE_HEAD_WITH_RATE = "Pos. Bezeichnung Menge Einheit Einzelpreis USt. Betrag"
# Words only a printout that falls back to the English source holds.
ENGLISH = ("Invoice", "Amount", "Page", "Quantity", "Description", "Reverse charge:", "Total Amount")
# A last page holds at least this many lines of its body; a page with less is a bad break, such as a summary torn
# from its block.
LAST_PAGE_LINES = 6
SUMMARY = (
	"Zusammenfassung: Leistungsnachweis zur Rechnung RE-2026-0114 vom 20.11.2026",
	"Stunden je Projekt",
	"Datenmigration 92,75",
	"Einführung ERP 102,00",
	"Stunden je Person",
	"Dr. Anna Beispiel 76,25",
	"Erika Mustermann 76,00",
	"Max Mustermann 42,50",
	"Summe der Stunden 194,75",
	"Abgerechnet in Position 1, 2 194,75",
)
# Words only a printout that falls back to German holds where it should be English.
GERMAN_WORDS = ("Rechnungsdatum", "Gesamtbetrag", "Seite", "Bezeichnung", "Umsatzsteuer")
ENGLISH_HEAD = "Pos. Description Quantity Unit Unit Price Amount"
ENGLISH_PARTICULARS = (
	"Beispiel GmbH",
	"Musterweg 1",
	"Registered Office: Musterstadt",
	"VAT ID: DE123456789",
	"Managing Directors:",
	"DE02 1203 0000 0000 2020 51",
)
# What a font that replaces letters by ligatures prints for „Nr.“.
LIGATURES = ("№",)
# The margins of the body: everything ends 10 mm from the right edge, with the information block; the fold marks
# carry no text.
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
	"Sitz: Musterstadt",
	"USt-IdNr.: DE123456789",
	"Amtsgericht Musterstadt",
	"HRB 99999",
	"Geschäftsführer:",
	"Erika Mustermann",
	"Max Mustermann",
	"DE02 1203 0000 0000 2020 51",
)
RATE_19 = "Umsatzsteuer 19 % auf"
# The right edge of the text in millimetres, where the information block of DIN 5008 ends.
RIGHT_EDGE = 200.0
# The edges a logo aligns with on its side of the letterhead, in millimetres from the left edge of the sheet, and how
# far its painted box may differ from where and how large it should be.
LOGO_EDGES = {"left": 25.0, "right": RIGHT_EDGE}
LOGO_TOLERANCE = 1.0
RASTER_DPI = 100
# The least room between a label of the information block and its value.
LABEL_GAP = 3.0
# The longest a printout may take to render, and a tool of Poppler to read it, in seconds; a Chromium that starts
# slowly on a busy runner gets one more try.
RENDER_SECONDS = 90
TOOL_SECONDS = 60
RENDER_TRIES = 2
INCOMPLETE = "Dieses Dokument ist unvollständig"
# The marks of a draft and of a cancelled document: the word across each page and in the page line.
MARKS = {
	("de", 0): ("ENTWURF", "· Entwurf · Seite"),
	("de", 2): ("STORNIERT", "· Storniert · Seite"),
	("en", 0): ("DRAFT", "· Draft · Page"),
	("en", 2): ("CANCELLED", "· Cancelled · Page"),
}
UNMARKED = ("ENTWURF", "STORNIERT", "DRAFT", "CANCELLED")
# The least width of the column of the descriptions: about half of the text, and of the activities of a
# Leistungsnachweis a third.
DESCRIPTION = 0.45 * 175
ACTIVITY = 0.33 * 175


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
	language: str = "de"
	kept: tuple[str, ...] = ()
	# A variant of a document under settings of its own, such as another logo, and its name in the file names.
	variant: str = ""
	settings: dict = field(default_factory=dict)
	incomplete: bool = False
	# A submitted document printed as if it were a draft (0) or cancelled (2).
	docstatus: int | None = None
	# The supplier a Request for Quotation is printed for, as the dialog of ERPNext chooses it (get_pdf); without
	# one ERPNext prints it for the first of its suppliers (before_print).
	for_supplier: str = ""
	# The number the printout gives the document where it is not its name, as the number of a Proforma Invoice on the
	# copy of its Sales Order.
	number: str = ""


def document_of(case: Case):
	"""The document a case prints: the document itself, or for a Proforma Invoice the copy of its Sales Order that
	ERPNext prints (get_sales_order_copy in erpnext/selling/doctype/proforma_invoice/proforma_invoice.py)."""
	if case.doctype == "Proforma Invoice":
		doc = frappe.get_doc(case.doctype, case.name).get_sales_order_copy()
	else:
		doc = frappe.get_doc(case.doctype, case.name)
	if case.docstatus is not None:
		doc.docstatus = DocStatus(case.docstatus)
	return doc


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
			"kein Bankkonto gewählt",
		),
		("Umsatzsteuer 19 %", "Bitte überweisen"),
		particulars=(),
		incomplete=True,
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
		kept=SUMMARY,
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
		kept=SUMMARY,
	),
	# The logos a company uploads, each printed at its height and the width of its proportions on its side.
	*(
		Case(
			"RE-2026-0101",
			(1, 1),
			"Gesamtbetrag",
			(RATE_19,),
			variant=f"logo-{name.replace('.', '-')}-{side}",
			settings={
				"logo": f"/files/briefbote-proof-logo-{name}",
				"logo_position": side.title(),
				"logo_height": height,
			},
		)
		for name, side, height in (
			("export.svg", "right", 24),
			("export.svg", "left", 24),
			("wide.svg", "right", 24),
			("wide.png", "right", 18),
			("wide.jpg", "left", 18),
			("tall.png", "right", 24),
		)
	),
	# A company whose return address does not fit one line of the remarks zone.
	Case(
		"HB-2026-0001",
		(1, 1),
		"Gesamtbetrag",
		(
			"Holzbau und Innenausbau Rheinisch-Bergisches Land GmbH & Co. KG",
			RATE_19,
			"kein Bankkonto gewählt",
		),
		("Bitte überweisen",),
		particulars=(),
		incomplete=True,
	),
	# Documents that lack a particular the law asks of them print what they lack, and no label without its value.
	Case(
		"RE-2026-0115",
		(1, 1),
		"Gesamtbetrag",
		(INCOMPLETE, "Die vollständige Anschrift des Leistungsempfängers fehlt"),
		incomplete=True,
	),
	Case(
		"RE-2026-0116",
		(1, 1),
		"Gesamtbetrag",
		(INCOMPLETE, "Die USt-IdNr. des Leistungsempfängers fehlt", "Unsere USt-IdNr."),
		("Ihre USt-IdNr.",),
		incomplete=True,
	),
	Case(
		documents.EXAMPLE_INVOICE,
		(1, 1),
		"Gesamtbetrag",
		(
			"Rechnung RE-2026-0117",
			"Fachbuch Buchhaltung",
			"Umsatzsteuer 19 % auf 4.580,00 €",
			"Umsatzsteuer 7 % auf 119,70 €",
			"5.578,28 €",
			"2 % Skonto bei Zahlung bis zum",
		),
	),
	Case(
		"KB-2026-0002",
		(1, 1),
		"Gesamtbetrag",
		(INCOMPLETE, "Die Steuernummer oder USt-IdNr. des Unternehmens fehlt"),
		particulars=(),
		variant="ohne-steuernummer",
		settings={"tax_number": ""},
		incomplete=True,
	),
	Case(
		"GS-2026-0005",
		(1, 1),
		"Gesamtbetrag",
		(
			INCOMPLETE,
			"Die Steuernummer oder USt-IdNr. des Lieferanten fehlt",
			"weist aber keine Umsatzsteuer und keinen Grund dafür aus",
		),
		("Ihre Steuernummer", "Ihre USt-IdNr."),
		doctype="Purchase Invoice",
		print_format="Gutschrift",
		incomplete=True,
	),
	# Drafts and cancelled documents: the mark on every page, also on the pages of a Leistungsnachweis, and no
	# request for payment.
	Case(
		"RE-2026-0102",
		(2, 8),
		"Gesamtbetrag",
		("Rechnung RE-2026-0102",),
		("Bitte überweisen Sie",),
		variant="entwurf",
		docstatus=0,
	),
	Case(
		"RE-2026-0101",
		(1, 1),
		"Gesamtbetrag",
		("Rechnung RE-2026-0101",),
		("Bitte überweisen Sie",),
		variant="storniert",
		docstatus=2,
	),
	Case(
		"RE-2026-0114",
		(3, 8),
		"Summe der Stunden",
		("Gesamtbetrag",),
		("Bitte überweisen Sie",),
		section="Leistungsnachweis zur Rechnung RE-2026-0114 vom 20.11.2026",
		section_after="Gesamtbetrag",
		table_head="Datum Person Tätigkeit Projekt und Aufgabe Stunden",
		kept=SUMMARY,
		variant="entwurf",
		docstatus=0,
	),
	Case(
		"GS-2026-0001",
		(1, 1),
		"Gesamtbetrag",
		("Gutschrift GS-2026-0001",),
		("überweisen wir",),
		doctype="Purchase Invoice",
		print_format="Gutschrift",
		variant="entwurf",
		docstatus=0,
	),
	Case(
		"GS-2026-0001",
		(1, 1),
		"Gesamtbetrag",
		("Gutschrift GS-2026-0001",),
		("überweisen wir",),
		doctype="Purchase Invoice",
		print_format="Gutschrift",
		variant="storniert",
		docstatus=2,
	),
	Case(
		"RE-2026-0101",
		(1, 1),
		"Total Amount",
		("Invoice RE-2026-0101",),
		("Please transfer",),
		language="en",
		particulars=ENGLISH_PARTICULARS,
		variant="entwurf",
		docstatus=0,
	),
	# Invoices whose end falls near the end of a page: the closing texts stay with the totals, and both generators
	# break alike.
	*(
		Case(
			documents.closing_name(count),
			(2, 6),
			"Gesamtbetrag",
			("Bitte überweisen Sie",),
			particulars=(),
			incomplete=True,
			# The request to pay needs an account to pay to; the company of the family has none of its own.
			settings={"bank_accounts": [documents.LONG_BANK_ACCOUNT]},
		)
		for count in documents.CLOSING_FAMILY
	),
	# The foot with one, two, three and four blocks, a long name, two managing directors, a long bank and IBAN: the
	# same geometry on every page of every printout.
	# The main case: a GmbH with every particular and one managing director, four blocks.
	Case(
		"RE-2026-0101",
		(1, 1),
		"Gesamtbetrag",
		("Telefon +49 30 1234567", "Geschäftsführer: Erika Mustermann", "BSPLDEB1XXX"),
		particulars=(),
		variant="fuss-4",
		settings={"managing_directors": "Erika Mustermann"},
	),
	Case(
		"RE-2026-0101",
		(1, 1),
		"Gesamtbetrag",
		("BIC GENODEF1XYZ", "IBAN FR76", "7890 189"),
		particulars=(),
		variant="fuss-lange-bank",
		settings={"bank_accounts": [documents.LONG_BANK_ACCOUNT]},
	),
	*(
		Case(
			"HB-2026-0001",
			(1, 1),
			"Gesamtbetrag",
			(),
			particulars=(),
			variant=f"fuss-{blocks}",
			settings=settings,
			# The company has no bank account: the request to pay is a finding.
			incomplete=True,
		)
		for blocks, settings in (
			(3, {"company": {"phone_no": "", "email": "", "website": ""}}),
			(
				2,
				{
					"company": {"phone_no": "", "email": "", "website": ""},
					"registered_office": "",
					"register_court": "",
					"register_number": "",
					"managing_directors": "",
				},
			),
			(
				1,
				{
					"company": {"phone_no": "", "email": "", "website": "", "tax_id": ""},
					"registered_office": "",
					"register_court": "",
					"register_number": "",
					"managing_directors": "",
					"tax_number": "",
				},
			),
		)
	),
	# One invoice of each tax case in English, the language of a document for a customer abroad.
	Case(
		"RE-2026-0101",
		(1, 1),
		"Total Amount",
		("Invoice RE-2026-0101", "Invoice Date", "Service Period", "VAT 19 % on 960,00 €", "Please transfer"),
		language="en",
		particulars=ENGLISH_PARTICULARS,
	),
	Case(
		"RE-2026-0103",
		(1, 2),
		"Total Amount",
		("Reverse charge: the recipient of the service is liable for the tax.", "Your VAT ID", "Our VAT ID"),
		("VAT 19 %",),
		language="en",
		particulars=ENGLISH_PARTICULARS,
	),
	# The English printout of a company with one managing director, whose register and management keep four lines.
	Case(
		"RE-2026-0103",
		(1, 2),
		"Total Amount",
		(
			"Reverse charge: the recipient of the service is liable for the tax.",
			"Managing Director:",
			"Erika Mustermann",
		),
		("VAT 19 %", "Max Mustermann"),
		language="en",
		particulars=tuple(text for text in ENGLISH_PARTICULARS if text != "Managing Directors:"),
		variant="ein-geschaeftsfuehrer",
		settings={"managing_directors": "Erika Mustermann"},
	),
	Case(
		"RE-2026-0104",
		(1, 1),
		"Total Amount",
		("Tax-exempt intra-Community supply",),
		language="en",
		particulars=ENGLISH_PARTICULARS,
	),
	Case(
		"RE-2026-0105",
		(1, 1),
		"Total Amount",
		("Reverse charge: the recipient of the service is liable for the tax (Section 13b UStG).",),
		("VAT 19 %",),
		language="en",
		particulars=ENGLISH_PARTICULARS,
	),
	Case(
		"RE-2026-0106",
		(1, 1),
		"Total Amount",
		("Tax-exempt export delivery",),
		language="en",
		particulars=ENGLISH_PARTICULARS,
	),
	Case(
		"RE-2026-0107",
		(1, 1),
		"Total Amount",
		("Not taxable in Germany",),
		language="en",
		particulars=ENGLISH_PARTICULARS,
	),
	Case(
		"RE-2026-0108",
		(1, 1),
		"Total Amount",
		("Tax-exempt supply:",),
		language="en",
		particulars=ENGLISH_PARTICULARS,
	),
	Case(
		"RE-2026-0111",
		(1, 1),
		"Credited Amount",
		("Commercial Credit Note RE-2026-0111", "billing invoice under Section 14(2) sentence 5 UStG"),
		language="en",
		particulars=ENGLISH_PARTICULARS,
	),
	Case(
		"KB-2026-0001",
		(1, 1),
		"Total Amount",
		("No VAT is charged: tax exemption for small businesses under Section 19 UStG.", "No bank account"),
		("VAT 19 %", "Please transfer"),
		language="en",
		particulars=(),
		incomplete=True,
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
		# Frappe prints a cancelled document only where the Print Settings allow it; a draft by default.
		frappe.db.set_single_value(
			"Print Settings", {"allow_print_for_draft": 1, "allow_print_for_cancelled": 1}
		)
		proof_all(Path(directory))


def proof_all(out: Path) -> None:
	out.mkdir(parents=True, exist_ok=True)
	report, failed = ["# Ausdrucke als PDF", ""], False
	breaks: dict[str, dict[str, tuple[int, list[str]]]] = {}
	FEET.clear()
	for case in CASES:
		doc = frappe.get_doc(case.doctype, case.name)
		if case.docstatus is not None:
			doc.docstatus = DocStatus(case.docstatus)
		for paper in case.papers:
			for engine in ENGINES:
				name = f"{case.name}-{case.variant}" if case.variant else case.name
				stem = f"{case.print_format.lower()}__{name}__{case.language}__{paper}__{engine}"
				with print_language(case.language), settings_of(doc.company, case.settings):
					problems, count = proof(out, stem, doc, case, paper, engine)
				breaks.setdefault(stem.rsplit("__", 1)[0], {})[engine] = page_breaks(
					out / f"{stem}.bbox.html", case
				)
				failed = failed or bool(problems)
				report.append(f"- {stem}: {count} Seiten{'' if not problems else ', ' + '; '.join(problems)}")
	for problem in feet_alike():
		failed = True
		report.append(f"- {problem}")
	# wkhtmltopdf adds blank room inside table rows where its pages break (docs/architektur.md), which moves its breaks
	# against those of the Chromium-based generator and may cost or save a page; the run fails where the two lie more
	# than a page apart, the report names every difference.
	for printout, engines in breaks.items():
		for problem in checks.pages_apart({engine: count for engine, (count, _starts) in engines.items()}):
			failed = True
			report.append(f"- {printout}: {problem}")
		if len(set(engines.values())) > 1:
			report.append(
				f"- Hinweis {printout}: die Generatoren brechen verschieden: "
				+ "; ".join(
					f"{engine} {count} Seiten ab {', '.join(starts)}"
					for engine, (count, starts) in engines.items()
				)
			)
	(out / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
	sys.stdout.write("\n".join(report) + "\n")
	if failed:
		raise SystemExit("Ausdrucke mit Problemen, siehe report.md")


@contextmanager
def settings_of(company: str, values: dict) -> Iterator[None]:
	"""The Einstellungen Geschäftspost of the company with the values of a case, for the time of its printouts: its
	fields, under the key company fields of the Company, under the key bank_accounts the bank accounts it names."""
	if not values:
		yield
		return
	doctype = "Business Document Settings"
	values = dict(values)
	company_fields = values.pop("company", {})
	banks = values.pop("bank_accounts", None)
	before = frappe.db.get_value(doctype, company, list(values), as_dict=True) if values else {}
	company_before = (
		frappe.db.get_value("Company", company, list(company_fields), as_dict=True) if company_fields else {}
	)
	banks_before = frappe.get_all(
		"Business Document Bank Account", filters={"parent": company}, pluck="bank_account", order_by="idx"
	)
	if values:
		frappe.db.set_value(doctype, company, values)
	if company_fields:
		frappe.db.set_value("Company", company, company_fields)
	if banks is not None:
		_set_banks(company, banks)
	frappe.clear_cache()
	try:
		yield
	finally:
		if values:
			frappe.db.set_value(doctype, company, before)
		if company_fields:
			frappe.db.set_value("Company", company, company_before)
		if banks is not None:
			_set_banks(company, banks_before)
		frappe.clear_cache()


def _set_banks(company: str, accounts: list[str]) -> None:
	frappe.db.delete("Business Document Bank Account", {"parent": company})
	for index, account in enumerate(accounts, start=1):
		frappe.get_doc(
			{
				"doctype": "Business Document Bank Account",
				"name": f"{company}-bank-{index}",
				"parent": company,
				"parenttype": "Business Document Settings",
				"parentfield": "bank_accounts",
				"idx": index,
				"bank_account": account,
			}
		).db_insert()


def expectations(doc, case: Case, own_paper: bool) -> checks.Expectations:
	letter = printing.briefbote_letter(doc, 0 if own_paper else 1)
	form = letter["form"]
	positions = doc.items
	head = case.table_head or (
		TABLE_HEAD_WITH_RATE if taxes.shows_rates(printing.position_rates(doc)) else TABLE_HEAD
	)
	return checks.Expectations(
		pages=case.pages,
		on_every_page=(
			f"{case.number or doc.name} · {'Page' if case.language == 'en' else 'Seite'}"
			if case.docstatus is None
			else case.number or doc.name,
		),
		together=() if case.table_head else ((" ".join(positions[-1].item_name.split()[:2]), case.total),),
		somewhere=(
			doc.name,
			*case.somewhere,
			*(case.particulars if own_paper else ()),
		),
		nowhere=(
			*(GERMAN_WORDS if case.language == "en" else ENGLISH),
			*LIGATURES,
			*case.nowhere,
			*(() if case.incomplete or case.language == "en" else (INCOMPLETE,)),
			*(() if case.docstatus is not None else UNMARKED),
		),
		page_label="Page {0} of {1}" if case.language == "en" else "Seite {0} von {1}",
		table_head=ENGLISH_HEAD if case.language == "en" else head,
		table_end=case.total,
		address=tuple(letter["recipient"]),
		window=form.recipient,
		margins=MARGINS,
		last_page_lines=LAST_PAGE_LINES,
		kept=case.kept
		or (
			() if case.table_head else ("Net Amount" if case.language == "en" else "Nettobetrag", case.total)
		),
		section=case.section,
		section_after=case.section_after,
	)


def proof(out: Path, stem: str, doc, case: Case, paper: str, engine: str) -> tuple[list[str], int]:
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
	problems = checks.check(checks.without_mark(pages), expectations(doc, case, own_paper))
	problems += fonts(path, theme.embeds(printing.settings(doc.company).get("font")))
	problems += hours_billed(doc)
	frame = printing.briefbote_letter(doc, 0 if own_paper else 1)
	config = printing.settings(doc.company)
	if config.print_return_address:
		company = printing.company_particulars(doc.company, config)
		problems += [
			problem.replace("Anschrift", "Rücksendeangabe")
			for problem in checks.in_window(
				pages, letter.return_address(company).lines, frame["form"].remarks
			)
		]
	problems += checks.label_gaps(pages, information(doc), LABEL_GAP, frame["form"].information.left - 1)
	problems += columns_of(pages, case)
	problems += checks.anchored(checks.without_mark(pages), anchors(case))
	feet = feet_of(path, checks.without_mark(pages), own_paper and bool(frame["footer"]))
	needed = letter.foot_overflows(printing.company_particulars(doc.company, config), printing.t)
	problems += foot_problems(feet, max((lines for _name, lines in needed), default=FOOT_LINES))
	FEET.append((path.stem, own_paper and bool(frame["footer"]), feet))
	if case.docstatus is not None:
		# wkhtmltopdf repeats no fixed element: there the mark across stands on the first page, the framed mark in the
		# foot and the word in the page line on every page.
		problems += checks.marked(
			pages, *MARKS[(case.language, case.docstatus)], across_every_page=engine == "chrome"
		)
		problems += mark_painted(path, pages if engine == "chrome" else pages[:1])
		problems += [f"PDF/A: {problem}" for problem in marked_as_pdfa(path, case, engine)]
	if own_paper and config.logo:
		problems += logo_painted(path, frame["form"], config)
	return problems, len(pages)


def columns_of(pages, case: Case) -> list[str]:
	"""The column of the descriptions, or of the activities in a Leistungsnachweis, has its room."""
	if case.table_head:
		return checks.column_width(pages, "Datum Person Tätigkeit", "Tätigkeit", "Projekt", ACTIVITY)
	if case.language == "en":
		return checks.column_width(pages, "Pos. Description", "Description", "Quantity", DESCRIPTION)
	return checks.column_width(pages, "Pos. Bezeichnung", "Bezeichnung", "Menge", DESCRIPTION)


def icc_profiles(gs: str) -> str:
	"""The folder of the ICC profiles of Ghostscript beside the folder lib of its search path, as eu_einvoice finds
	it (_get_icc_profile_path)."""
	help_text = subprocess.run(  # noqa: S603 - Ghostscript of the runner
		[gs, "-h"], capture_output=True, text=True, check=True, timeout=TOOL_SECONDS
	).stdout
	lib = next(
		(Path(token) for token in help_text.split() if token.endswith("/lib") and Path(token).is_dir()), None
	)
	if lib is None:
		raise RuntimeError("Ghostscript nennt keinen Ordner lib in seinem Suchpfad")
	return str(lib.parent / "iccprofiles")


def marked_as_pdfa(path: Path, case: Case, engine: str) -> list[str]:
	"""The mark of a draft or a cancelled document survives the conversion to PDF/A-3 with Ghostscript that
	eu_einvoice applies to every PDF of a Sales Invoice it embeds its XML in (_convert_pdf_to_pdfa), with its
	options."""
	gs = shutil.which("gs")
	if not gs:
		return ["Ghostscript fehlt"]
	converted = subprocess.run(  # noqa: S603 - Ghostscript of the runner on a PDF this run wrote
		[
			gs,
			"-q",
			"-sstdout=%stderr",
			"-dPDFA=3",
			"-dBATCH",
			"-dNOPAUSE",
			"-dPDFACompatibilityPolicy=2",
			"-sColorConversionStrategy=RGB",
			"--permit-file-read=srgb.icc",
			"-sDEVICE=pdfwrite",
			"-sOutputFile=-",
			"PDFA_def.ps",
			"-",
		],
		cwd=icc_profiles(gs),
		input=path.read_bytes(),
		capture_output=True,
		check=True,
		timeout=TOOL_SECONDS,
	).stdout
	pdfa = path.parent / f"{path.stem}.pdfa.pdf"
	pdfa.write_bytes(converted)
	pdftotext = shutil.which("pdftotext") or "pdftotext"
	words = subprocess.run(  # noqa: S603 - Poppler on a PDF this run wrote
		[pdftotext, "-bbox", str(pdfa), "-"], capture_output=True, text=True, check=True, timeout=TOOL_SECONDS
	).stdout
	pages = checks.read_bbox(words)
	marked = checks.marked(
		pages, *MARKS[(case.language, case.docstatus)], across_every_page=engine == "chrome"
	)
	return marked + mark_painted(pdfa, pages if engine == "chrome" else pages[:1])


# The middle of a page in millimetres, where the mark across it stands, the grey of the mark, translucent black over
# white paper, and the least share of such pixels there; text alone, black on white, leaves far less in that range.
MARK_BAND = raster.Area(30, 90, 195, 210)
MARK_GREY = (200, 238)
MARK_SHARE = 0.04


def mark_painted(path: Path, pages) -> list[str]:
	"""The mark across each page is painted, not only in the layer of text: the middle of every page holds enough
	pixels of its grey."""
	pdftoppm = shutil.which("pdftoppm") or "pdftoppm"
	problems = []
	for number in range(1, len(pages) + 1):
		root = path.parent / f"{path.stem}-mark-{number}"
		subprocess.run(  # noqa: S603 - Poppler on a PDF this run wrote
			[
				pdftoppm,
				"-r",
				"50",
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
		image = raster.read_pgm(pgm.read_bytes(), 50)
		pgm.unlink()
		found = raster.share(image, MARK_BAND, *MARK_GREY)
		if found < MARK_SHARE:
			problems.append(
				f"Seite {number}: Markierung quer über der Seite nicht sichtbar ({found:.1%} graue Fläche)"
			)
	return problems


def page_breaks(words: Path, case: Case) -> tuple[int, tuple[str, ...]]:
	"""The pages of a printout and where each starts, to compare the two generators."""
	if not words.exists():
		return 0, ()
	pages = checks.without_mark(checks.read_bbox(words.read_text(encoding="utf-8")))
	head = case.table_head or ("Pos. Description" if case.language == "en" else "Pos. Bezeichnung")
	return len(pages), tuple(checks.page_starts(pages, head))


# The foot of every page of every printout, to compare them: the stem of the printout, whether it has blocks, and
# the rule above them and the foot of each page.
FEET: list[tuple[str, bool, list[tuple[float | None, checks.Foot | None, float | None, float | None]]]] = []
FOOT_LINES = 4
# The lowest ink stands at least this many millimetres above the edge of the paper.
FOOT_CLEARANCE = 12.0
# Two feet whose rule, first line or page line differ by more than this many millimetres do not stand alike.
FOOT_TOLERANCE = 0.6
FOOT_ZONE = raster.Area(15, 250, 205, 297)
# Where the rule above the foot stands: below the text, which ends 36 mm above the edge, above the blocks.
FOOT_RULE = raster.Area(25, 261.5, 200, 270)
# From the rule to the top of the row of the page line, in millimetres: 66 pixels of blocks and gap below the rule of
# one pixel (style.html).
FOOT_PAGE_LINE = 67 * 25.4 / 96
# The least blank room between a line of the blocks and the page line or the framed mark beneath it, in millimetres.
FOOT_GAP = 0.3


def feet_of(
	path: Path, pages, blocks: bool
) -> list[tuple[float | None, checks.Foot | None, float | None, float | None]]:
	"""The rule, the foot and the lowest ink of each page, measured on the page rendered as an image."""
	pdftoppm = shutil.which("pdftoppm") or "pdftoppm"
	found = []
	for number, page in enumerate(pages, start=1):
		root = path.parent / f"{path.stem}-foot-{number}"
		subprocess.run(  # noqa: S603 - Poppler on a PDF this run wrote
			[
				pdftoppm,
				"-r",
				"100",
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
		image = raster.read_pgm(pgm.read_bytes(), 100)
		pgm.unlink()
		rule = raster.rule(image, FOOT_RULE) if blocks else None
		foot = checks.foot(page, rule)
		gap = foot_gap(image, rule, foot.starts) if rule is not None and foot is not None else None
		found.append((rule, foot, raster.lowest(image, FOOT_ZONE), gap))
	return found


def foot_gap(image: raster.Raster, rule: float, starts: list[float]) -> float | None:
	"""The least blank room, in millimetres, between the lowest line of a block and the page line or the framed mark
	beneath it in the same column, measured in pixels; 0 where they touch. A fifth line of a block runs into the gap
	above the page line and must stay clear of it."""
	threshold = rule + FOOT_PAGE_LINE - 0.2
	gaps = []
	for left, right in itertools.pairwise([*starts, RIGHT_EDGE + 0.5]):
		found = raster.bands(image, raster.Area(left - 0.5, rule + 0.5, right - 0.5, 297))
		if any(top < threshold < bottom for top, bottom in found):
			gaps.append(0.0)
			continue
		above = [bottom for top, bottom in found if bottom <= threshold]
		below = [top for top, bottom in found if top >= threshold]
		if above and below:
			gaps.append(min(below) - max(above))
	return min(gaps) if gaps else None


def foot_problems(feet, allowed: int = FOOT_LINES) -> list[str]:
	"""Each foot keeps its blocks to four lines, or to the lines the check of the settings warns of, its columns
	close, its blocks clear of the page line and its ink clear of the edge of the paper."""
	problems = []
	for number, (_rule, foot, lowest, gap) in enumerate(feet, start=1):
		if foot is None:
			continue
		if foot.lines > allowed:
			problems.append(f"Seite {number}: Fuß mit {foot.lines} Zeilen statt höchstens {allowed}")
		if gap is not None and gap < FOOT_GAP:
			problems.append(f"Seite {number}: Block des Fußes nur {gap:.2f} mm über der Seitenzeile")
		column = 175 / max(len(foot.starts), 1)
		problems += [
			f"Seite {number}: Lücke von {hole:.1f} mm zwischen Spalten des Fußes, breiter als eine Spalte"
			for hole in foot.holes
			if hole > column
		]
		if lowest is not None and 297 - lowest < FOOT_CLEARANCE:
			problems.append(
				f"Seite {number}: Fuß endet {297 - lowest:.1f} mm über dem Rand statt mindestens 12 mm"
			)
	return problems


def feet_alike() -> list[str]:
	"""Every foot of every printout stands alike: the rule, the first line of the blocks and the page line."""
	measures: dict[str, list[tuple[str, float]]] = {"Linie": [], "erste Zeile": [], "Seitenzeile": []}
	for stem, blocks, feet in FEET:
		for number, (rule, foot, _lowest, _gap) in enumerate(feet, start=1):
			where = f"{stem} Seite {number}"
			if foot is not None:
				measures["Seitenzeile"].append((where, foot.page_line))
			if blocks and rule is not None:
				measures["Linie"].append((where, rule))
			if blocks and foot is not None and foot.first_line is not None:
				measures["erste Zeile"].append((where, foot.first_line))
	problems = []
	for name, values in measures.items():
		if (
			values
			and max(value for _where, value in values) - min(value for _where, value in values)
			> FOOT_TOLERANCE
		):
			low, high = min(values, key=lambda item: item[1]), max(values, key=lambda item: item[1])
			problems.append(f"Fuß: {name} bei {low[1]:.1f} mm ({low[0]}) bis {high[1]:.1f} mm ({high[0]})")
	return problems


def anchors(case: Case) -> tuple[str, ...]:
	"""What every page of a printout must hold: a row of a table, known by its head, or the totals."""
	heads = (TABLE_HEAD, TABLE_HEAD_WITH_RATE, ENGLISH_HEAD, case.table_head)
	return tuple(text for text in (*heads, case.total, *case.kept[:1], "Nettobetrag", "Net Amount") if text)


def information(doc) -> list[tuple[str, str]]:
	"""The labels and values of the information block of the document."""
	if doc.doctype == "Purchase Invoice":
		return printing.briefbote_self_billing(doc)["info"]
	return printing.briefbote_invoice(doc)["info"]


def logo_painted(path: Path, form: din5008.Form, config) -> list[str]:
	"""The logo stands painted in the letterhead at the height of the settings, as wide as its proportions ask, at
	its edge: measured on the first page rendered as an image, since a logo has no words."""
	proportions = printing.logo_proportions(config.logo)
	if not proportions:
		return [f"Logo {config.logo} ohne lesbare Größe"]
	height = Decimal(
		str(theme.logo_height(float(config.logo_height or 0), form.letterhead_height, printing.TOP_MARGIN))
	)
	width, height = logo.box(proportions, height, logo.MAX_WIDTH)
	pdftoppm = shutil.which("pdftoppm") or "pdftoppm"
	root = path.parent / f"{path.stem}-logo"
	subprocess.run(  # noqa: S603 - Poppler on a PDF this run wrote
		[pdftoppm, "-r", str(RASTER_DPI), "-gray", "-f", "1", "-l", "1", "-singlefile", str(path), str(root)],
		capture_output=True,
		check=True,
		timeout=TOOL_SECONDS,
	)
	pgm = path.parent / f"{root.name}.pgm"
	image = pgm.read_bytes()
	pgm.unlink()
	letterhead = raster.Area(0, 0, din5008.PAGE[0], form.address.top - 1)
	found = raster.painted(raster.read_pgm(image, RASTER_DPI), letterhead)
	if found is None:
		return ["kein Logo im Briefkopf"]
	side = theme.logo_side(config.get("logo_position"))
	edge = found.right if side == "right" else found.left
	problems = []
	if abs(found.height - float(height)) > LOGO_TOLERANCE or abs(found.width - float(width)) > LOGO_TOLERANCE:
		problems.append(
			f"Logo {found.width:.1f} x {found.height:.1f} mm statt {float(width):.1f} x {float(height):.1f} mm"
		)
	if abs(edge - LOGO_EDGES[side]) > LOGO_TOLERANCE:
		problems.append(f"Logo endet bei {edge:.1f} mm statt {LOGO_EDGES[side]:.1f} mm")
	return problems


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
		[pdffonts, str(path)], capture_output=True, text=True, check=True, timeout=TOOL_SECONDS
	).stdout.splitlines()[2:]
	names = sorted({line.split()[0].split("+")[-1] for line in listed if line.strip()})
	if not embedded:
		return [
			f"Schrift {name} statt der Schrift des Systems" for name in names if name.startswith("Inter-")
		]
	others = [name for name in names if not name.startswith("Inter-")]
	return [f"Schrift {name} statt Inter" for name in others] if others or not names else []


class RenderTimeout(BaseException):
	"""A BaseException, so that no handler of Frappe that catches Exception swallows the time limit."""


def _expired(signum, frame):
	raise RenderTimeout


def render_in_time(doc, print_format: str, engine: str, own_paper: bool, keep: Path) -> bytes:
	"""render() within RENDER_SECONDS, tried twice; a printout that takes longer fails with its document and engine
	instead of holding up the run. bench execute runs the proof in the main thread, where an alarm can interrupt it."""
	previous = signal.signal(signal.SIGALRM, _expired)
	try:
		for attempt in range(1, RENDER_TRIES + 1):
			signal.alarm(RENDER_SECONDS)
			try:
				return render(doc, print_format, engine, own_paper, keep)
			except RenderTimeout:
				if attempt == RENDER_TRIES:
					raise TimeoutError(
						f"{doc.name} mit {engine} nach {RENDER_TRIES} Versuchen zu je {RENDER_SECONDS} s nicht fertig"
					) from None
			finally:
				signal.alarm(0)
	finally:
		signal.signal(signal.SIGALRM, previous)
	raise AssertionError("unreachable")  # pragma: no cover


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
