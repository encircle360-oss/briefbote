"""The documents of sales for the proof of the printouts: quotations, sales orders and delivery notes of the invented companies of
print_documents.py, written to a test site as ERPNext keeps them once submitted.

	bench --site <site> execute briefbote.tests.print_documents_sales.run

It runs after print_documents.run, whose companies, customers, templates and settings it uses. The taxes are those of
the German templates of ERPNext: each tax line has the rate 0 and names an account, each position carries the rate of
its item tax template in the tax details, and the net amount of a line counts every position whose template names its
account, also at 0 % (erpnext/setup/setup_wizard/data/country_wise_tax.json, get_current_tax_and_net_amount in
erpnext/controllers/taxes_and_totals.py). A second run changes nothing.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

import frappe

from briefbote.tests.print_documents import (
	ABBR,
	COMPANY,
	CUSTOMERS,
	GERMAN_ACCOUNTS,
	SMALL_ABBR,
	SMALL_COMPANY,
	Invoice,
	Item,
	insert,
	make_invoice,
	money,
)

QUOTED = date(2026, 11, 16)
ORDERED = date(2026, 11, 20)
# The tax lines of the template „Lieferung oder sonstige Leistung im Inland“ and the item tax templates of the rates.
TAX_LINES = (19, 7)
DOMESTIC = "Lieferung oder sonstige Leistung im Inland"
EU_SERVICE = "Sonstige Leistung an Unternehmen in der EU"


@dataclass
class Position:
	name: str
	qty: Decimal
	rate: Decimal
	uom: str = "Stunde"
	description: str = ""
	tax_rate: int = 19
	alternative: bool = False
	delivery: date | None = None
	quotation: str = ""


@dataclass
class Sale:
	name: str
	customer: str
	template: str
	positions: list[Position]
	company: str = COMPANY
	day: date = QUOTED
	valid_till: date | None = None
	po_no: str = ""
	po_date: date | None = None
	delivery: date | None = None
	period: tuple[date, date] | None = None
	schedule: list[tuple[Decimal, str, str, date]] = field(default_factory=list)
	terms: str = ""
	language: str = "de"


TERMS = (
	"<p>Es gelten unsere Allgemeinen Geschäftsbedingungen in der Fassung vom 01.01.2026. "
	"Preise in Euro zuzüglich der gesetzlichen Umsatzsteuer.</p>"
)
LONG_TEXT = (
	"Konzeption, Einrichtung und Test der Schnittstelle zwischen Warenwirtschaft und Onlineshop einschließlich "
	"Übernahme der Artikelstammdaten und Einweisung der Mitarbeiterinnen und Mitarbeiter vor Ort"
)


def quotations() -> list[Sale]:
	many = [
		Position(
			f"Modul {index:02d} Einrichtung",
			Decimal(index % 5 + 1),
			Decimal("118.00") + index,
			description=LONG_TEXT if index % 4 == 0 else "Einrichtung nach Leistungsbeschreibung",
			tax_rate=7 if index % 6 == 0 else 19,
			uom="Stunde" if index % 6 else "Stück",
		)
		for index in range(1, 37)
	]
	return [
		Sale(
			"AN-2026-0001",
			"inland",
			DOMESTIC,
			[
				Position(
					"Einführung ERP, Konzeptphase",
					Decimal(24),
					Decimal("120.00"),
					description="Workshops vor Ort",
				),
				Position("Schulung der Anwender", Decimal(2), Decimal("950.00"), uom="Tag"),
				Position(
					"Schulung der Anwender als Onlinekurs",
					Decimal(2),
					Decimal("690.00"),
					uom="Tag",
					alternative=True,
				),
				Position("Fachbuch Buchhaltung", Decimal(3), Decimal("39.90"), uom="Stück", tax_rate=7),
			],
			valid_till=date(2026, 12, 18),
			schedule=[(Decimal(100), "14 Tage netto", "", QUOTED + timedelta(days=14))],
			terms=TERMS,
		),
		Sale("AN-2026-0002", "inland", DOMESTIC, many, valid_till=date(2026, 12, 31), terms=TERMS),
		Sale(
			"AN-2026-0003",
			"privat",
			DOMESTIC,
			[
				Position("Einbau Küchenarbeitsplatte", Decimal(1), Decimal("680.00"), uom="Pauschal"),
				Position("Zusätzliche Arbeitsstunde Montage", Decimal(0), Decimal("65.00")),
			],
		),
		Sale(
			"AN-2026-0004",
			"lang",
			EU_SERVICE,
			[
				Position(
					"Softwareentwicklung nach Aufwand", Decimal(40), Decimal("110.00"), description=LONG_TEXT
				)
			],
			valid_till=date(2026, 12, 15),
			language="en",
		),
		Sale(
			"KA-2026-0001",
			"privat",
			"",
			[Position("Gartenpflege Frühjahr", Decimal(8), Decimal("35.00"))],
			company=SMALL_COMPANY,
			valid_till=date(2027, 1, 31),
		),
	]


def sales_orders() -> list[Sale]:
	deliveries = [date(2026, 12, 1) + timedelta(days=7 * (index % 4)) for index in range(30)]
	return [
		Sale(
			"AB-2026-0001",
			"inland",
			DOMESTIC,
			[
				Position(
					"Einführung ERP, Konzeptphase",
					Decimal(24),
					Decimal("120.00"),
					description="Workshops vor Ort",
					quotation="AN-2026-0001",
				),
				Position(
					"Schulung der Anwender",
					Decimal(2),
					Decimal("950.00"),
					uom="Tag",
					quotation="AN-2026-0001",
				),
				Position(
					"Fachbuch Buchhaltung",
					Decimal(3),
					Decimal("39.90"),
					uom="Stück",
					tax_rate=7,
					quotation="AN-2026-0001",
				),
			],
			day=ORDERED,
			po_no="B-4711",
			po_date=date(2026, 11, 18),
			delivery=date(2026, 12, 15),
			schedule=[
				(Decimal(30), "Anzahlung", "Anzahlung bei Auftragserteilung", ORDERED + timedelta(days=7)),
				(Decimal(70), "Restzahlung", "Rest 14 Tage nach Abnahme", date(2027, 1, 15)),
			],
			terms=TERMS,
		),
		Sale(
			"AB-2026-0002",
			"inland",
			DOMESTIC,
			[
				Position(
					f"Regal {index:02d}, Lagerregal verzinkt",
					Decimal(index % 6 + 1),
					Decimal("219.00") + index,
					uom="Stück",
					description=LONG_TEXT if index % 5 == 0 else "Montage inklusive",
					delivery=deliveries[index],
				)
				for index in range(30)
			],
			day=ORDERED,
			po_no="B-4802",
			delivery=date(2026, 12, 22),
		),
		Sale(
			"AB-2026-0003",
			"inland",
			DOMESTIC,
			[Position("Wartung und Betreuung ERP, monatlich", Decimal(12), Decimal("450.00"), uom="Monat")],
			day=ORDERED,
			delivery=date(2027, 1, 1),
			period=(date(2027, 1, 1), date(2027, 12, 31)),
			schedule=[(Decimal(100), "", "Monatlich im Voraus", ORDERED)],
			language="en",
		),
	]


def run() -> None:
	for sale in quotations():
		write("Quotation", sale)
	for sale in sales_orders():
		write("Sales Order", sale)
	write_delivery_notes()
	write_advances()
	frappe.clear_cache()


def write(doctype: str, sale: Sale) -> None:
	"""A submitted Quotation or Sales Order with its positions, tax lines, tax details and payment schedule."""
	if frappe.db.exists(doctype, sale.name):
		return
	customer = CUSTOMERS[sale.customer]
	abbr = ABBR if sale.company == COMPANY else SMALL_ABBR
	taxed = sale.template == DOMESTIC
	item_doctype = f"{doctype} Item"
	counted: list[tuple[str, Position, Decimal]] = []
	for index, position in enumerate(sale.positions, start=1):
		row = f"{sale.name}-{index:03d}"
		amount = money(position.qty * position.rate)
		fields = {
			"name": row,
			"parent": sale.name,
			"parenttype": doctype,
			"parentfield": "items",
			"idx": index,
			"docstatus": 1,
			"item_name": position.name,
			"description": position.description or position.name,
			"qty": position.qty,
			"uom": position.uom,
			"stock_uom": position.uom,
			"conversion_factor": 1,
			"rate": position.rate,
			"amount": amount,
			"net_rate": position.rate,
			"net_amount": amount,
			"base_rate": position.rate,
			"base_amount": amount,
			"base_net_amount": amount,
			"item_tax_template": f"Umsatzsteuer {position.tax_rate} % - {abbr}" if taxed else None,
		}
		if doctype == "Quotation":
			fields["is_alternative"] = int(position.alternative)
			fields["has_alternative_item"] = int(
				index < len(sale.positions) and sale.positions[index].alternative and not position.alternative
			)
		else:
			fields["delivery_date"] = position.delivery or sale.delivery
			fields["prevdoc_docname"] = position.quotation or None
		insert(item_doctype, **fields)
		if not position.alternative:
			counted.append((row, position, amount))
	net = sum((amount for _row, _position, amount in counted), Decimal(0))
	tax_total, running = Decimal(0), net
	if taxed:
		for index, rate in enumerate(TAX_LINES, start=1):
			tax = money(
				sum((amount for _r, p, amount in counted if p.tax_rate == rate), Decimal(0)) * rate / 100
			)
			tax_total += tax
			running += tax
			insert(
				"Sales Taxes and Charges",
				name=f"{sale.name}-tax-{index}",
				parent=sale.name,
				parenttype=doctype,
				parentfield="taxes",
				idx=index,
				docstatus=1,
				charge_type="On Net Total",
				# The accounts the item tax templates name, so that ERPNext computes the same tax again where it
				# recalculates a copy of the order, as a Proforma Invoice does.
				account_head=f"{GERMAN_ACCOUNTS[rate]} - {abbr}",
				description=f"Umsatzsteuer {rate} %",
				rate=0,
				net_amount=net,
				base_net_amount=net,
				tax_amount=tax,
				base_tax_amount=tax,
				tax_amount_after_discount_amount=tax,
				base_tax_amount_after_discount_amount=tax,
				total=running,
				base_total=running,
			)
		for number, (row, position, amount) in enumerate(counted, start=1):
			for index, rate in enumerate(TAX_LINES, start=1):
				applied = rate if position.tax_rate == rate else 0
				insert(
					"Item Wise Tax Detail",
					name=f"{sale.name}-detail-{number:03d}-{index}",
					parent=sale.name,
					parenttype=doctype,
					parentfield="item_wise_tax_details",
					idx=(number - 1) * len(TAX_LINES) + index,
					docstatus=1,
					item_row=row,
					tax_row=f"{sale.name}-tax-{index}",
					rate=applied,
					taxable_amount=amount,
					amount=money(amount * applied / 100),
				)
	grand = net + tax_total
	for index, (portion, term, description, due) in enumerate(sale.schedule, start=1):
		insert(
			"Payment Schedule",
			name=f"{sale.name}-schedule-{index}",
			parent=sale.name,
			parenttype=doctype,
			parentfield="payment_schedule",
			idx=index,
			docstatus=1,
			payment_term=term or None,
			description=description,
			due_date=due,
			invoice_portion=portion,
			payment_amount=money(grand * portion / 100),
		)
	fields = {
		"name": sale.name,
		"company": sale.company,
		"customer_name": customer.name,
		"customer_address": f"{customer.name}-Billing",
		"transaction_date": sale.day,
		"currency": "EUR",
		"conversion_rate": 1,
		"docstatus": 1,
		"taxes_and_charges": f"{sale.template} - {abbr}" if sale.template else None,
		"language": sale.language,
		"total": net,
		"net_total": net,
		"base_total": net,
		"base_net_total": net,
		"total_taxes_and_charges": tax_total,
		"base_total_taxes_and_charges": tax_total,
		"grand_total": grand,
		"base_grand_total": grand,
		"rounded_total": grand,
		"base_rounded_total": grand,
		"rounding_adjustment": 0,
		"disable_rounded_total": 1,
		"terms": sale.terms,
	}
	if doctype == "Quotation":
		fields |= {
			"quotation_to": "Customer",
			"party_name": customer.name,
			"valid_till": sale.valid_till,
			"has_unit_price_items": int(any(not position.qty for position in sale.positions)),
		}
	else:
		fields |= {
			"customer": customer.name,
			"tax_id": customer.tax_id,
			"po_no": sale.po_no,
			"po_date": sale.po_date,
			"delivery_date": sale.delivery,
			"from_date": sale.period[0] if sale.period else None,
			"to_date": sale.period[1] if sale.period else None,
		}
	insert(doctype, **fields)


@dataclass
class Shipment:
	name: str
	customer: str
	positions: list[Position]
	company: str = COMPANY
	day: date = date(2026, 11, 23)
	order: str = ""
	po_no: str = ""
	po_date: date | None = None
	ship_to: str = ""
	serials: dict[int, list[str]] = field(default_factory=dict)
	batches: dict[int, list[tuple[str, Decimal]]] = field(default_factory=dict)
	is_return: bool = False
	return_against: str = ""
	weight: Decimal = Decimal(0)
	language: str = "de"
	without_amount: bool = False


# The warehouse of Kunde Muster AG, where the goods go rather than to the address of its invoices.
SHIP_TO = ("Kunde Muster AG", "Wareneingang Tor 3", "Industriestraße 40", "54329", "Beispielstadt")


def delivery_notes() -> list[Shipment]:
	shelves = [
		Position(
			f"Regal {index:02d}, Lagerregal verzinkt",
			Decimal(index % 6 + 1),
			Decimal("219.00") + index,
			uom="Stück",
			description=LONG_TEXT if index % 5 == 0 else "Montage inklusive",
		)
		for index in range(40)
	]
	return [
		Shipment(
			"LS-2026-0001",
			"inland",
			[
				Position("Etikettendrucker TD-200", Decimal(3), Decimal("349.00"), uom="Stück"),
				Position(
					"Etikettenrolle 100 x 50 mm", Decimal(24), Decimal("12.90"), uom="Stück", tax_rate=19
				),
				Position("Montagewinkel verzinkt", Decimal(200), Decimal("1.85"), uom="Stück"),
			],
			order="AB-2026-0001",
			po_no="B-4711",
			po_date=date(2026, 11, 18),
			ship_to="lager",
			serials={1: ["TD200-26-00417", "TD200-26-00418", "TD200-26-00419"]},
			batches={
				2: [("CH-2026-311", Decimal(16)), ("CH-2026-327", Decimal(8))],
				3: [("CH-2026-102", Decimal(200))],
			},
			weight=Decimal("41.6"),
		),
		Shipment("LS-2026-0002", "inland", shelves, order="AB-2026-0002", po_no="B-4802"),
		Shipment(
			"LS-2026-0003",
			"usa",
			[
				Position(
					"Eichenholzplatte 2000 x 600 mm, geölt", Decimal(12), Decimal("189.00"), uom="Stück"
				),
				Position("Montagewinkel verzinkt", Decimal(200), Decimal("1.85"), uom="Stück"),
			],
			language="en",
		),
		Shipment(
			"LS-2026-0004",
			"inland",
			[Position("Etikettendrucker TD-200", Decimal(-1), Decimal("349.00"), uom="Stück")],
			serials={1: ["TD200-26-00418"]},
			is_return=True,
			return_against="LS-2026-0001",
			day=date(2026, 11, 25),
		),
		Shipment(
			"KL-2026-0001",
			"privat",
			[Position("Blumenerde, 40 l", Decimal(6), Decimal("7.90"), uom="Sack")],
			company=SMALL_COMPANY,
		),
	]


def write_delivery_notes() -> None:
	"""The delivery notes, and the settings that print prices for the small business and no line for the signature."""
	frappe.db.set_value(
		"Business Document Settings",
		SMALL_COMPANY,
		{"delivery_note_prices": 1, "delivery_note_signature": 0},
	)
	address = insert(
		"Address",
		name="Kunde Muster AG-Lager",
		address_title=SHIP_TO[0],
		address_type="Shipping",
		address_line1=SHIP_TO[1],
		address_line2=SHIP_TO[2],
		pincode=SHIP_TO[3],
		city=SHIP_TO[4],
		country="Germany",
	)
	insert(
		"Dynamic Link",
		name=f"{address}-Customer",
		parent=address,
		parenttype="Address",
		parentfield="links",
		idx=1,
		link_doctype="Customer",
		link_name=CUSTOMERS["inland"].name,
	)
	for shipment in delivery_notes():
		write_delivery_note(shipment)


def write_delivery_note(shipment: Shipment) -> None:
	if frappe.db.exists("Delivery Note", shipment.name):
		return
	customer = CUSTOMERS[shipment.customer]
	net = Decimal(0)
	for index, position in enumerate(shipment.positions, start=1):
		row = f"{shipment.name}-{index:03d}"
		amount = money(position.qty * position.rate)
		net += amount
		bundle = None
		if index in shipment.serials or index in shipment.batches:
			bundle = insert(
				"Serial and Batch Bundle",
				name=f"SABB-{row}",
				company=shipment.company,
				item_name=position.name,
				voucher_type="Delivery Note",
				voucher_no=shipment.name,
				type_of_transaction="Inward" if shipment.is_return else "Outward",
				docstatus=1,
			)
			entries = [(serial, "", Decimal(1)) for serial in shipment.serials.get(index, [])]
			entries += [("", batch, qty) for batch, qty in shipment.batches.get(index, [])]
			for number, (serial, batch, qty) in enumerate(entries, start=1):
				insert(
					"Serial and Batch Entry",
					name=f"SABB-{row}-{number:03d}",
					parent=bundle,
					parenttype="Serial and Batch Bundle",
					parentfield="entries",
					idx=number,
					docstatus=1,
					serial_no=serial or None,
					batch_no=batch or None,
					qty=-qty if not shipment.is_return else qty,
				)
		insert(
			"Delivery Note Item",
			name=row,
			parent=shipment.name,
			parenttype="Delivery Note",
			parentfield="items",
			idx=index,
			docstatus=1,
			item_name=position.name,
			description=position.description or position.name,
			qty=position.qty,
			uom=position.uom,
			stock_uom=position.uom,
			conversion_factor=1,
			rate=position.rate,
			amount=amount,
			net_rate=position.rate,
			net_amount=amount,
			base_rate=position.rate,
			base_amount=amount,
			base_net_amount=amount,
			against_sales_order=shipment.order or None,
			weight_uom="kg" if shipment.weight else None,
			serial_and_batch_bundle=bundle,
		)
	insert(
		"Delivery Note",
		name=shipment.name,
		company=shipment.company,
		customer=customer.name,
		customer_name=customer.name,
		customer_address=f"{customer.name}-Billing",
		shipping_address_name="Kunde Muster AG-Lager" if shipment.ship_to else None,
		posting_date=shipment.day,
		currency="EUR",
		conversion_rate=1,
		docstatus=1,
		is_return=int(shipment.is_return),
		return_against=shipment.return_against or None,
		po_no=shipment.po_no,
		po_date=shipment.po_date,
		language=shipment.language,
		print_without_amount=int(shipment.without_amount),
		total_net_weight=shipment.weight,
		total=net,
		net_total=net,
		base_total=net,
		base_net_total=net,
		grand_total=net,
		base_grand_total=net,
		rounded_total=net,
		base_rounded_total=net,
		disable_rounded_total=1,
		taxes_and_charges=None,
		terms="",
	)


# The proformas and advance invoices of the orders, the advances received and the final invoices that deduct them
# (docs/proforma-rechnung.md, docs/anzahlungsrechnung.md, docs/rechnung.md).
ADVANCE_ORDER = "AB-2026-0010"
ADVANCE_INVOICE = "AZ-2026-0001"
FINAL_INVOICE = "RE-2026-0401"


@dataclass
class Proforma:
	"""A Proforma Invoice of an order: its lines by the number of the row of the order, with their quantity and, billed
	by amount, their amount and text."""

	name: str
	order: str
	day: date
	lines: list[tuple[int, Decimal, Decimal, str]]
	print_format: str = "Proforma-Rechnung"
	by_amount: bool = False


@dataclass
class Advance:
	"""A payment received from a customer: a Payment Entry, with a tax line of the rate included in the paid amount
	where it has one, booked against the order where it names one; or a Journal Entry."""

	name: str
	day: date
	paid: Decimal
	order: str = ""
	rate: int = 0
	journal: bool = False


def advance_orders() -> list[Sale]:
	return [
		Sale(
			ADVANCE_ORDER,
			"inland",
			DOMESTIC,
			[
				Position("Abfüllanlage Typ AF 200", Decimal(1), Decimal("12000.00"), uom="Stück"),
				Position("Montage und Inbetriebnahme", Decimal(16), Decimal("95.00")),
			],
			day=ORDERED,
			po_no="B-5120",
			po_date=date(2026, 11, 19),
			delivery=date(2026, 12, 18),
		)
	]


def whole(rows: int) -> list[tuple[int, Decimal, Decimal, str]]:
	"""Every row of an order at its quantity, as the quantities of AB-2026-0002 run."""
	return [(index, Decimal((index - 1) % 6 + 1), Decimal(0), "") for index in range(1, rows + 1)]


def proformas() -> list[Proforma]:
	return [
		Proforma(
			ADVANCE_INVOICE,
			ADVANCE_ORDER,
			date(2026, 11, 23),
			[(1, Decimal(1), Decimal("3600.00"), "Anzahlung 30 % auf die Abfüllanlage Typ AF 200")],
			print_format="Anzahlungsrechnung",
			by_amount=True,
		),
		Proforma(
			"AZ-2026-0002", "AB-2026-0002", date(2026, 11, 23), whole(30), print_format="Anzahlungsrechnung"
		),
		Proforma(
			"AZ-2026-0003",
			"AB-2026-0003",
			date(2026, 11, 24),
			[(1, Decimal(1), Decimal("1350.00"), "Advance payment for the first quarter of 2027")],
			print_format="Anzahlungsrechnung",
			by_amount=True,
		),
		Proforma(
			"PRO-2026-0001",
			"AB-2026-0001",
			date(2026, 11, 21),
			[
				(1, Decimal(24), Decimal(0), ""),
				(2, Decimal(2), Decimal(0), ""),
				(3, Decimal(3), Decimal(0), ""),
			],
		),
		Proforma("PRO-2026-0002", "AB-2026-0002", date(2026, 11, 21), whole(30)),
		Proforma(
			"PRO-2026-0003",
			"AB-2026-0003",
			date(2026, 11, 21),
			[(1, Decimal(1), Decimal("5400.00"), "Maintenance and support of the ERP system, 2027")],
			by_amount=True,
		),
	]


def advances() -> list[Advance]:
	return [
		Advance("ZE-2026-0101", date(2026, 11, 27), Decimal("4284.00"), ADVANCE_ORDER, rate=19),
		Advance("JV-2026-0101", date(2026, 11, 10), Decimal("2000.00"), journal=True),
		Advance("ZE-2026-0102", date(2026, 12, 16), Decimal("500.00")),
		Advance("ZE-2026-0103", date(2026, 12, 1), Decimal("1190.00"), "AB-2026-0003", rate=19),
	]


def final_invoices() -> list[tuple[Invoice, date, str, list[tuple[str, Decimal]]]]:
	"""The final invoices: the invoice, its day, its language and the advances it allocates with the amount each
	allocates, as ERPNext allocates them, without the tax a payment includes."""
	many = [
		Item(
			f"Leistungspaket {index:02d}",
			Decimal(index % 5 + 1),
			Decimal("85.00") + index,
			description=LONG_TEXT if index % 4 == 0 else "Umsetzung nach Leistungsbeschreibung",
			tax_rate=7 if index % 6 == 0 else 19,
		)
		for index in range(1, 37)
	]
	return [
		(
			Invoice(
				FINAL_INVOICE,
				"inland",
				DOMESTIC,
				[
					Item("Abfüllanlage Typ AF 200", Decimal(1), Decimal("12000.00"), uom="Stück"),
					Item("Montage und Inbetriebnahme", Decimal(16), Decimal("95.00")),
				],
				po_no="B-5120",
				german_templates=True,
			),
			date(2026, 12, 18),
			"de",
			[("ZE-2026-0101", Decimal("3600.00"))],
		),
		(
			Invoice(
				"RE-2026-0402",
				"inland",
				DOMESTIC,
				many,
				period=(date(2026, 12, 1), date(2026, 12, 15)),
				german_templates=True,
			),
			date(2026, 12, 22),
			"de",
			[("JV-2026-0101", Decimal("2000.00")), ("ZE-2026-0102", Decimal("500.00"))],
		),
		(
			Invoice(
				"RE-2026-0403",
				"inland",
				DOMESTIC,
				[Item("Wartung und Betreuung ERP, monatlich", Decimal(12), Decimal("450.00"), uom="Monat")],
				period=(date(2027, 1, 1), date(2027, 12, 31)),
				german_templates=True,
			),
			date(2027, 12, 31),
			"en",
			[("ZE-2026-0103", Decimal("1000.00"))],
		),
	]


def write_advances() -> None:
	for sale in advance_orders():
		write("Sales Order", sale)
	for found in proformas():
		write_proforma(found)
	for found in advances():
		write_advance(found)
	for invoice, day, language, allocated in final_invoices():
		write_final_invoice(invoice, day, language, allocated)


def write_proforma(found: Proforma) -> None:
	"""A submitted Proforma Invoice as ERPNext 16 keeps it: its lines name the rows of the order, and its total is the
	grand total of the copy of the order it prints (render_pdf in
	erpnext/selling/doctype/proforma_invoice/proforma_invoice.py)."""
	if frappe.db.exists("Proforma Invoice", found.name):
		return
	order = frappe.get_doc("Sales Order", found.order)
	rows = {row.idx: row for row in order.items}
	for index, (number, qty, amount, description) in enumerate(found.lines, start=1):
		row = rows[number]
		value = amount or money(qty * Decimal(str(row.rate)))
		insert(
			"Proforma Invoice Item",
			name=f"{found.name}-{index:03d}",
			parent=found.name,
			parenttype="Proforma Invoice",
			parentfield="items",
			idx=index,
			docstatus=1,
			item_name=row.item_name,
			description=description or row.description,
			qty=qty,
			uom=row.uom,
			rate=value / qty,
			amount=value,
			so_detail=row.name,
		)
	insert(
		"Proforma Invoice",
		name=found.name,
		naming_series="AZ-.YYYY.-" if found.print_format == "Anzahlungsrechnung" else "PRO-.YYYY.-",
		sales_order=found.order,
		customer=order.customer,
		customer_name=order.customer_name,
		proforma_date=found.day,
		company=order.company,
		currency="EUR",
		based_on="Amount" if found.by_amount else "Quantity",
		hide_item_qty=int(found.by_amount),
		print_format=found.print_format,
		docstatus=1,
		status="Issued",
	)
	copy = frappe.get_doc("Proforma Invoice", found.name).get_sales_order_copy()
	frappe.db.set_value("Proforma Invoice", found.name, "grand_total", copy.grand_total)


def write_advance(found: Advance) -> None:
	"""A payment as ERPNext books it: a tax line included in the paid amount, and the paid amount less that tax
	credited to the customer, against the order where it names one (get_base_unallocated_amount in
	erpnext/accounts/doctype/payment_entry/payment_entry.py)."""
	doctype = "Journal Entry" if found.journal else "Payment Entry"
	if frappe.db.exists(doctype, found.name):
		return
	if found.journal:
		insert(
			"Journal Entry",
			name=found.name,
			company=COMPANY,
			voucher_type="Bank Entry",
			posting_date=found.day,
			total_debit=found.paid,
			total_credit=found.paid,
			docstatus=1,
		)
		return
	customer = CUSTOMERS["inland"].name
	tax = money(found.paid * found.rate / (100 + found.rate)) if found.rate else Decimal(0)
	credited = found.paid - tax
	if found.rate:
		insert(
			"Advance Taxes and Charges",
			name=f"{found.name}-tax-1",
			parent=found.name,
			parenttype="Payment Entry",
			parentfield="taxes",
			idx=1,
			docstatus=1,
			charge_type="On Paid Amount",
			account_head=f"{GERMAN_ACCOUNTS[found.rate]} - {ABBR}",
			description=f"Umsatzsteuer {found.rate} %",
			rate=found.rate,
			included_in_paid_amount=1,
			add_deduct_tax="Add",
			tax_amount=tax,
			base_tax_amount=tax,
			total=found.paid,
			base_total=found.paid,
		)
	if found.order:
		insert(
			"Payment Entry Reference",
			name=f"{found.name}-001",
			parent=found.name,
			parenttype="Payment Entry",
			parentfield="references",
			idx=1,
			docstatus=1,
			reference_doctype="Sales Order",
			reference_name=found.order,
			allocated_amount=credited,
		)
	insert(
		"Payment Entry",
		name=found.name,
		company=COMPANY,
		payment_type="Receive",
		posting_date=found.day,
		mode_of_payment="Überweisung",
		party_type="Customer",
		party=customer,
		party_name=customer,
		paid_amount=found.paid,
		received_amount=found.paid,
		base_paid_amount=found.paid,
		base_received_amount=found.paid,
		paid_amount_after_tax=credited,
		base_paid_amount_after_tax=credited,
		total_taxes_and_charges=tax,
		base_total_taxes_and_charges=tax,
		paid_from_account_currency="EUR",
		paid_to_account_currency="EUR",
		source_exchange_rate=1,
		target_exchange_rate=1,
		total_allocated_amount=credited if found.order else 0,
		base_total_allocated_amount=credited if found.order else 0,
		unallocated_amount=0 if found.order else credited,
		reference_no=f"SEPA-{found.day:%Y-%m-%d}",
		reference_date=found.day,
		docstatus=1,
		status="Submitted",
	)


def write_final_invoice(
	invoice: Invoice, day: date, language: str, allocated: list[tuple[str, Decimal]]
) -> None:
	"""A Sales Invoice of the whole supply with the advances it allocates (Sales Invoice Advance), its total advance and
	the outstanding amount ERPNext leaves: the total less the allocated amounts (calculate_outstanding_amount in
	erpnext/controllers/taxes_and_totals.py)."""
	if frappe.db.exists("Sales Invoice", invoice.name):
		return
	make_invoice(invoice)
	for index, (name, amount) in enumerate(allocated, start=1):
		insert(
			"Sales Invoice Advance",
			name=f"{invoice.name}-advance-{index}",
			parent=invoice.name,
			parenttype="Sales Invoice",
			parentfield="advances",
			idx=index,
			docstatus=1,
			reference_type="Journal Entry" if name.startswith("JV-") else "Payment Entry",
			reference_name=name,
			advance_amount=amount,
			allocated_amount=amount,
			remarks=f"Zahlung {name}",
		)
	advanced = sum((amount for _name, amount in allocated), Decimal(0))
	total = Decimal(str(frappe.db.get_value("Sales Invoice", invoice.name, "grand_total")))
	frappe.db.set_value(
		"Sales Invoice",
		invoice.name,
		{
			"posting_date": day,
			"due_date": day + timedelta(days=14),
			"language": language,
			"total_advance": advanced,
			"outstanding_amount": total - advanced,
		},
	)
