"""The proof of the print format Kontoauszug as PDF, for CI: the Party Statements of print_documents_statement.py with
both PDF generators, checked page by page with the checks of print_proof.py:

	bench --site <site> execute briefbote.tests.print_proof_statement.run --kwargs "{'directory': '<directory>'}"
"""

from briefbote.tests.print_proof import ENGLISH_PARTICULARS, Case
from briefbote.tests.proof_runner import Layout, listing, run_cases

HEAD = "Beleg Nummer Datum Fällig am Betrag Bezahlt Offen"
SUPPLIER_HEAD = "Beleg Nummer Ihre Rechnung Datum Fällig am Betrag Bezahlt Offen"
ENGLISH_HEAD = "Document Number Date Due Date Amount Paid Open"
BALANCE = "Saldo"
STATEMENT = {"doctype": "Party Statement", "print_format": "Kontoauszug"}
NO_DEMAND = ("Bitte überweisen", "Unterschrift", "bestätigen")
STATES_NOTHING = "Dieses Dokument weist nichts aus"

CASES = (
	Case(
		"KA-2026-0001",
		(2, 8),
		BALANCE,
		(
			"Offene Posten zum 26.11.2026",
			"Stichtag",
			"Zum 26.11.2026 weisen unsere Bücher für Ihr Konto die folgenden offenen Posten aus.",
			"RE-2026-0201",
			"RE-2026-0340",
			"ZE-2026-0001",
			"-25,00 €",
			"13.565,00 €",
			"Zum 26.11.2026 beträgt der Saldo 13.565,00 € zu unseren Gunsten.",
		),
		(*NO_DEMAND, STATES_NOTHING, "RE-2026-0203"),
		papers=("eigenes-papier", "briefpapier"),
		kept=(BALANCE, "ZE-2026-0001"),
		table_head=HEAD,
		**STATEMENT,
	),
	Case(
		"KA-2026-0002",
		(1, 1),
		"Balance",
		(
			"Open items as of 25.11.2026",
			"Cut-off Date",
			"RE-2026-0205",
			"As of 25.11.2026, the balance is 1.680,00 € in our favour.",
		),
		("Please transfer",),
		language="en",
		particulars=ENGLISH_PARTICULARS,
		kept=("Balance", "RE-2026-0205"),
		table_head=ENGLISH_HEAD,
		**STATEMENT,
	),
	Case(
		"KA-2026-0003",
		(1, 1),
		"",
		("Zum 30.11.2026 weisen unsere Bücher für Ihr Konto keine offenen Posten aus.",),
		(*NO_DEMAND, BALANCE, "Betrag"),
		**STATEMENT,
	),
	Case(
		"KA-2026-0004",
		(1, 1),
		BALANCE,
		(
			"Muster Trockenbau GmbH",
			"RG-2026-1187",
			"ER-2026-0101",
			"Zum 26.11.2026 beträgt der Saldo 2.975,00 € zu Ihren Gunsten.",
		),
		NO_DEMAND,
		kept=(BALANCE, "ER-2026-0102"),
		table_head=SUPPLIER_HEAD,
		**STATEMENT,
	),
	# Submitted before the booking BU-2026-0001 of 20.11.2026 against RE-2026-0201: it keeps 1.190,00 €.
	Case(
		"KA-2026-0005",
		(2, 8),
		BALANCE,
		("Offene Posten zum 25.11.2026", "1.190,00 €"),
		(*NO_DEMAND, "BU-2026-0001"),
		kept=(BALANCE, "RE-2026-0203"),
		table_head=HEAD,
		**STATEMENT,
	),
	# The draft of the same account and day, written after the booking: it reads 1.000,00 €.
	Case(
		"KA-2026-0006",
		(2, 8),
		BALANCE,
		("Offene Posten zum 25.11.2026", "1.000,00 €"),
		NO_DEMAND,
		kept=(BALANCE, "RE-2026-0203"),
		table_head=HEAD,
		variant="entwurf",
		docstatus=0,
		**STATEMENT,
	),
	Case(
		"KA-2026-0001",
		(2, 8),
		BALANCE,
		("Dieses Dokument ist storniert.", STATES_NOTHING),
		(*NO_DEMAND, "zu unseren Gunsten", "weisen unsere Bücher"),
		kept=(BALANCE, "ZE-2026-0001"),
		table_head=HEAD,
		variant="storniert",
		docstatus=2,
		**STATEMENT,
	),
)

# Each amount of the sums ends where the column of the open amounts ends; the text keeps its distance from the table.
LAYOUTS = {
	"KA-2026-0001": Layout(aligned=(("Offen", BALANCE),), space_above=(HEAD, 4)),
	"KA-2026-0002": Layout(aligned=(("Open", "Balance"),), space_above=(ENGLISH_HEAD, 4)),
	"KA-2026-0004": Layout(aligned=(("Offen", BALANCE),), space_above=(SUPPLIER_HEAD, 4)),
	"KA-2026-0005": Layout(aligned=(("Offen", BALANCE),), space_above=(HEAD, 4)),
	"KA-2026-0006": Layout(aligned=(("Offen", BALANCE),), space_above=(HEAD, 4)),
}


def run(directory: str) -> None:
	run_cases(directory, CASES, "# Kontoauszüge als PDF", listing, LAYOUTS)
