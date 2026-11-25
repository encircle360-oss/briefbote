"""The Leistungsnachweis of a Sales Invoice, read from its table timesheets (briefbote/annex/timesheets.py), for the
print formats Rechnung, as an annex, and Leistungsnachweis, as a document of its own; and the warning on saving an
invoice whose hours differ from the quantity it bills by time."""

from decimal import Decimal

import frappe
from frappe.utils import flt, getdate

from briefbote.annex import timesheets
from briefbote.briefbote import printing
from briefbote.briefbote.printing import t
from briefbote.layout import columns, din5008


def _hours(value: Decimal) -> str:
	"""Hours with two decimals in the number format of the site: 102,00."""
	return frappe.utils.fmt_money(value, precision=2)


def _logs(doc) -> dict[str, frappe._dict]:
	"""The time logs behind the rows, with the person and the task of their Timesheet."""
	names = [row.timesheet_detail for row in doc.get("timesheets") or () if row.get("timesheet_detail")]
	if not names:
		return {}
	logs = frappe.get_all(
		"Timesheet Detail",
		filters={"name": ("in", names)},
		fields=["name", "parent", "task", "project"],
	)
	sheets = {
		sheet.name: sheet
		for sheet in frappe.get_all(
			"Timesheet",
			filters={"name": ("in", sorted({log.parent for log in logs}))},
			fields=["name", "employee", "employee_name"],
		)
	}
	employees = {
		employee.name: employee
		for employee in frappe.get_all(
			"Employee",
			filters={"name": ("in", sorted({sheet.employee for sheet in sheets.values() if sheet.employee}))},
			fields=["name", "designation"],
		)
	}
	tasks = dict(
		frappe.get_all(
			"Task",
			filters={"name": ("in", sorted({log.task for log in logs if log.task}))},
			fields=["name", "subject"],
			as_list=True,
		)
	)
	found = {}
	for log in logs:
		sheet = sheets.get(log.parent) or frappe._dict()
		employee = employees.get(sheet.get("employee")) or frappe._dict()
		found[log.name] = frappe._dict(
			person=sheet.get("employee_name") or "",
			role=employee.get("designation") or "",
			task=tasks.get(log.task, log.task or ""),
			project=log.project or "",
		)
	return found


def entries(doc, mode: timesheets.Person) -> list[timesheets.Entry]:
	logs = _logs(doc)
	result = []
	for row in doc.get("timesheets") or ():
		log = logs.get(row.get("timesheet_detail") or "") or frappe._dict()
		project = row.get("project_name") or log.get("project") or ""
		result.append(
			timesheets.Entry(
				day=getdate(row.from_time) if row.get("from_time") else getdate(doc.posting_date),
				person=timesheets.person(log.get("person", ""), log.get("role", ""), mode),
				activity=row.get("activity_type") or "",
				description=(row.get("description") or "").strip(),
				project=project,
				task=log.get("task", ""),
				hours=Decimal(str(flt(row.billing_hours))),
			)
		)
	return result


def billed_by_time(doc, unit: str | None) -> list:
	"""The positions the invoice bills by time: those in the unit of time of the settings."""
	return [row for row in doc.items if unit and (row.uom or row.stock_uom) == unit]


def briefbote_timesheets(doc) -> dict:
	"""What the annex prints, empty where the invoice has no timesheets or the settings print none."""
	config = printing.settings(doc.company)
	where = timesheets.placement(config.get("timesheet_annex"))
	mode = timesheets.person_mode(config.get("person_display"))
	found = timesheets.ordered(entries(doc, mode))
	if not found:
		return {"placement": where.value, "rows": []}
	positions = billed_by_time(doc, config.get("time_unit"))
	total = timesheets.total(found)
	matched, billed = timesheets.reconcile(total, [Decimal(str(flt(row.qty))) for row in positions])
	rows = [
		{
			"day": printing._date(entry.day),
			"person": entry.person,
			"activity": entry.activity,
			"description": entry.description,
			"project": entry.project,
			"task": entry.task,
			"hours": _hours(entry.hours),
		}
		for entry in found
	]
	show_person = mode is not timesheets.Person.NONE
	return {
		"placement": where.value,
		"title": t("Timesheet Annex to Invoice {0} of {1}").format(
			doc.name, printing._date(doc.posting_date)
		),
		"show_person": show_person,
		"rows": rows,
		"columns": annex_columns(rows, show_person),
		"by_project": [(label, _hours(hours)) for label, hours in timesheets.subtotals(found, "project")],
		"by_person": [(label, _hours(hours)) for label, hours in timesheets.subtotals(found, "person")]
		if mode is not timesheets.Person.NONE
		else [],
		"total": _hours(total),
		"matched": matched,
		"billed": _hours(billed),
		"positions": ", ".join(str(row.idx) for row in positions),
		"reference": t("Annex: Timesheet with {0} hours.").format(_hours(total)),
	}


# A project with its task may wrap in its column rather than narrow the activities.
PROJECT_LIMIT = Decimal(42)


def annex_columns(rows: list[dict], show_person: bool) -> dict:
	"""The widths of the columns of the Leistungsnachweis in millimetres (briefbote/layout/columns.py): day, person,
	project and hours as wide as they need, the project at most PROJECT_LIMIT, the activities the rest."""
	body, head = printing.BODY_PT, printing.HEAD_PT
	heads = {
		"day": "Date",
		**({"person": "Person"} if show_person else {}),
		"project": "Project and Task",
		"hours": "Hours",
	}
	cells = {key: [columns.Cell(t(label), head, True)] for key, label in heads.items()}
	for row in rows:
		cells["day"].append(columns.Cell(row["day"], body))
		if show_person:
			cells["person"].append(columns.Cell(row["person"], body))
		cells["project"] += [columns.Cell(row["project"], body), columns.Cell(row["task"] or "", body)]
		cells["hours"].append(columns.Cell(row["hours"], body))
	cells["activity"] = []
	padding = dict.fromkeys(heads, printing.CELL_PADDING) | {
		"day": printing.EDGE_PADDING,
		"hours": printing.EDGE_PADDING,
	}
	found = columns.widths(
		Decimal(din5008.TEXT_WIDTH), cells, padding, "activity", limits={"project": PROJECT_LIMIT}
	)
	return {key: float(value) for key, value in found.items()}


def warn_on_mismatch(doc, method=None):
	"""On saving a Sales Invoice: tell the user when the hours of its timesheets differ from the quantity of its
	positions in the unit of time, which the Leistungsnachweis would show against each other."""
	if not doc.get("timesheets"):
		return
	config = printing.settings(doc.company)
	if timesheets.placement(config.get("timesheet_annex")) is timesheets.Placement.NONE:
		return
	hours = sum((Decimal(str(flt(row.billing_hours))) for row in doc.timesheets), Decimal(0))
	positions = billed_by_time(doc, config.get("time_unit"))
	matched, billed = timesheets.reconcile(hours, [Decimal(str(flt(row.qty))) for row in positions])
	if not matched:
		frappe.msgprint(
			t(
				"The timesheets of this invoice hold {0} hours, its positions in {1} bill {2}. The Leistungsnachweis shows both."
			).format(_hours(hours), config.get("time_unit") or "", _hours(billed)),
			indicator="orange",
			alert=True,
		)
