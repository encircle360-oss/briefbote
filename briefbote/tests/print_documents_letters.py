"""The business letters of the proof, written to a test site with erpnext_germany as its Business Letter keeps them:
saved, so that the controller of the owning app renders subject and content into subject_preview and
content_preview, and submitted. It runs after print_documents.run, whose company, customers and addresses it uses;
a second run changes nothing. Every name, address and text is invented.

	bench --site <site> execute briefbote.tests.print_documents_letters.run
"""

from dataclasses import dataclass
from datetime import date

import frappe

from briefbote.tests import print_documents as documents
from briefbote.tests.print_documents import ABBR, COMPANY, insert, png

DOCTYPE = "Business Letter"
WRITTEN = date(2026, 11, 26)
IMAGE = "/files/briefbote-proof-brief-grafik.png"
DEPARTMENT = f"Vertrieb - {ABBR}"
EMPLOYEE = "HR-EMP-BSP-0001"
CLOSING = (
	"<p>Mit freundlichen Grüßen</p><p><br></p><p>Beispiel GmbH</p><p><br></p><p><br></p>"
	"<p>Max Mustermann</p><p>Vertrieb</p>"
)
# The first paragraph after the salutation goes on in lower case.
OPENING = (
	"wir danken Ihnen für das freundliche Gespräch und die Gelegenheit, Ihnen unser Vorgehen vorzustellen. "
	"Gern fassen wir die wichtigsten Punkte zusammen, damit Sie und Ihr Team sie in Ruhe prüfen können."
)
PARAGRAPH = (
	"Wir danken Ihnen für das freundliche Gespräch und die Gelegenheit, Ihnen unser Vorgehen vorzustellen. "
	"Gern fassen wir die wichtigsten Punkte zusammen, damit Sie und Ihr Team sie in Ruhe prüfen können, bevor "
	"wir den nächsten Termin vereinbaren."
)


@dataclass(frozen=True)
class Letter:
	name: str
	subject: str
	content: str
	address: str = ""
	contact: str = ""
	link: tuple[str, str] | None = None
	employee: bool = True
	submit: bool = True


CONTACTS = {
	"Erika Muster": ("Erika", "Muster", "Kunde Muster AG"),
	"Erika Beispiel": ("Erika", "Beispiel", ""),
	"Max Beispielmann": ("Max", "Beispielmann", "Musterhandel Gesellschaft m.b.H."),
	"Jane Example": ("Jane", "Example", "Example Trading Inc."),
	"Hans Ohneanschrift": ("Hans", "Ohneanschrift", "Beispiel Handels KG"),
}


def long_letter() -> str:
	"""Three pages: headings, a list with levels, a table and the closing after the last paragraph."""
	sections = []
	for number, title in enumerate(
		("Ausgangslage", "Vorgehen", "Leistungen im Einzelnen", "Termine", "Zusammenarbeit"), start=1
	):
		sections.append(f"<h2>{number}. {title}</h2>")
		sections.append(f"<p>Zu Abschnitt {number}: {PARAGRAPH} {PARAGRAPH}</p><p><br></p>")
		if number == 2:
			sections.append(
				'<ol><li data-list="ordered">Aufnahme der bestehenden Abläufe</li>'
				'<li data-list="bullet" class="ql-indent-1">Gespräche mit den Fachbereichen</li>'
				'<li data-list="bullet" class="ql-indent-1">Auswertung der vorhandenen Unterlagen</li>'
				'<li data-list="ordered">Entwurf des neuen Ablaufs</li>'
				'<li data-list="ordered">Einführung und Schulung</li></ol><p><br></p>'
			)
		if number == 3:
			rows = "".join(
				f"<tr><td>{index}</td><td>Leistung {index}: Beratung und Begleitung vor Ort</td><td>{index * 4} Stunden</td></tr>"
				for index in range(1, 9)
			)
			sections.append(
				'<table class="table table-bordered"><thead><tr><th>Nr.</th><th>Leistung</th><th>Umfang</th></tr></thead>'
				f"<tbody>{rows}</tbody></table><p><br></p>"
			)
		sections.append(f"<p>{PARAGRAPH}</p><p><br></p>")
	return (
		"<p>Sehr geehrte Frau Muster,</p><p><br></p><p>gern beschreiben wir Ihnen unser Vorgehen.</p><p><br></p>"
		+ "".join(sections)
		+ f"<p>{PARAGRAPH} Wir freuen uns auf Ihre Rückmeldung.</p><p><br></p>"
		+ CLOSING
	)


def word_processor_letter() -> str:
	"""Pasted from a word processor: its styles, fonts, sizes and colours, which the letter does not print."""
	return (
		"<!--[if gte mso 9]><xml><o:OfficeDocumentSettings></o:OfficeDocumentSettings></xml><![endif]-->"
		"<style>p.MsoNormal {margin:0cm; font-family:Calibri}</style>"
		'<p class="MsoNormal"><span style="font-family:&quot;Times New Roman&quot;;font-size:16pt;color:#C00000">'
		"Sehr geehrter Herr Beispielmann,<o:p></o:p></span></p><p><br></p>"
		'<p class="MsoNormal" style="mso-margin-top-alt:auto"><font face="Comic Sans MS" color="#ff0000" size="6">'
		"Rote Schrift in großer Schrift aus der Textverarbeitung.</font> "
		'<span style="background-color:yellow;font-size:28px">Gelb hinterlegt und riesig.</span> '
		'<span class="ql-size-huge ql-font-serif" style="color:rgb(0, 112, 192)">Blau in einer Serifenschrift.</span></p>'
		"<p><br></p>"
		f'<p><img src="{IMAGE}" width="900" style="float:right; width:900px"></p><p><br></p>'
		'<p class="MsoNormal">Ein letzter Satz in der Schrift des Briefs.</p><p><br></p>' + CLOSING
	)


def letters() -> list[Letter]:
	return [
		Letter(
			"GB-2026-0001",
			"Ihre Anfrage zur Wartung",
			"<p>Sehr geehrte Frau Muster,</p><p><br></p>"
			f"<p>{OPENING}</p><p><br></p>"
			"<p>Für Rückfragen erreichen Sie uns gern telefonisch oder per E-Mail.</p><p><br></p>" + CLOSING,
			address="Kunde Muster AG-Billing",
			contact="Erika Muster",
		),
		Letter(
			"GB-2026-0002",
			"Unser Vorgehen in Ihrem Projekt",
			long_letter(),
			address="Kunde Muster AG-Billing",
			contact="Erika Muster",
		),
		Letter(
			"GB-2026-0003",
			"Ihr Termin am 3. Dezember",
			"<p>Sehr geehrte Frau Beispiel,</p><p><br></p>"
			"<p>wir bestätigen Ihnen gern den Termin am 3. Dezember um 10 Uhr.</p><p><br></p>" + CLOSING,
			address="Erika Beispiel-Billing",
			contact="Erika Beispiel",
		),
		Letter(
			"GB-2026-0004",
			"Lieferung nach Österreich",
			f"<p>Sehr geehrter Herr Beispielmann,</p><p><br></p><p>{OPENING}</p><p><br></p>" + CLOSING,
			address="Musterhandel Gesellschaft m.b.H.-Billing",
			contact="Max Beispielmann",
		),
		Letter(
			"GB-2026-0005",
			"Ihre Rechnung {{ reference.name }}",
			"<p>Sehr geehrte Frau {{ contact.last_name }},</p><p><br></p>"
			"<p>zu unserer Rechnung {{ reference.name }} vom 20.11.2026 senden wir Ihnen die gewünschte Aufstellung."
			" Platzhalter wie {% raw %}{{ name }}{% endraw %} druckt der Brief, wie sie dastehen.</p><p><br></p>"
			+ CLOSING,
			address="Kunde Muster AG-Billing",
			contact="Erika Muster",
			link=("Sales Invoice", "RE-2026-0101"),
		),
		Letter(
			"GB-2026-0006",
			"Your enquiry",
			"<p>Dear Ms Example,</p><p><br></p>"
			"<p>Thank you for your enquiry. We will gladly send you our offer by the end of the week.</p><p><br></p>"
			"<p>Kind regards</p><p><br></p><p><br></p><p>Max Mustermann</p>",
			address="Example Trading Inc.-Billing",
			contact="Jane Example",
		),
		Letter(
			"GB-2026-0007",
			"Ihr Schreiben vom 20. November",
			word_processor_letter(),
			address="Musterhandel Gesellschaft m.b.H.-Billing",
			contact="Max Beispielmann",
		),
		Letter(
			"GB-2026-0008", "", "", address="Kunde Muster AG-Billing", contact="Erika Muster", employee=False
		),
		Letter(
			"GB-2026-0009",
			"Ohne Anschrift",
			"<p>Sehr geehrter Herr Ohneanschrift,</p><p><br></p><p>dieser Brief hat keine Anschrift.</p>",
			contact="Hans Ohneanschrift",
			employee=False,
		),
	]


def make_people() -> None:
	insert(
		"Department", name=DEPARTMENT, department_name="Vertrieb", company=COMPANY, lft=1, rgt=2, is_group=0
	)
	insert(
		"Employee",
		name=EMPLOYEE,
		first_name="Max",
		last_name="Mustermann",
		employee_name="Max Mustermann",
		company=COMPANY,
		department=DEPARTMENT,
		status="Active",
		gender="Male",
		date_of_birth=date(1980, 1, 1),
		date_of_joining=date(2020, 1, 1),
		company_email="max.mustermann@beispiel.example",
	)
	for name, (first, last, company) in CONTACTS.items():
		insert(
			"Contact",
			name=name,
			first_name=first,
			last_name=last,
			full_name=name,
			company_name=company,
		)


def make_image() -> None:
	"""A grey picture wider than the text, so that the proof sees it scaled and finds colour only in text."""
	if frappe.db.exists("File", {"file_url": IMAGE}):
		return
	frappe.get_doc(
		{
			"doctype": "File",
			"file_name": IMAGE.rsplit("/", 1)[1],
			"content": png(600, 200, b"\xcc\xcc\xcc"),
			"is_private": 0,
		}
	).insert(ignore_permissions=True)


def write(letter: Letter) -> None:
	if frappe.db.exists(DOCTYPE, letter.name):
		return
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE,
			"company": COMPANY,
			"date": WRITTEN,
			"address": letter.address,
			"contact": letter.contact,
			"subject": letter.subject,
			"content": letter.content,
			"department": DEPARTMENT if letter.employee else "",
			"employee": EMPLOYEE if letter.employee else "",
			"employee_name": "Max Mustermann" if letter.employee else "",
			"link_document_type": letter.link[0] if letter.link else "",
			"link_name": letter.link[1] if letter.link else "",
		}
	)
	doc.insert(ignore_permissions=True, set_name=letter.name)
	if letter.submit:
		doc.submit()


def run() -> None:
	if not frappe.db.exists("DocType", DOCTYPE):
		raise SystemExit(
			"Die Geschäftsbriefe des Nachweises brauchen erpnext_germany mit dem DocType Business Letter."
		)
	documents.run()
	make_people()
	make_image()
	for letter in letters():
		write(letter)
	frappe.clear_cache()
