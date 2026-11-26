"""The proof of the print format Zahlungsavis as PDF, for CI: the payments to suppliers of
print_documents_remittance.py with both PDF generators, checked page by page with the checks of print_proof.py, and
each print format of a Payment Entry chosen for a payment in the other direction:

	bench --site <site> execute briefbote.tests.print_proof_remittance.run --kwargs "{'directory': '<directory>'}"
"""

from briefbote.tests.print_proof import ENGLISH_PARTICULARS, Case
from briefbote.tests.proof_runner import Layout, listing, run_cases

HEAD = "Ihre Rechnung Datum Unser Beleg Betrag Skonto Ausgeglichen"
PLAIN_HEAD = "Ihre Rechnung Datum Unser Beleg Betrag Ausgeglichen"
ENGLISH_HEAD = "Your Invoice Date Our Reference Amount Settled"
SETTLED = "Ausgeglichen"
TRANSFERRED = "Überwiesen"
ADVICE = {"doctype": "Payment Entry", "print_format": "Zahlungsavis"}
NO_DEMAND = ("Bitte überweisen", "Fällig zum", "Unterschrift")
NO_PAYMENT = "Dieses Dokument meldet keine Zahlung"

CASES = (
	Case(
		"ZA-2026-0002",
		(1, 1),
		TRANSFERRED,
		(
			"Zahlungsavis ZA-2026-0002",
			"Wir haben am 27.11.2026 den Betrag von 2.927,40 € überwiesen und wie folgt verrechnet.",
			"RG-2026-1187",
			"02.11.2026",
			"ER-2026-0101",
			"47,60 €",
			"Erhaltene Skonti",
			"-47,60 €",
			"2.927,40 €",
			"SEPA-2026-11-27-0311",
			"Unser Konto",
		),
		(*NO_DEMAND, NO_PAYMENT, "fehlt etwas"),
		papers=("eigenes-papier", "briefpapier"),
		kept=(TRANSFERRED, SETTLED),
		table_head=HEAD,
		**ADVICE,
	),
	Case(
		"ZA-2026-0003",
		(1, 1),
		"Paid",
		(
			"Remittance Advice ZA-2026-0003",
			"we paid the amount of 1.350,00 €",
			"FA-26-00981",
			"Not applied to an invoice",
			"100,00 €",
			"L-0007",
		),
		("Please transfer", "Cash Discount", "Our account"),
		language="en",
		particulars=ENGLISH_PARTICULARS,
		kept=("Paid", "Settled"),
		table_head=ENGLISH_HEAD,
		**ADVICE,
	),
	Case(
		"ZA-2026-0004",
		(2, 8),
		TRANSFERRED,
		("Zahlungsavis ZA-2026-0004", "AB/2026/001", "AB/2026/042", "ER-2026-0242", "Skonto"),
		(*NO_DEMAND, NO_PAYMENT),
		kept=(TRANSFERRED, SETTLED),
		table_head=HEAD,
		**ADVICE,
	),
	Case(
		"ZA-2026-0005",
		(1, 1),
		TRANSFERRED,
		(
			"Diesem Zahlungsavis fehlt etwas:",
			"Die Rechnung ER-2026-0105 trägt keine Rechnungsnummer des Lieferanten.",
			"Wir haben am 27.11.2026 den Betrag von 980,00 € überwiesen",
		),
		(*NO_DEMAND, NO_PAYMENT, "Skonto"),
		kept=(TRANSFERRED, SETTLED),
		table_head=PLAIN_HEAD,
		**ADVICE,
	),
)

# Drafts and cancelled payments: the mark on every page and no payment announced.
CASES = (
	*CASES,
	Case(
		"ZA-2026-0002",
		(1, 1),
		TRANSFERRED,
		("Zahlungsavis ZA-2026-0002", NO_PAYMENT),
		(*NO_DEMAND, "überwiesen und", "Unser Konto"),
		kept=(TRANSFERRED, SETTLED),
		table_head=HEAD,
		variant="entwurf",
		docstatus=0,
		**ADVICE,
	),
	Case(
		"ZA-2026-0004",
		(2, 8),
		TRANSFERRED,
		("Zahlungsavis ZA-2026-0004", NO_PAYMENT),
		(*NO_DEMAND, "überwiesen und", "Unser Konto"),
		kept=(TRANSFERRED, SETTLED),
		table_head=HEAD,
		variant="storniert",
		docstatus=2,
		**ADVICE,
	),
)

# A print format of a Payment Entry chosen for the other direction prints a finding and announces or confirms
# nothing.
CASES = (
	*CASES,
	Case(
		"ZE-2026-0001",
		(1, 1),
		"",
		("Zahlungsavis ZE-2026-0001", NO_PAYMENT),
		(*NO_DEMAND, "überwiesen und", "gezahlt und", "Unser Konto", SETTLED, TRANSFERRED, "RE-2026-0202"),
		variant="eingang",
		**ADVICE,
	),
	Case(
		"ZA-2026-0002",
		(1, 1),
		"",
		("Zahlungsbestätigung ZA-2026-0002", "Dieses Dokument bestätigt nichts"),
		(*NO_DEMAND, "ist eingegangen", "Angerechnet", "Zahlungseingang", "ER-2026-0101"),
		variant="ausgang",
		doctype="Payment Entry",
		print_format="Zahlungsbestätigung",
	),
)

# The sums end where the column of the settled amounts ends; the text keeps its distance from the table.
ADVICE_LAYOUT = Layout(
	aligned=((SETTLED, SETTLED), (SETTLED, "Erhaltene Skonti"), (SETTLED, TRANSFERRED)),
	one_line=("vom 27.11.2026",),
	space_above=(HEAD, 4),
)
LAYOUTS = {
	"ZA-2026-0002": ADVICE_LAYOUT,
	"ZA-2026-0003": Layout(
		aligned=(("Settled", "Settled"), ("Settled", "Not applied to an invoice"), ("Settled", "Paid")),
		space_above=(ENGLISH_HEAD, 4),
	),
	"ZA-2026-0004": Layout(
		aligned=((SETTLED, SETTLED), (SETTLED, "Erhaltene Skonti"), (SETTLED, TRANSFERRED)),
		space_above=(HEAD, 4),
	),
	"ZA-2026-0005": Layout(aligned=((SETTLED, SETTLED), (SETTLED, TRANSFERRED)), space_above=(PLAIN_HEAD, 4)),
}


def run(directory: str) -> None:
	run_cases(directory, CASES, "# Zahlungsavise als PDF", listing, LAYOUTS)
