"""Über Briefbote: who makes Briefbote and where its source, documentation, issues and disclaimer are, the block at the
bottom of the workspace Geschäftspost. The block loads nothing from another site; its links open in a new tab and tell
their target nothing of the site. Nothing of it reaches a printout: a business document carries no hint of the
software that printed it."""

from collections.abc import Callable
from html import escape

from briefbote import __version__

# The Custom HTML Block of the workspace. The desk finds a block of a workspace by its translated label, so the name
# reads the same in every language.
BLOCK = "Über Briefbote"
REPOSITORY = "https://github.com/encircle360-oss/briefbote"
LOGO = "/assets/briefbote/images/briefbote-logo.svg"
SERVICES = "https://encircle360.com/?ref=briefbote"
LINKS = (
	("Source Code", REPOSITORY),
	("Documentation", f"{REPOSITORY}/tree/main/docs"),
	("Report a Problem", f"{REPOSITORY}/issues"),
	("Disclaimer", f"{REPOSITORY}/blob/main/docs/haftungsausschluss.md"),
)
TITLE = "About Briefbote"
LICENCE = "Briefbote is free software (AGPL-3.0) by encircle360 GmbH and all contributors."
DISCLAIMER = "No warranty. Briefbote is no substitute for legal or tax advice."
SERVICES_TEXT = "Introduction, Operation and Support: {0}"
TEXTS = (TITLE, LICENCE, DISCLAIMER, SERVICES_TEXT, *(label for label, _url in LINKS))


def _link(text: str, url: str) -> str:
	return f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer">{escape(text)}</a>'


def render(translate: Callable[[str], str], version: str = __version__) -> str:
	"""The block in the language of translate, with the colours of the desk and wrapping on a narrow screen."""
	links = "".join(
		f'<li class="list-inline-item">{_link(translate(label), url)}</li>' for label, url in LINKS
	)
	services = escape(translate(SERVICES_TEXT)).replace("{0}", _link("encircle360.com", SERVICES))
	return (
		f'<section class="briefbote-about" aria-label="{escape(translate(TITLE))}" style="display: flex; '
		"flex-wrap: wrap; align-items: flex-start; gap: var(--padding-md, 1rem); padding: var(--padding-md, 1rem); "
		"border: 1px solid var(--border-color); border-radius: var(--border-radius-md, 0.5rem); "
		'background: var(--card-bg); color: var(--text-color);">'
		f'<img src="{LOGO}" alt="" width="40" height="40" style="flex: none;">'
		'<div style="flex: 1 1 16rem; min-width: 0;">'
		f'<div style="font-weight: 600;">Briefbote {escape(version)}</div>'
		f'<p class="text-muted" style="margin: 0.25rem 0 0;">{escape(translate(LICENCE))}</p>'
		f'<p class="text-muted" style="margin: 0 0 0.25rem;">{escape(translate(DISCLAIMER))}</p>'
		f'<ul class="list-inline" style="margin: 0 0 0.25rem;">{links}</ul>'
		f'<p class="text-muted" style="margin: 0;">{services}</p>'
		"</div></section>"
	)
