"""What a Dunning prints as a letter: its title and text by level, the deadline, and whether the interest and the fee
ERPNext booked on it may be claimed. The texts are the English source; the settings may replace them per level.
docs/mahnung.md names each source.
"""

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import date, timedelta
from decimal import Decimal

from briefbote.dunning import interest

PAYMENT_REMINDER = "Payment Reminder"
REMINDER = "Reminder"
SECOND_REMINDER = "Second Reminder"
FINAL_REMINDER = "Final Reminder"

TEXT_1 = "According to our records, the invoices below are still open. Please transfer the amount due by {deadline}. If you have paid in the meantime, please disregard this letter."
TEXT_2 = "Despite our payment reminder, the invoices below are still open. Please transfer the amount due by {deadline}."
TEXT_3 = (
	"The invoices below are still open despite our reminders. Please transfer the amount due by {deadline}."
)
TEXT_4 = "The invoices below are still open despite several reminders. Please transfer the amount due by {deadline} at the latest."


@dataclass(frozen=True, slots=True)
class Level:
	number: int
	title: str
	text: str
	days: int


DEFAULTS = {
	1: Level(1, PAYMENT_REMINDER, TEXT_1, 10),
	2: Level(2, REMINDER, TEXT_2, 10),
	3: Level(3, SECOND_REMINDER, TEXT_3, 7),
	4: Level(4, FINAL_REMINDER, TEXT_4, 7),
}


def level(number: int, own: Iterable[Level]) -> Level:
	"""The level of a dunning letter: the default of its number, the last default for higher numbers, with what the
	settings give that number."""
	number = max(number, 1)
	found = replace(DEFAULTS[min(number, max(DEFAULTS))], number=number)
	for row in own:
		if row.number == number:
			found = Level(number, row.title or found.title, row.text or found.text, row.days or found.days)
	return found


def deadline(day: date, of: Level) -> date:
	return day + timedelta(days=of.days)


def fill(text: str, deadline_text: str) -> str:
	"""The text with its deadline; a placeholder of its own, since a text from the settings may hold any braces."""
	return text.replace("{deadline}", deadline_text)


@dataclass(frozen=True, slots=True)
class Charges:
	"""What ERPNext booked on the Dunning, the lawful maximum of its interest (None where not known) and how many of
	its invoices are in default."""

	interest: Decimal
	fee: Decimal
	lawful: Decimal | None
	in_default: int


REMINDER_CHARGES = "A payment reminder carries neither interest nor a fee, but this Dunning has them booked. Give its Dunning Type neither."
INTEREST_EXCEEDS = "The interest booked on this Dunning exceeds the default interest of Sections 286 and 288 BGB from the dates of its invoices; ERPNext counts it from the due date at the rate of the Dunning Type."
NO_BASE_RATE = "The Einstellungen Geschäftspost hold no base rate for every day of the interest; the interest cannot be checked."
FEE_CONSUMER = "The fee booked on this Dunning is charged to a consumer; the lump sum of Section 288(5) BGB applies only to a debtor who is not a consumer."
FEE_NO_DEFAULT = "The fee booked on this Dunning is charged although none of its invoices is in default."
FEE_EXCEEDS = "The fee booked on this Dunning exceeds the lump sum of 40 euros for each invoice in default (Section 288(5) BGB)."
NO_BANK = "No bank account is chosen in the Einstellungen Geschäftspost, so the request to transfer cannot say where to pay."
FINDINGS = (
	REMINDER_CHARGES,
	INTEREST_EXCEEDS,
	NO_BASE_RATE,
	FEE_CONSUMER,
	FEE_NO_DEFAULT,
	FEE_EXCEEDS,
	NO_BANK,
)
CENT = Decimal("0.005")


def assess(number: int, charges: Charges, consumer: bool, bank: bool = True) -> tuple[list[str], bool, bool]:
	"""The findings that stand instead of a claim, and whether the booked interest and fee may be printed as claims. A
	letter that cannot say where to pay asks for nothing."""
	if not bank:
		return [NO_BANK], False, False
	if number <= 1:
		return ([REMINDER_CHARGES] if charges.interest or charges.fee else []), False, False
	found, claim_interest, claim_fee = [], False, False
	if charges.interest:
		if charges.lawful is None:
			found.append(NO_BASE_RATE)
		elif charges.interest > charges.lawful + CENT:
			found.append(INTEREST_EXCEEDS)
		else:
			claim_interest = True
	if charges.fee:
		if consumer:
			found.append(FEE_CONSUMER)
		elif not charges.in_default:
			found.append(FEE_NO_DEFAULT)
		elif charges.fee > interest.lump_sum(consumer, charges.in_default):
			found.append(FEE_EXCEEDS)
		else:
			claim_fee = True
	if found:
		return found, False, False
	return found, claim_interest, claim_fee
