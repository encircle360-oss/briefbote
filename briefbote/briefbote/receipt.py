"""What the print formats of a Payment Entry read beyond the frame of the letter: for Zahlungsbestätigung and Quittung
the payment received, the documents it was applied to, deductions and what is not yet applied
(briefbote/sales/receipt.py); for the Zahlungsavis the payment to a supplier, its invoices by the supplier's own
numbers and the cash discount taken (briefbote/purchase/remittance.py). Both print the same letter
(payment_letter.html) with columns of their own."""

import frappe
from frappe.contacts.doctype.address.address import get_default_address
from frappe.utils import flt, formatdate

from briefbote.briefbote.printing import briefbote_letter, company_particulars, document_status, settings, t
from briefbote.layout import letter as letters
from briefbote.layout import status
from briefbote.purchase import remittance
from briefbote.sales import receipt

# A Payment Entry has no field currency; its references are in the currency of the party's account: that of the
# account paid from for a payment received, that of the account paid to for a payment made.
CURRENCY = {"fieldtype": "Currency", "options": "paid_from_account_currency"}
PAID_CURRENCY = {"fieldtype": "Currency", "options": "paid_to_account_currency"}
# The deductions of a Payment Entry are in the currency of the company.
DEDUCTION_CURRENCY = {"fieldtype": "Currency", "options": "Company:company:default_currency"}
DATES = {"Sales Invoice": "posting_date", "Sales Order": "transaction_date", "Dunning": "posting_date"}
PRIMARY_ADDRESS = {"Customer": "customer_primary_address", "Supplier": "supplier_primary_address"}


def _date(value) -> str:
	return formatdate(value) if value else ""


def _money(doc, value, currency=CURRENCY) -> str:
	return frappe.format(value, currency, doc)


def _column(key: str, label: str, width: int | None = None, kind: str = "date") -> dict:
	"""A column of the table of documents: its width in millimetres (the one without takes the rest) and the class
	of its cells; the first column starts at the left edge, the amounts stand right."""
	return {"key": key, "label": t(label), "width": width, "kind": kind}


def _party_address(doc) -> str | None:
	field = PRIMARY_ADDRESS.get(doc.party_type)
	if not field:
		return None
	return frappe.db.get_value(doc.party_type, doc.party, field) or get_default_address(
		doc.party_type, doc.party
	)


def briefbote_payment_letter(doc, no_letterhead=0) -> dict:
	"""The frame of the letter of a Payment Entry, which has no address of its own: addressed to the primary address
	of the customer or the supplier."""
	frame = briefbote_letter(doc, no_letterhead)
	name = _party_address(doc)
	if name:
		address = frappe.get_cached_doc("Address", name)
		party = letters.Party(
			name=doc.party_name or doc.party,
			street=address.address_line1 or "",
			street2=address.address_line2 or "",
			pincode=address.pincode or "",
			city=address.city or "",
			country=address.country or "",
		)
		frame["recipient"] = letters.address_lines(party, frame["company"].country, t)
		frame["dense"] = letters.dense(frame["recipient"])
	return frame


def _issued(row) -> str:
	field = DATES.get(row.reference_doctype)
	return _date(frappe.db.get_value(row.reference_doctype, row.reference_name, field)) if field else ""


def _reference(doc) -> str:
	if doc.get("reference_no") and doc.get("reference_date"):
		return t("{0} of {1}").format(doc.reference_no, _date(doc.reference_date))
	return doc.get("reference_no") or ""


def briefbote_payment(doc, as_receipt=False) -> dict:
	"""What a Zahlungsbestätigung or, with as_receipt, a Quittung prints of a Payment Entry."""
	confirmed = receipt.confirms(doc.payment_type, doc.party_type, doc.docstatus) and status.asks_for_payment(
		document_status(doc)
	)
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
	info = [
		(t("Number"), doc.name),
		(t("Date"), _date(doc.posting_date)),
		(t("Customer No."), doc.party if doc.party != doc.party_name else ""),
		(t("Mode of Payment"), t(doc.mode_of_payment or "")),
		(t("Reference"), _reference(doc)),
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
		"findings_title": t(receipt.FINDINGS_TITLE),
		"text": text,
		"columns": [
			_column("kind", "Document", 22, "first"),
			_column("name", "Number", 30),
			_column("date", "Date", 22),
			_column("due", "Due Date", 22),
			_column("total", "Amount", None, "money"),
			_column("applied", "Applied", 28, "money"),
		],
		"rows": rows,
		"totals": totals,
		"unallocated": t(receipt.UNALLOCATED).format(_money(doc, doc.unallocated_amount))
		if confirmed and flt(doc.unallocated_amount) > 0
		else "",
		"signature": bool(as_receipt) and confirmed,
		"signature_fields": [t("Place and date"), t("Signature")],
	}


def _bill(row) -> tuple[str, str]:
	"""The supplier's number and date of the invoice a reference pays."""
	if row.reference_doctype != "Purchase Invoice":
		return row.get("bill_no") or "", ""
	bill_no, bill_date = frappe.db.get_value(
		"Purchase Invoice", row.reference_name, ["bill_no", "bill_date"]
	) or ("", None)
	return row.get("bill_no") or bill_no or "", _date(bill_date)


def _deduction_label(row) -> str:
	if row.description:
		return row.description
	return frappe.db.get_value("Account", row.account, "account_name") or row.account or ""


def _own_account(doc) -> str:
	"""The IBAN the payment came from, where it is the account the foot of the letter shows: the first bank account
	of the settings (foot_blocks in briefbote/layout/letter.py)."""
	iban = frappe.db.get_value("Bank Account", doc.bank_account, "iban") if doc.get("bank_account") else ""
	banks = company_particulars(doc.company, settings(doc.company)).banks
	shown = [banks[0].iban] if banks else []
	number = remittance.own_account(iban or "", shown)
	return letters.iban(number) if number else ""


def _remittance_totals(doc, paid: str, mode_type: str) -> list[tuple[str, str, str]]:
	"""Settled, the deductions but exchange differences, what is not applied and what was paid: the amount paid to the
	supplier is the sum of the others (get_base_unallocated_amount in
	erpnext/accounts/doctype/payment_entry/payment_entry.py)."""
	totals = [(t(remittance.SETTLED), _money(doc, doc.total_allocated_amount, PAID_CURRENCY), "sum")]
	totals += [
		(_deduction_label(row), _money(doc, row.amount, DEDUCTION_CURRENCY), "")
		for row in doc.get("deductions") or ()
		if not row.is_exchange_gain_loss
	]
	if flt(doc.unallocated_amount) > 0:
		totals.append((t(remittance.NOT_APPLIED), _money(doc, doc.unallocated_amount, PAID_CURRENCY), ""))
	totals.append((t(remittance.total_label(mode_type)), paid, "total"))
	return totals


def briefbote_remittance(doc) -> dict:
	"""What a Zahlungsavis prints of a Payment Entry."""
	advised = remittance.advises(doc.payment_type, doc.party_type, doc.docstatus) and status.asks_for_payment(
		document_status(doc)
	)
	# A payment in the other direction lists nothing: its documents and sums are no supplier's.
	references = (
		list(doc.get("references") or ()) if remittance.to_supplier(doc.payment_type, doc.party_type) else []
	)
	bills = [_bill(row) for row in references]
	discounts = [flt(row.get("payment_term_discount")) for row in references]
	rows = [
		{
			"bill_no": bill_no,
			"bill_date": bill_date,
			"name": row.reference_name,
			"total": _money(doc, row.total_amount, PAID_CURRENCY),
			"discount": _money(doc, discount, PAID_CURRENCY) if discount else "",
			"settled": _money(doc, row.allocated_amount, PAID_CURRENCY),
		}
		for row, (bill_no, bill_date), discount in zip(references, bills, discounts, strict=True)
	]
	columns = [
		_column("bill_no", "Your Invoice", 30, "first"),
		_column("bill_date", "Date", 22),
		_column("name", "Our Reference", 30),
		_column("total", "Amount", None, "money"),
	]
	if remittance.shows_discount(discounts):
		columns.append(_column("discount", "Cash Discount", 22, "money"))
	columns.append(_column("settled", remittance.SETTLED, 28, "money"))
	mode_type = (
		frappe.db.get_value("Mode of Payment", doc.mode_of_payment, "type") if doc.mode_of_payment else ""
	)
	paid = _money(doc, doc.received_amount, PAID_CURRENCY)
	totals = (
		_remittance_totals(doc, paid, mode_type or "")
		if remittance.to_supplier(doc.payment_type, doc.party_type)
		else []
	)
	title = t(remittance.TITLE)
	info = [
		(t("Number"), doc.name),
		(t("Date"), _date(doc.posting_date)),
		(t("Supplier No."), doc.party if doc.party != doc.party_name else ""),
		(t("Mode of Payment"), t(doc.mode_of_payment or "")),
		(t("Reference"), _reference(doc)),
		(t("Our account"), _own_account(doc) if advised else ""),
	]
	missing = remittance.without_bill_number(
		(row.reference_doctype, row.reference_name, bill_no)
		for row, (bill_no, _date_of_bill) in zip(references, bills, strict=True)
	)
	if advised:
		findings = [t(remittance.NO_BILL_NUMBER).format(name) for name in missing]
		findings_title = t(remittance.INCOMPLETE_TITLE)
	else:
		findings, findings_title = [t(remittance.NOT_ADVISED)], t(remittance.NO_PAYMENT_TITLE)
	return {
		"title": title,
		"subject": f"{title} {doc.name}",
		"info": [(label, value) for label, value in info if value],
		"findings": findings,
		"findings_title": findings_title,
		"text": t(remittance.text(mode_type or "")).format(_date(doc.posting_date), paid) if advised else "",
		"columns": columns,
		"rows": rows,
		"totals": totals,
		"unallocated": "",
		"signature": False,
		"signature_fields": [],
	}
