"""The proof of the print formats of sales as PDF, for CI: Angebot, Auftragsbestätigung and Lieferschein for the
documents of print_documents_sales.py, with both PDF generators, on blank and on pre-printed paper, checked page by page with the
checks of print_proof.py:

	bench --site <site> execute briefbote.tests.print_proof_sales.run --kwargs "{'directory': '<directory>'}"

Neither document is an invoice: none may ask for a transfer or carry the particulars of an invoice.
"""

from frappe.translate import print_language

from briefbote.briefbote import printing
from briefbote.tests.print_proof import ENGLISH_PARTICULARS, TABLE_HEAD, Case
from briefbote.tests.proof_runner import Layout, run_cases, with_positions

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


# Advance invoices and proformas from the copies of their orders, and the final invoices that deduct advances.
ADVANCE = {"doctype": "Proforma Invoice", "print_format": "Anzahlungsrechnung"}
PROFORMA = {"doctype": "Proforma Invoice", "print_format": "Proforma-Rechnung"}
BY_AMOUNT_HEAD = "Pos. Bezeichnung Betrag"
WITH_VAT = "Gesamtbetrag einschließlich Umsatzsteuer"
# A proforma names no tax amount and no rate (UStAE 14c.2 Abs. 1 Satz 6), asks for no transfer and is no invoice.
PROFORMA_NEVER = ("Umsatzsteuer 19 %", "Umsatzsteuer 7 %", "USt.", *NO_INVOICE)
REMAINDER = "Verbleibender Restbetrag"

CASES = (
	*CASES,
	Case(
		"AZ-2026-0001",
		(1, 1),
		"Gesamtbetrag",
		(
			"Anzahlungsrechnung AZ-2026-0001 zum Auftrag AB-2026-0010",
			"Rechnungsnummer AZ-2026-0001",
			"Rechnungsdatum 23.11.2026",
			"Leistungsdatum voraussichtlich 18.12.2026",
			"Anzahlung 30 % auf die Abfüllanlage Typ AF 200",
			"Umsatzsteuer 19 % auf 3.600,00 €",
			"Gesamtbetrag 4.284,00 €",
			"Diese Rechnung rechnet über eine Anzahlung vor Ausführung der Lieferung oder Leistung ab",
			"Bitte überweisen Sie 4.284,00 €",
		),
		("Menge", "Einzelpreis", "Vereinnahmt am"),
		papers=("eigenes-papier", "briefpapier"),
		table_head=BY_AMOUNT_HEAD,
		kept=("Abfüllanlage Typ AF 200", "Gesamtbetrag", "Bitte überweisen Sie"),
		number="AZ-2026-0001",
		**ADVANCE,
	),
	Case(
		"AZ-2026-0001",
		(1, 1),
		"Gesamtbetrag",
		("Anzahlungsrechnung AZ-2026-0001",),
		("Bitte überweisen",),
		table_head=BY_AMOUNT_HEAD,
		kept=("Abfüllanlage Typ AF 200", "Gesamtbetrag"),
		number="AZ-2026-0001",
		variant="entwurf",
		docstatus=0,
		**ADVANCE,
	),
	Case(
		"AZ-2026-0002",
		(2, 8),
		"Gesamtbetrag",
		(
			"Anzahlungsrechnung AZ-2026-0002",
			"Leistungszeitraum voraussichtlich 01.12.2026 bis 22.12.2026",
			"Regal 29, Lagerregal verzinkt",
			"Bitte überweisen Sie",
		),
		number="AZ-2026-0002",
		**ADVANCE,
	),
	Case(
		"AZ-2026-0003",
		(1, 1),
		"Total Amount",
		(
			"Advance Invoice AZ-2026-0003 for Order AB-2026-0003",
			"Service Period expected",
			"This invoice bills an advance payment before the supply or service is rendered",
			"Please transfer 1.606,50 €",
		),
		language="en",
		particulars=ENGLISH_PARTICULARS,
		table_head="Pos. Description Amount",
		kept=("Wartung und Betreuung", "Total Amount", "Please transfer"),
		number="AZ-2026-0003",
		**ADVANCE,
	),
	Case(
		"AB-2026-0010",
		(1, 1),
		"Gesamtbetrag",
		("Anzahlungsrechnung zum Auftrag AB-2026-0010", "Dieses Dokument hat keine eigene Rechnungsnummer"),
		("Bitte überweisen", "Rechnungsdatum"),
		doctype="Sales Order",
		print_format="Anzahlungsrechnung",
		variant="ohne-nummer",
		incomplete=True,
	),
	Case(
		"PRO-2026-0001",
		(1, 1),
		WITH_VAT,
		(
			"Proforma-Rechnung PRO-2026-0001",
			"Proforma-Nr. PRO-2026-0001",
			"Unser Auftrag AB-2026-0001 vom 20.11.2026",
			"Liefertermin 15.12.2026",
			"Diese Proforma-Rechnung ist keine Rechnung im Sinne des § 14 UStG",
			"berechtigt nicht zum Vorsteuerabzug",
			"Die Rechnung erhalten Sie gesondert.",
		),
		PROFORMA_NEVER,
		papers=("eigenes-papier", "briefpapier"),
		table_head=TABLE_HEAD,
		kept=("Fachbuch Buchhaltung", "Nettobetrag", WITH_VAT, "keine Rechnung"),
		number="PRO-2026-0001",
		**PROFORMA,
	),
	Case(
		"PRO-2026-0001",
		(1, 1),
		WITH_VAT,
		("Diese Proforma-Rechnung ist keine Rechnung",),
		(*PROFORMA_NEVER, "Die Rechnung erhalten Sie gesondert."),
		table_head=TABLE_HEAD,
		kept=("Fachbuch Buchhaltung", WITH_VAT),
		number="PRO-2026-0001",
		variant="storniert",
		docstatus=2,
		**PROFORMA,
	),
	Case(
		"PRO-2026-0002",
		(2, 8),
		WITH_VAT,
		("Proforma-Rechnung PRO-2026-0002", "Regal 29, Lagerregal verzinkt", "keine Rechnung"),
		PROFORMA_NEVER,
		table_head=TABLE_HEAD,
		kept=("Regal 29, Lagerregal verzinkt", WITH_VAT),
		number="PRO-2026-0002",
		**PROFORMA,
	),
	Case(
		"PRO-2026-0003",
		(1, 1),
		"Total Amount including VAT",
		(
			"Proforma Invoice PRO-2026-0003",
			"Proforma No.",
			"not an invoice within the meaning of Section 14 UStG",
			"does not entitle the recipient to deduct input tax",
		),
		("VAT 19 %", "VAT.", *NO_INVOICE_EN),
		language="en",
		particulars=ENGLISH_PARTICULARS,
		table_head="Pos. Description Amount",
		kept=("Wartung und Betreuung", "Total Amount including VAT"),
		number="PRO-2026-0003",
		**PROFORMA,
	),
	Case(
		"RE-2026-0401",
		(1, 2),
		"Gesamtbetrag",
		(
			"Schlussrechnung RE-2026-0401",
			"Abzüglich der vor der Leistung erhaltenen Anzahlungen (§ 14 Abs. 5 Satz 2 UStG):",
			"Anzahlung vom 27.11.2026",
			"AZ-2026-0001",
			"Summe der Anzahlungen 3.600,00 € 684,00 € 4.284,00 €",
			f"{REMAINDER} 11.804,80 €",
			"Bitte überweisen Sie 11.804,80 €",
		),
		("12.488,80", "Abzüglich erhaltener Anzahlungen", "Zu zahlen"),
		papers=("eigenes-papier", "briefpapier"),
		kept=("Montage und Inbetriebnahme", "Gesamtbetrag", REMAINDER, "Bitte überweisen Sie"),
	),
	Case(
		"RE-2026-0401",
		(1, 2),
		"Gesamtbetrag",
		("Schlussrechnung RE-2026-0401", REMAINDER),
		("Bitte überweisen",),
		kept=("Montage und Inbetriebnahme", "Gesamtbetrag", REMAINDER),
		variant="entwurf",
		docstatus=0,
	),
	Case(
		"RE-2026-0402",
		(2, 8),
		"Gesamtbetrag",
		(
			"Schlussrechnung RE-2026-0402",
			"Die Anzahlung JV-2026-0101 weist keine Umsatzsteuer aus",
			"Abzüglich erhaltener Zahlungen 500,00 €",
			"Leistungspaket 36",
		),
		kept=("Nettobetrag", "Gesamtbetrag", REMAINDER),
		incomplete=True,
	),
	Case(
		"RE-2026-0403",
		(1, 1),
		"Total Amount",
		(
			"Final Invoice RE-2026-0403",
			"Advance payment of 01.12.2026,",
			"payment ZE-2026-0103",
			"Remaining Amount 5.236,00 €",
			"Please transfer 5.236,00 €",
		),
		("advance invoice",),
		language="en",
		particulars=ENGLISH_PARTICULARS,
	),
)


def run(directory: str) -> None:
	with print_language("de"):
		if printing.t("Quotation") == "Quotation":
			raise SystemExit(
				"Die deutschen Übersetzungen von Briefbote fehlen, die Ausdrucke wären englisch."
			)
	run_cases(directory, CASES, "# Ausdrucke des Verkaufs als PDF", with_positions, LAYOUTS)


# „vom“ and its date stand together in the information block; the lines to sign on are painted.
LAYOUTS = {
	"AB-2026-0001": Layout(one_line=("vom 18.11.2026", "vom 16.11.2026")),
	"LS-2026-0001": Layout(one_line=("vom 20.11.2026",), rules_above=("Unterschrift", "Druckbuchstaben")),
	"LS-2026-0004": Layout(one_line=("vom 23.11.2026",)),
	# The deduction of a final invoice: each amount at the right edge of the column of the amounts.
	"RE-2026-0401": Layout(
		aligned=(("Betrag", "Gesamtbetrag"), ("Betrag", "Summe der Anzahlungen"), ("Betrag", REMAINDER))
	),
	"RE-2026-0402": Layout(aligned=(("Betrag", "Summe der Anzahlungen"), ("Betrag", REMAINDER))),
	"AZ-2026-0001": Layout(aligned=(("Betrag", "Gesamtbetrag"),), one_line=("vom 20.11.2026",)),
}
