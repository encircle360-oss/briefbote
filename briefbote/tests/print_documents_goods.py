"""The requests for quotation, returns to suppliers and packing slips of the proof, written to a test site as ERPNext
keeps them once submitted. It runs after print_documents.run, print_documents_sales.run and
print_documents_purchase.run, whose company, suppliers, delivery notes, purchase orders and warehouse address it
uses. A second run changes nothing.

	bench --site <site> execute briefbote.tests.print_documents_goods.run

A return keeps its quantities negative, the accepted one in qty and the rejected one in rejected_qty, as
make_return_doc in erpnext/controllers/sales_and_purchase_return.py writes them. A Packing Slip names the rows of
its delivery note in dn_detail and its packages in from_case_no and to_case_no
(erpnext/stock/doctype/packing_slip/packing_slip.py).
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

import frappe

from briefbote.tests.print_documents import COMPANY, SUPPLIERS, insert
from briefbote.tests.print_documents_sales import LONG_TEXT, delivery_notes

REQUESTED = date(2026, 11, 24)
REQUIRED = date(2026, 12, 8)
WAREHOUSE = "Beispiel GmbH-Lager"
MESSAGE = (
	"<p>Sehr geehrte Damen und Herren,</p><p>für den Ausbau unseres Lagers bitten wir um Ihr Angebot über die "
	"folgenden Positionen.</p>"
)
# The items of the proof with our item number and, for the supplier Muster Trockenbau GmbH, its own.
ITEMS = {
	"GK-125": ("Gipskartonplatte 12,5 mm", "MT-4711"),
	"CW-50": ("Ständerprofil CW 50, 2.600 mm", "MT-0815"),
	"SCH-35": ("Schnellbauschrauben 3,5 x 35 mm", ""),
}


@dataclass
class Line:
	name: str
	qty: Decimal
	uom: str = "Stück"
	item_code: str = ""
	description: str = ""
	required: date | None = None


@dataclass
class Request:
	name: str
	suppliers: list[str]
	lines: list[Line]
	message: str = MESSAGE
	incoterm: str = ""
	place: str = ""
	ship_to: bool = True
	terms: str = ""


def requests() -> list[Request]:
	many = [
		Line(
			f"Profil {index:02d}, Stahl verzinkt",
			Decimal(index % 7 + 5),
			description=LONG_TEXT if index % 6 == 0 else "Länge 3.000 mm",
			required=REQUIRED + timedelta(days=7 * (index % 3)),
		)
		for index in range(36)
	]
	return [
		Request(
			"AF-2026-0001",
			["bau", "klein"],
			[
				Line("Gipskartonplatte 12,5 mm", Decimal(120), item_code="GK-125", required=REQUIRED),
				Line("Ständerprofil CW 50, 2.600 mm", Decimal(80), item_code="CW-50", required=REQUIRED),
				Line(
					"Schnellbauschrauben 3,5 x 35 mm",
					Decimal(10),
					uom="Packung",
					item_code="SCH-35",
					description="1.000 Stück je Packung",
					required=REQUIRED,
				),
			],
			incoterm="FCA",
			place="Baustadt",
			terms="<p>Es gelten unsere Einkaufsbedingungen.</p>",
		),
		Request("AF-2026-0002", ["bau"], many),
		Request(
			"AF-2026-0003",
			["klein"],
			[
				Line("Design of the annual report", Decimal(1), uom="Pauschal", required=date(2027, 1, 15)),
				Line("Additional hour of layout", Decimal(0), uom="Stunde"),
			],
			message="<p>Please supply the specified items at the best possible rates.</p>",
			ship_to=False,
		),
		Request("AF-2026-0004", [], [Line("Gipskartonplatte 12,5 mm", Decimal(40), item_code="GK-125")]),
	]


@dataclass
class Receipt:
	name: str
	supplier: str
	lines: list[Line]
	day: date = date(2026, 11, 26)
	is_return: bool = False
	return_against: str = ""
	delivery_note: str = ""
	rejected: dict[int, Decimal] = field(default_factory=dict)
	from_rejected: tuple[int, ...] = ()
	serials: dict[int, list[str]] = field(default_factory=dict)
	batches: dict[int, str] = field(default_factory=dict)
	order: str = ""
	weight: Decimal = Decimal(0)
	dispatch: bool = False
	carrier: str = ""
	language: str = "de"


DISPATCH = ("Muster Trockenbau GmbH", "Warenannahme Halle 2", "Industrieweg 11", "34569", "Baustadt")


def receipts() -> list[Receipt]:
	panels = [
		Line(
			f"Dämmplatte {index:02d}, Mineralwolle 50 mm",
			Decimal(-(index % 4 + 1)),
			uom="Paket",
			description=LONG_TEXT if index % 7 == 0 else "Wärmeleitstufe 035",
		)
		for index in range(36)
	]
	return [
		Receipt(
			"WE-2026-0001",
			"bau",
			[
				Line("Akku-Bohrschrauber BS-18", Decimal(4)),
				Line("Dämmplatte Mineralwolle 50 mm", Decimal(30), uom="Paket"),
			],
			day=date(2026, 11, 20),
			delivery_note="LF-88231",
			order="BE-2026-0001",
		),
		Receipt("WE-2026-0002", "bau", [Line("Dämmplatte Mineralwolle 50 mm", Decimal(90), uom="Paket")]),
		Receipt(
			"RS-2026-0001",
			"bau",
			[
				Line("Akku-Bohrschrauber BS-18", Decimal(-2)),
				Line("Dämmplatte Mineralwolle 50 mm", Decimal(-6), uom="Paket"),
			],
			is_return=True,
			return_against="WE-2026-0001",
			delivery_note="LF-88231",
			rejected={2: Decimal(-4)},
			serials={1: ["BS18-26-1041", "BS18-26-1042"]},
			batches={2: "CH-D-0815"},
			order="BE-2026-0001",
			weight=Decimal("-38.5"),
			dispatch=True,
			carrier="Spedition Beispiel KG",
		),
		Receipt(
			"RS-2026-0002",
			"bau",
			panels,
			is_return=True,
			return_against="WE-2026-0002",
			day=date(2026, 11, 27),
		),
		Receipt(
			"WE-2026-0003",
			"klein",
			[Line("Printed brochure, 500 copies", Decimal(0), uom="Pauschal")],
			rejected={1: Decimal(1)},
			language="en",
		),
		Receipt(
			"RS-2026-0003",
			"klein",
			[Line("Printed brochure, 500 copies", Decimal(-1), uom="Pauschal")],
			is_return=True,
			return_against="WE-2026-0003",
			from_rejected=(1,),
			language="en",
		),
	]


@dataclass
class Packed:
	"""A Packing Slip: its packages, the rows of the delivery note it packs with their quantities, and its weights."""

	name: str
	delivery_note: str
	first: int
	last: int
	rows: list[tuple[int, Decimal, Decimal]]
	gross: Decimal = Decimal(0)
	weight_uom: str = "kg"


def packing_slips() -> list[Packed]:
	shelves = [
		Packed(
			f"PK-2026-{number:04d}",
			"LS-2026-0002",
			first,
			last,
			[(index, Decimal(0), Decimal("18.5")) for index in rows],
		)
		for number, (first, last, rows) in enumerate(
			(
				(1, 2, range(1, 11)),
				(3, 4, range(11, 21)),
				(5, 5, range(21, 31)),
				(6, 8, range(31, 41)),
			),
			start=3,
		)
	]
	return [
		Packed(
			"PK-2026-0001", "LS-2026-0001", 1, 1, [(1, Decimal(3), Decimal("4.2"))], gross=Decimal("14.2")
		),
		Packed(
			"PK-2026-0002",
			"LS-2026-0001",
			2,
			3,
			[(2, Decimal(24), Decimal("0.4")), (3, Decimal(200), Decimal("0.097"))],
			gross=Decimal("31.5"),
		),
		*shelves,
		Packed(
			"PK-2026-0007",
			"LS-2026-0003",
			1,
			1,
			[(1, Decimal(12), Decimal("7.5")), (2, Decimal(200), Decimal("0.04"))],
			gross=Decimal(112),
		),
	]


def run() -> None:
	for code, (name, part) in ITEMS.items():
		insert("Item", name=code, item_code=code, item_name=name, stock_uom="Stück", item_group="Products")
		if part:
			insert(
				"Item Supplier",
				name=f"{code}-bau",
				parent=code,
				parenttype="Item",
				parentfield="supplier_items",
				idx=1,
				supplier=SUPPLIERS["bau"].name,
				supplier_part_no=part,
			)
	insert(
		"Contact",
		name="Max Bauer-Muster Trockenbau GmbH",
		first_name="Max",
		last_name="Bauer",
		full_name="Max Bauer",
	)
	for item in requests():
		write_request(item)
	address = insert(
		"Address",
		name="Muster Trockenbau GmbH-Lager",
		address_title=DISPATCH[0],
		address_type="Shipping",
		address_line1=DISPATCH[1],
		address_line2=DISPATCH[2],
		pincode=DISPATCH[3],
		city=DISPATCH[4],
		country="Germany",
	)
	insert(
		"Dynamic Link",
		name=f"{address}-Supplier",
		parent=address,
		parenttype="Address",
		parentfield="links",
		idx=1,
		link_doctype="Supplier",
		link_name=SUPPLIERS["bau"].name,
	)
	for receipt in receipts():
		write_receipt(receipt)
	for slip in packing_slips():
		write_packing_slip(slip)
	frappe.clear_cache()


def write_request(item: Request) -> None:
	if frappe.db.exists("Request for Quotation", item.name):
		return
	for index, key in enumerate(item.suppliers, start=1):
		supplier = SUPPLIERS[key].name
		insert(
			"Request for Quotation Supplier",
			name=f"{item.name}-supplier-{index}",
			parent=item.name,
			parenttype="Request for Quotation",
			parentfield="suppliers",
			idx=index,
			docstatus=1,
			supplier=supplier,
			supplier_name=supplier,
			contact="Max Bauer-Muster Trockenbau GmbH" if key == "bau" else None,
			send_email=1,
		)
	for index, line in enumerate(item.lines, start=1):
		insert(
			"Request for Quotation Item",
			name=f"{item.name}-{index:03d}",
			parent=item.name,
			parenttype="Request for Quotation",
			parentfield="items",
			idx=index,
			docstatus=1,
			item_code=line.item_code or None,
			item_name=line.name,
			description=line.description or line.name,
			qty=line.qty,
			uom=line.uom,
			stock_uom=line.uom,
			conversion_factor=1,
			stock_qty=line.qty,
			schedule_date=line.required,
		)
	dates = [line.required for line in item.lines if line.required]
	insert(
		"Request for Quotation",
		name=item.name,
		company=COMPANY,
		transaction_date=REQUESTED,
		schedule_date=min(dates) if dates else None,
		status="Submitted",
		docstatus=1,
		subject="Request for Quotation",
		message_for_supplier=item.message,
		incoterm=item.incoterm or None,
		named_place=item.place or None,
		shipping_address=WAREHOUSE if item.ship_to else None,
		has_unit_price_items=int(any(not line.qty for line in item.lines)),
		terms=item.terms,
	)


def write_receipt(receipt: Receipt) -> None:
	if frappe.db.exists("Purchase Receipt", receipt.name):
		return
	supplier = SUPPLIERS[receipt.supplier].name
	for index, line in enumerate(receipt.lines, start=1):
		row = f"{receipt.name}-{index:03d}"
		rejected = receipt.rejected.get(index, Decimal(0))
		bundle = None
		if index in receipt.serials:
			bundle = insert(
				"Serial and Batch Bundle",
				name=f"SABB-{row}",
				company=COMPANY,
				item_name=line.name,
				voucher_type="Purchase Receipt",
				voucher_no=receipt.name,
				type_of_transaction="Outward" if receipt.is_return else "Inward",
				docstatus=1,
			)
			for number, serial in enumerate(receipt.serials[index], start=1):
				insert(
					"Serial and Batch Entry",
					name=f"SABB-{row}-{number:03d}",
					parent=bundle,
					parenttype="Serial and Batch Bundle",
					parentfield="entries",
					idx=number,
					docstatus=1,
					serial_no=serial,
					qty=-1 if receipt.is_return else 1,
				)
		insert(
			"Purchase Receipt Item",
			name=row,
			parent=receipt.name,
			parenttype="Purchase Receipt",
			parentfield="items",
			idx=index,
			docstatus=1,
			item_name=line.name,
			description=line.description or line.name,
			qty=line.qty,
			rejected_qty=rejected,
			received_qty=line.qty + rejected,
			uom=line.uom,
			stock_uom=line.uom,
			conversion_factor=1,
			purchase_order=receipt.order or None,
			batch_no=receipt.batches.get(index),
			serial_and_batch_bundle=bundle,
			weight_uom="kg" if receipt.weight else None,
			return_qty_from_rejected_warehouse=int(index in receipt.from_rejected),
		)
	insert(
		"Purchase Receipt",
		name=receipt.name,
		company=COMPANY,
		supplier=supplier,
		supplier_name=supplier,
		supplier_address=f"{supplier}-Billing",
		dispatch_address="Muster Trockenbau GmbH-Lager" if receipt.dispatch else None,
		shipping_address=WAREHOUSE if receipt.is_return and receipt.supplier == "bau" else None,
		supplier_delivery_note=receipt.delivery_note or None,
		posting_date=receipt.day,
		currency="EUR",
		conversion_rate=1,
		docstatus=1,
		is_return=int(receipt.is_return),
		return_against=receipt.return_against or None,
		transporter_name=receipt.carrier or None,
		total_net_weight=receipt.weight,
		language=receipt.language,
	)


def write_packing_slip(slip: Packed) -> None:
	if frappe.db.exists("Packing Slip", slip.name):
		return
	shipment = next(note for note in delivery_notes() if note.name == slip.delivery_note)
	net = Decimal(0)
	for index, (position, qty, weight) in enumerate(slip.rows, start=1):
		line = shipment.positions[position - 1]
		qty = qty or line.qty
		net += qty * weight
		insert(
			"Packing Slip Item",
			name=f"{slip.name}-{index:03d}",
			parent=slip.name,
			parenttype="Packing Slip",
			parentfield="items",
			idx=index,
			docstatus=1,
			item_name=line.name,
			description=line.description or line.name,
			qty=qty,
			stock_uom=line.uom,
			net_weight=weight or None,
			weight_uom=slip.weight_uom if weight else None,
			dn_detail=f"{slip.delivery_note}-{position:03d}",
		)
	insert(
		"Packing Slip",
		name=slip.name,
		delivery_note=slip.delivery_note,
		from_case_no=slip.first,
		to_case_no=slip.last,
		net_weight_pkg=net,
		net_weight_uom=slip.weight_uom if net else None,
		gross_weight_pkg=slip.gross or net,
		gross_weight_uom=slip.weight_uom if slip.gross or net else None,
		docstatus=1,
	)
