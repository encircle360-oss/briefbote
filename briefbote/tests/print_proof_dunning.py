"""The proof of the print format Mahnung as PDF, for CI: the Dunnings of print_documents_dunning.py with both PDF
generators, on blank and on pre-printed paper, checked page by page with the checks of print_proof.py:

	bench --site <site> execute briefbote.tests.print_proof_dunning.run --kwargs "{'directory': '<directory>'}"

A Dunning has no positions; its table is that of the open invoices, which ends with their sum.
"""

import dataclasses

from briefbote.tests.print_proof import ENGLISH_PARTICULARS, Case
from briefbote.tests.proof_runner import Layout, listing, run_cases

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


# A company without a bank account: a finding instead of the demand.
CASES = (
	*CASES,
	Case(
		"MZ-2026-0008",
		(1, 1),
		OPEN,
		("Zahlungserinnerung MZ-2026-0008", "kein Bankkonto gewählt"),
		(*NO_INVOICE, *NO_CHARGES, "Bitte überweisen", "Bankverbindung"),
		particulars=(),
		kept=(OPEN,),
		**DUNNING,
	),
)

# Drafts and cancelled documents: the mark on every page and no demand.
CASES = (
	*CASES,
	Case(
		"MZ-2026-0002",
		(1, 2),
		"Gesamtbetrag",
		("Mahnung MZ-2026-0002",),
		(*NO_INVOICE, "Bitte überweisen", "Bankverbindung"),
		kept=(OPEN, "Gesamtbetrag"),
		variant="entwurf",
		docstatus=0,
		**DUNNING,
	),
	Case(
		"MZ-2026-0006",
		(2, 8),
		OPEN,
		("Letzte Mahnung MZ-2026-0006",),
		(*NO_INVOICE, "Bitte überweisen", "Bankverbindung"),
		kept=(OPEN,),
		variant="storniert",
		docstatus=2,
		**DUNNING,
	),
)


# The sum and the claims end where the column of the open amounts ends; the text keeps its distance from the table.
CHARGED = Layout(
	aligned=(
		("Offen", "Offene Rechnungen"),
		("Offen", "Verzugszinsen"),
		("Offen", "Gesamtbetrag"),
	),
	space_above=(HEAD, 4),
)
LAYOUTS = {
	"MZ-2026-0001": Layout(aligned=(("Offen", "Offene Rechnungen"),), space_above=(HEAD, 4)),
	"MZ-2026-0002": dataclasses.replace(CHARGED, aligned=(*CHARGED.aligned, ("Offen", "Pauschale"))),
	"MZ-2026-0003": CHARGED,
	"MZ-2026-0005": Layout(aligned=(("Offen", "Offene Rechnungen"),)),
	"MZ-2026-0006": Layout(aligned=(("Offen", "Offene Rechnungen"),), space_above=(HEAD, 4)),
	"MZ-2026-0007": Layout(aligned=(("Open", "Open invoices"),), space_above=(HEAD_EN, 4)),
	"MZ-2026-0008": Layout(aligned=(("Offen", "Offene Rechnungen"),)),
}


def run(directory: str) -> None:
	run_cases(directory, CASES, "# Mahnungen als PDF", listing, LAYOUTS)
