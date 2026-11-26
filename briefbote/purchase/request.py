"""The Anfrage of a Request for Quotation: a letter to one supplier asking for a quotation, with the positions
without prices, the days they are required by and the delivery terms. No law prescribes its content; it is a
business letter (§ 35a Abs. 1 GmbHG), whose particulars the frame of the letter prints. ERPNext keeps several
suppliers on one request and prints it for one of them at a time, the one in its field vendor
(update_supplier_part_no, get_pdf and before_print in
erpnext/buying/doctype/request_for_quotation/request_for_quotation.py). docs/anfrage.md names the sources.
"""

from collections.abc import Iterable
from datetime import date

TITLE = "Request for Quotation"
NUMBER = "Request No."
REQUIRED_BY = "Required by"
POSITION_REQUIRED = "Required by {0}"
OUR_PART = "Our item number {0}"
SUPPLIER_PART = "Your item number {0}"
UNIT_PRICE = "Please quote the price per unit; the quantity is still open."
ASK_PRICES = "Please state in your quotation the price per unit of each position."
ASK_DATES = "Please also state whether you can deliver by the required dates."
ASK_INCOTERM = "Please quote on the basis of the delivery terms {0}."
NO_SUPPLIER = "The request names no supplier. ERPNext prints it for one supplier of its list of suppliers."
NOT_LISTED = "The supplier {0} is not among the suppliers of this request."
FINDINGS_TITLE = "This request cannot be sent as it stands:"
# What the e-mail of ERPNext renders as a Jinja template and paper would print as it stands.
TEMPLATE_MARKS = ("{{", "{%")


def supplier_findings(vendor: str | None, listed: Iterable[str]) -> list[tuple[str, tuple]]:
	"""What keeps the request from going to the supplier it is printed for: none at all, or one it does not list."""
	if not vendor:
		return [(NO_SUPPLIER, ())]
	if vendor not in set(listed):
		return [(NOT_LISTED, (vendor,))]
	return []


def required(request_date: date | None, position_dates: Iterable[date | None]) -> tuple[date, ...]:
	"""The days the goods are required by: the first and the last of the positions, one where they share it, else
	the day of the request."""
	days = sorted({day for day in position_dates if day})
	if len(days) > 1:
		return (days[0], days[-1])
	if days:
		return (days[0],)
	return (request_date,) if request_date else ()


def message(text: str | None, use_html: bool) -> str:
	"""The message for the supplier as plain text, or nothing where it is HTML or a template of the e-mail."""
	text = (text or "").strip()
	if use_html or any(mark in text for mark in TEMPLATE_MARKS):
		return ""
	return text


def item_numbers(
	item_code: str | None, item_name: str | None, supplier_part: str | None
) -> list[tuple[str, tuple]]:
	"""Our item number where it is not the name of the item, and the supplier's where ERPNext knows it."""
	found: list[tuple[str, tuple]] = []
	if item_code and item_code != (item_name or ""):
		found.append((OUR_PART, (item_code,)))
	if supplier_part:
		found.append((SUPPLIER_PART, (supplier_part,)))
	return found


def unit_price_note(quantity) -> list[tuple[str, tuple]]:
	"""A position without a quantity asks for the price per unit."""
	return [] if quantity else [(UNIT_PRICE, ())]


def delivery_terms(incoterm: str | None, place: str | None) -> str:
	if not incoterm:
		return ""
	return " ".join(part for part in (incoterm, place) if part)


def closing(asks: bool, required: bool, incoterm: str) -> list[tuple[str, tuple]]:
	"""What the request asks the supplier to state, only as far as the request has data for it; nothing on a draft
	or a cancelled request (briefbote/layout/status.py)."""
	if not asks:
		return []
	lines: list[tuple[str, tuple]] = [(ASK_PRICES, ())]
	if required:
		lines.append((ASK_DATES, ()))
	if incoterm:
		lines.append((ASK_INCOTERM, (incoterm,)))
	return lines
