"""When a debtor is in default and how much default interest the law allows, from dated base rates the company keeps
in its Einstellungen Geschäftspost. Nothing here knows a base rate of its own: PUBLISHED only seeds the table of new
settings. docs/mahnung.md names each source.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

ONE_DAY = timedelta(days=1)


@dataclass(frozen=True, slots=True)
class BaseRate:
	valid_from: date
	rate: Decimal


# The base rate of § 247 BGB as the Deutsche Bundesbank publishes it, read on 25.11.2026 from
# https://www.bundesbank.de/de/bundesbank/organisation/agb-und-regelungen/basiszinssatz-607820; three years back, the
# usual limitation period of § 195 BGB.
PUBLISHED = (
	BaseRate(date(2023, 1, 1), Decimal("1.62")),
	BaseRate(date(2023, 7, 1), Decimal("3.12")),
	BaseRate(date(2024, 1, 1), Decimal("3.62")),
	BaseRate(date(2024, 7, 1), Decimal("3.37")),
	BaseRate(date(2025, 1, 1), Decimal("2.27")),
	BaseRate(date(2025, 7, 1), Decimal("1.27")),
	BaseRate(date(2026, 1, 1), Decimal("1.27")),
	BaseRate(date(2026, 7, 1), Decimal("1.52")),
)

NO_BASE_RATE_TODAY = "No base rate of the Einstellungen Geschäftspost covers {0}; dunning letters cannot check their interest. Enter the base rate the Bundesbank publishes for each 1 January and 1 July."


def _half_year(day: date) -> date:
	return date(day.year, 1 if day.month < 7 else 7, 1)


def rate_on(rates: Iterable[BaseRate], day: date) -> Decimal | None:
	"""The base rate of a day: that of the latest row that is valid from it or before."""
	valid = [row for row in rates if row.valid_from <= day]
	return max(valid, key=lambda row: row.valid_from).rate if valid else None


def covers(rates: Iterable[BaseRate], start: date, end: date) -> bool:
	"""Whether the table knows the rate of every day from start to end: a row valid from start or before, and a row
	for the half-year of end or later, since § 247 Abs. 1 Satz 2 BGB changes the rate on each 1 January and 1 July
	and a rate is known only once it is published."""
	rates = list(rates)
	if not rates or rate_on(rates, start) is None:
		return False
	return max(row.valid_from for row in rates) >= _half_year(end)


def _workday(day: date) -> date:
	"""§ 193 BGB: a period that ends on a Saturday or Sunday ends on the next working day. Public holidays, which
	depend on the place of performance, are not known here."""
	while day.weekday() >= 5:
		day += ONE_DAY
	return day


DAYS_TO_DEFAULT = 30


def default_start(
	due: date, issued: date, consumer: bool, notice: bool, reminders: Iterable[date]
) -> date | None:
	"""The first day of default of an invoice, or None where it is not in default.

	§ 286 Abs. 1 Satz 1 BGB: a reminder after the due date puts the debtor in default; the day after the reminder
	counts as the first, since its receipt is not known. § 286 Abs. 3 Satz 1 BGB: a debtor is in default at the
	latest 30 days after the due date and the receipt of the invoice, the day of that event not counted (§ 187 Abs. 1
	BGB), the period ending with its last day (§ 188 Abs. 1 BGB) or the next working day (§ 193 BGB); the day of the
	invoice stands for its receipt, which is not earlier. Towards a consumer only where the invoice pointed this out.
	The due date of an invoice is no time fixed by the calendar in the sense of § 286 Abs. 2 Nr. 1 BGB, since the
	creditor sets it alone (docs/mahnung.md)."""
	found = [day + ONE_DAY for day in reminders if day > due]
	if not consumer or notice:
		event = max(due, issued)
		found.append(_workday(event + timedelta(days=DAYS_TO_DEFAULT)) + ONE_DAY)
	return min(found) if found else None


# § 288 Abs. 1 Satz 2 and Abs. 2 BGB: percentage points above the base rate.
POINTS_CONSUMER = Decimal(5)
POINTS_BUSINESS = Decimal(9)
DAYS_IN_YEAR = 365


def lawful(
	amount: Decimal, start: date | None, end: date, rates: Iterable[BaseRate], consumer: bool
) -> Decimal | None:
	"""The default interest on an amount from the first day of default to the day of the dunning letter, both
	counted, at 5 or 9 points above the base rate of each day; None where the table does not know every rate."""
	if start is None or start > end:
		return Decimal(0)
	rates = list(rates)
	if not covers(rates, start, end):
		return None
	points = POINTS_CONSUMER if consumer else POINTS_BUSINESS
	changes = sorted({row.valid_from for row in rates if start < row.valid_from <= end})
	total, day = Decimal(0), start
	for until in [*changes, end + ONE_DAY]:
		total += (rate_on(rates, day) + points) * (until - day).days
		day = until
	return amount * total / 100 / DAYS_IN_YEAR


# § 288 Abs. 5 Satz 1 BGB: per claim in default, towards a debtor who is no consumer.
LUMP_SUM = Decimal(40)


def lump_sum(consumer: bool, in_default: int) -> Decimal:
	return Decimal(0) if consumer else LUMP_SUM * in_default
