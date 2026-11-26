"""The Lieferantenrücksendung of a Purchase Receipt with is_return: the letter that goes with goods back to the
supplier, with the receipt it returns, the quantity that goes back as a positive number, what was rejected on
receipt and a line for the carrier to confirm the goods taken over. No law prescribes its content; it is a business
letter (§ 35a Abs. 1 GmbHG), whose particulars the frame of the letter prints. A Purchase Receipt that is no return
records goods received, an internal document this print format does not print. docs/lieferantenruecksendung.md
names the sources.
"""

from decimal import Decimal

TITLE = "Return Shipment"
GOODS_RECEIPT = "Our Goods Receipt"
SUPPLIER_DELIVERY_NOTE = "Your Delivery Note"
OUR_PURCHASE_ORDER = "Our Purchase Order"
CARRIER = "Carrier"
SUBJECT = "{0} {1} to our Goods Receipt {2} of {3}"
REJECTED = "Rejected on receipt."
REJECTED_PART = "Of which rejected on receipt: {0}"
PICK_UP = "Pick-up address"
TAKEN_OVER = "Goods taken over for return"
NOT_A_RETURN = "This Purchase Receipt is no return; the print format Lieferantenrücksendung prints only a return to the supplier."
FINDINGS_TITLE = "This document is no return to the supplier:"


def findings(is_return: bool) -> list[str]:
	return [] if is_return else [NOT_A_RETURN]


def returned(quantity: Decimal, rejected: Decimal) -> Decimal:
	"""What goes back: the accepted and the rejected quantity, which ERPNext keeps negative on a return."""
	return abs(quantity) + abs(rejected)


def rejected_note(
	quantity: Decimal, rejected: Decimal, from_rejected_warehouse: bool
) -> tuple[str, tuple] | None:
	"""The share that was rejected on receipt, only where there is one: all of it for a return from the warehouse of
	rejected goods or one of rejected goods alone, else the rejected part."""
	if not rejected and not (from_rejected_warehouse and quantity):
		return None
	if from_rejected_warehouse or not quantity:
		return (REJECTED, ())
	return (REJECTED_PART, (abs(rejected),))


def asks_signature(submitted: bool) -> bool:
	"""The line for the carrier's signature on a submitted return only: a draft or a cancelled return asks nobody
	to confirm anything."""
	return submitted
