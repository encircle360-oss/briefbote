"""The parts of Briefbote for a DocType of another app, such as the Business Letter of erpnext_germany: the print
formats of this folder and the entries of menu.json in the sidebar Briefbote and the workspace Geschäftspost. Each
exists on the site exactly where its DocType exists (briefbote/setup/optional.py), so that Briefbote needs no other
app and a site without one holds neither a print format for a missing DocType nor a link that leads nowhere.

Frappe imports the print formats under print_format/ of the module on every migration, whatever DocTypes the site
has; the records here are imported by sync instead, with Frappe's import of a file. The template of each stays under
print_format/<name>/<name>.html, where Frappe reads the template of a standard print format of the module when it
prints. The sidebar and the workspace belong to Briefbote and change on a site only in developer mode; a site
changes them through a Custom Sidebar or Custom Workspace, which this leaves alone. sync writes their rows in the
database, without saving the documents, so that developer mode exports nothing to the files of the app.

sync runs after Briefbote is installed and after every migration; after another app is installed, so that it brings
its part; and before another app is uninstalled, so that the parts of its DocTypes go before they do.
"""

import json
from collections.abc import Callable
from pathlib import Path

import frappe
from frappe.modules.import_file import import_file_by_path

from briefbote.setup import optional

FOLDER = Path(__file__).resolve().parent
MENU = FOLDER / "menu.json"
SIDEBAR = "Briefbote"
WORKSPACE = "Geschäftspost"
APP = "briefbote"


def menu() -> dict:
	return json.loads(MENU.read_text(encoding="utf-8"))


def _paths() -> list[Path]:
	return sorted(path for path in FOLDER.glob("*.json") if path != MENU)


def records() -> list[dict]:
	"""The print formats for a DocType of another app, as their files hold them."""
	return [json.loads(path.read_text(encoding="utf-8")) for path in _paths()]


def doctype_exists(doctype: str) -> bool:
	return bool(doctype and frappe.db.exists("DocType", doctype))


def _print_formats(exists: Callable[[str], bool]) -> bool:
	changed = False
	for path in _paths():
		record = json.loads(path.read_text(encoding="utf-8"))
		if optional.wanted(record, exists):
			changed = import_file_by_path(str(path)) or changed
		elif frappe.db.exists("Print Format", record["name"]):
			frappe.delete_doc("Print Format", record["name"], force=True, ignore_permissions=True)
			changed = True
	return changed


def _sidebar(exists: Callable[[str], bool]) -> bool:
	if not frappe.db.exists("Sidebar", SIDEBAR):
		return False
	items = frappe.get_all(
		"Sidebar Item",
		filters={"parent": SIDEBAR, "parenttype": "Sidebar", "parentfield": "items"},
		fields=["name", "idx", "type", "label", "link_type", "link_to"],
		order_by="idx",
	)
	add, remove = optional.sidebar_changes(items, menu()["sidebar"], exists)
	for row in remove:
		frappe.db.delete("Sidebar Item", row["name"])
	last = max((row["idx"] for row in items), default=0)
	for index, row in enumerate(add, start=last + 1):
		frappe.get_doc(
			{
				"doctype": "Sidebar Item",
				"parent": SIDEBAR,
				"parenttype": "Sidebar",
				"parentfield": "items",
				"idx": index,
				**row,
			}
		).db_insert()
	return bool(add or remove)


def _workspace(exists: Callable[[str], bool]) -> bool:
	if not frappe.db.exists("Workspace", WORKSPACE):
		return False
	wanted = menu()["workspace"]
	shortcuts = frappe.get_all(
		"Workspace Shortcut",
		filters={"parent": WORKSPACE, "parenttype": "Workspace", "parentfield": "shortcuts"},
		fields=["name", "idx", "label", "link_to", "type"],
		order_by="idx",
	)
	add, remove = optional.shortcut_changes(shortcuts, wanted["shortcuts"], exists)
	for row in remove:
		frappe.db.delete("Workspace Shortcut", row["name"])
	last = max((row["idx"] for row in shortcuts), default=0)
	for index, row in enumerate(add, start=last + 1):
		frappe.get_doc(
			{
				"doctype": "Workspace Shortcut",
				"parent": WORKSPACE,
				"parenttype": "Workspace",
				"parentfield": "shortcuts",
				"idx": index,
				**row,
			}
		).db_insert()
	stored = json.loads(frappe.db.get_value("Workspace", WORKSPACE, "content") or "[]")
	blocks = optional.content(stored, wanted["shortcuts"], exists, wanted["after"])
	if blocks != stored:
		frappe.db.set_value("Workspace", WORKSPACE, "content", json.dumps(blocks), update_modified=False)
	return bool(add or remove or blocks != stored)


def sync(exists: Callable[[str], bool] = doctype_exists) -> None:
	"""Give the site the parts whose DocType exists and take away the others."""
	changed = _print_formats(exists)
	changed = _sidebar(exists) or changed
	changed = _workspace(exists) or changed
	if changed:
		frappe.clear_cache()


def app_installed(app: str) -> None:
	"""After an app is installed, which may bring a DocType of the parts."""
	sync()


def app_uninstalling(app: str) -> None:
	"""Before an app is uninstalled: its DocTypes still exist, but their parts go now. Briefbote's own parts go with
	its module when Briefbote is uninstalled."""
	if app == APP:
		return
	owned = {name for name in _doctypes() if doctype_exists(name) and frappe.get_doctype_app(name) == app}
	if owned:
		sync(lambda doctype: doctype_exists(doctype) and doctype not in owned)


def _doctypes() -> set[str]:
	wanted = menu()
	rows = [*wanted["sidebar"], *wanted["workspace"]["shortcuts"], *records()]
	return {row.get("link_to") or row.get("doc_type") for row in rows} - {None, ""}
