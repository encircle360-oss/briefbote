"""The payments of the proof: received payments of customers of Beispiel GmbH against the invoices of
print_documents_dunning.py, written to a test site as ERPNext keeps them once submitted, and one payment to a
supplier, which is no receipt.

	bench --site <site> execute briefbote.tests.print_documents_payment.run

It runs after print_documents.run and print_documents_dunning.run. A second run changes nothing.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

import frappe

from briefbote.tests.print_documents import COMPANY, CUSTOMERS, SUPPLIERS, insert
from briefbote.tests.print_documents_dunning import invoices


@dataclass
class Payment:
	name: str
	party: str
	day: date
	mode: str
	paid: Decimal
	references: list[tuple[str, Decimal]]
	deductions: list[tuple[str, Decimal]] = field(default_factory=list)
	reference_no: str = ""
	payment_type: str = "Receive"
	language: str = "de"


def payments() -> list[Payment]:
	many = [(f"RE-2026-{300 + index:04d}", Decimal("119.00") * (index % 4 + 1)) for index in range(1, 41)]
	return [
		Payment(
			"ZE-2026-0001",
			"inland",
			date(2026, 11, 26),
			"Überweisung",
			Decimal("2500.00"),
			[("RE-2026-0202", Decimal("1880.00")), ("RE-2026-0203", Decimal("595.00"))],
			reference_no="SEPA-2026-11-26-0042",
		),
		Payment(
			"ZE-2026-0002",
			"privat",
			date(2026, 11, 26),
			"Bar",
			Decimal("476.00"),
			[("RE-2026-0204", Decimal("476.00"))],
		),
		Payment(
			"ZE-2026-0003",
			"usa",
			date(2026, 11, 26),
			"Überweisung",
			Decimal("1665.00"),
			[("RE-2026-0205", Decimal("1680.00"))],
			deductions=[("Bankgebühren", Decimal("15.00"))],
			reference_no="SWIFT 7731",
			language="en",
		),
		Payment(
			"ZE-2026-0004",
			"inland",
			date(2026, 11, 27),
			"Überweisung",
			sum((amount for _name, amount in many), Decimal(0)),
			many,
			reference_no="SEPA-2026-11-27-0007",
		),
		Payment(
			"ZA-2026-0001",
			"beraterin",
			date(2026, 11, 26),
			"Überweisung",
			Decimal("1832.60"),
			[],
			payment_type="Pay",
		),
	]


def run() -> None:
	for mode in ("Überweisung", "Bar"):
		insert("Mode of Payment", name=mode, mode_of_payment=mode, type="Bank" if mode != "Bar" else "Cash")
	opened = {invoice.name: invoice for invoice in invoices()}
	for payment in payments():
		write(payment, opened)
	frappe.clear_cache()


def write(payment: Payment, opened: dict) -> None:
	if frappe.db.exists("Payment Entry", payment.name):
		return
	receive = payment.payment_type == "Receive"
	party = CUSTOMERS[payment.party].name if receive else SUPPLIERS[payment.party].name
	allocated = sum((amount for _name, amount in payment.references), Decimal(0))
	for index, (name, amount) in enumerate(payment.references, start=1):
		invoice = opened[name]
		insert(
			"Payment Entry Reference",
			name=f"{payment.name}-{index:03d}",
			parent=payment.name,
			parenttype="Payment Entry",
			parentfield="references",
			idx=index,
			docstatus=1,
			reference_doctype="Sales Invoice",
			reference_name=name,
			due_date=invoice.due,
			total_amount=invoice.total,
			outstanding_amount=invoice.outstanding,
			allocated_amount=amount,
		)
	for index, (description, amount) in enumerate(payment.deductions, start=1):
		insert(
			"Payment Entry Deduction",
			name=f"{payment.name}-deduction-{index}",
			parent=payment.name,
			parenttype="Payment Entry",
			parentfield="deductions",
			idx=index,
			docstatus=1,
			account=f"Nebenkosten des Geldverkehrs - {COMPANY}",
			description=description,
			amount=amount,
		)
	insert(
		"Payment Entry",
		name=payment.name,
		company=COMPANY,
		payment_type=payment.payment_type,
		posting_date=payment.day,
		mode_of_payment=payment.mode,
		party_type="Customer" if receive else "Supplier",
		party=party,
		party_name=party,
		paid_amount=payment.paid,
		received_amount=payment.paid,
		base_paid_amount=payment.paid,
		base_received_amount=payment.paid,
		paid_from_account_currency="EUR",
		paid_to_account_currency="EUR",
		source_exchange_rate=1,
		target_exchange_rate=1,
		total_allocated_amount=allocated,
		base_total_allocated_amount=allocated,
		unallocated_amount=max(
			payment.paid + sum((a for _d, a in payment.deductions), Decimal(0)) - allocated, Decimal(0)
		),
		reference_no=payment.reference_no,
		reference_date=payment.day if payment.reference_no else None,
		docstatus=1,
		status="Submitted",
	)
