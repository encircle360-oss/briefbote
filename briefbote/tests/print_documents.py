"""The documents of the proof of the printouts: invented companies, customers and invoices that stress the layout and
cover every tax case and kind of document, written to a test site as ERPNext keeps them once submitted.

    bench --site <site> execute briefbote.tests.print_documents.run

The records go to the database without the validations of their forms (db_insert), the way the tests of the siblings
write submitted documents: printing needs neither a chart of accounts nor stock, only what the print formats read.
Every name, address, number and account is invented; the IBAN is the example IBAN of German banking literature and the
VAT IDs are placeholders in a valid format. A second run changes nothing.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

import frappe

from briefbote.invoice.document import Case
from briefbote.invoice.self_billing import PurchaseCase

COMPANY = "Beispiel GmbH"
ABBR = "BSP"
SMALL_COMPANY = "Kleinbetrieb Beispiel"
SMALL_ABBR = "KLB"
LOGO = "/files/briefbote-proof-logo.svg"
# Shapes only: text in an SVG would print in a font of the system.
LOGO_SVG = (
	'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 64" width="240" height="64">'
	'<rect width="64" height="64" rx="14" fill="#1F4E79"/>'
	'<path d="M18 46V18h16c7 0 11 3 11 8 0 3-2 6-5 7 4 1 7 4 7 8 0 6-5 9-12 9z" fill="#fff"/>'
	'<rect x="80" y="18" width="140" height="10" rx="5" fill="#1F4E79"/>'
	'<rect x="80" y="36" width="96" height="10" rx="5" fill="#7FA7C9"/>'
	"</svg>"
)
GERMAN_REGIONAL_SETTINGS = {
	"date_format": "dd.mm.yyyy",
	"time_format": "HH:mm",
	"number_format": "#.###,##",
	"time_zone": "Europe/Berlin",
	"currency_precision": "2",
}
POSTING = date(2026, 11, 20)
CENT = Decimal("0.01")

TEMPLATES = {
	"Inland 19 %": (Case.DOMESTIC, 19, ""),
	"Innergemeinschaftliche Lieferung": (Case.INTRA_COMMUNITY_SUPPLY, 0, ""),
	"Leistung EU": (Case.EU_SERVICE, 0, ""),
	"Bauleistung § 13b": (Case.REVERSE_CHARGE, 0, ""),
	"Ausfuhr": (Case.EXPORT, 0, ""),
	"Leistung Drittland": (Case.NON_EU_SERVICE, 0, ""),
	"Steuerfrei Unterricht": (Case.EXEMPT, 0, "§ 4 Nr. 21 UStG (Unterrichtsleistungen)"),
}


PURCHASE_TEMPLATES = {
	"Vorsteuer 19 %": (PurchaseCase.DOMESTIC, 19),
	"Bauleistung § 13b Einkauf": (PurchaseCase.REVERSE_CHARGE, 19),
	"Kleinunternehmer Einkauf": (PurchaseCase.SMALL_BUSINESS, 0),
}


@dataclass
class Supplier:
	name: str
	street: str
	pincode: str
	city: str
	tax_id: str


SUPPLIERS = {
	"beraterin": Supplier(
		"Dr. Anna Beispiel Unternehmensberatung", "Am Beraterhof 3", "12349", "Musterstadt", "21/815/08150"
	),
	"bau": Supplier("Muster Trockenbau GmbH", "Industrieweg 9", "34569", "Baustadt", "DE111111111"),
	"klein": Supplier("Grafikbüro Klein", "Gartenweg 2", "23458", "Musterdorf", "31/999/00001"),
}


@dataclass
class Customer:
	name: str
	country: str
	street: str
	pincode: str
	city: str
	tax_id: str = ""
	customer_type: str = "Company"
	street2: str = ""


CUSTOMERS = {
	"inland": Customer(
		"Kunde Muster AG", "Germany", "Hauptstraße 5", "54321", "Beispielstadt", "DE987654321"
	),
	"bau": Customer("Beispiel Bau GmbH", "Germany", "Am Werkhof 12", "34567", "Baustadt"),
	"oesterreich": Customer(
		"Musterhandel Gesellschaft m.b.H.", "Austria", "Ringstraße 1", "1010", "Wien", "ATU12345678"
	),
	"lang": Customer(
		"Holzbau und Innenausbau Rheinisch-Bergisches Land Beteiligungsgesellschaft mbH & Co. KG",
		"Austria",
		"Industriestraße 123, Gebäude C, Eingang Nord",
		"5020",
		"Salzburg",
		"ATU87654321",
		street2="Zentraleinkauf und Rechnungsprüfung",
	),
	"usa": Customer(
		"Example Trading Inc.", "United States", "100 Sample Street, Suite 200", "10001", "New York"
	),
	"privat": Customer(
		"Erika Beispiel", "Germany", "Lindenweg 7", "23456", "Musterdorf", customer_type="Individual"
	),
}


@dataclass
class Item:
	name: str
	qty: Decimal
	rate: Decimal
	uom: str = "Stunde"
	description: str = ""
	tax_rate: int | None = None
	period: tuple[date, date] | None = None
	delivery_note: str = ""


@dataclass
class Invoice:
	name: str
	customer: str
	template: str
	items: list[Item]
	company: str = COMPANY
	is_return: bool = False
	return_against: str = ""
	period: tuple[date, date] | None = None
	po_no: str = ""
	schedule: list[tuple[date, Decimal, Decimal]] = field(default_factory=list)
	terms: str = ""


LONG_TEXT = (
	"Konzeption, Umsetzung und Abnahme der Schnittstelle zwischen Warenwirtschaft und Onlineshop einschließlich "
	"Datenmigration der Artikelstammdaten, Testprotokoll und Einweisung der Mitarbeiterinnen und Mitarbeiter vor Ort"
)


def invoices() -> list[Invoice]:
	november = (date(2026, 11, 1), date(2026, 11, 30))
	consulting = Item(
		"Beratung Projektsteuerung", Decimal(8), Decimal("120.00"), description="Workshop zur Planung"
	)
	many = [
		Item(
			f"Leistungspaket {index:02d}",
			Decimal(index % 7 + 1),
			Decimal("95.50") + index,
			description=LONG_TEXT if index % 3 == 0 else "Umsetzung nach Leistungsbeschreibung",
			tax_rate=7 if index % 5 == 0 else 19,
			period=(date(2026, 10, 1), date(2026, 10, 31)) if index % 4 == 0 else None,
		)
		for index in range(1, 41)
	]
	goods = [
		Item("Eichenholzplatte 2000 x 600 mm, geölt", Decimal(12), Decimal("189.00"), uom="Stück"),
		Item("Montagewinkel verzinkt", Decimal(200), Decimal("1.85"), uom="Stück"),
	]
	return [
		Invoice("RE-2026-0101", "inland", "Inland 19 %", [consulting], period=november, po_no="B-4711"),
		Invoice("RE-2026-0102", "inland", "Inland 19 %", many, period=november),
		Invoice(
			"RE-2026-0103",
			"lang",
			"Leistung EU",
			[
				Item(
					"Softwareentwicklung nach Aufwand",
					Decimal("37.5"),
					Decimal("110.00"),
					description=LONG_TEXT,
				)
			],
			period=november,
		),
		Invoice("RE-2026-0104", "oesterreich", "Innergemeinschaftliche Lieferung", goods),
		Invoice(
			"RE-2026-0105",
			"bau",
			"Bauleistung § 13b",
			[
				Item(
					"Trockenbauarbeiten Bauvorhaben Musterstraße 3",
					Decimal(1),
					Decimal("8400.00"),
					uom="Pauschal",
				)
			],
			period=(date(2026, 10, 5), date(2026, 11, 13)),
		),
		Invoice("RE-2026-0106", "usa", "Ausfuhr", goods),
		Invoice(
			"RE-2026-0107",
			"usa",
			"Leistung Drittland",
			[Item("Remote consulting, software architecture", Decimal(12), Decimal("140.00"))],
			period=november,
		),
		Invoice(
			"RE-2026-0108",
			"inland",
			"Steuerfrei Unterricht",
			[Item("Schulung Buchhaltung für Auszubildende", Decimal(2), Decimal("450.00"), uom="Tag")],
		),
		Invoice(
			"RE-2026-0109",
			"inland",
			"Inland 19 %",
			[Item("Beratung Projektsteuerung", Decimal(-2), Decimal("120.00"))],
			is_return=True,
			return_against="RE-2026-0101",
			period=november,
		),
		Invoice(
			"RE-2026-0110",
			"inland",
			"Inland 19 %",
			[
				Item(
					"Beratung Projektsteuerung",
					Decimal(-8),
					Decimal("120.00"),
					description="Workshop zur Planung",
				)
			],
			is_return=True,
			return_against="RE-2026-0101",
			period=november,
		),
		Invoice(
			"RE-2026-0111",
			"inland",
			"Inland 19 %",
			[Item("Jahresbonus 2026 laut Rahmenvertrag", Decimal(-1), Decimal("250.00"), uom="Pauschal")],
			is_return=True,
		),
		Invoice(
			"RE-2026-0112",
			"privat",
			"Inland 19 %",
			[Item("Einbau Küchenarbeitsplatte", Decimal(1), Decimal("680.00"), uom="Pauschal")],
			schedule=[(POSTING + timedelta(days=14), Decimal("1.00"), Decimal(2))],
		),
		Invoice(
			"RE-2026-0113",
			"inland",
			"Inland 19 %",
			[
				Item("Lagerregal Stahl, verzinkt", Decimal(4), Decimal("219.00"), uom="Stück"),
				Item(
					"Transportversicherung",
					Decimal(1),
					Decimal("38.00"),
					uom="Pauschal",
					description="steuerfrei nach § 4 Nr. 10 Buchst. a UStG",
					tax_rate=0,
				),
			],
		),
		Invoice(
			"KB-2026-0001",
			"privat",
			"",
			[Item("Gartenpflege November", Decimal(6), Decimal("35.00"))],
			company=SMALL_COMPANY,
			period=november,
		),
	]


def self_billing_invoices() -> list[Invoice]:
	november = (date(2026, 11, 1), date(2026, 11, 30))
	return [
		Invoice(
			"GS-2026-0001",
			"beraterin",
			"Vorsteuer 19 %",
			[Item("Beratung Organisationsentwicklung", Decimal(14), Decimal("110.00"))],
			period=november,
		),
		Invoice(
			"GS-2026-0002",
			"bau",
			"Bauleistung § 13b Einkauf",
			[
				Item(
					"Trockenbau Bürotrakt, 2. Abschlag nach Aufmaß",
					Decimal(1),
					Decimal("6200.00"),
					uom="Pauschal",
				)
			],
			period=(date(2026, 10, 1), date(2026, 11, 15)),
		),
		Invoice(
			"GS-2026-0003",
			"klein",
			"Kleinunternehmer Einkauf",
			[Item("Gestaltung Messeplakat", Decimal(1), Decimal("480.00"), uom="Pauschal")],
		),
		Invoice(
			"GS-2026-0004",
			"beraterin",
			"Vorsteuer 19 %",
			[Item("Beratung Organisationsentwicklung", Decimal(-2), Decimal("110.00"))],
			is_return=True,
			return_against="GS-2026-0001",
			period=november,
		),
	]


def run() -> None:
	complete_setup()
	set_german_regional_settings()
	make_company(COMPANY, ABBR, "DE123456789")
	make_company(SMALL_COMPANY, SMALL_ABBR, "")
	make_company_address(
		COMPANY, "Musterweg 1", "12345", "Musterstadt", "+49 30 1234567", "info@beispiel.example"
	)
	make_company_address(SMALL_COMPANY, "Gartenstraße 3", "12347", "Musterstadt", "+49 30 7654321", "")
	make_logo()
	make_templates()
	make_bank_account()
	make_settings()
	for key, customer in CUSTOMERS.items():
		make_customer(key, customer)
	for invoice in invoices():
		make_invoice(invoice)
	make_purchase_templates()
	make_purchase_settings()
	for key, supplier in SUPPLIERS.items():
		make_supplier(key, supplier)
	for invoice in self_billing_invoices():
		make_purchase_invoice(invoice)
	frappe.clear_cache()


def complete_setup() -> None:
	frappe.db.set_value(
		"Installed Application", {"app_name": ("in", ["frappe", "erpnext"])}, "is_setup_complete", 1
	)
	frappe.db.set_single_value("System Settings", "setup_complete", 1)


def set_german_regional_settings() -> None:
	"""The regional settings of a site in Germany: 20.11.2026 and 1.234,56 €."""
	for key, value in GERMAN_REGIONAL_SETTINGS.items():
		frappe.db.set_single_value("System Settings", key, value)
		frappe.db.set_default(key, value)
	frappe.db.set_value("Currency", "EUR", "symbol_on_right", 1)
	frappe.clear_cache()


def insert(doctype: str, **fields) -> str:
	if fields.get("name") and frappe.db.exists(doctype, fields["name"]):
		return fields["name"]
	doc = frappe.get_doc({"doctype": doctype, **fields})
	doc.db_insert()
	return doc.name


def make_company(name: str, abbr: str, tax_id: str) -> None:
	if frappe.db.exists("Company", name):
		return
	company = frappe.new_doc("Company")
	company.update(
		{
			"company_name": name,
			"abbr": abbr,
			"default_currency": "EUR",
			"country": "Germany",
			"tax_id": tax_id,
			"phone_no": "+49 30 1234567",
			"email": "info@beispiel.example",
			"website": "www.beispiel.example",
		}
	)
	frappe.local.flags.ignore_chart_of_accounts = True
	try:
		company.insert(ignore_permissions=True)
	finally:
		frappe.local.flags.ignore_chart_of_accounts = False


def link(address: str, doctype: str, name: str) -> None:
	insert(
		"Dynamic Link",
		name=f"{address}-{doctype}",
		parent=address,
		parenttype="Address",
		parentfield="links",
		idx=1,
		link_doctype=doctype,
		link_name=name,
	)


def make_company_address(company: str, street: str, pincode: str, city: str, phone: str, email: str) -> None:
	address = insert(
		"Address",
		name=f"{company}-Sitz",
		address_title=company,
		address_type="Billing",
		address_line1=street,
		pincode=pincode,
		city=city,
		country="Germany",
		phone=phone,
		email_id=email,
		is_your_company_address=1,
		is_primary_address=1,
	)
	link(address, "Company", company)


def make_logo() -> None:
	if frappe.db.exists("File", {"file_url": LOGO}):
		return
	frappe.get_doc(
		{
			"doctype": "File",
			"file_name": LOGO.rsplit("/", 1)[1],
			"content": LOGO_SVG,
			"is_private": 0,
		}
	).insert(ignore_permissions=True)


def make_templates() -> None:
	for title in TEMPLATES:
		insert(
			"Sales Taxes and Charges Template",
			name=f"{title} - {ABBR}",
			title=title,
			company=COMPANY,
		)


def make_bank_account() -> None:
	insert("Bank", name="Beispielbank", bank_name="Beispielbank", swift_number="BSPLDEB1XXX")
	insert(
		"Bank Account",
		name="Geschäftskonto - Beispielbank",
		account_name="Geschäftskonto",
		bank="Beispielbank",
		company=COMPANY,
		is_company_account=1,
		iban="DE02120300000000202051",
	)


def make_settings() -> None:
	if not frappe.db.exists("Business Document Settings", COMPANY):
		settings = frappe.new_doc("Business Document Settings")
		settings.update(
			{
				"company": COMPANY,
				"letter_form": "B",
				"stationery": "Blank paper",
				"logo": frappe.db.get_value(
					"File", {"file_url": ("like", "%briefbote-proof-logo%")}, "file_url"
				),
				"registered_office": "Musterstadt",
				"register_court": "Amtsgericht Musterstadt",
				"register_number": "HRB 99999",
				"tax_number": "12/345/67890",
				"managing_directors": "Erika Mustermann\nMax Mustermann",
				"accent_color": "#0B6E99",
				"logo_position": "Right",
				"logo_height": 18,
				"font": "Inter (embedded)",
			}
		)
		for column, block in (
			(1, "Company and Contact"),
			(2, "Register and Management"),
			(2, "Tax Numbers"),
			(3, "Bank Accounts"),
		):
			settings.append("footer_layout", {"column": column, "block": block})
		settings.append("bank_accounts", {"bank_account": "Geschäftskonto - Beispielbank"})
		for title, (case, _rate, reason) in TEMPLATES.items():
			settings.append(
				"tax_cases",
				{
					"taxes_and_charges": f"{title} - {ABBR}",
					"tax_case": case.value,
					"exemption_reason": reason,
				},
			)
		settings.insert(ignore_permissions=True)
	if not frappe.db.exists("Business Document Settings", SMALL_COMPANY):
		small = frappe.new_doc("Business Document Settings")
		small.update(
			{
				"company": SMALL_COMPANY,
				"letter_form": "A",
				"stationery": "Blank paper",
				"tax_number": "98/765/43210",
				"small_business": 1,
				"accent_color": "#7A3E9D",
				"logo_position": "Left",
				"font": "System sans-serif",
			}
		)
		small.insert(ignore_permissions=True)


def make_customer(key: str, customer: Customer) -> None:
	address = insert(
		"Address",
		name=f"{customer.name}-Billing",
		address_title=customer.name,
		address_type="Billing",
		address_line1=customer.street,
		address_line2=customer.street2,
		pincode=customer.pincode,
		city=customer.city,
		country=customer.country,
		is_primary_address=1,
	)
	link(address, "Customer", customer.name)
	insert(
		"Customer",
		name=customer.name,
		customer_name=customer.name,
		customer_type=customer.customer_type,
		tax_id=customer.tax_id,
		customer_primary_address=address,
	)


def money(value: Decimal) -> Decimal:
	return value.quantize(CENT, ROUND_HALF_UP)


def make_invoice(invoice: Invoice) -> None:
	if frappe.db.exists("Sales Invoice", invoice.name):
		return
	customer = CUSTOMERS[invoice.customer]
	abbr = ABBR if invoice.company == COMPANY else SMALL_ABBR
	template = f"{invoice.template} - {abbr}" if invoice.template else ""
	default_rate = TEMPLATES[invoice.template][1] if invoice.template else 0
	net_by_rate: dict[int, Decimal] = {}
	for index, item in enumerate(invoice.items, start=1):
		amount = money(item.qty * item.rate)
		rate = default_rate if item.tax_rate is None or not default_rate else item.tax_rate
		net_by_rate[rate] = net_by_rate.get(rate, Decimal(0)) + amount
		insert(
			"Sales Invoice Item",
			name=f"{invoice.name}-{index:03d}",
			parent=invoice.name,
			parenttype="Sales Invoice",
			parentfield="items",
			idx=index,
			docstatus=1,
			item_name=item.name,
			description=item.description or item.name,
			qty=item.qty,
			uom=item.uom,
			stock_uom=item.uom,
			rate=item.rate,
			amount=amount,
			net_rate=item.rate,
			net_amount=amount,
			base_rate=item.rate,
			base_amount=amount,
			base_net_amount=amount,
			service_start_date=item.period[0] if item.period else None,
			service_end_date=item.period[1] if item.period else None,
			delivery_note=item.delivery_note or None,
		)
	net = sum(net_by_rate.values(), Decimal(0))
	tax_total = Decimal(0)
	running = net
	tax_rows = {}
	for index, (rate, base) in enumerate(sorted((r, b) for r, b in net_by_rate.items() if r), start=1):
		tax_rows[rate] = f"{invoice.name}-tax-{index}"
		tax = money(base * rate / 100)
		tax_total += tax
		running += tax
		insert(
			"Sales Taxes and Charges",
			name=f"{invoice.name}-tax-{index}",
			parent=invoice.name,
			parenttype="Sales Invoice",
			parentfield="taxes",
			idx=index,
			docstatus=1,
			charge_type="On Net Total",
			account_head=f"Umsatzsteuer {rate} % - {abbr}",
			description=f"Umsatzsteuer {rate} %",
			rate=rate,
			net_amount=base,
			base_net_amount=base,
			tax_amount=tax,
			base_tax_amount=tax,
			tax_amount_after_discount_amount=tax,
			base_tax_amount_after_discount_amount=tax,
			total=running,
			base_total=running,
		)
	grand = net + tax_total
	for index, item in enumerate(invoice.items, start=1):
		rate = default_rate if item.tax_rate is None or not default_rate else item.tax_rate
		if rate:
			amount = money(item.qty * item.rate)
			insert(
				"Item Wise Tax Detail",
				name=f"{invoice.name}-detail-{index:03d}",
				parent=invoice.name,
				parenttype="Sales Invoice",
				parentfield="item_wise_tax_details",
				idx=index,
				docstatus=1,
				item_row=f"{invoice.name}-{index:03d}",
				tax_row=tax_rows[rate],
				rate=rate,
				taxable_amount=amount,
				amount=money(amount * rate / 100),
			)
	due = POSTING + timedelta(days=14)
	for index, (due_date, portion, discount) in enumerate(invoice.schedule, start=1):
		insert(
			"Payment Schedule",
			name=f"{invoice.name}-schedule-{index}",
			parent=invoice.name,
			parenttype="Sales Invoice",
			parentfield="payment_schedule",
			idx=index,
			docstatus=1,
			due_date=due_date,
			invoice_portion=portion * 100,
			payment_amount=money(grand * portion),
			outstanding=money(grand * portion),
			discount_type="Percentage",
			discount=discount,
			discount_date=POSTING + timedelta(days=7),
		)
	insert(
		"Sales Invoice",
		name=invoice.name,
		company=invoice.company,
		customer=customer.name,
		customer_name=customer.name,
		customer_address=f"{customer.name}-Billing",
		tax_id=customer.tax_id,
		posting_date=POSTING,
		due_date=due,
		currency="EUR",
		party_account_currency="EUR",
		conversion_rate=1,
		docstatus=1,
		is_return=int(invoice.is_return),
		return_against=invoice.return_against or None,
		taxes_and_charges=template or None,
		from_date=invoice.period[0] if invoice.period else None,
		to_date=invoice.period[1] if invoice.period else None,
		po_no=invoice.po_no,
		language="de",
		total=net,
		net_total=net,
		base_total=net,
		base_net_total=net,
		total_taxes_and_charges=tax_total,
		base_total_taxes_and_charges=tax_total,
		grand_total=grand,
		base_grand_total=grand,
		rounded_total=grand,
		base_rounded_total=grand,
		rounding_adjustment=0,
		disable_rounded_total=1,
		outstanding_amount=grand,
		terms="",
	)


def make_purchase_templates() -> None:
	for title in PURCHASE_TEMPLATES:
		insert("Purchase Taxes and Charges Template", name=f"{title} - {ABBR}", title=title, company=COMPANY)


def make_purchase_settings() -> None:
	settings = frappe.get_doc("Business Document Settings", COMPANY)
	if settings.get("purchase_tax_cases"):
		return
	for title, (case, _rate) in PURCHASE_TEMPLATES.items():
		settings.append(
			"purchase_tax_cases", {"purchase_taxes_and_charges": f"{title} - {ABBR}", "tax_case": case.value}
		)
	settings.save(ignore_permissions=True)


def make_supplier(key: str, supplier: Supplier) -> None:
	address = insert(
		"Address",
		name=f"{supplier.name}-Billing",
		address_title=supplier.name,
		address_type="Billing",
		address_line1=supplier.street,
		pincode=supplier.pincode,
		city=supplier.city,
		country="Germany",
		is_primary_address=1,
	)
	link(address, "Supplier", supplier.name)
	insert("Supplier", name=supplier.name, supplier_name=supplier.name, tax_id=supplier.tax_id)


def make_purchase_invoice(invoice: Invoice) -> None:
	"""A Purchase Invoice marked as self-billing. The tax of § 13b UStG is booked as ERPNext books it, added and
	deducted again, so that the Gutschrift must leave it out."""
	if frappe.db.exists("Purchase Invoice", invoice.name):
		return
	supplier = SUPPLIERS[invoice.customer]
	case, rate = PURCHASE_TEMPLATES[invoice.template]
	net = Decimal(0)
	for index, item in enumerate(invoice.items, start=1):
		amount = money(item.qty * item.rate)
		net += amount
		insert(
			"Purchase Invoice Item",
			name=f"{invoice.name}-{index:03d}",
			parent=invoice.name,
			parenttype="Purchase Invoice",
			parentfield="items",
			idx=index,
			docstatus=1,
			item_name=item.name,
			description=item.description or item.name,
			qty=item.qty,
			uom=item.uom,
			stock_uom=item.uom,
			rate=item.rate,
			amount=amount,
			net_rate=item.rate,
			net_amount=amount,
			base_rate=item.rate,
			base_amount=amount,
			base_net_amount=amount,
		)
	tax = money(net * rate / 100)
	rows = []
	if case is PurchaseCase.DOMESTIC:
		rows = [("Add", tax)]
	elif case is PurchaseCase.REVERSE_CHARGE:
		rows = [("Add", tax), ("Deduct", tax)]
	for index, (direction, amount) in enumerate(rows, start=1):
		insert(
			"Purchase Taxes and Charges",
			name=f"{invoice.name}-tax-{index}",
			parent=invoice.name,
			parenttype="Purchase Invoice",
			parentfield="taxes",
			idx=index,
			docstatus=1,
			category="Total",
			add_deduct_tax=direction,
			charge_type="On Net Total",
			account_head=f"Vorsteuer {rate} % - {ABBR}"
			if direction == "Add"
			else f"Umsatzsteuer 13b - {ABBR}",
			description="Vorsteuer" if direction == "Add" else "Umsatzsteuer 13b",
			rate=rate,
			net_amount=net,
			base_net_amount=net,
			tax_amount=amount,
			base_tax_amount=amount,
			tax_amount_after_discount_amount=amount,
			base_tax_amount_after_discount_amount=amount,
		)
	grand = net + (tax if case is PurchaseCase.DOMESTIC else Decimal(0))
	insert(
		"Purchase Invoice",
		name=invoice.name,
		company=COMPANY,
		supplier=supplier.name,
		supplier_name=supplier.name,
		supplier_address=f"{supplier.name}-Billing",
		tax_id=supplier.tax_id,
		posting_date=POSTING,
		due_date=POSTING + timedelta(days=10),
		currency="EUR",
		party_account_currency="EUR",
		conversion_rate=1,
		docstatus=1,
		is_return=int(invoice.is_return),
		return_against=invoice.return_against or None,
		taxes_and_charges=f"{invoice.template} - {ABBR}",
		from_date=invoice.period[0] if invoice.period else None,
		to_date=invoice.period[1] if invoice.period else None,
		language="de",
		self_billing=1,
		total=net,
		net_total=net,
		base_total=net,
		base_net_total=net,
		grand_total=grand,
		base_grand_total=grand,
		rounded_total=grand,
		base_rounded_total=grand,
		disable_rounded_total=1,
		outstanding_amount=grand,
	)
