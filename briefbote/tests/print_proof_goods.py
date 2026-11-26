"""The proof of the print formats Anfrage, Lieferantenrücksendung and Packliste as PDF, for CI: the documents of
print_documents_goods.py with both PDF generators, on blank and on pre-printed paper, checked page by page with the
checks of print_proof.py:

	bench --site <site> execute briefbote.tests.print_proof_goods.run --kwargs "{'directory': '<directory>'}"

None of them is an invoice or names a price: none may ask for a transfer or carry an amount.
"""

from briefbote.tests.print_proof import ENGLISH_PARTICULARS, Case
from briefbote.tests.print_proof_sales import NO_INVOICE, NO_INVOICE_EN
from briefbote.tests.proof_runner import Layout, listing, run_cases

REQUEST = {"doctype": "Request for Quotation", "print_format": "Anfrage"}
RETURN = {"doctype": "Purchase Receipt", "print_format": "Lieferantenrücksendung"}
PACKING = {"doctype": "Packing Slip", "print_format": "Packliste"}
HEAD = "Pos. Bezeichnung Menge Einheit"
HEAD_EN = "Pos. Description Quantity Unit"
PACKING_HEAD = "Packstück Bezeichnung Menge Einheit"
NO_PRICES = (*NO_INVOICE, "Gesamtbetrag", "Einzelpreis", "Nettobetrag", "Umsatzsteuer")
NO_PRICES_EN = (*NO_INVOICE_EN, "Total Amount", "Unit Price", "Net Amount")
ASK = "Bitte nennen Sie in Ihrem Angebot"
TAKEN_OVER = "Ware zur Rücksendung übernommen"

CASES = (
	Case(
		"AF-2026-0001",
		(1, 1),
		"Lieferanschrift",
		(
			"Anfrage AF-2026-0001",
			"Max Bauer",
			"Benötigt bis 08.12.2026",
			"Unsere Artikelnummer GK-125",
			"Ihre Artikelnummer MT-4711",
			"bitten wir um Ihr Angebot",
			ASK,
			"Lieferbedingung FCA Baustadt",
			"Lieferanschrift: Lager Süd",
			"Einkaufsbedingungen",
		),
		NO_PRICES,
		papers=("eigenes-papier", "briefpapier"),
		table_head=HEAD,
		kept=("Schnellbauschrauben", ASK),
		**REQUEST,
	),
	Case(
		"AF-2026-0001",
		(1, 1),
		"Lieferanschrift",
		("Grafikbüro Klein", "Unsere Artikelnummer GK-125"),
		(*NO_PRICES, "Ihre Artikelnummer", "Max Bauer"),
		table_head=HEAD,
		kept=("Schnellbauschrauben", ASK),
		variant="grafikbuero-klein",
		for_supplier="Grafikbüro Klein",
		**REQUEST,
	),
	Case(
		"AF-2026-0002",
		(2, 8),
		"Bitte nennen Sie auch",
		("Anfrage AF-2026-0002", "Profil 35, Stahl verzinkt", "Bedarfstermine 08.12.2026 bis 22.12.2026"),
		NO_PRICES,
		table_head=HEAD,
		kept=("Profil 35, Stahl verzinkt", ASK),
		**REQUEST,
	),
	Case(
		"AF-2026-0003",
		(1, 1),
		"Please state in your quotation",
		(
			"Request for Quotation AF-2026-0003",
			"Required by 15.01.2027",
			"Please quote the price per unit; the quantity is still open.",
			"Please supply the specified items",
		),
		(*NO_PRICES_EN, "Delivery terms"),
		language="en",
		particulars=ENGLISH_PARTICULARS,
		table_head=HEAD_EN,
		kept=("Additional hour of layout", "Please state in your quotation"),
		**REQUEST,
	),
	Case(
		"AF-2026-0004",
		(1, 1),
		"",
		("Diese Anfrage kann so nicht versandt werden", "nennt keinen Lieferanten"),
		(*NO_PRICES, ASK, "Gipskartonplatte"),
		unsent=True,
		**REQUEST,
	),
	Case(
		"RS-2026-0001",
		(1, 1),
		TAKEN_OVER,
		(
			"Rücksendung RS-2026-0001 zu unserem Wareneingang WE-2026-0001",
			"Warenannahme Halle 2",
			"Ihr Lieferschein LF-88231",
			"Unsere Bestellung BE-2026-0001",
			"Frachtführer Spedition Beispiel KG",
			"Seriennummern: BS18-26-1041, BS18-26-1042",
			"Davon beim Wareneingang abgelehnt: 4",
			"Charge: CH-D-0815",
			"Gesamtgewicht netto: 38,5 kg",
			"Abholanschrift: Lager Süd",
			"Unterschrift",
		),
		NO_PRICES,
		papers=("eigenes-papier", "briefpapier"),
		table_head=HEAD,
		kept=("Dämmplatte Mineralwolle 50 mm", TAKEN_OVER, "Unterschrift"),
		**RETURN,
	),
	Case(
		"RS-2026-0002",
		(2, 8),
		TAKEN_OVER,
		("Rücksendung RS-2026-0002", "Dämmplatte 35, Mineralwolle 50 mm"),
		(*NO_PRICES, "abgelehnt"),
		table_head=HEAD,
		kept=("Dämmplatte 35, Mineralwolle 50 mm", TAKEN_OVER),
		**RETURN,
	),
	Case(
		"RS-2026-0003",
		(1, 1),
		"Goods taken over for return",
		("Return Shipment RS-2026-0003", "Rejected on receipt.", "Signature"),
		NO_PRICES_EN,
		language="en",
		particulars=ENGLISH_PARTICULARS,
		table_head=HEAD_EN,
		kept=("Printed brochure, 500 copies", "Goods taken over for return"),
		**RETURN,
	),
	Case(
		"WE-2026-0001",
		(1, 1),
		"",
		("Dieses Dokument ist keine Rücksendung an den Lieferanten", "Wareneingang ist keine Rücksendung"),
		(*NO_PRICES, TAKEN_OVER, "Akku-Bohrschrauber"),
		unsent=True,
		**RETURN,
	),
	Case(
		"PK-2026-0001",
		(1, 1),
		"Gesamt",
		(
			"Packliste: Packstücke 1 bis 3 zum Lieferschein LS-2026-0001",
			"Wareneingang Tor 3",
			"Lieferschein LS-2026-0001 vom 23.11.2026",
			"Ihre Bestellung B-4711",
			"Packstücke 2 bis 3 29 kg 31,5 kg",
			"Gesamt 41,6 kg 45,7 kg",
		),
		(*NO_PRICES, "349,00", "Unterschrift"),
		papers=("eigenes-papier", "briefpapier"),
		table_head=PACKING_HEAD,
		kept=("Montagewinkel verzinkt", "Gesamt"),
		**PACKING,
	),
	Case(
		"PK-2026-0003",
		(2, 8),
		"Gesamt",
		("Packliste: Packstücke 1 bis 8 zum Lieferschein LS-2026-0002", "Packstücke 6 bis 8", "Regal 39"),
		(*NO_PRICES, "Unterschrift"),
		table_head=PACKING_HEAD,
		kept=("Regal 39, Lagerregal verzinkt", "Gesamt"),
		**PACKING,
	),
	Case(
		"PK-2026-0007",
		(1, 1),
		"Net weight",
		(
			"Packing List: Package 1 for Delivery Note LS-2026-0003",
			"UNITED STATES",
			"Net weight 98 kg · Gross weight 112 kg",
		),
		(*NO_PRICES_EN, "Total"),
		language="en",
		particulars=ENGLISH_PARTICULARS,
		table_head="Package Description Quantity Unit",
		kept=("Montagewinkel verzinkt", "Net weight"),
		**PACKING,
	),
)


# Drafts and cancelled documents: the mark on every page and no call to act; a draft packing slip lists only itself.
CASES = (
	*CASES,
	Case(
		"AF-2026-0001",
		(1, 1),
		"Lieferanschrift",
		("Anfrage AF-2026-0001",),
		(*NO_PRICES, ASK, "bitten wir um Ihr Angebot"),
		table_head=HEAD,
		kept=("Schnellbauschrauben", "Lieferanschrift"),
		variant="entwurf",
		docstatus=0,
		**REQUEST,
	),
	Case(
		"AF-2026-0002",
		(2, 8),
		"Profil 35, Stahl verzinkt",
		("Anfrage AF-2026-0002",),
		(*NO_PRICES, ASK),
		table_head=HEAD,
		kept=("Profil 35, Stahl verzinkt",),
		variant="storniert",
		docstatus=2,
		**REQUEST,
	),
	Case(
		"RS-2026-0001",
		(1, 1),
		"Abholanschrift",
		("Rücksendung RS-2026-0001",),
		(*NO_PRICES, TAKEN_OVER, "Unterschrift"),
		table_head=HEAD,
		kept=("Dämmplatte Mineralwolle 50 mm", "Abholanschrift"),
		variant="storniert",
		docstatus=2,
		**RETURN,
	),
	Case(
		"PK-2026-0002",
		(1, 1),
		"Nettogewicht",
		(
			"Packliste: Packstücke 2 bis 3 zum Lieferschein LS-2026-0001",
			"Nettogewicht 29 kg · Bruttogewicht 31,5 kg",
		),
		(*NO_PRICES, "Etikettendrucker", "Gesamt 4"),
		table_head=PACKING_HEAD,
		kept=("Montagewinkel verzinkt", "Nettogewicht"),
		variant="entwurf",
		docstatus=0,
		**PACKING,
	),
)


# „vom“ and its date stand together in the information block; the lines to sign on are painted.
LAYOUTS = {
	"RS-2026-0001": Layout(one_line=("vom 20.11.2026",), rules_above=("Unterschrift", "Druckbuchstaben")),
	"RS-2026-0003": Layout(rules_above=("Signature",)),
	"PK-2026-0001": Layout(one_line=("vom 23.11.2026",)),
}


def run(directory: str) -> None:
	run_cases(directory, CASES, "# Anfragen, Rücksendungen und Packlisten als PDF", listing, LAYOUTS)
