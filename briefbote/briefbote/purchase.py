"""What the print format Bestellung reads of a Purchase Order beyond the frame of the letter: its dates, the
delivery address, the positions with the item numbers of the supplier, the totals with the tax of the supplier where
the supply is taxable in Germany, the payment terms and the request to confirm (briefbote/purchase/order.py). The
positions and totals are read as for the documents of sales (briefbote/briefbote/sales.py)."""

import frappe
from frappe.utils import getdate

from briefbote.briefbote.printing import settings, t
from briefbote.briefbote.sales import _date, _dates, _filled, _payment_terms, _position, _rates, _totals
from briefbote.invoice import document, self_billing, taxes
from briefbote.layout import letter as letters
from briefbote.purchase import order as purchase
from briefbote.sales import order


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
	return {
		"kind": "purchase order",
		"title": title,
		"subject": f"{title} {doc.name}",
		"info": _filled(info),
		"positions": positions,
		"show_rates": taxes.shows_rates(rates),
		"totals": _totals(doc, rates, counted, with_tax=shows_tax),
		"notices": notices,
		"payment": [*_payment_terms(doc), *(t(text) for text in purchase.closing(doc.docstatus == 1))],
		"terms": doc.get("terms") or "",
		"delivery_address": _delivery_address(doc, country),
		"delivery_label": t(purchase.DELIVERY_ADDRESS),
	}
