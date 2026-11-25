"""The widths of the columns of a table of positions or of a Leistungsnachweis, from what the columns hold.

Each column of figures, units and short labels takes the width of its widest cell, its head included, and the
padding of its cells; the column of the descriptions takes the rest of the width of the text. The totals below the
table start with the column of the quantity where their labels fit in one line, else further left. The widths are
measured in the regular weight of Inter (briefbote/layout/metrics.py) with a reserve for the semibold weight.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal

from briefbote.layout import metrics

SEMIBOLD = Decimal("1.06")
STEP = Decimal("0.5")


@dataclass(frozen=True, slots=True)
class Cell:
	text: str
	size: Decimal
	semibold: bool = False


def need(cells: Iterable[Cell]) -> Decimal:
	"""The width the widest cell needs in millimetres, rounded up to half a millimetre."""
	widest = max(
		(metrics.width(cell.text, cell.size) * (SEMIBOLD if cell.semibold else 1) for cell in cells),
		default=Decimal(0),
	)
	return (widest / STEP).to_integral_value(rounding=ROUND_CEILING) * STEP


def widths(
	width: Decimal,
	columns: dict[str, list[Cell]],
	padding: dict[str, Decimal],
	rest: str,
	limits: dict[str, Decimal] | None = None,
) -> dict[str, Decimal]:
	"""The width of each column in millimetres, at most its limit, where a column such as a project may wrap; the
	column rest takes what the others leave of width."""
	limits = limits or {}
	found = {
		key: min(need(cells) + padding.get(key, Decimal(0)), limits.get(key, width))
		for key, cells in columns.items()
	}
	found[rest] = width - sum(found.values(), Decimal(0))
	return found


def totals(
	width: Decimal,
	start: Decimal,
	end: Decimal,
	labels: Iterable[Cell],
	amounts: Iterable[Cell],
	label_padding: Decimal,
	amount_padding: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
	"""The columns of the totals below a table: blank, label and amount in millimetres. The labels start where the
	column start starts, the amounts end at the right edge in a column at least as wide as end, the column of the
	amounts above; where a label or an amount needs more room, the labels start further left, so that the
	description above keeps its width."""
	amount = max(end, need(amounts) + amount_padding)
	left = min(start, width - amount - need(labels) - label_padding)
	return left, width - amount - left, amount
