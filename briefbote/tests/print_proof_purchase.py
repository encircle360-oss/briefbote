"""The proof of the print format Bestellung as PDF, for CI: the purchase orders of print_documents_purchase.py with
both PDF generators, checked page by page with the checks of print_proof.py:

	bench --site <site> execute briefbote.tests.print_proof_purchase.run --kwargs "{'directory': '<directory>'}"
"""

from pathlib import Path

from briefbote.tests.print_proof import ENGLISH_PARTICULARS, Case
from briefbote.tests.print_proof_dunning import run_cases
from briefbote.tests.print_proof_sales import NO_INVOICE, NO_INVOICE_EN, proof

ORDER = {"doctype": "Purchase Order", "print_format": "Bestellung"}

CASES = (
	Case(
		"BE-2026-0001",
		(1, 1),
		"Gesamtbetrag",
		(
			"Bestellung BE-2026-0001",
			"Liefertermin 08.12.2026",
			"Lieferanschrift",
			"Lager Süd",
			"Umsatzsteuer 19 % auf 768,00 €",
			"Ihre Artikelnummer L-0001",
			"Zahlungsbedingungen: 30 Tage netto",
			"Bitte bestätigen Sie uns diese Bestellung",
		),
		(*NO_INVOICE, "Vorsteuer"),
		papers=("eigenes-papier", "briefpapier"),
		**ORDER,
	),
	Case(
		"BE-2026-0002",
		(2, 8),
		"Gesamtbetrag",
		("Bestellung BE-2026-0002", "Profil 35", "Liefertermine"),
		(*NO_INVOICE, "Vorsteuer"),
		**ORDER,
	),
	Case(
		"BE-2026-0003",
		(1, 1),
		"Gesamtbetrag",
		("Bestellung BE-2026-0003", "Steuerschuldnerschaft des Leistungsempfängers"),
		(*NO_INVOICE, "Umsatzsteuer 19 %", "Vorsteuer", "Umsatzsteuer 13b"),
		**ORDER,
	),
	Case(
		"BE-2026-0004",
		(1, 1),
		"Total Amount",
		("Purchase Order BE-2026-0004", "Scheduled Delivery"),
		(*NO_INVOICE_EN, "VAT 19 %"),
		language="en",
		particulars=ENGLISH_PARTICULARS,
		**ORDER,
	),
)


def run(directory: str) -> None:
	run_cases(Path(directory), CASES, "# Bestellungen als PDF", proof)
