"""The Bestellung of a Purchase Order: an order form, which is always a business letter (§ 35a Abs. 3 GmbHG, § 80
Abs. 3 AktG), with the tax of the supplier only where the supply is taxable in Germany, the delivery address and the
request to confirm. docs/bestellung.md names the sources.
"""

from briefbote.invoice.self_billing import PurchaseCase, charges_tax

TITLE = "Purchase Order"
DELIVERY_ADDRESS = "Delivery Address"
SUPPLIER_PART = "Your item number {0}"
CONFIRM = "Please confirm this order to us, stating the order number."


def shows_tax(case: PurchaseCase) -> bool:
	"""The tax of the supplier, as the Gutschrift shows it: a purchase template of § 13b UStG adds and deducts the
	tax of the company, which is no line of the order."""
	return charges_tax(case)


def closing(submitted: bool) -> list[str]:
	"""The request to confirm, on a submitted order only."""
	return [CONFIRM] if submitted else []
