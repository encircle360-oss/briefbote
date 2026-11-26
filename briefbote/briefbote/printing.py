"""What the print formats read beyond the fields of their document: the settings of the company, its particulars,
the address of the recipient, the fonts and the logo, and for an invoice its kind, notices and totals. The print
formats call these as Jinja methods (hooks.py); the rules live in the pure modules under briefbote/layout and
briefbote/invoice. Nothing here loads anything over the network: the fonts and the logo come from disk as data URLs.
"""

import base64
import mimetypes
import re
from datetime import date
from decimal import Decimal
from functools import cache
from pathlib import Path

import frappe
from frappe import _
from frappe.contacts.doctype.address.address import get_default_address
from frappe.utils import cint, flt, formatdate, getdate, strip_html

from briefbote.invoice import completeness, document, self_billing, taxes
from briefbote.layout import columns, din5008, letter, logo, medium, status, theme

SETTINGS = "Business Document Settings"
FONTS = Path(__file__).resolve().parents[1] / "public" / "fonts"
FONT_FAMILY = "Inter Tabular"
BLANK_PAPER = "Blank paper"
# The context of the texts of the printouts in briefbote/translations/de.csv, so that a short text such as „Amount“
# reads on paper as Briefbote translates it and leaves the desk of ERPNext alone.
CONTEXT = "Briefbote"
# The top margin of every page in millimetres; the first page puts letterhead, address field and information block
# below it, at their places on the sheet.
TOP_MARGIN = 12
# The foot of every page has one height, in whole CSS pixels (style.html): a gap, the rule, four lines of blocks, a
# gap of a line and the page line. wkhtmltopdf prints it at the top of its bottom margin of FOOTER_ZONE millimetres;
# the Chromium-based generator of Frappe measures the foot and sets its bottom margin below it
# (prepare_options_for_pdf in frappe/utils/pdf_generator/browser.py), which is therefore the rest of the zone: both
# leave the text the same height of the page and put the foot at the same place, its page line 13 mm above the edge.
FOOT_PIXELS = 87
FOOTER_ZONE = 36
FOOT_HEIGHT = FOOT_PIXELS * 25.4 / 96
BOTTOM_MARGIN = {"chrome": round(FOOTER_ZONE - FOOT_HEIGHT, 3)}
# The lines of a description in the editor of ERPNext, which strip_html would join into one.
BREAKS = re.compile(r"<br\s*/?>|</p>|</div>|</li>", re.IGNORECASE)


def t(text: str) -> str:
	"""A text of a printout in the language of the document."""
	return _(text, context=CONTEXT)


@cache
def font_faces() -> str:
	"""The @font-face rules of the two weights of Inter, embedded, so that no PDF generator fetches a font.

	Two spaces stand between src: and url(: before wkhtmltopdf, Frappe appends !important to every CSS url( that
	follows a colon and at most one space (URL_NOTATION_PATTERN in frappe/utils/data.py, expand_relative_urls), which
	makes the src of a @font-face invalid and drops the font."""
	rules = []
	for weight, name in ((400, "Inter-Regular.ttf"), (600, "Inter-SemiBold.ttf")):
		data = base64.b64encode((FONTS / name).read_bytes()).decode("ascii")
		rules.append(
			f'@font-face {{ font-family: "{FONT_FAMILY}"; font-style: normal; font-weight: {weight}; '
			f'src:  url(data:font/ttf;base64,{data}) format("truetype"); }}'
		)
	return "\n".join(rules)


def settings(company: str):
	"""The Einstellungen Geschäftspost of the company, or empty ones with the defaults of the DocType."""
	if frappe.db.exists(SETTINGS, company):
		return frappe.get_cached_doc(SETTINGS, company)
	return frappe.new_doc(SETTINGS, company=company)


def _lines(text: str | None) -> tuple[str, ...]:
	return tuple(line.strip() for line in (text or "").splitlines() if line.strip())


def _address(name: str | None):
	return frappe.get_cached_doc("Address", name) if name else None


def _register(company_doc, config) -> tuple[str, str]:
	"""Register court and number from the settings, else from the fields erpnext_germany gives the Company."""
	court = config.register_court or company_doc.get("register_court") or ""
	number = config.register_number or " ".join(
		part for part in (company_doc.get("register_type"), company_doc.get("register_number")) if part
	)
	return court, number


def _bank(row) -> letter.Bank:
	account = frappe.get_cached_doc("Bank Account", row.bank_account)
	bank = frappe.db.get_value("Bank", account.bank, ["bank_name", "swift_number"], as_dict=True) or {}
	return letter.Bank(
		name=bank.get("bank_name") or account.bank or "",
		iban=account.iban or "",
		bic=bank.get("swift_number") or "",
	)


def company_particulars(company: str, config) -> letter.Company:
	company_doc = frappe.get_cached_doc("Company", company)
	address = _address(config.company_address or get_default_address("Company", company))
	court, number = _register(company_doc, config)
	return letter.Company(
		name=company_doc.company_name,
		street=address.address_line1 if address else "",
		street2=(address.address_line2 or "") if address else "",
		pincode=(address.pincode or "") if address else "",
		city=(address.city or "") if address else "",
		country=company_doc.country or "",
		phone=company_doc.phone_no or "",
		email=company_doc.email or "",
		website=company_doc.website or "",
		registered_office=config.registered_office or "",
		register_court=court,
		register_number=number,
		managing_directors=_lines(config.managing_directors),
		executive_board=_lines(config.executive_board),
		supervisory_chair=config.supervisory_board_chair or "",
		vat_id=company_doc.tax_id or "",
		tax_number=config.tax_number or "",
		banks=tuple(_bank(row) for row in config.bank_accounts),
	)


def _logo_content(url: str | None) -> bytes:
	"""The file of the logo from the files of the site, or nothing where it cannot be read."""
	if not url:
		return b""
	name = frappe.db.get_value("File", {"file_url": url}, "name")
	if not name:
		return b""
	try:
		content = frappe.get_doc("File", name).get_content()
	except frappe.DoesNotExistError:
		return b""
	except OSError:
		return b""
	return content.encode("utf-8") if isinstance(content, str) else content or b""


def logo_proportions(url: str | None) -> logo.Size | None:
	"""Width and height of the logo in its own units, or None where it cannot be read or has no size."""
	return logo.size(_logo_content(url))


def _logo(url: str | None, height: float) -> dict:
	"""The logo as a data URL with the width and height it prints at, in millimetres; empty where it cannot be read or
	has no size, so that the letterhead shows the name of the company (briefbote/layout/logo.py)."""
	content = _logo_content(url)
	proportions = logo.size(content)
	if not proportions:
		return {}
	kind = mimetypes.guess_type(url)[0] or "image/png"
	if kind == "image/svg+xml":
		content = logo.clean_svg(content)
	width, height = logo.box(proportions, Decimal(str(height)), logo.MAX_WIDTH)
	return {
		"src": f"data:{kind};base64,{base64.b64encode(content).decode('ascii')}",
		"width": float(width),
		"height": float(height),
	}


def recipient(doc, home_country: str) -> list[str]:
	"""The address of the recipient of a document of a customer or a supplier."""
	party_name = doc.get("customer_name") or doc.get("supplier_name") or doc.get("party_name") or ""
	address = _address(doc.get("customer_address") or doc.get("supplier_address"))
	contact = doc.get("contact_display") or ""
	party = letter.Party(
		name=party_name,
		contact=contact if contact and contact != party_name else "",
		street=(address.address_line1 or "") if address else "",
		street2=(address.address_line2 or "") if address else "",
		pincode=(address.pincode or "") if address else "",
		city=(address.city or "") if address else "",
		country=(address.country or "") if address else "",
	)
	return letter.address_lines(party, home_country, t)


def pre_printed(no_letterhead) -> bool:
	"""Whether the print view asks for pre-printed paper: „No Letterhead“ chosen where the site has letter heads to
	choose from. The print view sends no_letterhead=1 also when its letter head is empty, as on a site without any
	(get_letterhead in frappe/printing/page/print/print.js); blank paper stays blank paper then."""
	return bool(cint(no_letterhead)) and bool(frappe.db.exists("Letter Head", {"disabled": 0}))


def briefbote_letter(doc, no_letterhead=0) -> dict:
	"""The frame of a business letter: form, paper, return address, recipient, logo and footer."""
	config = settings(doc.company)
	company = company_particulars(doc.company, config)
	form = din5008.form(config.letter_form)
	own_paper = config.stationery == BLANK_PAPER and not pre_printed(no_letterhead)
	address = recipient(doc, company.country)
	footer = letter.foot_blocks(company, t) if own_paper else []
	height = theme.logo_height(flt(config.get("logo_height")), form.letterhead_height, TOP_MARGIN)
	returned = letter.return_address(company) if cint(config.print_return_address) else None
	found = document_status(doc)
	bottom = BOTTOM_MARGIN.get(frappe.form_dict.get("pdf_generator") or "", FOOTER_ZONE)
	request = getattr(frappe.local, "request", None)
	return {
		"form": form,
		"medium": medium.medium(request.path if request else None),
		"top": TOP_MARGIN,
		"bottom": bottom,
		"foot_pixels": FOOT_PIXELS,
		"foot_zone": FOOTER_ZONE,
		"page_line_clearance": BOTTOM_MARGIN["chrome"],
		"own_paper": own_paper,
		"fold_marks": cint(config.print_fold_marks),
		"return_address": returned.lines if returned else (),
		"return_size": float(returned.size) if returned else 0,
		"recipient": address,
		"dense": letter.dense(address),
		"company": company,
		"logo": _logo(config.logo, height) if own_paper else {},
		"logo_side": theme.logo_side(config.get("logo_position")),
		"accent": theme.colour(config.get("accent_color")),
		"accent_text": theme.text_colour(theme.colour(config.get("accent_color"))),
		"font_stack": theme.font_stack(config.get("font")),
		"fonts": font_faces() if theme.embeds(config.get("font")) else "",
		"footer": footer,
		"punch_mark": din5008.PUNCH_MARK,
		"status": found.name if found else "",
		"mark": t(found.mark) if found else "",
		"status_label": t(found.label) if found else "",
	}


def document_status(doc) -> status.Status | None:
	"""The mark of a draft or a cancelled document (briefbote/layout/status.py)."""
	return status.of(bool(doc.meta.is_submittable), int(doc.docstatus or 0))


def _date(value) -> str:
	return formatdate(value) if value else ""


def _description(row) -> str:
	text = strip_html(BREAKS.sub("\n", row.description or "")).strip()
	text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
	return "" if text == (row.item_name or "").strip() else text


def _service_text(dates: tuple[date, ...]) -> str:
	if len(dates) == 2:
		return t("{0} to {1}").format(_date(dates[0]), _date(dates[1]))
	return _date(dates[0])


def _delivery_dates(doc) -> list[date]:
	notes = sorted({row.delivery_note for row in doc.items if row.get("delivery_note")})
	if not notes:
		return []
	return [
		getdate(day)
		for day in frappe.get_all(
			"Delivery Note", filters={"name": ("in", notes)}, pluck="posting_date", order_by="posting_date"
		)
	]


def _tax_case(doc, config) -> tuple[document.Case, str]:
	for row in config.tax_cases:
		if row.taxes_and_charges == doc.taxes_and_charges:
			return document.case(row.tax_case), row.exemption_reason or doc.get("tax_exemption_reason") or ""
	return document.Case.DOMESTIC, doc.get("tax_exemption_reason") or ""


def briefbote_invoice(doc) -> dict:
	"""What the print format Rechnung prints besides the frame of the letter."""
	config = settings(doc.company)
	original = (
		frappe.db.get_value(
			"Sales Invoice", doc.return_against, ["posting_date", "grand_total"], as_dict=True
		)
		if doc.is_return and doc.return_against
		else None
	)
	kind = document.kind_of(
		bool(doc.is_return),
		doc.return_against or "",
		Decimal(str(flt(doc.grand_total))),
		Decimal(str(flt(original.grand_total))) if original else None,
	)
	tax_case, reason = _tax_case(doc, config)
	rates = position_rates(doc)
	small_business = bool(cint(config.small_business))
	label, dates = document.service(
		posting_date=getdate(doc.posting_date),
		from_date=getdate(doc.from_date) if doc.get("from_date") else None,
		to_date=getdate(doc.to_date) if doc.get("to_date") else None,
		item_periods=[
			(
				getdate(row.service_start_date) if row.get("service_start_date") else None,
				getdate(row.service_end_date) if row.get("service_end_date") else None,
			)
			for row in doc.items
		],
		delivery_dates=_delivery_dates(doc),
	)
	company_vat_id = frappe.get_cached_value("Company", doc.company, "tax_id") or ""
	both_ids = document.needs_both_vat_ids(tax_case, small_business)
	title = t(document.TITLES[kind])
	info = [(t("Invoice No.") if kind is document.Kind.INVOICE else t("Number"), doc.name)]
	info.append((t("Invoice Date") if kind is document.Kind.INVOICE else t("Date"), _date(doc.posting_date)))
	if original:
		info.append((t("Invoice"), t("{0} of {1}").format(doc.return_against, _date(original.posting_date))))
	if doc.customer != doc.customer_name:
		info.append((t("Customer No."), doc.customer))
	if doc.get("po_no"):
		order = doc.po_no if not doc.get("po_date") else t("{0} of {1}").format(doc.po_no, _date(doc.po_date))
		info.append((t("Your Order"), order))
	info.append((t(label), _service_text(dates)))
	if doc.get("tax_id") or both_ids:
		info.append((t("Your VAT ID"), doc.get("tax_id") or ""))
	if both_ids:
		info.append((t("Our VAT ID"), company_vat_id))
	if kind is document.Kind.INVOICE and doc.get("due_date"):
		info.append((t("Due Date"), _date(doc.due_date)))
	totals, bases_known = _totals(doc, kind, rates)
	positions = _positions(doc, rates)
	facts = completeness.Facts(
		credit=kind is document.Kind.CREDIT,
		small_amount=abs(flt(doc.grand_total)) <= completeness.SMALL_AMOUNT,
		recipient_address=_complete_address(doc.get("customer_address")),
		issuer_tax_id=bool(company_vat_id or config.tax_number),
		service_date=bool(dates),
		needs_both_vat_ids=both_ids,
		recipient_vat_id=bool(doc.get("tax_id")),
		own_vat_id=bool(company_vat_id),
		taxable=document.charges_tax(tax_case, small_business),
		charges_tax=any(flt(tax.tax_amount) for tax in doc.taxes),
		states_reason=bool(reason),
		bases_known=bases_known,
		asks_payment=_asks_payment(doc, kind),
		bank_account=bool(config.bank_accounts),
	)
	notices = [
		t(text).format(*values) for text, values in document.notices(kind, tax_case, small_business, reason)
	]
	consumer = frappe.get_cached_value("Customer", doc.customer, "customer_type") == "Individual"
	if kind is document.Kind.INVOICE and consumer:
		notices.append(t(document.CONSUMER_DEFAULT))
	return {
		"kind": kind.value,
		"title": title,
		"subject": _subject(doc, kind, title, original),
		"info": _filled(info),
		"findings": [t(text) for text in completeness.missing(facts)],
		"positions": positions,
		"show_rates": taxes.shows_rates(rates),
		"columns": position_columns(positions, totals, taxes.shows_rates(rates)),
		"totals": totals,
		"notices": notices,
		"payment": _payment(doc, kind, config),
		"terms": (doc.get("terms") or "") if kind is document.Kind.INVOICE else "",
	}


BODY_PT = Decimal("9.5")
HEAD_PT = Decimal(8)
TOTAL_PT = Decimal("10.5")
# The padding of a cell of a table of positions in millimetres, as style.html sets it: 1 mm on each side; 3 mm before
# an amount or a rate, so that figures that stand side by side keep apart; none at the edges of the text.
CELL_PADDING = Decimal(2)
FIGURE_PADDING = Decimal(4)
EDGE_PADDING = Decimal(1)
AMOUNT_PADDING = Decimal(3)


def position_columns(positions: list[dict], totals: list[tuple[str, str, str]], show_rates: bool) -> dict:
	"""The widths of the columns of the table of positions and of the totals below it in millimetres
	(briefbote/layout/columns.py): the figures as wide as they need, the description the rest; the totals from the
	column of the quantity to the right edge."""
	head = {
		"number": "Pos.",
		"quantity": "Quantity",
		"unit": "Unit",
		"rate": "Unit Price",
		**({"tax": "VAT"} if show_rates else {}),
		"amount": "Amount",
	}
	field = {"tax": "tax_rate"}
	cells = {
		key: [columns.Cell(t(label), HEAD_PT, True)]
		+ [columns.Cell(str(row[field.get(key, key)]), BODY_PT) for row in positions]
		for key, label in head.items()
	}
	cells["description"] = []
	padding = dict.fromkeys(head, CELL_PADDING) | {
		"number": EDGE_PADDING,
		"rate": FIGURE_PADDING,
		"tax": FIGURE_PADDING,
		"amount": AMOUNT_PADDING,
	}
	width = Decimal(din5008.TEXT_WIDTH)
	found = columns.widths(width, cells, padding, "description")
	start = found["number"] + found["description"]
	blank, label, amount = columns.totals(
		width,
		start,
		found["amount"],
		[
			columns.Cell(text, TOTAL_PT if style == "total" else BODY_PT, bool(style))
			for text, _amount, style in totals
		],
		[
			columns.Cell(value, TOTAL_PT if style == "total" else BODY_PT, bool(style))
			for _text, value, style in totals
		],
		CELL_PADDING,
		AMOUNT_PADDING,
	)
	found |= {"totals_blank": blank, "totals_label": label, "totals_amount": amount}
	return {key: float(value) for key, value in found.items()}


def _filled(info: list[tuple[str, str]]) -> list[tuple[str, str]]:
	"""The rows of the information block that have a value: a label never stands alone; a particular the law asks for
	is a finding instead (briefbote/invoice/completeness.py)."""
	return [(label, value) for label, value in info if value]


def _complete_address(name: str | None) -> bool:
	"""Whether the address has a street, a postcode or town, as the full address of § 14 Abs. 4 Satz 1 Nr. 1 UStG."""
	address = _address(name)
	return bool(address and address.address_line1 and (address.pincode or address.city))


def _subject(doc, kind: document.Kind, title: str, original) -> str:
	if original:
		return t("{0} {1} to Invoice {2} of {3}").format(
			title, doc.name, doc.return_against, _date(original.posting_date)
		)
	return f"{title} {doc.name}"


def position_rates(doc) -> dict[str, Decimal]:
	"""The tax rate of each position by its row name (briefbote/invoice/taxes.py)."""
	net_rates = [
		Decimal(str(flt(tax.rate)))
		for tax in doc.get("taxes") or ()
		if tax.charge_type == "On Net Total"
		and flt(tax.rate)
		and tax.get("add_deduct_tax", "Add") != "Deduct"
	]
	details = [
		taxes.Detail(item=row.item_row, tax=row.tax_row, rate=Decimal(str(flt(row.rate))))
		for row in doc.get("item_wise_tax_details") or ()
	]
	return taxes.position_rates(
		[row.name for row in doc.items], details, taxes.single_rate(net_rates) if net_rates else Decimal(0)
	)


def _positions(doc, rates: dict[str, Decimal]) -> list[dict]:
	return [
		{
			"number": row.idx,
			"name": row.item_name,
			"description": _description(row),
			"period": t("Service Period {0}").format(
				_service_text((getdate(row.service_start_date), getdate(row.service_end_date)))
			)
			if row.get("service_start_date") and row.get("service_end_date")
			else "",
			"quantity": row.get_formatted("qty", doc),
			"unit": t(row.uom or row.stock_uom or ""),
			"rate": row.get_formatted("rate", doc),
			"tax_rate": f"{taxes.percent(rates[row.name])} %" if row.name in rates else "",
			"amount": row.get_formatted("amount", doc),
		}
		for row in doc.items
	]


def _details(doc) -> list[taxes.Detail]:
	return [
		taxes.Detail(item=row.item_row, tax=row.tax_row, rate=Decimal(str(flt(row.rate))))
		for row in doc.get("item_wise_tax_details") or ()
	]


def _nets(doc) -> dict[str, Decimal]:
	return {row.name: Decimal(str(flt(row.net_amount or row.amount))) for row in doc.items}


def _tax_lines(doc, rows, rates: dict[str, Decimal]) -> tuple[list[tuple[str, str, str]], bool]:
	"""A line for each tax line of the document with its rate and base (§ 14 Abs. 4 Satz 1 Nr. 8 UStG), and whether
	every base could be known (briefbote/invoice/taxes.py). A tax line of another kind than On Net Total keeps its
	description; with positions at different rates its base is not known."""
	details, nets = _details(doc), _nets(doc)
	lines, known = [], True
	for tax in rows:
		found = (
			taxes.tax_base(
				tax.name,
				Decimal(str(flt(tax.rate))),
				Decimal(str(flt(tax.net_amount))),
				details,
				nets,
			)
			if tax.charge_type == "On Net Total"
			else None
		)
		if found:
			label = t("VAT {0} % on {1}").format(
				taxes.percent(found.rate),
				frappe.format(found.base, {"fieldtype": "Currency", "options": "currency"}, doc),
			)
		else:
			label = tax.description or tax.account_head
			known = known and tax.charge_type != "On Net Total" and not taxes.shows_rates(rates)
		lines.append((label, tax.get_formatted("tax_amount", doc), ""))
	return lines, known


def _totals(doc, kind: document.Kind, rates: dict[str, Decimal]) -> tuple[list[tuple[str, str, str]], bool]:
	"""The lines of the totals: label, amount and style, „sum“ for a subtotal and „total“ for what the document
	comes to, and whether the base of every tax line is known. Each tax line names its rate and base; the positions
	without tax get a line of their own where the invoice also has taxed ones (§ 14 Abs. 4 Satz 1 Nr. 7 and 8
	UStG)."""
	lines = []
	if flt(doc.discount_amount):
		lines.append((t("Total of the Positions"), doc.get_formatted("total"), ""))
		lines.append((t("Discount"), doc.get_formatted("discount_amount"), ""))
	lines.append((t("Net Amount"), doc.get_formatted("net_total"), "sum"))
	untaxed = taxes.untaxed(_nets(doc), rates)
	taxed_lines = [tax for tax in doc.taxes if flt(tax.tax_amount)]
	if untaxed and taxed_lines:
		lines.append(
			(
				t("Consideration without VAT"),
				frappe.format(untaxed, {"fieldtype": "Currency", "options": "currency"}, doc),
				"",
			)
		)
	tax_lines, known = _tax_lines(doc, taxed_lines, rates)
	lines += tax_lines
	rounded = not cint(doc.disable_rounded_total) and flt(doc.rounding_adjustment)
	if rounded:
		lines.append((t("Rounding"), doc.get_formatted("rounding_adjustment"), ""))
	totals = {
		document.Kind.INVOICE: "Total Amount",
		document.Kind.CANCELLATION: "Cancelled Amount",
		document.Kind.CORRECTION: "Corrected Amount",
		document.Kind.CREDIT: "Credited Amount",
	}
	lines.append((t(totals[kind]), doc.get_formatted("rounded_total" if rounded else "grand_total"), "total"))
	if kind is document.Kind.INVOICE and flt(doc.total_advance):
		lines.append((t("Less Payments on Account"), doc.get_formatted("total_advance"), ""))
		lines.append((t("Amount Due"), doc.get_formatted("outstanding_amount"), "total"))
	return lines, known


def _asks_payment(doc, kind: document.Kind) -> bool:
	"""Whether an invoice asks to be paid: an open invoice, neither a draft nor cancelled."""
	return (
		kind is document.Kind.INVOICE
		and flt(doc.outstanding_amount) > 0
		and status.asks_for_payment(document_status(doc))
	)


def _payment(doc, kind: document.Kind, config) -> list[str]:
	"""The request to pay an invoice to the account below, with its instalments and their cash discounts; none for a
	draft or a cancelled invoice, and none without an account to pay to, which is a finding instead
	(briefbote/invoice/completeness.py)."""
	if not _asks_payment(doc, kind) or not config.bank_accounts:
		return []
	schedule = [row for row in doc.get("payment_schedule") or () if flt(row.payment_amount)]
	if len(schedule) <= 1:
		lines = [
			t("Please transfer {0} by {1} to the account below, stating the invoice number.").format(
				doc.get_formatted("outstanding_amount" if flt(doc.total_advance) else "grand_total"),
				_date(doc.due_date),
			)
		]
	else:
		lines = [
			t("Please transfer the amount in instalments to the account below, stating the invoice number:")
		]
		lines += [
			t("{0} by {1}").format(row.get_formatted("payment_amount", doc), _date(row.due_date))
			for row in schedule
		]
	for row in schedule:
		if flt(row.get("discount")) and row.get("discount_date"):
			if row.discount_type == "Percentage":
				discount = t("{0} % cash discount").format(
					frappe.format(row.discount, {"fieldtype": "Float", "precision": 2})
					.rstrip("0")
					.rstrip(",.")
				)
			else:
				discount = t("{0} cash discount").format(row.get_formatted("discount", doc))
			lines.append(t("{0} for payment by {1}.").format(discount, _date(row.discount_date)))
	return lines


def _purchase_case(doc, config) -> tuple[self_billing.PurchaseCase, str]:
	for row in config.get("purchase_tax_cases") or ():
		if row.purchase_taxes_and_charges == doc.taxes_and_charges:
			return self_billing.case(row.tax_case), row.exemption_reason or ""
	return self_billing.PurchaseCase.DOMESTIC, ""


def _self_billing_totals(
	doc, kind: document.Kind, tax_case, rates
) -> tuple[list[tuple[str, str, str]], bool]:
	"""Net amount, the supplier's Umsatzsteuer by rate and base where the supply is taxable in Germany, and the total.
	A purchase tax template books the tax of § 13b UStG as added and deducted again; it is the company's tax, not the
	supplier's, and no line of the Gutschrift."""
	lines = [(t("Net Amount"), doc.get_formatted("net_total"), "sum")]
	total = doc.get_formatted("net_total")
	known = True
	if self_billing.charges_tax(tax_case):
		added = [tax for tax in doc.taxes if flt(tax.tax_amount) and tax.get("add_deduct_tax") != "Deduct"]
		tax_lines, known = _tax_lines(doc, added, rates)
		lines += tax_lines
		total = doc.get_formatted("grand_total")
	labels = {
		document.Kind.INVOICE: "Total Amount",
		document.Kind.CANCELLATION: "Cancelled Amount",
		document.Kind.CORRECTION: "Corrected Amount",
		document.Kind.CREDIT: "Corrected Amount",
	}
	lines.append((t(labels[kind]), total, "total"))
	return lines, known


def briefbote_self_billing(doc) -> dict:
	"""What the print format Gutschrift prints of a Purchase Invoice marked as self-billing (custom field
	self_billing): the document the company issues to its supplier (briefbote/invoice/self_billing.py)."""
	config = settings(doc.company)
	original = (
		frappe.db.get_value(
			"Purchase Invoice", doc.return_against, ["posting_date", "grand_total"], as_dict=True
		)
		if doc.is_return and doc.return_against
		else None
	)
	kind = document.kind_of(
		bool(doc.is_return),
		doc.return_against or "",
		Decimal(str(flt(doc.grand_total))),
		Decimal(str(flt(original.grand_total))) if original else None,
	)
	tax_case, reason = _purchase_case(doc, config)
	rates = position_rates(doc) if self_billing.charges_tax(tax_case) else {}
	label, dates = document.service(
		posting_date=getdate(doc.posting_date),
		from_date=getdate(doc.from_date) if doc.get("from_date") else None,
		to_date=getdate(doc.to_date) if doc.get("to_date") else None,
	)
	supplier_tax_id = doc.get("tax_id") or frappe.get_cached_value("Supplier", doc.supplier, "tax_id") or ""
	title = t(self_billing.TITLES[kind])
	info = [(t("Number"), doc.name), (t("Date"), _date(doc.posting_date))]
	if original:
		info.append(
			(
				t("Self-Billing Invoice"),
				t("{0} of {1}").format(doc.return_against, _date(original.posting_date)),
			)
		)
	if doc.supplier != doc.supplier_name:
		info.append((t("Supplier No."), doc.supplier))
	info.append((t(label), _service_text(dates)))
	info.append((t(self_billing.tax_id_label(supplier_tax_id)), supplier_tax_id))
	totals, bases_known = _self_billing_totals(doc, kind, tax_case, rates)
	positions = _positions(doc, rates)
	marked = bool(cint(doc.get("self_billing")))
	facts = completeness.Facts(
		self_billing=True,
		credit=kind is document.Kind.CREDIT,
		small_amount=abs(flt(doc.grand_total)) <= completeness.SMALL_AMOUNT,
		recipient_address=_complete_address(doc.get("supplier_address")),
		issuer_tax_id=bool(supplier_tax_id),
		service_date=bool(dates),
		taxable=self_billing.charges_tax(tax_case),
		charges_tax=any(
			flt(tax.tax_amount) and tax.get("add_deduct_tax") != "Deduct" for tax in doc.get("taxes") or ()
		),
		bases_known=bases_known,
	)
	findings = completeness.missing(facts) if marked else [completeness.NOT_SELF_BILLING]
	notices = [t(text).format(*values) for text, values in self_billing.notices(tax_case, reason)]
	payment = []
	if (
		kind is document.Kind.INVOICE
		and flt(doc.outstanding_amount) > 0
		and status.asks_for_payment(document_status(doc))
	):
		payment.append(
			t("We will transfer {0} to your account by {1}.").format(
				doc.get_formatted("outstanding_amount"), _date(doc.due_date or doc.posting_date)
			)
		)
	return {
		"marked": marked,
		"findings": [t(text) for text in findings],
		"kind": kind.value,
		"title": title,
		"subject": t("{0} {1} to the Self-Billing Invoice {2} of {3}").format(
			title, doc.name, doc.return_against, _date(original.posting_date)
		)
		if original
		else f"{title} {doc.name}",
		"info": _filled(info),
		"positions": positions,
		"show_rates": taxes.shows_rates(rates),
		"columns": position_columns(positions, totals, taxes.shows_rates(rates)),
		"totals": totals,
		"notices": notices,
		"payment": payment,
		"terms": "",
	}


def briefbote_page_counter(title: str) -> str:
	"""The page line of a printout the browser prints itself, as CSS content with the counters of its pages."""
	return medium.page_counter(title, t("Page {0} of {1}"))
