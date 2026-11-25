"""The rate and base of a tax line of a document of sales, by the positions it taxes.

§ 14 Abs. 4 Satz 1 Nr. 7 and 8 UStG ask an invoice for the consideration by rate; a quotation and an order
confirmation show their tax the same way, so that the customer reads the price as the invoice will state it.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from briefbote.invoice.taxes import Detail


@dataclass(frozen=True, slots=True)
class Base:
	rate: Decimal
	base: Decimal


def tax_base(
	tax: str, line_rate: Decimal, line_net: Decimal, details: Iterable[Detail], nets: dict[str, Decimal]
) -> Base | None:
	"""The rate and the consideration of a tax line, or None where they cannot be known.

	With tax details, the line taxes the positions whose detail on it has a rate other than 0, at that rate, and its
	base is their net amount. The net amount ERPNext keeps on the line itself counts every position whose item tax
	template names the account of the line, also with 0 %, as the German templates of ERPNext do
	(get_current_tax_and_net_amount in erpnext/controllers/taxes_and_totals.py), and the rate of the line is 0 where
	the item tax templates carry the rates. Without tax details, the line keeps its own rate and net amount."""
	details = list(details)
	if not details:
		return Base(line_rate, line_net) if line_rate else None
	taxed = [detail for detail in details if detail.tax == tax and detail.rate and detail.item in nets]
	rates = {detail.rate for detail in taxed}
	if len(rates) != 1:
		return None
	return Base(rates.pop(), sum((nets[detail.item] for detail in taxed), Decimal(0)))
