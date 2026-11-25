"""The dunning letters of the proof: open invoices and Dunnings of the invented company Beispiel GmbH, written to a
test site as ERPNext keeps them once submitted.

	bench --site <site> execute briefbote.tests.print_documents_dunning.run

It runs after print_documents.run, whose company, customers and settings it uses. The cases: a payment reminder that
puts two invoices in default; a Mahnung to a business with one invoice in default by the 30 days of § 286 Abs. 3 BGB
across the change of the base rate on 1 July, one by thirty days and one by the reminder, with lawful interest and the
lump sum; a Mahnung to a consumer in default by reminder only; a Dunning with interest as ERPNext books it, from the
due date at the rate of its Dunning Type, above the lawful maximum; a final reminder over forty invoices; an English
reminder. A second run changes nothing.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_DOWN, Decimal

import frappe

from briefbote.dunning import interest
from briefbote.tests.print_documents import COMPANY, CUSTOMERS, insert, money

TODAY = date(2026, 11, 25)
CENT = Decimal("0.01")


@dataclass
class Open:
	name: str
	customer: str
	issued: date
	due: date
	total: Decimal
	outstanding: Decimal
	language: str = "de"


def invoices() -> list[Open]:
	found = [
		Open(
			"RE-2026-0201",
			"inland",
			date(2026, 5, 4),
			date(2026, 5, 18),
			Decimal("1190.00"),
			Decimal("1190.00"),
		),
		Open(
			"RE-2026-0202",
			"inland",
			date(2026, 9, 1),
			date(2026, 9, 15),
			Decimal("2380.00"),
			Decimal("1880.00"),
		),
		Open(
			"RE-2026-0203",
			"inland",
			date(2026, 10, 20),
			date(2026, 11, 3),
			Decimal("595.00"),
			Decimal("595.00"),
		),
		Open(
			"RE-2026-0204",
			"privat",
			date(2026, 8, 3),
			date(2026, 8, 17),
			Decimal("476.00"),
			Decimal("476.00"),
		),
		Open(
			"RE-2026-0205",
			"usa",
			date(2026, 9, 1),
			date(2026, 10, 1),
			Decimal("1680.00"),
			Decimal("1680.00"),
			"en",
		),
	]
	found += [
		Open(
			f"RE-2026-{300 + index:04d}",
			"inland",
			date(2026, 6, 1) + timedelta(days=2 * index),
			date(2026, 6, 15) + timedelta(days=2 * index),
			Decimal("119.00") * (index % 4 + 1),
			Decimal("119.00") * (index % 4 + 1),
		)
		for index in range(1, 41)
	]
	return found


@dataclass
class Notice:
	name: str
	customer: str
	day: date
	level: int
	rows: list[str]
	fee: Decimal = Decimal(0)
	# "lawful": the maximum of briefbote/dunning/interest.py, to the cent below; "erpnext": from the due date at the
	# rate of the Dunning Type, as validate_overdue_payments of ERPNext 16 books it.
	interest: str = ""
	rate: Decimal = Decimal(0)
	language: str = "de"


def notices() -> list[Notice]:
	return [
		Notice("MZ-2026-0001", "inland", date(2026, 11, 10), 1, ["RE-2026-0202", "RE-2026-0203"]),
		Notice("MZ-2026-0004", "privat", date(2026, 10, 1), 1, ["RE-2026-0204"]),
		Notice(
			"MZ-2026-0002",
			"inland",
			TODAY,
			2,
			["RE-2026-0201", "RE-2026-0202", "RE-2026-0203"],
			fee=Decimal(40),
			interest="lawful",
		),
		Notice("MZ-2026-0003", "privat", TODAY, 2, ["RE-2026-0204"], interest="lawful"),
		Notice("MZ-2026-0005", "inland", TODAY, 3, ["RE-2026-0201"], interest="erpnext", rate=Decimal(12)),
		Notice("MZ-2026-0006", "inland", TODAY, 4, [f"RE-2026-{300 + index:04d}" for index in range(1, 41)]),
		Notice("MZ-2026-0007", "usa", TODAY, 2, ["RE-2026-0205"], language="en"),
	]


def run() -> None:
	settings = frappe.get_doc("Business Document Settings", COMPANY)
	if not settings.get("base_rates"):
		for row in interest.PUBLISHED:
			settings.append("base_rates", {"valid_from": row.valid_from, "rate": row.rate})
		settings.save(ignore_permissions=True)
	opened = {invoice.name: invoice for invoice in invoices()}
	for invoice in opened.values():
		write_invoice(invoice)
	written = {}
	for notice in sorted(notices(), key=lambda notice: notice.day):
		write_notice(notice, opened, written)
		written[notice.name] = notice
	frappe.clear_cache()


def write_invoice(invoice: Open) -> None:
	customer = CUSTOMERS[invoice.customer]
	insert(
		"Sales Invoice",
		name=invoice.name,
		company=COMPANY,
		customer=customer.name,
		customer_name=customer.name,
		customer_address=f"{customer.name}-Billing",
		posting_date=invoice.issued,
		due_date=invoice.due,
		currency="EUR",
		party_account_currency="EUR",
		conversion_rate=1,
		docstatus=1,
		language=invoice.language,
		total=invoice.total,
		net_total=invoice.total,
		grand_total=invoice.total,
		base_grand_total=invoice.total,
		rounded_total=invoice.total,
		base_rounded_total=invoice.total,
		disable_rounded_total=1,
		outstanding_amount=invoice.outstanding,
	)


def booked_interest(notice: Notice, invoice: Open, written: dict) -> Decimal:
	if notice.interest == "erpnext":
		days = (notice.day - invoice.due).days
		return money(invoice.outstanding * notice.rate / 100 / 365 * days)
	if notice.interest != "lawful":
		return Decimal(0)
	customer = CUSTOMERS[notice.customer]
	reminders = [
		earlier.day
		for earlier in written.values()
		if invoice.name in earlier.rows and earlier.day < notice.day
	]
	start = interest.default_start(
		due=invoice.due,
		issued=invoice.issued,
		consumer=customer.customer_type == "Individual",
		notice=False,
		reminders=reminders,
	)
	found = interest.lawful(
		invoice.outstanding, start, notice.day, interest.PUBLISHED, customer.customer_type == "Individual"
	)
	return found.quantize(CENT, ROUND_DOWN)


def write_notice(notice: Notice, opened: dict[str, Open], written: dict) -> None:
	if frappe.db.exists("Dunning", notice.name):
		return
	customer = CUSTOMERS[notice.customer]
	outstanding, interest_total = Decimal(0), Decimal(0)
	for index, name in enumerate(notice.rows, start=1):
		invoice = opened[name]
		accrued = booked_interest(notice, invoice, written)
		outstanding += invoice.outstanding
		interest_total += accrued
		insert(
			"Overdue Payment",
			name=f"{notice.name}-{index:03d}",
			parent=notice.name,
			parenttype="Dunning",
			parentfield="overdue_payments",
			idx=index,
			docstatus=1,
			sales_invoice=name,
			due_date=invoice.due,
			invoice_portion=100,
			payment_amount=invoice.total,
			outstanding=invoice.outstanding,
			paid_amount=invoice.total - invoice.outstanding,
			overdue_days=str((notice.day - invoice.due).days),
			dunning_level=notice.level,
			interest=accrued,
		)
	insert(
		"Dunning",
		name=notice.name,
		company=COMPANY,
		customer=customer.name,
		customer_name=customer.name,
		customer_address=f"{customer.name}-Billing",
		posting_date=notice.day,
		currency="EUR",
		conversion_rate=1,
		docstatus=1,
		status="Unresolved",
		language=notice.language,
		rate_of_interest=notice.rate,
		dunning_fee=notice.fee,
		total_outstanding=outstanding,
		total_interest=interest_total,
		dunning_amount=interest_total + notice.fee,
		base_dunning_amount=interest_total + notice.fee,
		grand_total=outstanding + interest_total + notice.fee,
	)
