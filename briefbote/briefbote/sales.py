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
	tax_details,
)
from briefbote.invoice import advance_invoice, completeness, document, taxes
from briefbote.layout import letter as letters
from briefbote.layout import status
from briefbote.sales import delivery, offer, order, proforma

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
	return tax_details(doc)


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


def _totals(
	doc, rates: dict[str, Decimal], counted: list[str], with_tax: bool = True
) -> list[tuple[str, str, str]]:
	"""Net amount, the tax by rate and base, as the invoice prints them, and the total. A tax line a purchase template
	deducts is the company's own tax and no line of the document."""
	lines = []
	if flt(doc.discount_amount):
		lines.append((t("Total of the Positions"), doc.get_formatted("total"), ""))
		lines.append((t("Discount"), doc.get_formatted("discount_amount"), ""))
	lines.append((t("Net Amount"), doc.get_formatted("net_total"), "sum"))
	nets = {
		row.name: Decimal(str(flt(row.net_amount or row.amount))) for row in doc.items if row.name in counted
	}
	taxed = [
		tax
		for tax in doc.get("taxes") or ()
		if with_tax and flt(tax.tax_amount) and tax.get("add_deduct_tax") != "Deduct"
	]
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
		found["columns"] = position_columns(
			found["positions"], found["totals"], found["show_rates"], not found.get("hide_quantities")
		)
	return found


def _vat_ids(doc, config, customer_vat_id: str) -> list[tuple[str, str]]:
	"""The rows of the USt-IdNrn. by the rule of the invoice (briefbote_invoice in printing.py): the customer's
	whenever it is known, and ours beside it where the tax case asks for both (§ 14a Abs. 1 Satz 3 and Abs. 3
	Satz 2 UStG), so that quotation, confirmation and invoice of one customer name the same numbers."""
	tax_case, _reason = _tax_case(doc, config)
	both = document.needs_both_vat_ids(tax_case, bool(cint(config.small_business)))
	rows = [(t("Your VAT ID"), customer_vat_id)] if customer_vat_id or both else []
	if both:
		rows.append((t("Our VAT ID"), frappe.get_cached_value("Company", doc.company, "tax_id") or ""))
	return rows


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
		*_vat_ids(
			doc, config, frappe.get_cached_value("Customer", customer, "tax_id") or "" if customer else ""
		),
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
		*_vat_ids(doc, config, doc.get("tax_id") or ""),
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
		position["description"] = "\n".join(
			text for text in (position["description"], *position["details"]) if text
		)
		# ERPNext keeps the quantity of a return negative; on paper it is what comes back.
		position["quantity"] = frappe.format(abs(flt(row.qty)), row.meta.get_field("qty"), row)
		positions.append(position)
	title = t(delivery.title(bool(cint(doc.is_return))))
	returned = (
		frappe.db.get_value("Delivery Note", doc.return_against, "posting_date")
		if doc.get("return_against")
		else None
	)
	subject = (
		t("{0} {1} to Delivery Note {2} of {3}").format(title, doc.name, doc.return_against, _date(returned))
		if returned
		else f"{title} {doc.name}"
	)
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
	return _measured(
		{
			"kind": "delivery",
			"title": title,
			"subject": subject,
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
				bool(cint(config.get("delivery_note_signature"))), _asks(doc)
			),
			"received": t(delivery.RECEIVED),
			"signature_fields": [t(field) for field in delivery.SIGNATURE_FIELDS],
		}
	)


def _order_reference(doc) -> str:
	return t("{0} of {1}").format(doc.name, _date(doc.transaction_date))


def _customer_order(doc) -> str:
	if doc.get("po_date"):
		return t("{0} of {1}").format(doc.po_no, _date(doc.po_date))
	return doc.get("po_no") or ""


def _charges_tax(doc) -> bool:
	return any(
		flt(tax.tax_amount) and tax.get("add_deduct_tax") != "Deduct" for tax in doc.get("taxes") or ()
	)


def briefbote_proforma(doc) -> dict:
	"""What the print format Proforma-Rechnung prints of the copy of a Sales Order that a Proforma Invoice of ERPNext 16
	renders (proforma_no, proforma_date, hide_item_qty on the copy; get_sales_order_copy in
	erpnext/selling/doctype/proforma_invoice/proforma_invoice.py), or of the order itself: the positions and their
	total with VAT, but no tax amount or rate, the notices of the tax case and that it is no invoice
	(briefbote/sales/proforma.py)."""
	config = settings(doc.company)
	hidden = bool(cint(doc.get("hide_item_qty")))
	when = order.delivery(
		getdate(doc.delivery_date) if doc.get("delivery_date") else None,
		[getdate(row.delivery_date) if row.get("delivery_date") else None for row in doc.items],
		(getdate(doc.from_date), getdate(doc.to_date))
		if doc.get("from_date") and doc.get("to_date")
		else None,
	)
	positions = [_position(doc, row, {}, []) for row in doc.items]
	number, _order = proforma.reference(
		doc.get("proforma_no") or "",
		getdate(doc.proforma_date) if doc.get("proforma_date") else None,
		doc.name,
		getdate(doc.transaction_date),
	)
	title = t(proforma.TITLE)
	info = [
		(t(proforma.PROFORMA_NO), number[0] if number else ""),
		(t("Date"), _date(number[1] if number else doc.transaction_date)),
		(t(proforma.OUR_ORDER), _order_reference(doc)),
		_customer_number(doc.customer, doc.customer_name),
		(t("Your Order"), _customer_order(doc)),
		(t(when.label), _dates(when.dates)) if when else ("", ""),
		*_vat_ids(doc, config, doc.get("tax_id") or ""),
	]
	lines = []
	if flt(doc.discount_amount):
		lines.append((t("Total of the Positions"), doc.get_formatted("total"), ""))
		lines.append((t("Discount"), doc.get_formatted("discount_amount"), ""))
	lines.append((t("Net Amount"), doc.get_formatted("net_total"), "sum"))
	rounded = not cint(doc.disable_rounded_total) and flt(doc.rounding_adjustment)
	lines.append(
		(
			t(proforma.total_label(_charges_tax(doc))),
			doc.get_formatted("rounded_total" if rounded else "grand_total"),
			"total",
		)
	)
	return _measured(
		{
			"kind": "proforma",
			"title": title,
			"number": number[0] if number else doc.name,
			"subject": f"{title} {number[0] if number else doc.name}",
			"info": _filled(info),
			"positions": positions,
			"hide_quantities": hidden,
			"show_rates": False,
			"totals": lines,
			"notices": [*_notices(doc, config), t(proforma.NOT_AN_INVOICE)],
			"payment": [t(text) for text in proforma.closing(_asks(doc))],
			"terms": doc.get("terms") or "",
		}
	)


def _receipts(doc) -> list[date]:
	"""The days of the payments booked against the order with the amount of the advance invoice."""
	entries = frappe.get_all(
		"Payment Entry Reference",
		filters={
			"reference_doctype": "Sales Order",
			"reference_name": doc.name,
			"parenttype": "Payment Entry",
		},
		pluck="parent",
	)
	if not entries:
		return []
	total = Decimal(str(flt(doc.grand_total)))
	return [
		getdate(entry.posting_date)
		for entry in frappe.get_all(
			"Payment Entry",
			filters={"name": ("in", entries), "docstatus": 1},
			fields=["posting_date", "paid_amount"],
		)
		if abs(Decimal(str(flt(entry.paid_amount))) - total) < document.CENT
	]


def _bases_known(doc, rates: dict[str, Decimal], counted: list[str]) -> bool:
	"""Whether every tax line of the document has a rate and base (briefbote/invoice/taxes.py)."""
	details = _details(doc)
	nets = {
		row.name: Decimal(str(flt(row.net_amount or row.amount))) for row in doc.items if row.name in counted
	}
	for tax in doc.get("taxes") or ():
		if not flt(tax.tax_amount) or tax.get("add_deduct_tax") == "Deduct":
			continue
		if tax.charge_type != "On Net Total":
			if taxes.shows_rates(rates):
				return False
			continue
		if not taxes.tax_base(
			tax.name, Decimal(str(flt(tax.rate))), Decimal(str(flt(tax.net_amount))), details, nets
		):
			return False
	return True


def _complete_address(name: str | None) -> bool:
	address = frappe.get_cached_doc("Address", name) if name else None
	return bool(address and address.address_line1 and (address.pincode or address.city))


def briefbote_advance_invoice(doc) -> dict:
	"""What the print format Anzahlungsrechnung prints of the copy of a Sales Order that a Proforma Invoice of
	ERPNext 16 renders for an amount of the order: an invoice over a payment before the supply (§ 14 Abs. 5 Satz 1
	UStG) with the number and date of the proforma, the expected time of the supply, the tax by rate and base and the
	request to pay; printed from the order itself it has no number of its own and is a finding
	(briefbote/invoice/advance_invoice.py)."""
	config = settings(doc.company)
	counted = [row.name for row in doc.items]
	rates = _rates(doc, counted)
	hidden = bool(cint(doc.get("hide_item_qty")))
	number = doc.get("proforma_no") or ""
	issued = getdate(doc.proforma_date) if doc.get("proforma_date") else None
	when = advance_invoice.expected(
		(getdate(doc.from_date), getdate(doc.to_date))
		if doc.get("from_date") and doc.get("to_date")
		else None,
		getdate(doc.delivery_date) if doc.get("delivery_date") else None,
		[getdate(row.delivery_date) if row.get("delivery_date") else None for row in doc.items],
	)
	receipt = advance_invoice.received(issued, _receipts(doc)) if number and issued else None
	tax_case, reason = _tax_case(doc, config)
	small_business = bool(cint(config.small_business))
	both = document.needs_both_vat_ids(tax_case, small_business)
	company_vat_id = frappe.get_cached_value("Company", doc.company, "tax_id") or ""
	title = t(advance_invoice.TITLE)
	info = [
		(t("Invoice No."), number),
		(t("Invoice Date"), _date(issued)),
		(t(advance_invoice.ORDER), _order_reference(doc)),
		_customer_number(doc.customer, doc.customer_name),
		(t("Your Order"), _customer_order(doc)),
		(t(when[0]), t(advance_invoice.EXPECTED).format(_dates(when[1]))) if when else ("", ""),
		(t(advance_invoice.RECEIVED), _date(receipt)),
		*_vat_ids(doc, config, doc.get("tax_id") or ""),
	]
	positions = [_position(doc, row, rates, []) for row in doc.items]
	asks = _asks(doc)
	numbered = bool(number)
	facts = completeness.Facts(
		small_amount=abs(flt(doc.grand_total)) <= completeness.SMALL_AMOUNT,
		recipient_address=_complete_address(doc.get("customer_address")),
		issuer_tax_id=bool(company_vat_id or config.tax_number),
		needs_both_vat_ids=both,
		recipient_vat_id=bool(doc.get("tax_id")),
		own_vat_id=bool(company_vat_id),
		taxable=document.charges_tax(tax_case, small_business),
		charges_tax=_charges_tax(doc),
		states_reason=bool(reason),
		bases_known=_bases_known(doc, rates, counted),
		asks_payment=numbered and asks,
		bank_account=bool(config.bank_accounts),
	)
	findings = [t(text) for text in (*advance_invoice.findings(numbered), *completeness.missing(facts))]
	request = advance_invoice.request(numbered, asks, bool(config.bank_accounts))
	text, values = advance_invoice.subject(number, doc.name)
	return _measured(
		{
			"kind": "advance invoice",
			"title": title,
			"number": number or doc.name,
			"subject": t(text).format(*values),
			"info": _filled(info),
			"findings": findings,
			"positions": positions,
			"hide_quantities": hidden,
			"show_rates": taxes.shows_rates(rates),
			"totals": _totals(doc, rates, counted),
			"notices": [*_notices(doc, config), *(t(notice) for notice in advance_invoice.notices(when))],
			"payment": [
				t(request).format(doc.get_formatted("rounded_total" if _rounded(doc) else "grand_total"))
			]
			if request
			else [],
			"terms": "",
		}
	)


def _rounded(doc) -> bool:
	return bool(not cint(doc.disable_rounded_total) and flt(doc.rounding_adjustment))
