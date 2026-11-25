"""The Leistungsnachweis: the time an invoice bills, entry by entry, as an annex to the invoice or as a document of its
own. An invoice may consist of several documents where the one with the consideration and the tax names the others
(§ 31 Abs. 1 UStDV); the invoice names the annex, and the annex proves the quantity the invoice bills by time.

ERPNext 16 links the time to the invoice in its table timesheets (Sales Invoice Timesheet): per time log the day and
time, the billing hours, the activity, the description and the project, and the Timesheet and its time log, which
give the person and the task. docs/leistungsnachweis.md says what each column comes from.
"""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

# Hours that differ by less than this are the same, as the rounding of a time tracking leaves them.
HUNDREDTH = Decimal("0.01")


class Person(StrEnum):
	"""How the annex names the person who worked, which the Einstellungen Geschäftspost choose."""

	NAME = "Name"
	INITIALS = "Initials"
	ROLE = "Role"
	NONE = "None"


class Placement(StrEnum):
	WITH_INVOICE = "With the invoice"
	SEPARATE = "Separate document"
	NONE = "Not printed"


def person_mode(name: str | None) -> Person:
	return Person(name) if name else Person.NAME


def placement(name: str | None) -> Placement:
	return Placement(name) if name else Placement.WITH_INVOICE


@dataclass(frozen=True, slots=True)
class Entry:
	day: date
	person: str
	activity: str
	description: str
	project: str
	task: str
	hours: Decimal


def person(name: str, role: str, mode: Person) -> str:
	"""The person as the annex prints it: full name, initials without titles, role, or nothing."""
	if mode is Person.NAME:
		return name
	if mode is Person.ROLE:
		return role
	if mode is Person.INITIALS:
		words = [part for word in name.split() if not word.endswith(".") for part in word.split("-")]
		return "".join(word[0].upper() for word in words if word)
	return ""


def ordered(entries: Iterable[Entry]) -> list[Entry]:
	return sorted(entries, key=lambda entry: (entry.day, entry.person, entry.project, entry.task))


def total(entries: Iterable[Entry]) -> Decimal:
	return sum((entry.hours for entry in entries), Decimal(0))


def subtotals(entries: Iterable[Entry], key: str) -> list[tuple[str, Decimal]]:
	"""The hours per project or per person, by label."""
	sums: dict[str, Decimal] = defaultdict(Decimal)
	for entry in entries:
		sums[getattr(entry, key)] += entry.hours
	return sorted(sums.items())


def reconcile(hours: Decimal, quantities: Iterable[Decimal]) -> tuple[bool, Decimal]:
	"""Whether the hours of the annex equal the quantity the invoice bills by time, with that quantity."""
	billed = sum(quantities, Decimal(0))
	return abs(billed - hours) < HUNDREDTH, billed
