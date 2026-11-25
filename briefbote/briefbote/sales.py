"""What the print formats of the documents of sales read beyond the frame of the letter: the Angebot of a Quotation,
the Auftragsbestätigung of a Sales Order and the Lieferschein of a Delivery Note. Each method gives its print format the same shape as briefbote_invoice
(briefbote/briefbote/printing.py), so that the shared part positions.html sets their positions and totals; the rules
live in the pure modules under briefbote/sales.
"""

from datetime import date
from decimal import Decimal

import frappe
from frappe.utils import cint, flt, formatdate, getdate, strip_html

from briefbote.briefbote.printing import (
	BREAKS,
	briefbote_letter,
	document_status,
	position_columns,
	settings,
	t,
)
from briefbote.invoice import document, taxes
from briefbote.layout import letter as letters
from briefbote.layout import status
from briefbote.sales import delivery, offer, order

CURRENCY = {"fieldtype": "Currency", "options": "currency"}


def _date(value) -> str:
	return formatdate(value) if value else ""


def _dates(dates: tuple[date, ...]) -> str:
	if len(dates) == 2:
		return t("{0} to {1}").format(_date(dates[0]), _date(dates[1]))
	return _date(dates[0])


def _filled(info: list[tuple[str, str]]) -> list[tuple[str, str]]:
	"""The rows of the information block that have a value; a label never stands alone."""
	return [(label, value) for label, value in info if value]


def _description(row) -> str:
	text = strip_html(BREAKS.sub("\n", row.description or "")).strip()
	text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
	return "" if text == (row.item_name or "").strip() else text


def _tax_case(doc, config) -> tuple[document.Case, str]:
	"""The tax case of the sales tax template of the document, as the Einstellungen Geschäftspost give it."""
	for row in config.tax_cases:
		if row.taxes_and_charges == doc.taxes_and_charges:
			return document.case(row.tax_case), row.exemption_reason or doc.get("tax_exemption_reason") or ""
	return document.Case.DOMESTIC, doc.get("tax_exemption_reason") or ""


def _notices(doc, config) -> list[str]:
	"""The notices of the tax case, as the invoice will carry them, so that the customer reads the price as it will be
	invoiced (briefbote/invoice/document.py)."""
	tax_case, reason = _tax_case(doc, config)
	small_business = bool(cint(config.small_business))
	return [
		t(text).format(*values)
		for text, values in document.notices(document.Kind.INVOICE, tax_case, small_business, reason)
	]


def _details(doc) -> list[taxes.Detail]:
	return [
		taxes.Detail(item=row.item_row, tax=row.tax_row, rate=Decimal(str(flt(row.rate))))
		for row in doc.get("item_wise_tax_details") or ()
	]


def _rates(doc, counted: list[str]) -> dict[str, Decimal]:
	"""The tax rate of each position that counts toward the total (briefbote/invoice/taxes.py)."""
	line_rates = [
		Decimal(str(flt(tax.rate)))
		for tax in doc.get("taxes") or ()
		if tax.charge_type == "On Net Total"
		and flt(tax.rate)
		and tax.get("add_deduct_tax", "Add") != "Deduct"
	]
	return taxes.position_rates(
		counted, _details(doc), taxes.single_rate(line_rates) if line_rates else Decimal(0)
	)


def _totals(doc, rates: dict[str, Decimal], counted: list[str]) -> list[tuple[str, str, str]]:
	"""Net amount, the tax by rate and base, as the invoice prints them, and the total."""
	lines = []
	if flt(doc.discount_amount):
		lines.append((t("Total of the Positions"), doc.get_formatted("total"), ""))
		lines.append((t("Discount"), doc.get_formatted("discount_amount"), ""))
	lines.append((t("Net Amount"), doc.get_formatted("net_total"), "sum"))
	nets = {
		row.name: Decimal(str(flt(row.net_amount or row.amount))) for row in doc.items if row.name in counted
	}
	taxed = [tax for tax in doc.get("taxes") or () if flt(tax.tax_amount)]
	untaxed = taxes.untaxed(nets, rates)
	if untaxed and taxed:
		lines.append((t("Consideration without VAT"), frappe.format(untaxed, CURRENCY, doc), ""))
	details = _details(doc)
	for tax in taxed:
		found = (
			taxes.tax_base(
				tax.name, Decimal(str(flt(tax.rate))), Decimal(str(flt(tax.net_amount))), details, nets
			)
			if tax.charge_type == "On Net Total"
			else None
		)
		label = (
			t("VAT {0} % on {1}").format(taxes.percent(found.rate), frappe.format(found.base, CURRENCY, doc))
			if found
			else tax.description or tax.account_head
		)
		lines.append((label, tax.get_formatted("tax_amount", doc), ""))
	rounded = not cint(doc.disable_rounded_total) and flt(doc.rounding_adjustment)
	if rounded:
		lines.append((t("Rounding"), doc.get_formatted("rounding_adjustment"), ""))
	lines.append(
		(t("Total Amount"), doc.get_formatted("rounded_total" if rounded else "grand_total"), "total")
	)
	return lines


def _position(doc, row, rates: dict[str, Decimal], notes: list[str], priced: bool = True) -> dict:
	description = "\n".join(text for text in (_description(row), *notes) if text)
	return {
		"number": row.idx,
		"name": row.item_name,
		"description": description,
		"period": "",
		"quantity": row.get_formatted("qty", doc) if priced or flt(row.qty) else "",
		"unit": t(row.uom or row.stock_uom or ""),
		"rate": row.get_formatted("rate", doc),
		"tax_rate": f"{taxes.percent(rates[row.name])} %" if row.name in rates else "",
		"amount": row.get_formatted("amount", doc) if priced else "",
	}


def _asks(doc) -> bool:
	"""Whether the document may ask the reader to act: not as a draft or cancelled (briefbote/layout/status.py)."""
	return status.asks_for_payment(document_status(doc))


def _measured(found: dict) -> dict:
	"""The document with the widths of the columns of its positions and totals, as positions.html sets them."""
	if found["totals"]:
		found["columns"] = position_columns(found["positions"], found["totals"], found["show_rates"])
	return found


def _customer_number(customer: str | None, name: str | None) -> tuple[str, str]:
	return (t("Customer No."), customer if customer and customer != name else "")


def briefbote_quotation(doc) -> dict:
	"""What the print format Angebot prints of a Quotation besides the frame of the letter: its positions with the
	alternatives and unit prices that do not count, the totals, the tax notices, its validity and how to accept it
	(briefbote/sales/offer.py)."""
	config = settings(doc.company)
	lines = offer.lines(
		offer.Row(row.name, row.idx, bool(cint(row.get("is_alternative"))), Decimal(str(flt(row.qty))))
		for row in doc.items
	)
	counted = [line.name for line in lines if line.counts]
	rates = _rates(doc, counted)
	roles = {line.name: line for line in lines}
	positions = []
	for row in doc.items:
		line = roles[row.name]
		found = offer.note(line)
		notes = [t(found[0]).format(*found[1])] if found else []
		positions.append(_position(doc, row, rates, notes, priced=line.role is not offer.Role.UNIT_PRICE))
	customer = doc.party_name if doc.get("quotation_to") == "Customer" else ""
	valid_till = getdate(doc.valid_till) if doc.get("valid_till") else None
	title = t(offer.TITLE)
	info = [
		(t("Quotation No."), doc.name),
		(t("Date"), _date(doc.transaction_date)),
		(t(offer.VALID_UNTIL), _date(valid_till)),
		_customer_number(customer, doc.customer_name),
	]
	closing = [
		t(text).format(*(_date(value) for value in values))
		for text, values in offer.closing(valid_till, _asks(doc))
	]
	return _measured(
		{
			"kind": "quotation",
			"title": title,
			"subject": f"{title} {doc.name}",
			"info": _filled(info),
			"positions": positions,
			"show_rates": taxes.shows_rates(rates),
			"totals": _totals(doc, rates, counted),
			"notices": _notices(doc, config),
			"payment": [*_payment_terms(doc), *closing],
			"terms": doc.get("terms") or "",
		}
	)


def _payment_terms(doc) -> list[str]:
	terms = [
		order.Term(
			portion=Decimal(str(flt(row.invoice_portion))),
			amount=row.get_formatted("payment_amount", doc),
			due=_date(row.due_date),
			term=row.get("payment_term") or "",
			description=strip_html(row.get("description") or "").strip(),
		)
		for row in doc.get("payment_schedule") or ()
		if flt(row.payment_amount)
	]
	return [t(text).format(*values) for text, values in order.payment_terms(terms)]


def _quotation_reference(doc) -> str:
	names = order.quotations(row.get("prevdoc_docname") for row in doc.items)
	if not names:
		return ""
	days = dict(
		frappe.get_all(
			"Quotation", filters={"name": ("in", names)}, fields=["name", "transaction_date"], as_list=True
		)
	)
	return ", ".join(
		t("{0} of {1}").format(name, _date(days[name])) if days.get(name) else name for name in names
	)


def briefbote_sales_order(doc) -> dict:
	"""What the print format Auftragsbestätigung prints of a Sales Order besides the frame of the letter: the quotation
	and the order of the customer it confirms, when it is delivered or performed, its positions and totals, the tax
	notices and the agreed payment terms (briefbote/sales/order.py)."""
	config = settings(doc.company)
	counted = [row.name for row in doc.items]
	rates = _rates(doc, counted)
	when = order.delivery(
		getdate(doc.delivery_date) if doc.get("delivery_date") else None,
		[getdate(row.delivery_date) if row.get("delivery_date") else None for row in doc.items],
		(getdate(doc.from_date), getdate(doc.to_date))
		if doc.get("from_date") and doc.get("to_date")
		else None,
	)
	positions = []
	for row in doc.items:
		position = _position(doc, row, rates, [])
		if when and when.per_position and row.get("delivery_date"):
			position["period"] = t(order.POSITION_DELIVERY).format(_date(row.delivery_date))
		positions.append(position)
	title = t(order.TITLE)
	customer_order = (
		t("{0} of {1}").format(doc.po_no, _date(doc.po_date))
		if doc.get("po_date")
		else doc.get("po_no") or ""
	)
	info = [
		(t("Order No."), doc.name),
		(t("Date"), _date(doc.transaction_date)),
		_customer_number(doc.customer, doc.customer_name),
		(t("Your Order"), customer_order),
		(t(order.OUR_QUOTATION), _quotation_reference(doc)),
		(t(when.label), _dates(when.dates)) if when else ("", ""),
		(t("Your VAT ID"), doc.get("tax_id") or ""),
	]
	return _measured(
		{
			"kind": "order",
			"title": title,
			"subject": f"{title} {doc.name}",
			"info": _filled(info),
			"positions": positions,
			"show_rates": taxes.shows_rates(rates),
			"totals": _totals(doc, rates, counted),
			"notices": _notices(doc, config),
			"payment": [*_payment_terms(doc), *(t(text) for text in order.closing(_asks(doc)))],
			"terms": doc.get("terms") or "",
		}
	)


def briefbote_delivery_letter(doc, no_letterhead=0) -> dict:
	"""The frame of the letter of a Delivery Note, addressed to where the goods go: the shipping address of the note
	where it has one, else the address of the customer."""
	frame = briefbote_letter(doc, no_letterhead)
	shipping = (
		frappe.get_cached_doc("Address", doc.shipping_address_name)
		if doc.get("shipping_address_name")
		else None
	)
	if shipping:
		party = letters.Party(
			name=shipping.address_title or doc.customer_name,
			street=shipping.address_line1 or "",
			street2=shipping.address_line2 or "",
			pincode=shipping.pincode or "",
			city=shipping.city or "",
			country=shipping.country or "",
		)
		frame["recipient"] = letters.address_lines(party, frame["company"].country, t)
		frame["dense"] = letters.dense(frame["recipient"])
	return frame


def _identifiers(row) -> list[str]:
	serials = delivery.split_serials(row.get("serial_no"))
	batches = [delivery.Batch(row.batch_no, Decimal(str(flt(row.qty))))] if row.get("batch_no") else []
	if row.get("serial_and_batch_bundle"):
		for entry in frappe.get_all(
			"Serial and Batch Entry",
			filters={"parent": row.serial_and_batch_bundle},
			fields=["serial_no", "batch_no", "qty"],
			order_by="idx",
		):
			if entry.serial_no:
				serials.append(entry.serial_no)
			if entry.batch_no:
				batches.append(delivery.Batch(entry.batch_no, Decimal(str(flt(entry.qty)))))
	return [t(text).format(*values) for text, values in delivery.identifiers(serials, batches)]


def _references(doctype: str, names: list[str]) -> str:
	if not names:
		return ""
	field = "posting_date" if doctype == "Delivery Note" else "transaction_date"
	days = dict(
		frappe.get_all(doctype, filters={"name": ("in", names)}, fields=["name", field], as_list=True)
	)
	return ", ".join(
		t("{0} of {1}").format(name, _date(days[name])) if days.get(name) else name for name in names
	)


def _weight(doc) -> str:
	units = {
		row.get("weight_uom")
		for row in doc.items
		if flt(row.get("total_weight") or row.get("weight_per_unit"))
	}
	units |= {row.get("weight_uom") for row in doc.items if row.get("weight_uom")}
	if not flt(doc.get("total_net_weight")) or len(units) != 1 or not next(iter(units)):
		return ""
	value = delivery.number(Decimal(str(flt(doc.total_net_weight))))
	return t(delivery.NET_WEIGHT).format(f"{value} {t(next(iter(units)))}")


def briefbote_delivery_note(doc) -> dict:
	"""What the print format Lieferschein prints of a Delivery Note besides the frame of the letter: its date and the
	day of delivery, the orders it delivers, its positions with serial numbers and batches, with prices only where
	the Einstellungen Geschäftspost ask for them, the net weight and the line for the signature of the recipient
	(briefbote/sales/delivery.py)."""
	config = settings(doc.company)
	priced = delivery.prices(
		bool(cint(config.get("delivery_note_prices"))), bool(cint(doc.get("print_without_amount")))
	)
	counted = [row.name for row in doc.items]
	rates = _rates(doc, counted) if priced else {}
	positions = []
	for row in doc.items:
		position = _position(doc, row, rates, [])
		position["details"] = _identifiers(row)
		position["description"] = "\n".join(filter(None, (position["description"], *position["details"])))
		position["quantity"] = row.get_formatted("qty", doc)
		positions.append(position)
	title = t(delivery.title(bool(cint(doc.is_return))))
	customer_order = (
		t("{0} of {1}").format(doc.po_no, _date(doc.po_date))
		if doc.get("po_date")
		else doc.get("po_no") or ""
	)
	info = [
		(t("Delivery Note No."), doc.name),
		*((t(label), _date(day)) for label, day in delivery.dates(getdate(doc.posting_date))),
		_customer_number(doc.customer, doc.customer_name),
		(t("Your Order"), customer_order),
		(
			t(delivery.OUR_ORDER),
			_references("Sales Order", order.quotations(row.get("against_sales_order") for row in doc.items)),
		),
		(
			t(delivery.TITLE),
			_references("Delivery Note", [doc.return_against]) if doc.get("return_against") else "",
		),
	]
	return {
		"kind": "delivery",
		"title": title,
		"subject": f"{title} {doc.name}",
		"info": _filled(info),
		"positions": positions,
		"prices": priced,
		"show_rates": taxes.shows_rates(rates),
		"totals": _totals(doc, rates, counted) if priced else [],
		"notices": [],
		"payment": [],
		"terms": doc.get("terms") or "",
		"weight": _weight(doc),
		"signature": delivery.asks_signature(
			bool(cint(config.get("delivery_note_signature"))), doc.docstatus == 1
		),
		"received": t(delivery.RECEIVED),
		"signature_fields": [t(field) for field in delivery.SIGNATURE_FIELDS],
	}
