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


# The most pages a document may have that each get the mark of a document laid out as one long page; the marks
# beyond the end of a shorter document are clipped with it.
MOST_PAGES = 60


def repeated_tops(
	page: float, top: float, bottom: float, pages: int = MOST_PAGES, offset: float = 0
) -> list[float]:
	"""Where the mark stands on each page of a document that a generator lays out as one long page and cuts into
	pages of the height of the sheet less its margins, as wkhtmltopdf does, which repeats no fixed element: in
	millimetres from the start of the document, offset into each page."""
	height = page - top - bottom
	return [number * height + offset for number in range(pages)]
