"""The Packliste of the Packing Slips of a Delivery Note: which packages the delivery holds, what each holds and
what it weighs. ERPNext packs a delivery note into Packing Slips, each for its packages from from_case_no to
to_case_no with their net and gross weight (erpnext/stock/doctype/packing_slip/packing_slip.py). The list of a
submitted slip covers every submitted slip of its delivery note, the list of a draft or a cancelled slip only that
slip, under its mark. No law prescribes its content. docs/packliste.md names the sources.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from briefbote.sales.delivery import number

TITLE = "Packing List"
PACKAGE = "Package {0}"
PACKAGES = "Packages {0} to {1}"
SUBJECT = "{0}: {1} for Delivery Note {2}"
PACKAGE_COUNT = "Packages"
NET = "Net weight"
GROSS = "Gross weight"
TOTAL = "Total"
# The head of the first column, which holds the numbers of the packages of each position, and its width in
# millimetres: „Packstück“ in the type of the head of the table, with its padding.
PACKAGE_HEAD = "Package"
PACKAGE_COLUMN = 17
RANGE = "\N{EN DASH}"


@dataclass(frozen=True, slots=True)
class Slip:
	name: str
	first: int
	last: int
	net: Decimal
	net_unit: str
	gross: Decimal
	gross_unit: str
	submitted: bool


def listed(printed: Slip, submitted: Iterable[Slip]) -> list[Slip]:
	"""The slips the list covers, by their first package: all submitted ones of the delivery note with the one
	printed, or the printed one alone where it is a draft or cancelled."""
	if not printed.submitted:
		return [printed]
	slips = {slip.name: slip for slip in submitted if slip.submitted}
	slips[printed.name] = printed
	return sorted(slips.values(), key=lambda slip: (slip.first, slip.name))


def _range(first: int, last: int) -> tuple[str, tuple]:
	return (PACKAGES, (first, last)) if last > first else (PACKAGE, (first,))


def label(slip: Slip) -> tuple[str, tuple]:
	return _range(slip.first, slip.last)


def covered(slips: list[Slip]) -> tuple[str, tuple]:
	"""The packages the list covers, from the first to the last."""
	return _range(slips[0].first, max(max(slip.last, slip.first) for slip in slips))


def numbers(slip: Slip) -> str:
	"""The numbers of the packages of a slip as the first column of the list prints them: 1, or 2 and 4 joined by an en dash for a range."""
	return f"{slip.first}{RANGE}{slip.last}" if slip.last > slip.first else str(slip.first)


def count(slips: Iterable[Slip]) -> int:
	return sum(max(slip.last, slip.first) - slip.first + 1 for slip in slips)


def weight(value: Decimal, unit: str) -> str:
	"""A weight in its unit, or nothing where it is unknown."""
	if not value or not unit:
		return ""
	return f"{number(value)} {unit}"


def _total(values: list[tuple[Decimal, str]]) -> tuple[Decimal | None, str]:
	units = {unit for _value, unit in values}
	if not values or len(units) != 1 or not all(value for value, _unit in values) or not next(iter(units)):
		return None, ""
	return sum((value for value, _unit in values), Decimal(0)), next(iter(units))


def totals(slips: list[Slip]) -> tuple[Decimal | None, str, Decimal | None, str]:
	"""Net and gross weight of all slips, each only where every slip states it in the same unit."""
	net, net_unit = _total([(slip.net, slip.net_unit) for slip in slips])
	gross, gross_unit = _total([(slip.gross, slip.gross_unit) for slip in slips])
	return net, net_unit, gross, gross_unit
