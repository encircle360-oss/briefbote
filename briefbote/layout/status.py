"""The mark of a document that is not, or no longer, valid: a draft (docstatus 0 of a submittable DocType) and a
cancelled document (docstatus 2). Each page carries the word across it and in the page line, so that a printout
can never pass for the final or a valid document; neither asks for payment. Frappe prints them at all only where
the Print Settings allow it (Allow Print for Draft, Allow Print for Cancelled; validate_print_for_docstatus in
frappe/www/printview.py). Other states, such as paid or overdue, change after printing and get no mark.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Status:
	name: str
	# The word across the page and the word in the page line, in English; the print formats translate both.
	mark: str
	label: str


DRAFT = Status("draft", "DRAFT", "Draft")
CANCELLED = Status("cancelled", "CANCELLED", "Cancelled")


def of(submittable: bool, docstatus: int) -> Status | None:
	if not submittable:
		return None
	return {0: DRAFT, 2: CANCELLED}.get(docstatus)


def asks_for_payment(found: Status | None) -> bool:
	return found is None
