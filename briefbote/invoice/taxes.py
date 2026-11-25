"""The tax rate of each position of an invoice and the consideration without tax.

§ 14 Abs. 4 Satz 1 Nr. 7 and 8 UStG ask for the consideration broken down by tax rates and exemptions and for the rate
that applies. ERPNext 16 keeps the tax of each position in the table item_wise_tax_details of the invoice (Item Wise
Tax Detail: item_row, tax_row, rate, amount, taxable_amount); an invoice from before that table has no rows there and
one rate for all positions where its tax lines share one.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Detail:
	item: str
	tax: str
	rate: Decimal


def single_rate(rates: Iterable[Decimal]) -> Decimal | None:
	"""The rate all tax lines share, or None where they differ or there are none."""
	distinct = set(rates)
	return distinct.pop() if len(distinct) == 1 else None


def position_rates(
	items: Iterable[str], details: Iterable[Detail], single_rate: Decimal | None
) -> dict[str, Decimal]:
	"""The rate of each position: the sum of the rates of its tax details, else the one rate of the invoice."""
	details = list(details)
	items = list(items)
	if details:
		rates = {item: Decimal(0) for item in items}
		for detail in details:
			if detail.item in rates:
				rates[detail.item] += detail.rate
		return rates
	if single_rate is None:
		return {}
	return dict.fromkeys(items, single_rate)


def shows_rates(rates: dict[str, Decimal]) -> bool:
	"""Whether the positions differ in their rate, so that each needs its own."""
	return len(set(rates.values())) > 1


def untaxed(nets: dict[str, Decimal], rates: dict[str, Decimal]) -> Decimal:
	"""The consideration of the positions without tax."""
	return sum((net for item, net in nets.items() if rates.get(item) == 0), Decimal(0))


def percent(rate: Decimal) -> str:
	"""A rate as German print shows it: 19, 7,5."""
	text = format(rate.normalize(), "f")
	return text.replace(".", ",") if "." in text else text
