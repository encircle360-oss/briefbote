"""The proof of the print formats Zahlungsbestätigung and Quittung as PDF, for CI: the payments of
print_documents_payment.py with both PDF generators, checked page by page with the checks of print_proof.py:

	bench --site <site> execute briefbote.tests.print_proof_payment.run --kwargs "{'directory': '<directory>'}"
"""

import dataclasses

from briefbote.tests.print_proof import ENGLISH_PARTICULARS, Case
from briefbote.tests.proof_runner import Layout, listing, run_cases

HEAD = "Beleg Nummer Datum Fällig am Betrag Angerechnet"
APPLIED = "Angerechnet"
CONFIRMATION = {"doctype": "Payment Entry", "print_format": "Zahlungsbestätigung", "table_head": HEAD}
RECEIPT = {"doctype": "Payment Entry", "print_format": "Quittung", "table_head": HEAD}
NO_DEMAND = ("Bitte überweisen", "Rechnungsnummer", "Fällig zum")

CASES = (
	Case(
		"ZE-2026-0001",
		(1, 1),
		APPLIED,
		(
			"Zahlungsbestätigung ZE-2026-0001",
			"Ihre Zahlung über 2.500,00 € vom 26.11.2026",
			"RE-2026-0202",
			"1.880,00 €",
			"25,00 € der Zahlung sind noch keiner Rechnung zugeordnet.",
			"SEPA-2026-11-26-0042",
		),
		(*NO_DEMAND, "Unterschrift"),
		papers=("eigenes-papier", "briefpapier"),
		kept=("Zahlungseingang", APPLIED),
		**CONFIRMATION,
	),
	Case(
		"ZE-2026-0002",
		(1, 1),
		APPLIED,
		(
			"Quittung ZE-2026-0002",
			"Den Betrag von 476,00 € haben wir am 26.11.2026 von Erika Beispiel erhalten.",
			"Unterschrift",
		),
		NO_DEMAND,
		papers=("eigenes-papier", "briefpapier"),
		kept=("Zahlungseingang", APPLIED),
		**RECEIPT,
	),
	Case(
		"ZE-2026-0003",
		(1, 1),
		"Applied",
		("Payment Confirmation ZE-2026-0003", "Bankgebühren", "15,00 €", "SWIFT 7731"),
		("Please transfer",),
		language="en",
		particulars=ENGLISH_PARTICULARS,
		kept=("Payment received", "Applied"),
		doctype="Payment Entry",
		print_format="Zahlungsbestätigung",
		table_head="Document Number Date Due Date Amount Applied",
	),
	Case(
		"ZE-2026-0004",
		(2, 8),
		APPLIED,
		("Zahlungsbestätigung ZE-2026-0004", "RE-2026-0340"),
		NO_DEMAND,
		kept=("Zahlungseingang", APPLIED),
		**CONFIRMATION,
	),
)


# Drafts and cancelled documents: the mark on every page and nothing confirmed.
CASES = (
	*CASES,
	Case(
		"ZE-2026-0002",
		(1, 1),
		APPLIED,
		("Quittung ZE-2026-0002", "Dieses Dokument bestätigt nichts"),
		(*NO_DEMAND, "haben wir am", "Unterschrift"),
		kept=("Zahlungseingang", APPLIED),
		variant="storniert",
		docstatus=2,
		**RECEIPT,
	),
	Case(
		"ZE-2026-0004",
		(2, 8),
		APPLIED,
		("Zahlungsbestätigung ZE-2026-0004", "Dieses Dokument bestätigt nichts"),
		(*NO_DEMAND, "ist eingegangen", "noch keiner Rechnung zugeordnet"),
		kept=("Zahlungseingang", APPLIED),
		variant="entwurf",
		docstatus=0,
		**CONFIRMATION,
	),
)


CASES = (
	*CASES,
	Case(
		"ZE-2026-0001",
		(1, 1),
		APPLIED,
		("Zahlungsbestätigung ZE-2026-0001", "Dieses Dokument bestätigt nichts"),
		(*NO_DEMAND, "ist eingegangen", "noch keiner Rechnung zugeordnet"),
		kept=("Zahlungseingang", APPLIED),
		variant="storniert",
		docstatus=2,
		**CONFIRMATION,
	),
	Case(
		"ZE-2026-0002",
		(1, 1),
		APPLIED,
		("Quittung ZE-2026-0002", "Dieses Dokument bestätigt nichts"),
		(*NO_DEMAND, "haben wir am", "Unterschrift", "Ort, Datum"),
		kept=("Zahlungseingang", APPLIED),
		variant="entwurf",
		docstatus=0,
		**RECEIPT,
	),
)

# The sums end where the column of the applied amounts ends; the text keeps its distance from the table.
APPLIED_LAYOUT = Layout(
	aligned=(("Angerechnet", "Zahlungseingang"), ("Angerechnet", APPLIED)), space_above=(HEAD, 4)
)
LAYOUTS = {
	"ZE-2026-0001": dataclasses.replace(APPLIED_LAYOUT, one_line=("vom 26.11.2026",)),
	"ZE-2026-0002": APPLIED_LAYOUT,
	"ZE-2026-0003": Layout(
		aligned=(("Applied", "Payment received"), ("Applied", "Bankgebühren"), ("Applied", "Applied")),
		space_above=("Document Number Date Due Date Amount Applied", 4),
	),
	"ZE-2026-0004": APPLIED_LAYOUT,
}


def run(directory: str) -> None:
	run_cases(directory, CASES, "# Zahlungsbestätigungen als PDF", listing, LAYOUTS)
