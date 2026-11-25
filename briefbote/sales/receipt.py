"""The Zahlungsbestätigung and the Quittung of a Payment Entry: which payment is confirmed, how its references are
named, and the texts. A Quittung is the written acknowledgement of receipt the creditor gives on request (§ 368 Satz 1
BGB); whoever brings one counts as entitled to collect the payment (§ 370 BGB), so only a submitted receipt from a
customer is confirmed. Neither is an invoice; both relate only to payment. docs/zahlungsbestaetigung.md names the
sources.
"""

TITLE = "Payment Confirmation"
RECEIPT_TITLE = "Receipt"


def title(as_receipt: bool) -> str:
	return RECEIPT_TITLE if as_receipt else TITLE


def confirms(payment_type: str, party_type: str, docstatus: int) -> bool:
	return payment_type == "Receive" and party_type == "Customer" and docstatus == 1


INVOICE = "Invoice"
ORDER = "Order"
DUNNING = "Dunning"
OTHER = "Document"
_KINDS = {"Sales Invoice": INVOICE, "Sales Order": ORDER, "Dunning": DUNNING}


def kind(doctype: str) -> str:
	return _KINDS.get(doctype, OTHER)


APPLIED = "Your payment of {0} of {1} has been received and applied as follows."
RECEIVED = "We have received the amount of {0} on {1} from {2}."
UNALLOCATED = "{0} of the payment is not yet applied to an invoice."
NOT_CONFIRMED = (
	"Only a submitted payment received from a customer is confirmed; this document confirms nothing."
)
