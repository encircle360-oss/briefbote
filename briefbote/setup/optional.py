"""What Briefbote adds to the desk only where another app brings the DocType: a print format for it, and the entries
of its sidebar and its workspace Geschäftspost that lead to the DocType (briefbote/briefbote/optional/). Each part
exists exactly where its DocType exists, so that a site without the app has neither a print format for a missing
DocType nor a link that leads nowhere. Every function here is idempotent: applied twice, the second time changes
nothing; an entry already there, wherever it stands, stays where it is.
"""

import re
from collections.abc import Callable

type Exists = Callable[[str], bool]
BLOCK_PREFIX = "bbopt-"


def identity(row: dict) -> tuple[str, ...]:
	"""What makes two rows of a sidebar the same row: a group by its label, since the site stores a group with the
	default link type of a Sidebar Item; a link by its target."""
	if row.get("type") == "Section Break":
		return ("Section Break", row.get("label") or "")
	return (row.get("type") or "", row.get("link_type") or "", row.get("link_to") or "")


def wanted(row: dict, exists: Exists) -> bool:
	"""Whether a print format or a shortcut belongs on the site: where its DocType exists."""
	return exists(row.get("doc_type") or row.get("link_to") or "")


def _wanted_rows(optional: list[dict], exists: Exists) -> list[dict]:
	"""The optional rows whose DocType exists, each group only with an entry after it."""
	found: list[dict] = []
	group: dict | None = None
	for row in optional:
		if row.get("type") == "Section Break":
			group = row
		elif exists(row.get("link_to") or ""):
			if group is not None:
				found.append(group)
				group = None
			found.append(row)
	return found


def sidebar_changes(items: list[dict], optional: list[dict], exists: Exists) -> tuple[list[dict], list[dict]]:
	"""The optional rows to append to the sidebar and the stored rows to remove from it."""
	keep = _wanted_rows(optional, exists)
	present = {identity(row) for row in items}
	kept = {identity(row) for row in keep}
	ours = {identity(row) for row in optional}
	add = [row for row in keep if identity(row) not in present]
	remove = [row for row in items if identity(row) in ours and identity(row) not in kept]
	return add, remove


def shortcut_changes(
	shortcuts: list[dict], optional: list[dict], exists: Exists
) -> tuple[list[dict], list[dict]]:
	"""The optional shortcuts to add to the workspace and the stored ones to remove from it."""
	labels = {row.get("label") for row in shortcuts}
	ours = {row["label"]: row for row in optional}
	add = [row for row in optional if wanted(row, exists) and row["label"] not in labels]
	remove = [row for row in shortcuts if row.get("label") in ours and not wanted(ours[row["label"]], exists)]
	return add, remove


def block_id(label: str) -> str:
	return BLOCK_PREFIX + re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def _block(label: str) -> dict:
	return {"id": block_id(label), "type": "shortcut", "data": {"shortcut_name": label, "col": 4}}


def content(blocks: list[dict], optional: list[dict], exists: Exists, after: str) -> list[dict]:
	"""The blocks of the workspace with a block for each optional shortcut whose DocType exists, placed after the
	block named after, in the order of the optional shortcuts, or at the end; without the blocks of the others."""
	gone = {row["label"] for row in optional if not wanted(row, exists)}

	def name(block: dict) -> str:
		return (block.get("data") or {}).get("shortcut_name") or ""

	found = [block for block in blocks if not (block.get("type") == "shortcut" and name(block) in gone)]
	shown = {name(block) for block in found if block.get("type") == "shortcut"}
	ids = [block.get("id") for block in found]
	position = ids.index(after) + 1 if after in ids else len(found)
	for row in optional:
		label = row["label"]
		if label in gone:
			continue
		if label in shown:
			position = next(index for index, block in enumerate(found) if name(block) == label) + 1
			continue
		found.insert(position, _block(label))
		position += 1
	return found
