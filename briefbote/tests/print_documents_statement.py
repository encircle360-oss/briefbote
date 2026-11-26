"""The statements of the proof: the Payment Ledger of the invented invoices and payments of Beispiel GmbH and the Party
Statements that read it, for the print formats Kontoauszug and Saldenbestätigung.

	bench --site <site> execute briefbote.tests.print_documents_statement.run

It runs after print_documents.run, print_documents_dunning.run, print_documents_payment.run and
print_documents_remittance.run, whose invoices and payments it books. The documents of the proof are written without
the validations of their forms (db_insert, see print_documents.py), so they post nothing; this module writes for each
of them the Payment Ledger Entries that ERPNext 16 makes when such a document is submitted (one per invoice with its
amount, one per allocation of a payment against the invoice, one for what a payment leaves unallocated, against the
payment itself; get_payment_ledger_entries and create_payment_ledger_entry in erpnext/accounts/utils.py), on the receivable and payable account of the
company. Everything else the statements show comes from ERPNext's reports Accounts Receivable and Accounts Payable,
which the Party Statements run when they are saved and submitted (insert and submit with all their validations);
test_statement_printing.py checks that the reports return what this module books. A second run changes nothing.

The cases: Kunde Muster AG as of 26.11.2026 with 42 open items over several pages, a partly paid invoice and an
unallocated payment, before the payment of 27.11.2026 that settles 40 of them; Example Trading Inc. in English;
Erika Beispiel with no open item; the supplier Muster Trockenbau GmbH with its own invoice numbers; and a statement
submitted before a booking dated before its cut-off date, which keeps its rows, next to a draft that shows the
booking.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import frappe

from briefbote.tests.print_documents import ABBR, COMPANY, CUSTOMERS, SUPPLIERS, insert
from briefbote.tests.print_documents_dunning import invoices
from briefbote.tests.print_documents_payment import payments
from briefbote.tests.print_documents_remittance import bills, party, remittances

RECEIVABLE = f"Forderungen aus Lieferungen und Leistungen - {ABBR}"
PAYABLE = f"Verbindlichkeiten aus Lieferungen und Leistungen - {ABBR}"
# A booking dated before the cut-off date of KA-2026-0005, written after that statement was submitted.
LATE = ("BU-2026-0001", date(2026, 11, 20), "RE-2026-0201", Decimal("190.00"))


@dataclass
class Statement:
	name: str
	kind: str
	party_type: str
	party: str
	report_date: date
	posting_date: date
	submit: bool = True


def statements() -> list[Statement]:
	inland, usa, privat = (CUSTOMERS[key].name for key in ("inland", "usa", "privat"))
	return [
		Statement("KA-2026-0001", "Open Items", "Customer", inland, date(2026, 11, 26), date(2026, 11, 27)),
		Statement("KA-2026-0002", "Open Items", "Customer", usa, date(2026, 11, 25), date(2026, 11, 27)),
		Statement("KA-2026-0003", "Open Items", "Customer", privat, date(2026, 11, 30), date(2026, 11, 30)),
		Statement(
			"KA-2026-0004",
			"Open Items",
			"Supplier",
			SUPPLIERS["bau"].name,
			date(2026, 11, 26),
			date(2026, 11, 27),
		),
		Statement("KA-2026-0005", "Open Items", "Customer", inland, date(2026, 11, 25), date(2026, 11, 27)),
	]


# Written after KA-2026-0005 is submitted: a draft of the same account and day, which reads the booking LATE.
LATER = Statement(
	"KA-2026-0006",
	"Open Items",
	"Customer",
	CUSTOMERS["inland"].name,
	date(2026, 11, 25),
	date(2026, 11, 27),
	False,
)


def run() -> None:
	for name, account_type, root_type in (
		(RECEIVABLE, "Receivable", "Asset"),
		(PAYABLE, "Payable", "Liability"),
	):
		insert(
			"Account",
			name=name,
			account_name=name.rsplit(" - ", 1)[0],
			company=COMPANY,
			account_type=account_type,
			root_type=root_type,
			report_type="Balance Sheet",
			account_currency="EUR",
			is_group=0,
		)
	book_sales()
	book_purchases()
	for found in statements():
		write(found)
	book_late()
	write(LATER)
	frappe.clear_cache()


def entry(
	name: str, party_type: str, party_name: str, day: date, voucher: tuple, against: tuple, amount, **more
):
	account = RECEIVABLE if party_type == "Customer" else PAYABLE
	insert(
		"Payment Ledger Entry",
		name=name,
		company=COMPANY,
		posting_date=day,
		account_type="Receivable" if party_type == "Customer" else "Payable",
		account=account,
		party_type=party_type,
		party=party_name,
		voucher_type=voucher[0],
		voucher_no=voucher[1],
		against_voucher_type=against[0],
		against_voucher_no=against[1],
		amount=amount,
		amount_in_account_currency=amount,
		account_currency="EUR",
		delinked=0,
		docstatus=1,
		**more,
	)


def book_sales() -> None:
	for invoice in invoices():
		if invoice.company != COMPANY:
			continue
		voucher = ("Sales Invoice", invoice.name)
		entry(
			f"PLE-{invoice.name}",
			"Customer",
			CUSTOMERS[invoice.customer].name,
			invoice.issued,
			voucher,
			voucher,
			invoice.total,
			due_date=invoice.due,
		)
	for payment in payments():
		if payment.payment_type != "Receive":
			continue
		customer = CUSTOMERS[payment.party].name
		voucher = ("Payment Entry", payment.name)
		allocated = Decimal(0)
		for index, (name, amount) in enumerate(payment.references, start=1):
			allocated += amount
			entry(
				f"PLE-{payment.name}-{index:03d}",
				"Customer",
				customer,
				payment.day,
				voucher,
				("Sales Invoice", name),
				-amount,
			)
		rest = payment.paid + sum((amount for _label, amount in payment.deductions), Decimal(0)) - allocated
		if rest > 0:
			entry(f"PLE-{payment.name}-rest", "Customer", customer, payment.day, voucher, voucher, -rest)


def book_purchases() -> None:
	for bill in bills():
		voucher = ("Purchase Invoice", bill.name)
		entry(
			f"PLE-{bill.name}", "Supplier", party(bill.supplier), bill.bill_date, voucher, voucher, bill.total
		)
	written = {bill.name: bill for bill in bills()}
	for remittance in remittances():
		supplier = party(remittance.supplier)
		voucher = ("Payment Entry", remittance.name)
		day = date(2026, 11, 27)
		for index, name in enumerate(remittance.bills, start=1):
			entry(
				f"PLE-{remittance.name}-{index:03d}",
				"Supplier",
				supplier,
				day,
				voucher,
				("Purchase Invoice", name),
				-written[name].total,
			)
		if remittance.unallocated:
			entry(
				f"PLE-{remittance.name}-rest",
				"Supplier",
				supplier,
				day,
				voucher,
				voucher,
				-remittance.unallocated,
			)


def book_late() -> None:
	name, day, invoice, amount = LATE
	if not frappe.db.exists("Journal Entry", name):
		insert(
			"Journal Entry",
			name=name,
			company=COMPANY,
			voucher_type="Credit Note",
			posting_date=day,
			docstatus=1,
			total_debit=amount,
			total_credit=amount,
		)
	entry(
		f"PLE-{name}",
		"Customer",
		CUSTOMERS["inland"].name,
		day,
		("Journal Entry", name),
		("Sales Invoice", invoice),
		-amount,
	)


def write(found: Statement) -> None:
	"""A Party Statement as the desk makes it: inserted with its validations, which run the report, and submitted."""
	if frappe.db.exists("Party Statement", found.name):
		return
	doc = frappe.get_doc(
		{
			"doctype": "Party Statement",
			"kind": found.kind,
			"company": COMPANY,
			"party_type": found.party_type,
			"party": found.party,
			"report_date": found.report_date,
			"posting_date": found.posting_date,
		}
	)
	doc.insert(ignore_permissions=True, set_name=found.name)
	if found.submit:
		doc.submit()
