"""What the print format Mahnung reads of a Dunning beyond the frame of the letter: its level, title and text, the open
invoices with their dates and amounts, and whether the interest and the fee ERPNext booked may be claimed, checked
against the default and the lawful interest of each invoice (briefbote/dunning). Nothing is computed for the books:
the letter prints what ERPNext booked, or a finding instead of it.
"""

from datetime import date
from decimal import Decimal

import frappe
from frappe.utils import cint, flt, formatdate, getdate

from briefbote.briefbote.printing import company_particulars, document_status, settings, t
from briefbote.dunning import interest, letter
from briefbote.layout import letter as letters
from briefbote.layout import status

# The title of the findings, which stand instead of a claim (findings.html).
FINDINGS_TITLE = "This letter claims nothing until the following is resolved:"
CURRENCY = {"fieldtype": "Currency", "options": "currency"}


def _date(value) -> str:
	return formatdate(value) if value else ""


def _money(doc, value) -> str:
	return frappe.format(value, CURRENCY, doc)


def _rates(config) -> list[interest.BaseRate]:
	return [
		interest.BaseRate(getdate(row.valid_from), Decimal(str(flt(row.rate))))
		for row in config.get("base_rates") or ()
	]


def _levels(config) -> list[letter.Level]:
	return [
		letter.Level(cint(row.level), row.title or "", row.text or "", cint(row.days_to_pay))
		for row in config.get("dunning_levels") or ()
	]


def _notice_on_invoices() -> bool:
	"""Whether the invoices told a consumer of § 286 Abs. 3 BGB: the print format Rechnung prints that notice to every
	consumer, so it counts where it is the default print format of the Sales Invoice."""
	return frappe.get_meta("Sales Invoice").default_print_format == "Rechnung"


def _reminders(doc, invoice: str) -> list[date]:
	"""The days of the earlier submitted Dunnings of an invoice."""
	parents = frappe.get_all(
		"Overdue Payment",
		filters={"sales_invoice": invoice, "docstatus": 1, "parent": ("!=", doc.name)},
		pluck="parent",
	)
	if not parents:
		return []
	days = frappe.get_all("Dunning", filters={"name": ("in", parents), "docstatus": 1}, pluck="posting_date")
	return [getdate(day) for day in days if getdate(day) < getdate(doc.posting_date)]


def _bank(config) -> str:
	if not config.bank_accounts:
		return ""
	bank = company_particulars(config.company, config).banks[0]
	parts = [
		bank.name,
		f"IBAN {letters.iban(bank.iban)}" if bank.iban else "",
		f"BIC {bank.bic}" if bank.bic else "",
	]
	return t("Bank details: {0}").format(" · ".join(part for part in parts if part))


def briefbote_dunning(doc) -> dict:
	"""What the print format Mahnung prints of a Dunning besides the frame of the letter."""
	config = settings(doc.company)
	posted = getdate(doc.posting_date)
	consumer = frappe.get_cached_value("Customer", doc.customer, "customer_type") == "Individual"
	notice = _notice_on_invoices()
	rates = _rates(config)
	number = max((cint(row.dunning_level) for row in doc.overdue_payments), default=1)
	found = letter.level(number, _levels(config))
	invoices = {
		row.name: row
		for row in frappe.get_all(
			"Sales Invoice",
			filters={"name": ("in", [row.sales_invoice for row in doc.overdue_payments])},
			fields=["name", "posting_date"],
		)
	}
	rows, lawful, in_default = [], Decimal(0), 0
	for row in doc.overdue_payments:
		issued = (
			getdate(invoices[row.sales_invoice].posting_date) if row.sales_invoice in invoices else posted
		)
		start = interest.default_start(
			due=getdate(row.due_date),
			issued=issued,
			consumer=consumer,
			notice=notice,
			reminders=_reminders(doc, row.sales_invoice),
		)
		in_default += bool(start and start <= posted)
		owed = interest.lawful(Decimal(str(flt(row.outstanding))), start, posted, rates, consumer)
		lawful = None if owed is None or lawful is None else lawful + owed
		amount = flt(row.payment_amount)
		rows.append(
			{
				"invoice": row.sales_invoice,
				"date": _date(issued),
				"due": _date(row.due_date),
				"amount": _money(doc, amount),
				"paid": _money(doc, amount - flt(row.outstanding)),
				"open": _money(doc, row.outstanding),
				"days": str(max((posted - getdate(row.due_date)).days, 0)),
			}
		)
	charges = letter.Charges(
		interest=Decimal(str(flt(doc.total_interest))).quantize(Decimal("0.01")),
		fee=Decimal(str(flt(doc.dunning_fee))).quantize(Decimal("0.01")),
		lawful=lawful,
		in_default=in_default,
	)
	findings, claim_interest, claim_fee = letter.assess(found.number, charges, consumer)
	totals = [(t("Open invoices"), _money(doc, doc.total_outstanding), "sum")]
	if claim_interest:
		totals.append(
			(
				t("Default interest (Section 288 BGB) up to {0}").format(_date(posted)),
				_money(doc, doc.total_interest),
				"",
			)
		)
	if claim_fee:
		totals.append((t("Lump sum (Section 288(5) BGB)"), _money(doc, doc.dunning_fee), ""))
	if claim_interest or claim_fee:
		totals.append((t("Total Amount"), _money(doc, doc.grand_total), "total"))
	asks = status.asks_for_payment(document_status(doc)) and not findings
	title = t(found.title)
	return {
		"title": title,
		"subject": f"{title} {doc.name}",
		"info": [
			(label, value)
			for label, value in (
				(t("Number"), doc.name),
				(t("Date"), _date(posted)),
				(t("Customer No."), doc.customer if doc.customer != doc.customer_name else ""),
			)
			if value
		],
		"findings": [t(text) for text in findings],
		"findings_title": t(FINDINGS_TITLE),
		"rows": rows,
		"totals": totals,
		"text": letter.fill(t(found.text), _date(letter.deadline(posted, found))) if asks else "",
		"bank": _bank(config) if asks else "",
		"closing": t("Payments received by {0} are taken into account.").format(_date(posted)),
	}
