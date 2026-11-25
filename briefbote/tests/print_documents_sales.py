"""The documents of sales for the proof of the printouts: quotations and sales orders of the invented companies of
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

from briefbote.tests.print_documents import ABBR, COMPANY, CUSTOMERS, SMALL_ABBR, SMALL_COMPANY, insert, money

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
					f"Lagerregal Typ {index:02d}, verzinkt",
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
				account_head=f"Umsatzsteuer {rate} % - {abbr}",
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
