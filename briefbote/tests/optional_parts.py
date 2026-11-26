"""What a site holds of the parts Briefbote adds only for a DocType of another app (briefbote/briefbote/optional),
for the tests of the site and for CI, which checks a site before erpnext_germany is installed, after, and after it
is uninstalled again:

	bench --site <site> execute briefbote.tests.optional_parts.check --kwargs "{'expected': False}"
"""

import json
import sys
from dataclasses import dataclass

import frappe

from briefbote.briefbote import optional

DOCTYPES = ("Business Letter", "Business Letter Template")


@dataclass(frozen=True)
class State:
	print_formats: tuple[str, ...]
	sidebar: tuple[str, ...]
	shortcuts: tuple[str, ...]
	blocks: tuple[str, ...]
	doctypes: tuple[str, ...]


def state() -> State:
	"""The optional print formats, sidebar rows, shortcuts and blocks of the workspace the site holds."""
	menu = optional.menu()
	records = [record["name"] for record in optional.records()]
	labels = {row["label"] for row in menu["sidebar"]}
	shortcuts = {row["label"] for row in menu["workspace"]["shortcuts"]}
	content = json.loads(frappe.db.get_value("Workspace", optional.WORKSPACE, "content") or "[]")
	return State(
		print_formats=tuple(sorted(name for name in records if frappe.db.exists("Print Format", name))),
		sidebar=tuple(
			frappe.get_all(
				"Sidebar Item",
				filters={"parent": optional.SIDEBAR, "parenttype": "Sidebar", "label": ("in", list(labels))},
				pluck="label",
				order_by="idx",
			)
		),
		shortcuts=tuple(
			sorted(
				frappe.get_all(
					"Workspace Shortcut",
					filters={
						"parent": optional.WORKSPACE,
						"parenttype": "Workspace",
						"label": ("in", list(shortcuts)),
					},
					pluck="label",
				)
			)
		),
		blocks=tuple(
			(block.get("data") or {}).get("shortcut_name")
			for block in content
			if block.get("type") == "shortcut" and (block.get("data") or {}).get("shortcut_name") in shortcuts
		),
		doctypes=tuple(name for name in DOCTYPES if frappe.db.exists("DocType", name)),
	)


FULL = State(
	print_formats=("Geschäftsbrief",),
	sidebar=("Correspondence", "Business Letters", "Letter Templates"),
	shortcuts=("Business Letters", "Letter Templates"),
	blocks=("Business Letters", "Letter Templates"),
	doctypes=DOCTYPES,
)
EMPTY = State((), (), (), (), ())


def problems(expected: bool) -> list[str]:
	"""How the site differs from one with erpnext_germany (expected) or without it."""
	found, wanted = state(), FULL if expected else EMPTY
	return [
		f"{field}: {getattr(found, field)} statt {getattr(wanted, field)}"
		for field in State.__dataclass_fields__
		if getattr(found, field) != getattr(wanted, field)
	]


def check(expected: bool) -> None:
	found = problems(expected)
	sys.stdout.write(
		(
			"\n".join(found)
			or f"Optionale Teile wie erwartet ({'mit' if expected else 'ohne'} erpnext_germany)."
		)
		+ "\n"
	)
	if found:
		raise SystemExit("Die Site hält die optionalen Teile nicht so, wie ihre DocTypes es verlangen.")
