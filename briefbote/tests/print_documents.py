"""The documents of the proof of the printouts: invented companies, customers and invoices that stress the layout and
cover every tax case and kind of document, written to a test site as ERPNext keeps them once submitted.

    bench --site <site> execute briefbote.tests.print_documents.run

The records go to the database without the validations of their forms (db_insert), the way the tests of the siblings
write submitted documents: printing needs neither a chart of accounts nor stock, only what the print formats read.
Every name, address, number and account is invented; the IBAN is the example IBAN of German banking literature and the
VAT IDs are placeholders in a valid format. A second run changes nothing.
"""

import base64
import json
import struct
import zlib
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
# A company whose name and street are long enough to break the return address of one line.
LONG_COMPANY = "Holzbau und Innenausbau Rheinisch-Bergisches Land GmbH & Co. KG"
LONG_ABBR = "HIB"
ABBRS = {COMPANY: ABBR, SMALL_COMPANY: SMALL_ABBR, LONG_COMPANY: LONG_ABBR}
LOGO = "/files/briefbote-proof-logo.svg"
# Shapes only: text in an SVG would print in a font of the system. The shapes reach every edge of the drawing, so
# that the painted logo is as large as its box.
LOGO_SVG = (
	'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 64" width="240" height="64">'
	'<rect width="64" height="64" rx="14" fill="#1F4E79"/>'
	'<path d="M18 46V18h16c7 0 11 3 11 8 0 3-2 6-5 7 4 1 7 4 7 8 0 6-5 9-12 9z" fill="#fff"/>'
	'<rect x="80" y="18" width="160" height="10" rx="5" fill="#1F4E79"/>'
	'<rect x="80" y="36" width="96" height="10" rx="5" fill="#7FA7C9"/>'
	"</svg>"
)
# The logos a company may upload: an SVG as a drawing program exports it, with XML declaration, comment and DOCTYPE,
# a viewBox that does not start at 0 0 and neither width nor height; a very wide SVG; a wide PNG and JPEG and a tall
# PNG. Each fills its whole drawing.
EXPORTED_SVG = (
	'<?xml version="1.0" encoding="utf-8"?>\n'
	"<!-- Generator: a drawing program -->\n"
	'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
	'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" '
	'y="0px"\n\t viewBox="34 36 532 228" enable-background="new 34 36 532 228" xml:space="preserve">\n'
	'<rect x="34" y="36" width="228" height="228" rx="40" fill="#1CAEE5"/>\n'
	'<rect x="290" y="36" width="276" height="100" fill="#1CAEE5"/>\n'
	'<rect x="290" y="164" width="200" height="100" fill="#1F4E79"/>\n'
	"</svg>\n"
)
WIDE_SVG = (
	'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2000 100">'
	'<rect width="2000" height="100" fill="#1F4E79"/></svg>'
)
JPEG_300_60 = (
	"/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8X"
	"GBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAAR"
	"CAA8ASwDAREAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAj/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAA"
	"AAf/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCYlNTcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
	"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
	"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
	"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB//9k="
)


def png(width: int, height: int, colour: bytes = b"\x1f\x4e\x79") -> bytes:
	"""A PNG of one colour."""

	def chunk(kind: bytes, data: bytes) -> bytes:
		return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

	rows = b"".join(b"\x00" + colour * width for _ in range(height))
	header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
	return (
		b"\x89PNG\r\n\x1a\n"
		+ chunk(b"IHDR", header)
		+ chunk(b"IDAT", zlib.compress(rows))
		+ chunk(b"IEND", b"")
	)


LOGOS = {
	"/files/briefbote-proof-logo-export.svg": EXPORTED_SVG.encode(),
	"/files/briefbote-proof-logo-wide.svg": WIDE_SVG.encode(),
	"/files/briefbote-proof-logo-wide.png": png(300, 60),
	"/files/briefbote-proof-logo-wide.jpg": base64.b64decode(JPEG_300_60),
	"/files/briefbote-proof-logo-tall.png": png(60, 120),
}
GERMAN_REGIONAL_SETTINGS = {
	"date_format": "dd.mm.yyyy",
	"time_format": "HH:mm",
	"number_format": "#.###,##",
	"time_zone": "Europe/Berlin",
	"currency_precision": "2",
}
POSTING = date(2026, 11, 20)
CENT = Decimal("0.01")

# The German tax templates of ERPNext: tax lines with rate 0 and one item tax template a rate, which names every tax
# account, its own with the rate and the others with 0.
GERMAN_ACCOUNTS = {19: "1776 - Umsatzsteuer 19 %", 7: "1771 - Umsatzsteuer 7 %"}

TEMPLATES = {
	"Lieferung oder sonstige Leistung im Inland": (Case.DOMESTIC, 19, ""),
	"Lieferung an Unternehmen in der EU": (Case.INTRA_COMMUNITY_SUPPLY, 0, ""),
	"Sonstige Leistung an Unternehmen in der EU": (Case.EU_SERVICE, 0, ""),
	"Bauleistungen nach § 13b UStG": (Case.REVERSE_CHARGE, 0, ""),
	"Lieferung in Drittland": (Case.EXPORT, 0, ""),
	"Sonstige Leistung an Unternehmen in Drittland": (Case.NON_EU_SERVICE, 0, ""),
	"Steuerfrei Unterricht": (Case.EXEMPT, 0, "§ 4 Nr. 21 UStG (Unterrichtsleistungen)"),
}


PURCHASE_TEMPLATES = {
	"Sonstige Leistung aus dem Inland": (PurchaseCase.DOMESTIC, 19),
	"Bauleistungen nach § 13b UStG": (PurchaseCase.REVERSE_CHARGE, 19),
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
	"ohne_nummer": Supplier("Fotostudio Beispiel", "Lichtweg 4", "12350", "Musterstadt", ""),
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
	address: bool = True


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
	"ohne_anschrift": Customer("Beispiel Handels KG", "Germany", "", "", "", address=False),
	"eu_ohne_id": Customer("Exemple Services SARL", "France", "1 Rue de l'Exemple", "75001", "Paris"),
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
	german_templates: bool = False
	no_tax: bool = False


LONG_TEXT = (
	"Konzeption, Umsetzung und Abnahme der Schnittstelle zwischen Warenwirtschaft und Onlineshop einschließlich "
	"Datenmigration der Artikelstammdaten, Testprotokoll und Einweisung der Mitarbeiterinnen und Mitarbeiter vor Ort"
)


EXAMPLE_INVOICE = "RE-2026-0117"


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
		Invoice(
			"RE-2026-0101",
			"inland",
			"Lieferung oder sonstige Leistung im Inland",
			[consulting],
			period=november,
			po_no="B-4711",
			german_templates=True,
		),
		Invoice(
			"RE-2026-0102",
			"inland",
			"Lieferung oder sonstige Leistung im Inland",
			many,
			period=november,
			german_templates=True,
		),
		Invoice(
			"RE-2026-0103",
			"lang",
			"Sonstige Leistung an Unternehmen in der EU",
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
		Invoice("RE-2026-0104", "oesterreich", "Lieferung an Unternehmen in der EU", goods),
		Invoice(
			"RE-2026-0105",
			"bau",
			"Bauleistungen nach § 13b UStG",
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
		Invoice("RE-2026-0106", "usa", "Lieferung in Drittland", goods),
		Invoice(
			"RE-2026-0107",
			"usa",
			"Sonstige Leistung an Unternehmen in Drittland",
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
			"Lieferung oder sonstige Leistung im Inland",
			[Item("Beratung Projektsteuerung", Decimal(-2), Decimal("120.00"))],
			is_return=True,
			return_against="RE-2026-0101",
			period=november,
		),
		Invoice(
			"RE-2026-0110",
			"inland",
			"Lieferung oder sonstige Leistung im Inland",
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
			"Lieferung oder sonstige Leistung im Inland",
			[Item("Jahresbonus 2026 laut Rahmenvertrag", Decimal(-1), Decimal("250.00"), uom="Pauschal")],
			is_return=True,
		),
		Invoice(
			"RE-2026-0112",
			"privat",
			"Lieferung oder sonstige Leistung im Inland",
			[Item("Einbau Küchenarbeitsplatte", Decimal(1), Decimal("680.00"), uom="Pauschal")],
			schedule=[(POSTING + timedelta(days=14), Decimal("1.00"), Decimal(2))],
		),
		Invoice(
			"RE-2026-0113",
			"inland",
			"Lieferung oder sonstige Leistung im Inland",
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
			TIMESHEET_INVOICE,
			"inland",
			"Lieferung oder sonstige Leistung im Inland",
			[
				Item(f"Beratung {title}", hours, Decimal("120.00"), description="laut Leistungsnachweis")
				for title, hours in project_hours().items()
			],
			period=november,
		),
		Invoice(
			"KB-2026-0001",
			"privat",
			"",
			[Item("Gartenpflege November", Decimal(6), Decimal("35.00"))],
			company=SMALL_COMPANY,
			period=november,
		),
		Invoice(
			"KB-2026-0002",
			"privat",
			"",
			[Item("Gartenpflege Jahrespauschale 2027", Decimal(1), Decimal("1200.00"), uom="Pauschal")],
			company=SMALL_COMPANY,
		),
		Invoice(
			"RE-2026-0115",
			"ohne_anschrift",
			"Lieferung oder sonstige Leistung im Inland",
			[Item("Lagerregal Stahl, verzinkt", Decimal(3), Decimal("400.00"), uom="Stück")],
		),
		Invoice(
			"RE-2026-0116",
			"eu_ohne_id",
			"Sonstige Leistung an Unternehmen in der EU",
			[Item("Beratung Projektsteuerung", Decimal(10), Decimal("120.00"))],
			period=november,
		),
		Invoice(
			"HB-2026-0001",
			"inland",
			"Lieferung oder sonstige Leistung im Inland",
			[Item("Einbau Eichentreppe", Decimal(1), Decimal("4800.00"), uom="Pauschal")],
			company=LONG_COMPANY,
		),
		# The invoice of the examples in the README: several positions at two rates, a discount for early payment.
		Invoice(
			EXAMPLE_INVOICE,
			"inland",
			"Lieferung oder sonstige Leistung im Inland",
			[
				Item(
					"Einführung ERP, Konzeptphase",
					Decimal(24),
					Decimal("120.00"),
					description="Workshops vor Ort mit Fachabteilungen",
				),
				Item(
					"Schulung der Anwender",
					Decimal(16),
					Decimal("95.00"),
					description="Zwei Gruppen zu je acht Personen",
				),
				Item("Fachbuch Buchhaltung", Decimal(3), Decimal("39.90"), uom="Stück", tax_rate=7),
				Item("Reisekosten", Decimal(1), Decimal("180.00"), uom="Pauschal"),
			],
			period=november,
			po_no="B-4712",
			schedule=[(POSTING + timedelta(days=14), Decimal("1.00"), Decimal(2))],
			german_templates=True,
		),
		*closing_family(),
	]


# Invoices whose end falls near the end of a page: one invoice for each count of positions, so that the request for
# payment of one of them stands within a line of the foot. Shaped as a real one: a name and two lines of description
# per position, every fourth at 7 %, a box of findings on the first page for the missing address, a foot without
# bank accounts.
CLOSING_FAMILY = range(33, 41)


def closing_name(count: int) -> str:
	return f"RE-2026-{120 + count - CLOSING_FAMILY.start:04d}"


def closing_family() -> list[Invoice]:
	return [
		Invoice(
			closing_name(count),
			"ohne_anschrift",
			"Lieferung oder sonstige Leistung im Inland",
			[
				Item(
					f"Beratung {index:02d}",
					Decimal(index % 3 + 1),
					Decimal("80.00") + index,
					uom="Stück",
					description=(
						f"Position {index}: Fachbuch zum Projekt „Mustermigration“\n(ermäßigter Steuersatz)"
						if index % 4 == 0
						else f"Position {index}: Beratung und Umsetzung, Arbeitspaket {index}\ndes Projekts „Mustermigration“"
					),
					tax_rate=7 if index % 4 == 0 else 19,
				)
				for index in range(1, count + 1)
			],
			company=LONG_COMPANY,
			german_templates=True,
		)
		for count in CLOSING_FAMILY
	]


def self_billing_invoices() -> list[Invoice]:
	november = (date(2026, 11, 1), date(2026, 11, 30))
	return [
		Invoice(
			"GS-2026-0001",
			"beraterin",
			"Sonstige Leistung aus dem Inland",
			[Item("Beratung Organisationsentwicklung", Decimal(14), Decimal("110.00"))],
			period=november,
		),
		Invoice(
			"GS-2026-0002",
			"bau",
			"Bauleistungen nach § 13b UStG",
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
			"Sonstige Leistung aus dem Inland",
			[Item("Beratung Organisationsentwicklung", Decimal(-2), Decimal("110.00"))],
			is_return=True,
			return_against="GS-2026-0001",
			period=november,
		),
		Invoice(
			"GS-2026-0005",
			"ohne_nummer",
			"Sonstige Leistung aus dem Inland",
			[Item("Produktfotos Katalog 2027", Decimal(1), Decimal("3000.00"), uom="Pauschal")],
			no_tax=True,
		),
	]


# The consultants of Beispiel GmbH and the time they spent for Kunde Muster AG in November 2026 on two projects.
CONSULTANTS = (
	("HR-EMP-0001", "Erika Mustermann", "Beraterin"),
	("HR-EMP-0002", "Max Mustermann", "Entwickler"),
	("HR-EMP-0003", "Dr. Anna Beispiel", "Projektleitung"),
)
PROJECTS = {
	"PROJ-0001": ("Einführung ERP", ("Konzept", "Schulung", "Abnahme")),
	"PROJ-0002": ("Datenmigration", ("Analyse", "Übernahme")),
}
ACTIVITIES = ("Beratung", "Entwicklung", "Projektleitung")
TIMESHEET_INVOICE = "RE-2026-0114"


def time_logs() -> list[dict]:
	"""45 invented entries: each workday from 2 to 26 November for one or two of the consultants."""
	logs = []
	projects = list(PROJECTS.items())
	workdays = [
		day for day in (date(2026, 11, 2) + timedelta(days=n) for n in range(26)) if day.weekday() < 5
	]
	for index in range(45):
		day = workdays[index * len(workdays) // 45]
		employee, name, _role = CONSULTANTS[index % 3]
		project, (title, tasks) = projects[(index // 3) % 2]
		hours = Decimal(("2.5", "4", "6.25", "8", "1.5", "3.75")[index % 6])
		logs.append(
			{
				"index": index + 1,
				"employee": employee,
				"employee_name": name,
				"day": day,
				"project": project,
				"project_name": title,
				"task": f"TASK-{project[-1]}-{index % len(tasks) + 1}",
				"activity": ACTIVITIES[index % 3],
				"description": (
					"Abstimmung der Stammdaten mit der Fachabteilung und Dokumentation der Entscheidungen"
					if index % 4 == 0
					else "Umsetzung laut Konzept"
				),
				"hours": hours,
			}
		)
	return logs


def make_timesheets() -> None:
	"""Employees, projects, tasks and one submitted Timesheet per consultant with the time logs of the invoice."""
	for activity in ACTIVITIES:
		insert("Activity Type", name=activity, activity_type=activity)
	for employee, name, role in CONSULTANTS:
		first, last = name.rsplit(" ", 1)
		insert("Designation", name=role, designation_name=role)
		insert(
			"Employee",
			name=employee,
			employee_name=name,
			first_name=first,
			last_name=last,
			designation=role,
			company=COMPANY,
			status="Active",
		)
	for project, (title, tasks) in PROJECTS.items():
		insert(
			"Project", name=project, project_name=title, company=COMPANY, customer=CUSTOMERS["inland"].name
		)
		for number, subject in enumerate(tasks, start=1):
			insert("Task", name=f"TASK-{project[-1]}-{number}", subject=subject, project=project)
	for employee, name, _role in CONSULTANTS:
		insert(
			"Timesheet",
			name=f"TS-2026-{employee[-4:]}",
			company=COMPANY,
			employee=employee,
			employee_name=name,
			customer=CUSTOMERS["inland"].name,
			docstatus=1,
			status="Billed",
		)
	for log in time_logs():
		insert(
			"Timesheet Detail",
			name=f"TSD-{log['index']:03d}",
			parent=f"TS-2026-{log['employee'][-4:]}",
			parenttype="Timesheet",
			parentfield="time_logs",
			idx=log["index"],
			docstatus=1,
			activity_type=log["activity"],
			from_time=f"{log['day']} 09:00:00",
			hours=log["hours"],
			billing_hours=log["hours"],
			project=log["project"],
			project_name=log["project_name"],
			task=log["task"],
			description=log["description"],
			is_billable=1,
			sales_invoice=TIMESHEET_INVOICE,
		)


def link_timesheets() -> None:
	"""The table timesheets of the invoice, as ERPNext fills it from the time logs."""
	for log in time_logs():
		insert(
			"Sales Invoice Timesheet",
			name=f"{TIMESHEET_INVOICE}-ts-{log['index']:03d}",
			parent=TIMESHEET_INVOICE,
			parenttype="Sales Invoice",
			parentfield="timesheets",
			idx=log["index"],
			docstatus=1,
			time_sheet=f"TS-2026-{log['employee'][-4:]}",
			timesheet_detail=f"TSD-{log['index']:03d}",
			activity_type=log["activity"],
			description=log["description"],
			from_time=f"{log['day']} 09:00:00",
			billing_hours=log["hours"],
			billing_amount=log["hours"] * 120,
			project_name=log["project_name"],
		)


def project_hours() -> dict[str, Decimal]:
	sums: dict[str, Decimal] = {}
	for log in time_logs():
		sums[log["project_name"]] = sums.get(log["project_name"], Decimal(0)) + log["hours"]
	return sums


def run() -> None:
	complete_setup()
	set_german_regional_settings()
	# The unit of time of the settings, which a fresh site of ERPNext has only in English.
	insert("UOM", name="Stunde", uom_name="Stunde")
	make_company(COMPANY, ABBR, "DE123456789")
	make_company(SMALL_COMPANY, SMALL_ABBR, "")
	make_company(LONG_COMPANY, LONG_ABBR, "DE222222222")
	# The company of the long name has neither telephone nor e-mail nor website, as many small companies.
	frappe.db.set_value("Company", LONG_COMPANY, {"phone_no": "", "email": "", "website": ""})
	make_company_address(
		COMPANY, "Musterweg 1", "12345", "Musterstadt", "+49 30 1234567", "info@beispiel.example"
	)
	make_company_address(SMALL_COMPANY, "Gartenstraße 3", "12347", "Musterstadt", "+49 30 7654321", "")
	make_company_address(
		LONG_COMPANY, "Industriestraße 123, Gebäude C", "12355", "Musterstadt-Nord", "+49 30 5550123", ""
	)
	make_logo()
	# The logo of the company, without which ERPNext asks for it in the print view of the desk.
	for company in (COMPANY, SMALL_COMPANY):
		frappe.db.set_value("Company", company, "company_logo", LOGO)
	make_templates()
	make_item_tax_templates()
	make_bank_account()
	make_settings()
	for key, customer in CUSTOMERS.items():
		make_customer(key, customer)
	make_timesheets()
	for invoice in invoices():
		make_invoice(invoice)
	link_timesheets()
	make_purchase_templates()
	make_purchase_settings()
	for key, supplier in SUPPLIERS.items():
		make_supplier(key, supplier)
	for invoice in self_billing_invoices():
		make_purchase_invoice(invoice)
	make_default_print_formats()
	make_address_template()
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
	for url, content in {LOGO: LOGO_SVG.encode(), **LOGOS}.items():
		if frappe.db.exists("File", {"file_url": url}):
			continue
		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": url.rsplit("/", 1)[1],
				"content": content,
				"is_private": 0,
			}
		).insert(ignore_permissions=True)


def make_templates() -> None:
	for company, abbr in ((COMPANY, ABBR), (LONG_COMPANY, LONG_ABBR)):
		for title in TEMPLATES:
			insert(
				"Sales Taxes and Charges Template",
				name=f"{title} - {abbr}",
				title=title,
				company=company,
			)


def make_item_tax_templates() -> None:
	"""The tax accounts and item tax templates of the German set-up of ERPNext, for Beispiel GmbH."""
	for account in GERMAN_ACCOUNTS.values():
		insert(
			"Account",
			name=f"{account} - {ABBR}",
			account_name=account.split(" - ", 1)[1],
			account_number=account.split(" - ", 1)[0],
			company=COMPANY,
			account_type="Tax",
			root_type="Liability",
			report_type="Balance Sheet",
			account_currency="EUR",
			is_group=0,
		)
	for rate in GERMAN_ACCOUNTS:
		name = f"Umsatzsteuer {rate} % - {ABBR}"
		insert("Item Tax Template", name=name, title=f"Umsatzsteuer {rate} %", company=COMPANY)
		for index, (tax_type, tax_rate) in enumerate(item_tax_map(rate, ABBR).items(), start=1):
			insert(
				"Item Tax Template Detail",
				name=f"{name}-{index}",
				parent=name,
				parenttype="Item Tax Template",
				parentfield="taxes",
				idx=index,
				tax_type=tax_type,
				tax_rate=tax_rate,
			)


LONG_BANK_ACCOUNT = "Zweitkonto - Volks- und Raiffeisenbank Musterstadt-Beispielhausen eG"


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
	# A bank with a long name and a long IBAN, the example IBAN of a French account, for the foot.
	insert(
		"Bank",
		name="Volks- und Raiffeisenbank Musterstadt-Beispielhausen eG",
		bank_name="Volks- und Raiffeisenbank Musterstadt-Beispielhausen eG",
		swift_number="GENODEF1XYZ",
	)
	insert(
		"Bank Account",
		name=LONG_BANK_ACCOUNT,
		account_name="Zweitkonto",
		bank="Volks- und Raiffeisenbank Musterstadt-Beispielhausen eG",
		company=COMPANY,
		is_company_account=1,
		iban="FR7630006000011234567890189",
	)


def make_settings() -> None:
	if not frappe.db.exists("Business Document Settings", COMPANY):
		settings = frappe.new_doc("Business Document Settings")
		settings.update(
			{
				"company": COMPANY,
				"letter_form": "B",
				"stationery": "Blank paper",
				"logo": LOGO,
				"registered_office": "Musterstadt",
				"register_court": "Amtsgericht Musterstadt",
				"register_number": "HRB 99999",
				"tax_number": "12/345/67890",
				"managing_directors": "Erika Mustermann\nMax Mustermann",
				"accent_color": "#0B6E99",
				"logo_position": "Right",
				"logo_height": 18,
				"font": "Inter (embedded)",
				"timesheet_annex": "With the invoice",
				"person_display": "Name",
				"time_unit": "Stunde",
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
	if not frappe.db.exists("Business Document Settings", LONG_COMPANY):
		long = frappe.new_doc("Business Document Settings")
		long.update(
			{
				"company": LONG_COMPANY,
				"letter_form": "B",
				"stationery": "Blank paper",
				"tax_number": "22/333/44444",
				"registered_office": "Musterstadt",
				"register_court": "Amtsgericht Musterstadt",
				"register_number": "HRA 99999",
				"managing_directors": "Max Mustermann",
			}
		)
		for title, (case, _rate, reason) in TEMPLATES.items():
			long.append(
				"tax_cases",
				{
					"taxes_and_charges": f"{title} - {LONG_ABBR}",
					"tax_case": case.value,
					"exemption_reason": reason,
				},
			)
		long.insert(ignore_permissions=True)


def make_customer(key: str, customer: Customer) -> None:
	if not customer.address:
		insert(
			"Customer",
			name=customer.name,
			customer_name=customer.name,
			customer_type=customer.customer_type,
			tax_id=customer.tax_id,
		)
		return
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
	abbr = ABBRS[invoice.company]
	template = f"{invoice.template} - {abbr}" if invoice.template else ""
	default_rate = TEMPLATES[invoice.template][1] if invoice.template else 0
	net_by_rate: dict[int, Decimal] = {}
	for index, item in enumerate(invoice.items, start=1):
		amount = money(item.qty * item.rate)
		rate = default_rate if item.tax_rate is None or not default_rate else item.tax_rate
		net_by_rate[rate] = net_by_rate.get(rate, Decimal(0)) + amount
		german = invoice.german_templates and rate
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
			item_tax_template=f"Umsatzsteuer {rate} % - {abbr}" if german else None,
			item_tax_rate=json.dumps(item_tax_map(rate, abbr)) if german else None,
		)
	if invoice.german_templates:
		make_german_taxes(invoice, abbr, net_by_rate)
		return
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
		customer_address=f"{customer.name}-Billing" if customer.address else None,
		company_address=f"{invoice.company}-Sitz",
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


def item_tax_map(rate: int, abbr: str) -> dict[str, float]:
	"""The item tax template of a rate as ERPNext's German set-up has it: every tax account, its own with the rate."""
	return {
		f"{account} - {abbr}": float(rate if other == rate else 0)
		for other, account in GERMAN_ACCOUNTS.items()
	}


def make_german_taxes(invoice: Invoice, abbr: str, net_by_rate: dict[int, Decimal]) -> None:
	"""Tax lines and tax details as ERPNext 16 computes them for the German templates: each tax line has rate 0 and
	the net amount of every position whose item tax template names its account, that is of all positions
	(get_current_tax_and_net_amount in erpnext/controllers/taxes_and_totals.py); each position has a detail on every
	tax line, with its rate on the line of its own account and 0 on the others."""
	customer = CUSTOMERS[invoice.customer]
	net = sum(net_by_rate.values(), Decimal(0))
	rates = sorted(rate for rate in net_by_rate if rate)
	tax_total, running = Decimal(0), net
	for index, rate in enumerate(rates, start=1):
		tax = money(net_by_rate[rate] * rate / 100)
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
	detail = 0
	for index, item in enumerate(invoice.items, start=1):
		amount = money(item.qty * item.rate)
		own = item.tax_rate if item.tax_rate is not None else TEMPLATES[invoice.template][1]
		for row, rate in enumerate(rates, start=1):
			detail += 1
			charged = rate if rate == own else 0
			insert(
				"Item Wise Tax Detail",
				name=f"{invoice.name}-detail-{detail:03d}",
				parent=invoice.name,
				parenttype="Sales Invoice",
				parentfield="item_wise_tax_details",
				idx=detail,
				docstatus=1,
				item_row=f"{invoice.name}-{index:03d}",
				tax_row=f"{invoice.name}-tax-{row}",
				rate=charged,
				taxable_amount=amount,
				amount=money(amount * charged / 100),
			)
	grand = net + tax_total
	insert(
		"Sales Invoice",
		name=invoice.name,
		company=invoice.company,
		customer=customer.name,
		customer_name=customer.name,
		customer_address=f"{customer.name}-Billing" if customer.address else None,
		company_address=f"{invoice.company}-Sitz",
		tax_id=customer.tax_id,
		posting_date=POSTING,
		due_date=POSTING + timedelta(days=14),
		currency="EUR",
		party_account_currency="EUR",
		conversion_rate=1,
		docstatus=1,
		taxes_and_charges=f"{invoice.template} - {abbr}",
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
	if invoice.no_tax:
		tax = Decimal(0)
	elif case is PurchaseCase.DOMESTIC:
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


def make_default_print_formats() -> None:
	"""Rechnung and Gutschrift as the default print formats of their DocTypes, as docs/einrichtung.md shows it, so
	that the print view of the browser tests opens with them."""
	for doctype, print_format in (("Sales Invoice", "Rechnung"), ("Purchase Invoice", "Gutschrift")):
		frappe.make_property_setter(
			{
				"doctype": doctype,
				"doctype_or_field": "DocType",
				"property": "default_print_format",
				"value": print_format,
				"property_type": "Data",
			}
		)


def make_address_template() -> None:
	"""The default Address Template, which the setup wizard of a site creates and without which the desk greets every
	document with an address with a message."""
	from frappe.contacts.doctype.address_template.address_template import get_default_address_template

	if frappe.db.exists("Address Template", {"is_default": 1}):
		return
	insert(
		"Address Template",
		name="Germany",
		country="Germany",
		is_default=1,
		template=get_default_address_template(),
	)
