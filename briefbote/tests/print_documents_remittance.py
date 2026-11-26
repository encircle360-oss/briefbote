"""The payments to suppliers of the proof: purchase invoices of the invented suppliers of Beispiel GmbH with their own
invoice numbers and the Payment Entries that pay them, written to a test site as ERPNext keeps them once submitted
(db_insert, as print_documents.py).

	bench --site <site> execute briefbote.tests.print_documents_remittance.run

It runs after print_documents.run and print_documents_payment.run, whose company, suppliers, settings and modes of
payment it uses. The cases: a transfer for two invoices, one with the cash discount of its payment term, booked as
ERPNext books it (payment_term_discount of the reference, a negative deduction on the discount account); a cash
payment in English to a supplier abroad with a long name, with an amount not applied to an invoice; a transfer for 42
invoices; an invoice without the supplier's number. A second run changes nothing.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

import frappe

from briefbote.tests.print_documents import ABBR, COMPANY, SUPPLIERS, insert, link

DAY = date(2026, 11, 27)
DISCOUNT_ACCOUNT = f"Erhaltene Skonti - {ABBR}"
BANK_ACCOUNT = "Geschäftskonto - Beispielbank"
# A supplier abroad whose number differs from its name and whose name fills two lines of the address field.
ABROAD = "L-0007"
ABROAD_NAME = "Exemple Fournitures Industrielles et Services Associés de la Région Parisienne SARL"


@dataclass
class Bill:
	name: str
	supplier: str
	bill_no: str
	bill_date: date
	total: Decimal
	discount: Decimal = Decimal(0)


@dataclass
class Remittance:
	name: str
	supplier: str
	mode: str
	bills: list[str]
	unallocated: Decimal = Decimal(0)
	reference_no: str = ""
	bank_account: str = ""


def bills() -> list[Bill]:
	found = [
		Bill("ER-2026-0101", "bau", "RG-2026-1187", date(2026, 11, 2), Decimal("2380.00"), Decimal("47.60")),
		Bill("ER-2026-0102", "bau", "RG-2026-1203", date(2026, 11, 9), Decimal("595.00")),
		Bill("ER-2026-0103", ABROAD, "FA-26-00981", date(2026, 10, 30), Decimal("1250.00")),
		Bill("ER-2026-0105", "klein", "", date(2026, 11, 12), Decimal("980.00")),
	]
	found += [
		Bill(
			f"ER-2026-{200 + index:04d}",
			"beraterin",
			f"AB/2026/{index:03d}",
			date(2026, 6, 1) + timedelta(days=3 * index),
			Decimal("142.80") * (index % 3 + 1),
			Decimal("2.86") * (index % 3 + 1) if index % 5 == 0 else Decimal(0),
		)
		for index in range(1, 43)
	]
	return found


def remittances() -> list[Remittance]:
	return [
		Remittance(
			"ZA-2026-0002",
			"bau",
			"Überweisung",
			["ER-2026-0101", "ER-2026-0102"],
			reference_no="SEPA-2026-11-27-0311",
			bank_account=BANK_ACCOUNT,
		),
		Remittance("ZA-2026-0003", ABROAD, "Bar", ["ER-2026-0103"], unallocated=Decimal("100.00")),
		Remittance(
			"ZA-2026-0004",
			"beraterin",
			"Überweisung",
			[f"ER-2026-{200 + index:04d}" for index in range(1, 43)],
			reference_no="SEPA-2026-11-27-0312",
			bank_account=BANK_ACCOUNT,
		),
		Remittance("ZA-2026-0005", "klein", "Überweisung", ["ER-2026-0105"], bank_account=BANK_ACCOUNT),
	]


def party(key: str) -> str:
	return ABROAD if key == ABROAD else SUPPLIERS[key].name


def make_abroad_supplier() -> None:
	address = insert(
		"Address",
		name=f"{ABROAD}-Billing",
		address_title=ABROAD_NAME,
		address_type="Billing",
		address_line1="12 Rue de l'Exemple, Bâtiment B",
		pincode="75011",
		city="Paris",
		country="France",
		is_primary_address=1,
	)
	link(address, "Supplier", ABROAD)
	insert(
		"Supplier",
		name=ABROAD,
		supplier_name=ABROAD_NAME,
		country="France",
		supplier_primary_address=address,
	)


def run() -> None:
	make_abroad_supplier()
	insert(
		"Account",
		name=DISCOUNT_ACCOUNT,
		account_name="Erhaltene Skonti",
		company=COMPANY,
		root_type="Income",
		report_type="Profit and Loss",
		account_currency="EUR",
		is_group=0,
	)
	written = {bill.name: bill for bill in bills()}
	for bill in written.values():
		write_bill(bill)
	for remittance in remittances():
		write(remittance, written)
	frappe.clear_cache()


def write_bill(bill: Bill) -> None:
	name = party(bill.supplier)
	insert(
		"Purchase Invoice",
		name=bill.name,
		company=COMPANY,
		supplier=name,
		supplier_name=ABROAD_NAME if bill.supplier == ABROAD else name,
		bill_no=bill.bill_no or None,
		bill_date=bill.bill_date,
		posting_date=bill.bill_date + timedelta(days=1),
		due_date=bill.bill_date + timedelta(days=30),
		currency="EUR",
		party_account_currency="EUR",
		conversion_rate=1,
		docstatus=1,
		language="de",
		total=bill.total,
		net_total=bill.total,
		grand_total=bill.total,
		base_grand_total=bill.total,
		rounded_total=bill.total,
		base_rounded_total=bill.total,
		disable_rounded_total=1,
		outstanding_amount=bill.total,
	)


def write(remittance: Remittance, written: dict[str, Bill]) -> None:
	if frappe.db.exists("Payment Entry", remittance.name):
		return
	allocated = discount = Decimal(0)
	for index, name in enumerate(remittance.bills, start=1):
		bill = written[name]
		allocated += bill.total
		discount += bill.discount
		insert(
			"Payment Entry Reference",
			name=f"{remittance.name}-{index:03d}",
			parent=remittance.name,
			parenttype="Payment Entry",
			parentfield="references",
			idx=index,
			docstatus=1,
			reference_doctype="Purchase Invoice",
			reference_name=name,
			bill_no=bill.bill_no or None,
			due_date=bill.bill_date + timedelta(days=30),
			total_amount=bill.total,
			outstanding_amount=bill.total,
			allocated_amount=bill.total,
			payment_term_discount=bill.discount,
		)
	if discount:
		# ERPNext books the cash discount of a payment to a supplier as a negative deduction
		# (set_pending_discount_loss in erpnext/accounts/doctype/payment_entry/payment_entry.py).
		insert(
			"Payment Entry Deduction",
			name=f"{remittance.name}-deduction-1",
			parent=remittance.name,
			parenttype="Payment Entry",
			parentfield="deductions",
			idx=1,
			docstatus=1,
			account=DISCOUNT_ACCOUNT,
			amount=-discount,
		)
	paid = allocated - discount + remittance.unallocated
	supplier = party(remittance.supplier)
	insert(
		"Payment Entry",
		name=remittance.name,
		company=COMPANY,
		payment_type="Pay",
		posting_date=DAY,
		mode_of_payment=remittance.mode,
		party_type="Supplier",
		party=supplier,
		party_name=ABROAD_NAME if remittance.supplier == ABROAD else supplier,
		bank_account=remittance.bank_account or None,
		paid_amount=paid,
		received_amount=paid,
		base_paid_amount=paid,
		base_received_amount=paid,
		paid_from_account_currency="EUR",
		paid_to_account_currency="EUR",
		source_exchange_rate=1,
		target_exchange_rate=1,
		total_allocated_amount=allocated,
		base_total_allocated_amount=allocated,
		unallocated_amount=remittance.unallocated,
		reference_no=remittance.reference_no,
		reference_date=DAY if remittance.reference_no else None,
		docstatus=1,
		status="Submitted",
	)
