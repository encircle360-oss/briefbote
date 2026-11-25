"""The proof of the print formats of sales as PDF, for CI: Angebot, Auftragsbestätigung and Lieferschein for the
documents of print_documents_sales.py, with both PDF generators, on blank and on pre-printed paper, checked page by page with the
checks of print_proof.py:

	bench --site <site> execute briefbote.tests.print_proof_sales.run --kwargs "{'directory': '<directory>'}"

Neither document is an invoice: none may ask for a transfer or carry the particulars of an invoice.
"""

from frappe.translate import print_language

from briefbote.briefbote import printing
from briefbote.tests.print_proof import ENGLISH_PARTICULARS, Case
from briefbote.tests.proof_runner import run_cases, with_positions

NO_INVOICE = ("Rechnungsdatum", "Rechnungsnummer", "Bitte überweisen", "Fällig am", "Leistungsdatum")
NO_INVOICE_EN = ("Invoice Date", "Invoice No.", "Please transfer", "Due Date")
QUOTATION = {"doctype": "Quotation", "print_format": "Angebot"}
ORDER = {"doctype": "Sales Order", "print_format": "Auftragsbestätigung"}
NOTE = {"doctype": "Delivery Note", "print_format": "Lieferschein"}
NOTE_HEAD = "Pos. Bezeichnung Menge Einheit"
RECEIVED = "Ware erhalten"

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
	Case(
		"LS-2026-0001",
		(1, 1),
		RECEIVED,
		(
			"Lieferschein LS-2026-0001",
			"Lieferdatum 23.11.2026",
			"Unser Auftrag",
			"Seriennummern: TD200-26-00417, TD200-26-00418, TD200-26-00419",
			"Chargen: CH-2026-311 (16), CH-2026-327 (8)",
			"Gesamtgewicht netto: 41,6 kg",
			"Unterschrift",
			"Wareneingang Tor 3",
		),
		(*NO_INVOICE, "349,00", "Gesamtbetrag", "Nettobetrag"),
		papers=("eigenes-papier", "briefpapier"),
		table_head=NOTE_HEAD,
		kept=("Montagewinkel verzinkt", RECEIVED, "Unterschrift"),
		**NOTE,
	),
	Case(
		"LS-2026-0002",
		(2, 8),
		RECEIVED,
		("Lieferschein LS-2026-0002", "Regal 39, Lagerregal verzinkt"),
		(*NO_INVOICE, "Gesamtbetrag"),
		table_head=NOTE_HEAD,
		kept=("Regal 39, Lagerregal verzinkt", RECEIVED, "Unterschrift"),
		**NOTE,
	),
	Case(
		"LS-2026-0003",
		(1, 1),
		"Goods received",
		("Delivery Note LS-2026-0003", "UNITED STATES", "Delivery Date"),
		(*NO_INVOICE_EN, "Total Amount"),
		language="en",
		particulars=ENGLISH_PARTICULARS,
		table_head="Pos. Description Quantity Unit",
		kept=("Montagewinkel verzinkt", "Goods received", "Signature"),
		**NOTE,
	),
	Case(
		"LS-2026-0004",
		(1, 1),
		RECEIVED,
		("Rücklieferschein LS-2026-0004", "Lieferschein LS-2026-0001", "Seriennummer: TD200-26-00418"),
		NO_INVOICE,
		table_head=NOTE_HEAD,
		kept=("Etikettendrucker TD-200", RECEIVED),
		**NOTE,
	),
	Case(
		"KL-2026-0001",
		(1, 1),
		"Gesamtbetrag",
		("Lieferschein KL-2026-0001", "47,40 €"),
		(*NO_INVOICE, "Unterschrift"),
		particulars=(),
		**NOTE,
	),
)


# Drafts and cancelled documents: the mark on every page and no call to act.
CASES = (
	*CASES,
	Case(
		"AN-2026-0001",
		(1, 1),
		"Gesamtbetrag",
		("Angebot AN-2026-0001",),
		(*NO_INVOICE, "Zur Annahme", "Dieses Angebot gilt bis"),
		variant="entwurf",
		docstatus=0,
		**QUOTATION,
	),
	Case(
		"AN-2026-0002",
		(2, 8),
		"Gesamtbetrag",
		("Angebot AN-2026-0002",),
		(*NO_INVOICE, "Zur Annahme", "Dieses Angebot gilt bis"),
		variant="storniert",
		docstatus=2,
		**QUOTATION,
	),
	Case(
		"AB-2026-0001",
		(1, 1),
		"Gesamtbetrag",
		("Auftragsbestätigung AB-2026-0001",),
		(*NO_INVOICE, "Die Rechnung erhalten Sie gesondert."),
		variant="entwurf",
		docstatus=0,
		**ORDER,
	),
	Case(
		"AB-2026-0003",
		(1, 1),
		"Total Amount",
		("Order Confirmation AB-2026-0003",),
		(*NO_INVOICE_EN, "You will receive the invoice separately."),
		language="en",
		particulars=ENGLISH_PARTICULARS,
		variant="storniert",
		docstatus=2,
		**ORDER,
	),
	Case(
		"LS-2026-0001",
		(1, 1),
		"Gesamtgewicht netto",
		("Lieferschein LS-2026-0001",),
		(*NO_INVOICE, RECEIVED, "Unterschrift"),
		table_head=NOTE_HEAD,
		kept=("Montagewinkel verzinkt", "Gesamtgewicht netto"),
		variant="entwurf",
		docstatus=0,
		**NOTE,
	),
	Case(
		"LS-2026-0002",
		(2, 8),
		"Regal 39, Lagerregal verzinkt",
		("Lieferschein LS-2026-0002",),
		(*NO_INVOICE, RECEIVED, "Unterschrift"),
		table_head=NOTE_HEAD,
		kept=("Regal 39, Lagerregal verzinkt",),
		variant="storniert",
		docstatus=2,
		**NOTE,
	),
)


def run(directory: str) -> None:
	with print_language("de"):
		if printing.t("Quotation") == "Quotation":
			raise SystemExit(
				"Die deutschen Übersetzungen von Briefbote fehlen, die Ausdrucke wären englisch."
			)
	run_cases(directory, CASES, "# Ausdrucke des Verkaufs als PDF", with_positions)
