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

from briefbote.invoice import document, self_billing, taxes
from briefbote.layout import din5008, letter, theme

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
# The bottom margin of every page in millimetres. wkhtmltopdf prints the footer inside it, so it holds the footer;
# the Chromium-based generator of Frappe prints the footer above it and measures the footer itself
# (prepare_options_for_pdf in frappe/utils/pdf_generator/browser.py), so a narrow margin puts the footer at the same place.
BOTTOM_MARGIN = {"chrome": 8}
FOOTER_ZONE = 36
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


def _logo(url: str | None) -> str:
	"""The logo as a data URL, read from the files of the site."""
	if not url:
		return ""
	name = frappe.db.get_value("File", {"file_url": url}, "name")
	if not name:
		return ""
	content = frappe.get_doc("File", name).get_content()
	if isinstance(content, str):
		content = content.encode("utf-8")
	kind = mimetypes.guess_type(url)[0] or "image/png"
	return f"data:{kind};base64,{base64.b64encode(content).decode('ascii')}"


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


def briefbote_letter(doc, no_letterhead=0) -> dict:
	"""The frame of a business letter: form, paper, return address, recipient, logo and footer."""
	config = settings(doc.company)
	company = company_particulars(doc.company, config)
	form = din5008.form(config.letter_form)
	own_paper = config.stationery == BLANK_PAPER and not cint(no_letterhead)
	address = recipient(doc, company.country)
	layout = tuple(
		theme.Placement(cint(row.column), theme.block(row.block)) for row in config.get("footer_layout") or ()
	)
	return {
		"form": form,
		"top": TOP_MARGIN,
		"bottom": BOTTOM_MARGIN.get(frappe.form_dict.get("pdf_generator") or "", FOOTER_ZONE),
		"own_paper": own_paper,
		"fold_marks": cint(config.print_fold_marks),
		"return_address": letter.sender_line(company) if cint(config.print_return_address) else "",
		"recipient": address,
		"dense": letter.dense(address),
		"company": company,
		"logo": _logo(config.logo) if own_paper else "",
		"logo_side": theme.logo_side(config.get("logo_position")),
		"logo_height": theme.logo_height(flt(config.get("logo_height")), form.letterhead_height, TOP_MARGIN),
		"accent": theme.colour(config.get("accent_color")),
		"font_stack": theme.font_stack(config.get("font")),
		"fonts": font_faces() if theme.embeds(config.get("font")) else "",
		"footer": letter.footer_columns(company, t, layout) if own_paper else [],
		"punch_mark": din5008.PUNCH_MARK,
	}


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
		"info": info,
		"positions": _positions(doc, rates),
		"show_rates": taxes.shows_rates(rates),
		"totals": _totals(doc, kind, rates),
		"notices": notices,
		"payment": _payment(doc, kind, config),
		"terms": (doc.get("terms") or "") if kind is document.Kind.INVOICE else "",
	}


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


def _rate_label(rate) -> str:
	return taxes.percent(Decimal(str(flt(rate))))


def _totals(doc, kind: document.Kind, rates: dict[str, Decimal]) -> list[tuple[str, str, str]]:
	"""The lines of the totals: label, amount and style, „sum“ for a subtotal and „total“ for what the document
	comes to. Each tax line names its rate and base; the positions without tax get a line of their own where the
	invoice also has taxed ones (§ 14 Abs. 4 Satz 1 Nr. 7 and 8 UStG)."""
	lines = []
	if flt(doc.discount_amount):
		lines.append((t("Total of the Positions"), doc.get_formatted("total"), ""))
		lines.append((t("Discount"), doc.get_formatted("discount_amount"), ""))
	lines.append((t("Net Amount"), doc.get_formatted("net_total"), "sum"))
	nets = {row.name: Decimal(str(flt(row.net_amount or row.amount))) for row in doc.items}
	untaxed = taxes.untaxed(nets, rates)
	taxed_lines = [tax for tax in doc.taxes if flt(tax.tax_amount)]
	if untaxed and taxed_lines:
		lines.append(
			(
				t("Consideration without VAT"),
				frappe.format(untaxed, {"fieldtype": "Currency", "options": "currency"}, doc),
				"",
			)
		)
	for tax in taxed_lines:
		if flt(tax.rate) and tax.charge_type == "On Net Total":
			label = t("VAT {0} % on {1}").format(_rate_label(tax.rate), tax.get_formatted("net_amount", doc))
		else:
			label = tax.description or tax.account_head
		lines.append((label, tax.get_formatted("tax_amount", doc), ""))
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
	return lines


def _payment(doc, kind: document.Kind, config) -> list[str]:
	"""The request to pay an invoice, with its instalments and their cash discounts."""
	if kind is not document.Kind.INVOICE or flt(doc.outstanding_amount) <= 0:
		return []
	to_account = bool(config.bank_accounts)
	schedule = [row for row in doc.get("payment_schedule") or () if flt(row.payment_amount)]
	if len(schedule) <= 1:
		lines = [
			t(
				"Please transfer {0} by {1} to the account below, stating the invoice number."
				if to_account
				else "Please transfer {0} by {1}, stating the invoice number."
			).format(
				doc.get_formatted("outstanding_amount" if flt(doc.total_advance) else "grand_total"),
				_date(doc.due_date),
			)
		]
	else:
		lines = [
			t(
				"Please transfer the amount in instalments to the account below, stating the invoice number:"
				if to_account
				else "Please transfer the amount in instalments, stating the invoice number:"
			)
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


def _self_billing_totals(doc, kind: document.Kind, tax_case) -> list[tuple[str, str, str]]:
	"""Net amount, the supplier's Umsatzsteuer by rate and base where the supply is taxable in Germany, and the total.
	A purchase tax template books the tax of § 13b UStG as added and deducted again; it is the company's tax, not the
	supplier's, and no line of the Gutschrift."""
	lines = [(t("Net Amount"), doc.get_formatted("net_total"), "sum")]
	total = doc.get_formatted("net_total")
	if self_billing.charges_tax(tax_case):
		for tax in doc.taxes:
			if flt(tax.tax_amount) and tax.get("add_deduct_tax") != "Deduct":
				label = (
					t("VAT {0} % on {1}").format(_rate_label(tax.rate), tax.get_formatted("net_amount", doc))
					if flt(tax.rate) and tax.charge_type == "On Net Total"
					else tax.description or tax.account_head
				)
				lines.append((label, tax.get_formatted("tax_amount", doc), ""))
		total = doc.get_formatted("grand_total")
	labels = {
		document.Kind.INVOICE: "Total Amount",
		document.Kind.CANCELLATION: "Cancelled Amount",
		document.Kind.CORRECTION: "Corrected Amount",
		document.Kind.CREDIT: "Corrected Amount",
	}
	lines.append((t(labels[kind]), total, "total"))
	return lines


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
	notices = [t(text).format(*values) for text, values in self_billing.notices(tax_case, reason)]
	payment = []
	if kind is document.Kind.INVOICE and flt(doc.outstanding_amount) > 0:
		payment.append(
			t("We will transfer {0} to your account by {1}.").format(
				doc.get_formatted("outstanding_amount"), _date(doc.due_date or doc.posting_date)
			)
		)
	return {
		"marked": bool(cint(doc.get("self_billing"))),
		"kind": kind.value,
		"title": title,
		"subject": t("{0} {1} to the Self-Billing Invoice {2} of {3}").format(
			title, doc.name, doc.return_against, _date(original.posting_date)
		)
		if original
		else f"{title} {doc.name}",
		"info": info,
		"positions": _positions(doc, rates),
		"show_rates": taxes.shows_rates(rates),
		"totals": _self_billing_totals(doc, kind, tax_case),
		"notices": notices,
		"payment": payment,
		"terms": "",
	}
