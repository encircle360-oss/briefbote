"""What the print format Geschäftsbrief reads of a Business Letter of erpnext_germany beyond the frame of the letter:
the recipient from the address and the contact of the letter, the information block, the subject and the text as
the owning app rendered them (subject_preview, content_preview), and what keeps the letter from being sent. The
rules live in briefbote/correspondence; nothing here renders a text of the letter as a template.

The recipient comes from the Address of the letter and not from its address_display: that field holds what the
address template of the country renders, which prints the country also on a letter within Germany, and the form
fills it only in the browser (business_letter.js of erpnext_germany). Where the Address cannot be read,
address_display is the fallback.
"""

import base64
import mimetypes

import frappe
from frappe import _
from frappe.utils import formatdate, strip_html

from briefbote.briefbote.printing import BREAKS, briefbote_letter, company_particulars, settings, t
from briefbote.correspondence import body, letter
from briefbote.layout import letter as letters

FILES = ("/files/", "/private/files/")


def _company(doc) -> str:
	return doc.get("company") or frappe.db.get_single_value("Global Defaults", "default_company") or ""


def _cached(doctype: str, name: str | None):
	return frappe.get_cached_doc(doctype, name) if name and frappe.db.exists(doctype, name) else None


def _person(contact) -> str:
	if not contact:
		return ""
	named = " ".join(part for part in (contact.first_name, contact.middle_name, contact.last_name) if part)
	return (contact.get("full_name") or named or "").strip()


def _organisation(address, contact) -> str:
	return (
		(address.address_title if address else "") or (contact.company_name if contact else "") or ""
	).strip()


def _displayed(text: str | None) -> list[str]:
	lines = strip_html(BREAKS.sub("\n", text or "")).splitlines()
	return [line.strip() for line in lines if line.strip()]


def recipient(doc, home_country: str) -> tuple[list[str], bool]:
	"""The lines of the address field and whether they reach the recipient by post. Without a postal address the
	window stays empty and the letter has a finding, rather than a name alone in the window."""
	address = _cached("Address", doc.get("address"))
	contact = _cached("Contact", doc.get("contact"))
	organisation, person = _organisation(address, contact), _person(contact)
	if address:
		party = letter.party(
			organisation,
			person,
			street=address.address_line1 or "",
			street2=address.address_line2 or "",
			pincode=address.pincode or "",
			city=address.city or "",
			country=address.country or "",
		)
		return letter.lines(party, home_country, t), letter.postal(party)
	displayed = _displayed(doc.get("address_display"))
	if len(displayed) < 2:
		return [], False
	head = letters.address_lines(letter.party(organisation, person), home_country, t)
	return [*head, *displayed][: letters.ADDRESS_LINES], True


def briefbote_business_letter_frame(doc, no_letterhead=0) -> dict:
	"""The frame of a business letter, addressed to the address and contact of the letter; the company of the letter,
	or the default company where the letter names none."""
	if not doc.get("company"):
		doc.company = _company(doc)
	frame = briefbote_letter(doc, no_letterhead)
	frame["recipient"], _postal = recipient(doc, frame["company"].country)
	frame["dense"] = letters.dense(frame["recipient"])
	return frame


def image(source: str) -> str | None:
	"""An image of the text as a data URL: a data URL as it is, a file of the site read from disk, nothing else."""
	if source.startswith("data:"):
		return source
	path = source.split("?", 1)[0]
	if not path.startswith(FILES):
		return None
	name = frappe.db.get_value("File", {"file_url": path}, "name")
	if not name:
		return None
	try:
		content = frappe.get_doc("File", name).get_content()
	except frappe.DoesNotExistError, OSError:
		return None
	if isinstance(content, str):
		content = content.encode("utf-8")
	kind = mimetypes.guess_type(path)[0] or ""
	return f"data:{kind};base64,{base64.b64encode(content).decode('ascii')}" if content else None


def _reference(doc) -> str:
	"""Unser Zeichen: the document the letter refers to, by the name of its DocType and its number."""
	if not (doc.get("link_document_type") and doc.get("link_name")):
		return ""
	return f"{_(doc.link_document_type)} {doc.link_name}"


def _department(doc) -> str:
	if not doc.get("department"):
		return ""
	return frappe.db.get_value("Department", doc.department, "department_name") or doc.department


def briefbote_business_letter(doc) -> dict:
	"""What the print format Geschäftsbrief prints of a Business Letter besides the frame of the letter."""
	company = _company(doc)
	particulars = company_particulars(company, settings(company)) if company else None
	home = particulars.country if particulars else ""
	lines, postal = recipient(doc, home)
	text = body.render(doc.get("content_preview"), image)
	email = ""
	if doc.get("employee"):
		email = frappe.db.get_value("Employee", doc.employee, "company_email") or ""
	date = formatdate(doc.date) if doc.get("date") else ""
	return {
		"subject": (doc.get("subject_preview") or "").strip(),
		"body": text.html,
		"info": letter.information(
			t,
			reference=_reference(doc),
			department=_department(doc),
			name=doc.get("employee_name") or "",
			phone=particulars.phone if particulars else "",
			email=email or (particulars.email if particulars else ""),
			date=date,
		),
		"findings": [t(found) for found in letter.findings(postal=postal, text=not text.empty)],
		"findings_title": t(letter.FINDINGS_TITLE),
		"running_title": letter.running_title(lines[0] if lines else "", date, t),
	}


def warn_without_subject(doc, method=None) -> None:
	"""A letter without a subject is saved, with a word that DIN 5008 makes a subject usual."""
	if letter.warns_without_subject(doc.get("subject")):
		frappe.msgprint(t(letter.NO_SUBJECT), indicator="orange", alert=True)
