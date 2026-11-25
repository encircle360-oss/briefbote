"""What the print formats Zahlungsbestätigung and Quittung read of a Payment Entry beyond the frame of the letter: the
payment, the documents it was applied to, deductions and what is not yet applied (briefbote/sales/receipt.py)."""

import frappe
from frappe.utils import flt, formatdate

from briefbote.briefbote.printing import t
from briefbote.sales import receipt

CURRENCY = {"fieldtype": "Currency", "options": "currency"}
DATES = {"Sales Invoice": "posting_date", "Sales Order": "transaction_date", "Dunning": "posting_date"}


def _date(value) -> str:
	return formatdate(value) if value else ""


def _money(doc, value) -> str:
	return frappe.format(value, CURRENCY, doc)


def _issued(row) -> str:
	field = DATES.get(row.reference_doctype)
	return _date(frappe.db.get_value(row.reference_doctype, row.reference_name, field)) if field else ""


def briefbote_payment(doc, as_receipt=False) -> dict:
	"""What a Zahlungsbestätigung or, with as_receipt, a Quittung prints of a Payment Entry."""
	confirmed = receipt.confirms(doc.payment_type, doc.party_type, doc.docstatus)
	title = t(receipt.title(bool(as_receipt)))
	rows = [
		{
			"kind": t(receipt.kind(row.reference_doctype)),
			"name": row.reference_name,
			"date": _issued(row),
			"due": _date(row.due_date),
			"total": _money(doc, row.total_amount),
			"applied": _money(doc, row.allocated_amount),
		}
		for row in doc.get("references") or ()
	]
	totals = [(t("Payment received"), _money(doc, doc.paid_amount), "sum")]
	totals += [
		(row.description or row.account, _money(doc, row.amount), "") for row in doc.get("deductions") or ()
	]
	totals.append((t("Applied"), _money(doc, doc.total_allocated_amount), "total"))
	reference = " ".join(part for part in (doc.get("reference_no"), _date(doc.get("reference_date"))) if part)
	info = [
		(t("Number"), doc.name),
		(t("Date"), _date(doc.posting_date)),
		(t("Customer No."), doc.party if doc.party != doc.party_name else ""),
		(t("Mode of Payment"), t(doc.mode_of_payment or "")),
		(t("Reference"), reference),
	]
	paid, day = _money(doc, doc.paid_amount), _date(doc.posting_date)
	text = ""
	if confirmed:
		text = (
			t(receipt.RECEIVED).format(paid, day, doc.party_name or doc.party)
			if as_receipt
			else t(receipt.APPLIED).format(paid, day)
		)
	return {
		"title": title,
		"subject": f"{title} {doc.name}",
		"info": [(label, value) for label, value in info if value],
		"findings": [] if confirmed else [t(receipt.NOT_CONFIRMED)],
		"text": text,
		"rows": rows,
		"totals": totals,
		"unallocated": t(receipt.UNALLOCATED).format(_money(doc, doc.unallocated_amount))
		if confirmed and flt(doc.unallocated_amount) > 0
		else "",
		"signature": bool(as_receipt) and confirmed,
		"signature_fields": [t("Place and date"), t("Signature")],
	}
