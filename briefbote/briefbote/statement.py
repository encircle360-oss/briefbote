"""What the print formats Kontoauszug and Saldenbestätigung read of a Party Statement: its open items, from ERPNext's
reports Accounts Receivable and Accounts Payable for a draft and from the rows it stored for a submitted document,
the balance of each currency and the texts (briefbote/statement/statement.py). The letter is that of a payment
(payment_letter.html) with columns of its own, addressed to the primary address of the customer or supplier
(briefbote_payment_letter)."""

import dataclasses

import frappe
from erpnext.accounts.report.accounts_payable.accounts_payable import execute as payables
from erpnext.accounts.report.accounts_receivable.accounts_receivable import execute as receivables
from frappe.utils import fmt_money, formatdate, getdate

from briefbote.briefbote.printing import t
from briefbote.briefbote.receipt import table_column as _column
from briefbote.statement import statement

# The reports of ERPNext that list the open items of a party from the Payment Ledger, the source of the
# receivables and payables in its books.
REPORTS = {"Customer": receivables, "Supplier": payables}
NAMES = {"Customer": "customer_name", "Supplier": "supplier_name"}
PARTY_NUMBERS = {"Customer": "Customer No.", "Supplier": "Supplier No."}
REFERENCES = {"Customer": "Your Order", "Supplier": "Your Invoice"}


def party_name(party_type: str, party: str) -> str:
	field = NAMES.get(party_type)
	return (frappe.db.get_value(party_type, party, field) if field and party else "") or party or ""


def report_rows(company: str, party_type: str, party: str, report_date) -> list:
	"""The rows of the report of the party as of the end of the cut-off date, in the currency of the party's account
	(in_party_currency), as the report shows them for one party."""
	filters = frappe._dict(
		company=company,
		report_date=report_date,
		party_type=party_type,
		party=[party],
		in_party_currency=1,
		ageing_based_on="Due Date",
		calculate_ageing_with="Report Date",
	)
	return REPORTS[party_type](filters)[1]


def ledger_items(company: str, party_type: str, party: str, report_date) -> list[statement.Item]:
	return statement.items(report_rows(company, party_type, party, report_date))


def item_row(item: statement.Item) -> dict:
	return {
		"voucher_type": item.voucher_type,
		"voucher_no": item.voucher_no,
		"kind": item.kind,
		"reference": item.reference,
		"posting_date": item.posting_date,
		"due_date": item.due_date,
		"invoiced": item.invoiced,
		"paid": item.paid,
		"outstanding": item.outstanding,
		"currency": item.currency,
	}


def balance_row(balance: statement.Balance) -> dict:
	return {
		"currency": balance.currency,
		"invoiced": balance.invoiced,
		"paid": balance.paid,
		"outstanding": balance.outstanding,
	}


def stored_items(doc) -> list[statement.Item]:
	"""The rows a submitted statement keeps, in the order it stored them."""
	return [
		dataclasses.replace(
			statement.item(
				{
					"voucher_type": row.voucher_type,
					"voucher_no": row.voucher_no,
					"posting_date": getdate(row.posting_date) if row.posting_date else None,
					"due_date": getdate(row.due_date) if row.due_date else None,
					"invoiced": row.invoiced,
					"paid": row.paid,
					"outstanding": row.outstanding,
					"currency": row.currency,
					"bill_no": row.reference,
				}
			),
			kind=row.kind,
		)
		for row in doc.get("items") or ()
	]


def items_of(doc) -> list[statement.Item]:
	if statement.reads_ledger(int(doc.docstatus or 0)):
		return ledger_items(doc.company, doc.party_type, doc.party, doc.report_date)
	return stored_items(doc)


def _date(value) -> str:
	return formatdate(value) if value else ""


def _money(value, currency: str) -> str:
	return fmt_money(value, currency=currency)


def briefbote_statement(doc, printed_kind: str = statement.OPEN_ITEMS) -> dict:
	"""What the print format of printed_kind prints of a Party Statement."""
	found = items_of(doc)
	balances = statement.balances(found)
	docstatus = int(doc.docstatus or 0)
	states = statement.states(doc.kind, printed_kind, docstatus)
	title = t(statement.title(printed_kind))
	day = _date(doc.report_date)
	references = any(each.reference for each in found)
	columns = [
		_column("kind", "Document", 20, "first"),
		_column("name", "Number", 26),
		*([_column("reference", REFERENCES[doc.party_type], 24)] if references else []),
		_column("date", "Date", 18),
		_column("due", "Due Date", 18),
		_column("invoiced", "Amount", None, "money"),
		_column("paid", "Paid", 22, "money"),
		_column("outstanding", "Open", 24, "money"),
	]
	rows = [
		{
			"kind": t(each.kind),
			"name": each.voucher_no,
			"reference": each.reference,
			"date": _date(each.posting_date),
			"due": _date(each.due_date),
			"invoiced": _money(each.invoiced, each.currency),
			"paid": _money(each.paid, each.currency),
			"outstanding": _money(each.outstanding, each.currency),
		}
		for each in found
	]
	single = len(balances) == 1
	totals = [
		(
			t("Balance") if single else t("Balance in {0}").format(balance.currency),
			_money(balance.outstanding, balance.currency),
			"total",
		)
		for balance in balances
	]
	closing = (
		[
			t(statement.BALANCE_TEXTS[statement.favour(doc.party_type, balance.outstanding)]).format(
				day, _money(abs(balance.outstanding), balance.currency)
			)
			for balance in balances
		]
		if states
		else []
	)
	findings = []
	if doc.kind != printed_kind:
		findings.append(t(statement.WRONG_KIND))
	elif docstatus == 2:
		findings.append(t(statement.CANCELLED))
	info = [
		(t("Number"), doc.name),
		(t("Date"), _date(doc.posting_date)),
		(t("Cut-off Date"), day),
		(t(PARTY_NUMBERS[doc.party_type]), doc.party if doc.party != doc.party_name else ""),
	]
	text = ""
	if states:
		text = t(statement.STATEMENT_TEXT if found else statement.NO_ITEMS).format(day)
	return {
		"title": title,
		"subject": t("Open items as of {0}").format(day),
		"info": [(label, value) for label, value in info if value],
		"findings": findings,
		"findings_title": t(statement.STATES_NOTHING_TITLE),
		"text": text,
		"columns": columns,
		"rows": rows,
		"totals": totals,
		"closing": closing,
		"unallocated": "",
		"signature": False,
		"signature_fields": [],
	}
