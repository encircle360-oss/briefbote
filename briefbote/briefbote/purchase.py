"""What the print formats of buying read beyond the frame of the letter: the Bestellung of a Purchase Order with its
dates, the delivery address, the positions with the item numbers of the supplier, the totals with the tax of the
supplier where the supply is taxable in Germany, the payment terms and the request to confirm
(briefbote/purchase/order.py); the Anfrage of a Request for Quotation (briefbote/purchase/request.py) and the
Lieferantenrücksendung of a Purchase Receipt that returns goods (briefbote/purchase/returns.py). The positions,
totals, serial numbers and batches are read as for the documents of sales (briefbote/briefbote/sales.py)."""

import frappe
from frappe.contacts.doctype.address.address import get_default_address
from frappe.utils import cint, flt, getdate, strip_html

from briefbote.briefbote.printing import BREAKS, briefbote_letter, settings, t
from briefbote.briefbote.sales import (
	_asks,
	_date,
	_dates,
	_filled,
	_measured,
	_payment_terms,
	_position,
	_rates,
	_totals,
	addressed,
	identifiers,
	references,
	weight,
)
from briefbote.invoice import document, self_billing, taxes
from briefbote.layout import letter as letters
from briefbote.purchase import order as purchase
from briefbote.purchase import request, returns
from briefbote.sales import delivery, order


def _case(doc, config) -> self_billing.PurchaseCase:
	for row in config.get("purchase_tax_cases") or ():
		if row.purchase_taxes_and_charges == doc.taxes_and_charges:
			return self_billing.case(row.tax_case)
	return self_billing.PurchaseCase.DOMESTIC


def _delivery_address(doc, home_country: str) -> list[str]:
	if not doc.get("shipping_address"):
		return []
	address = frappe.get_cached_doc("Address", doc.shipping_address)
	party = letters.Party(
		name="",
		street=address.address_line1 or "",
		street2=address.address_line2 or "",
		pincode=address.pincode or "",
		city=address.city or "",
		country=address.country or "",
	)
	return [line for line in letters.address_lines(party, home_country, t) if line]


def briefbote_purchase_order(doc) -> dict:
	"""What the print format Bestellung prints of a Purchase Order besides the frame of the letter."""
	config = settings(doc.company)
	case = _case(doc, config)
	counted = [row.name for row in doc.items]
	shows_tax = purchase.shows_tax(case)
	rates = _rates(doc, counted) if shows_tax else {}
	when = order.delivery(
		getdate(doc.schedule_date) if doc.get("schedule_date") else None,
		[getdate(row.schedule_date) if row.get("schedule_date") else None for row in doc.items],
	)
	positions = []
	for row in doc.items:
		notes = (
			[t(purchase.SUPPLIER_PART).format(row.supplier_part_no)] if row.get("supplier_part_no") else []
		)
		position = _position(doc, row, rates, notes)
		if when and when.per_position and row.get("schedule_date"):
			position["period"] = t(order.POSITION_DELIVERY).format(_date(row.schedule_date))
		positions.append(position)
	title = t(purchase.TITLE)
	country = frappe.get_cached_value("Company", doc.company, "country") or ""
	info = [
		(t("Purchase Order No."), doc.name),
		(t("Date"), _date(doc.transaction_date)),
		(t("Supplier No."), doc.supplier if doc.supplier != doc.supplier_name else ""),
		(t(when.label), _dates(when.dates)) if when else ("", ""),
	]
	notices = [t(document.REVERSE_CHARGE)] if case is self_billing.PurchaseCase.REVERSE_CHARGE else []
	return _measured(
		{
			"kind": "purchase order",
			"title": title,
			"subject": f"{title} {doc.name}",
			"info": _filled(info),
			"positions": positions,
			"show_rates": taxes.shows_rates(rates),
			"totals": _totals(doc, rates, counted, with_tax=shows_tax),
			"notices": notices,
			"payment": [*_payment_terms(doc), *(t(text) for text in purchase.closing(_asks(doc)))],
			"terms": doc.get("terms") or "",
			"delivery_address": _delivery_address(doc, country),
			"delivery_label": t(purchase.DELIVERY_ADDRESS),
		}
	)


def _texts(found: list[tuple[str, tuple]]) -> list[str]:
	return [t(text).format(*values) for text, values in found]


def _plain(html: str | None) -> str:
	text = strip_html(BREAKS.sub("\n", html or "")).strip()
	return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def _address_line(doc, label: str) -> str:
	country = frappe.get_cached_value("Company", doc.company, "country") or ""
	lines = _delivery_address(doc, country)
	return f"{t(label)}: {', '.join(lines)}" if lines else ""


def briefbote_request_letter(doc, no_letterhead=0) -> dict:
	"""The frame of the letter of a Request for Quotation, addressed to the supplier ERPNext prints it for (vendor),
	with the contact of its row; addressed to nobody where there is none."""
	frame = briefbote_letter(doc, no_letterhead)
	vendor = doc.get("vendor")
	if not vendor:
		frame["recipient"], frame["dense"] = [], False
		return frame
	row = next((row for row in doc.get("suppliers") or () if row.supplier == vendor), None)
	contact = frappe.db.get_value("Contact", row.contact, "full_name") if row and row.contact else ""
	name = frappe.get_cached_value("Supplier", vendor, "supplier_name") or vendor
	return addressed(frame, get_default_address("Supplier", vendor), name, contact or "", titled=False)


def briefbote_request_for_quotation(doc) -> dict:
	"""What the print format Anfrage prints of a Request for Quotation besides the frame of the letter: the message for
	the supplier, the positions without prices with our and the supplier's item numbers and the day each is required
	by, what the supplier is asked to state and the delivery address; findings instead where the request has no
	supplier to go to (briefbote/purchase/request.py)."""
	vendor = doc.get("vendor") or ""
	title = t(request.TITLE)
	days = request.required(
		getdate(doc.schedule_date) if doc.get("schedule_date") else None,
		[getdate(row.schedule_date) if row.get("schedule_date") else None for row in doc.items],
	)
	positions = []
	for row in doc.items:
		notes = _texts(
			request.item_numbers(row.get("item_code"), row.item_name, row.get("supplier_part_no"))
			+ request.unit_price_note(flt(row.qty))
		)
		position = _position(doc, row, {}, notes, priced=False)
		if row.get("schedule_date"):
			position["period"] = t(request.POSITION_REQUIRED).format(_date(row.schedule_date))
		positions.append(position)
	name = frappe.get_cached_value("Supplier", vendor, "supplier_name") if vendor else ""
	info = [
		(t(request.NUMBER), doc.name),
		(t("Date"), _date(doc.transaction_date)),
		(t("Supplier No."), vendor if vendor != name else ""),
		(t(request.REQUIRED_BY), _dates(days) if days else ""),
	]
	asks = _asks(doc)
	terms = request.delivery_terms(doc.get("incoterm"), doc.get("named_place"))
	closing = _texts(request.closing(asks, bool(days), terms))
	delivery_line = _address_line(doc, purchase.DELIVERY_ADDRESS)
	message = request.message(_plain(doc.get("message_for_supplier")), bool(cint(doc.get("use_html"))))
	return {
		"kind": "request",
		"title": title,
		"subject": f"{title} {doc.name}",
		"info": _filled(info),
		"findings": _texts(
			request.supplier_findings(vendor, [row.supplier for row in doc.get("suppliers") or ()])
		),
		"findings_title": t(request.FINDINGS_TITLE),
		"intro": message if asks else "",
		"positions": positions,
		"prices": False,
		"notices": [],
		"payment": [*closing, *([delivery_line] if delivery_line else [])],
		"terms": doc.get("terms") or "",
		"weight": "",
		"signature": False,
	}


def briefbote_return_letter(doc, no_letterhead=0) -> dict:
	"""The frame of the letter of a return to the supplier, addressed where the goods go back: the dispatch address
	of the supplier where the receipt has one, else the address of the supplier."""
	frame = briefbote_letter(doc, no_letterhead)
	if doc.get("dispatch_address"):
		return addressed(frame, doc.dispatch_address, doc.supplier_name, doc.get("contact_display") or "")
	return frame


def briefbote_purchase_return(doc) -> dict:
	"""What the print format Lieferantenrücksendung prints of a Purchase Receipt that returns goods besides the frame
	of the letter: the receipt it returns and the supplier's delivery note, the positions with the quantity that
	goes back, its serial numbers and batches and the share rejected on receipt, the weight, the pick-up address
	and the line for the carrier to sign; a finding instead where the receipt is no return
	(briefbote/purchase/returns.py)."""
	is_return = bool(cint(doc.get("is_return")))
	original = (
		frappe.db.get_value(
			"Purchase Receipt", doc.return_against, ["posting_date", "supplier_delivery_note"], as_dict=True
		)
		if doc.get("return_against")
		else None
	)
	title = t(returns.TITLE)
	positions = []
	for row in doc.items:
		quantity, rejected = flt(row.qty), flt(row.get("rejected_qty"))
		field = row.meta.get_field("qty")
		note = returns.rejected_note(
			quantity, rejected, bool(cint(row.get("return_qty_from_rejected_warehouse")))
		)
		notes = [t(note[0]).format(*(frappe.format(value, field, row) for value in note[1]))] if note else []
		position = _position(doc, row, {}, [], priced=False)
		position["details"] = [*identifiers(row), *notes]
		position["description"] = "\n".join(
			text for text in (position["description"], *position["details"]) if text
		)
		position["quantity"] = frappe.format(returns.returned(quantity, rejected), field, row)
		positions.append(position)
	info = [
		(t("Number"), doc.name),
		(t("Date"), _date(doc.posting_date)),
		(t("Supplier No."), doc.supplier if doc.supplier != doc.supplier_name else ""),
		(t(returns.GOODS_RECEIPT), references("Purchase Receipt", [doc.return_against]) if original else ""),
		(
			t(returns.SUPPLIER_DELIVERY_NOTE),
			doc.get("supplier_delivery_note") or (original.supplier_delivery_note if original else "") or "",
		),
		(
			t(returns.OUR_PURCHASE_ORDER),
			references("Purchase Order", order.quotations(row.get("purchase_order") for row in doc.items)),
		),
		(t(returns.CARRIER), doc.get("transporter_name") or ""),
	]
	pick_up = _address_line(doc, returns.PICK_UP)
	return {
		"kind": "return",
		"title": title,
		"subject": t(returns.SUBJECT).format(
			title, doc.name, doc.return_against, _date(original.posting_date)
		)
		if original
		else f"{title} {doc.name}",
		"info": _filled(info),
		"findings": [t(text) for text in returns.findings(is_return)],
		"findings_title": t(returns.FINDINGS_TITLE),
		"positions": positions,
		"prices": False,
		"notices": [],
		"payment": [pick_up] if pick_up else [],
		"terms": doc.get("terms") or "",
		"weight": weight(doc),
		"signature": returns.asks_signature(_asks(doc)),
		"received": t(returns.TAKEN_OVER),
		"signature_fields": [t(field) for field in delivery.SIGNATURE_FIELDS],
	}
