"""The purchase orders of the proof, written to a test site as ERPNext keeps them once submitted. It runs after
print_documents.run, whose company, suppliers, purchase templates and settings it uses. Taxes as the German purchase
templates book them: tax lines with the rate 0, the rate of each position in its tax details; § 13b UStG as a line
added and one deducted. A second run changes nothing.

	bench --site <site> execute briefbote.tests.print_documents_purchase.run
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

import frappe

from briefbote.tests.print_documents import ABBR, COMPANY, SUPPLIERS, insert, money
from briefbote.tests.print_documents_sales import LONG_TEXT, Position

ORDERED = date(2026, 11, 24)
DOMESTIC = "Sonstige Leistung aus dem Inland"
REVERSE_CHARGE = "Bauleistungen nach § 13b UStG"
SMALL_BUSINESS = "Kleinunternehmer Einkauf"
WAREHOUSE = ("Beispiel GmbH", "Lager Süd", "Am Güterbahnhof 8", "12355", "Musterstadt")


@dataclass
class Purchase:
	name: str
	supplier: str
	template: str
	positions: list[Position]
	schedule: date | None = None
	ship_to: bool = True
	terms: list[tuple[Decimal, str, str, date]] = field(default_factory=list)
	language: str = "de"


def orders() -> list[Purchase]:
	parts = [
		Position(
			f"Profil {index:02d}, Aluminium eloxiert",
			Decimal(index % 5 + 2),
			Decimal("24.80") + index,
			uom="Stück",
			description=LONG_TEXT if index % 6 == 0 else "Länge 2.000 mm",
			delivery=ORDERED + timedelta(days=14 + 7 * (index % 3)),
		)
		for index in range(36)
	]
	return [
		Purchase(
			"BE-2026-0001",
			"bau",
			DOMESTIC,
			[
				Position(
					"Gipskartonplatte 12,5 mm",
					Decimal(120),
					Decimal("6.40"),
					uom="Stück",
					description="Art.-Nr. GK-125",
				),
				Position("Fachbuch Trockenbau", Decimal(2), Decimal("49.00"), uom="Stück", tax_rate=7),
			],
			schedule=date(2026, 12, 8),
			terms=[(Decimal(100), "30 Tage netto", "", date(2026, 12, 24))],
		),
		Purchase("BE-2026-0002", "bau", DOMESTIC, parts),
		Purchase(
			"BE-2026-0003",
			"bau",
			REVERSE_CHARGE,
			[Position("Trockenbauarbeiten Büro 2. OG", Decimal(1), Decimal("7400.00"), uom="Pauschal")],
			schedule=date(2027, 1, 15),
			ship_to=False,
		),
		Purchase(
			"BE-2026-0004",
			"klein",
			SMALL_BUSINESS,
			[Position("Gestaltung Jahresbericht", Decimal(1), Decimal("980.00"), uom="Pauschal")],
			schedule=date(2026, 12, 15),
			ship_to=False,
			language="en",
		),
	]


def run() -> None:
	address = insert(
		"Address",
		name="Beispiel GmbH-Lager",
		address_title=WAREHOUSE[0],
		address_type="Shipping",
		address_line1=WAREHOUSE[1],
		address_line2=WAREHOUSE[2],
		pincode=WAREHOUSE[3],
		city=WAREHOUSE[4],
		country="Germany",
		is_your_company_address=1,
	)
	insert(
		"Dynamic Link",
		name=f"{address}-Company",
		parent=address,
		parenttype="Address",
		parentfield="links",
		idx=1,
		link_doctype="Company",
		link_name=COMPANY,
	)
	for purchase in orders():
		write(purchase)
	frappe.clear_cache()


def write(purchase: Purchase) -> None:
	if frappe.db.exists("Purchase Order", purchase.name):
		return
	supplier = SUPPLIERS[purchase.supplier]
	domestic = purchase.template == DOMESTIC
	net = Decimal(0)
	rows = []
	for index, position in enumerate(purchase.positions, start=1):
		row = f"{purchase.name}-{index:03d}"
		amount = money(position.qty * position.rate)
		net += amount
		rows.append((row, position, amount))
		insert(
			"Purchase Order Item",
			name=row,
			parent=purchase.name,
			parenttype="Purchase Order",
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
			schedule_date=position.delivery or purchase.schedule,
			supplier_part_no=f"L-{index:04d}" if purchase.name == "BE-2026-0001" else None,
		)
	lines = []
	if domestic:
		for rate in (19, 7):
			lines.append(
				(
					"Add",
					rate,
					money(sum((a for _r, p, a in rows if p.tax_rate == rate), Decimal(0)) * rate / 100),
				)
			)
	elif purchase.template == REVERSE_CHARGE:
		tax = money(net * 19 / 100)
		lines = [("Add", 19, tax), ("Deduct", 19, tax)]
	added = Decimal(0)
	for index, (direction, rate, tax) in enumerate(lines, start=1):
		added += tax if direction == "Add" else -tax
		insert(
			"Purchase Taxes and Charges",
			name=f"{purchase.name}-tax-{index}",
			parent=purchase.name,
			parenttype="Purchase Order",
			parentfield="taxes",
			idx=index,
			docstatus=1,
			category="Total",
			add_deduct_tax=direction,
			charge_type="On Net Total",
			account_head=f"Vorsteuer {rate} % - {ABBR}"
			if direction == "Add" and domestic
			else f"Umsatzsteuer 13b - {ABBR}",
			description=f"Vorsteuer {rate} %" if domestic else "Umsatzsteuer 13b",
			rate=0 if domestic else rate,
			net_amount=net,
			base_net_amount=net,
			tax_amount=tax,
			base_tax_amount=tax,
			tax_amount_after_discount_amount=tax,
			base_tax_amount_after_discount_amount=tax,
		)
	if domestic:
		for number, (row, position, amount) in enumerate(rows, start=1):
			for index, rate in enumerate((19, 7), start=1):
				applied = rate if position.tax_rate == rate else 0
				insert(
					"Item Wise Tax Detail",
					name=f"{purchase.name}-detail-{number:03d}-{index}",
					parent=purchase.name,
					parenttype="Purchase Order",
					parentfield="item_wise_tax_details",
					idx=(number - 1) * 2 + index,
					docstatus=1,
					item_row=row,
					tax_row=f"{purchase.name}-tax-{index}",
					rate=applied,
					taxable_amount=amount,
					amount=money(amount * applied / 100),
				)
	grand = net + added
	for index, (portion, term, description, due) in enumerate(purchase.terms, start=1):
		insert(
			"Payment Schedule",
			name=f"{purchase.name}-schedule-{index}",
			parent=purchase.name,
			parenttype="Purchase Order",
			parentfield="payment_schedule",
			idx=index,
			docstatus=1,
			payment_term=term or None,
			description=description,
			due_date=due,
			invoice_portion=portion,
			payment_amount=money(grand * portion / 100),
		)
	insert(
		"Purchase Order",
		name=purchase.name,
		company=COMPANY,
		supplier=supplier.name,
		supplier_name=supplier.name,
		supplier_address=f"{supplier.name}-Billing",
		shipping_address="Beispiel GmbH-Lager" if purchase.ship_to else None,
		transaction_date=ORDERED,
		schedule_date=purchase.schedule or min(p.delivery for p in purchase.positions if p.delivery),
		currency="EUR",
		conversion_rate=1,
		docstatus=1,
		taxes_and_charges=f"{purchase.template} - {ABBR}",
		language=purchase.language,
		total=net,
		net_total=net,
		base_total=net,
		base_net_total=net,
		total_taxes_and_charges=added,
		base_total_taxes_and_charges=added,
		grand_total=grand,
		base_grand_total=grand,
		rounded_total=grand,
		base_rounded_total=grand,
		disable_rounded_total=1,
		terms="<p>Es gelten unsere Einkaufsbedingungen. Bitte geben Sie auf Lieferschein und Rechnung die Bestellnummer an.</p>",
	)
