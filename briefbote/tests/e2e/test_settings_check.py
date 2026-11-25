"""The check of the Einstellungen Geschäftspost from their form: a user who sets up a company runs it with a button
and reads what is missing, in German, without the REST API."""

from collections.abc import Iterator
from urllib.parse import quote

import pytest

ADMINISTRATOR = "Administrator"


@pytest.fixture
def german(page) -> Iterator[None]:
	"""The desk in German for the user of the tests, as a German company runs it."""

	def language(value: str) -> None:
		answer = page.request.post(
			"/api/method/frappe.client.set_value",
			data={"doctype": "User", "name": ADMINISTRATOR, "fieldname": "language", "value": value},
		)
		assert answer.ok, answer.text()

	before = page.request.get(f"/api/resource/User/{ADMINISTRATOR}").json()["data"].get("language") or ""
	language("de")
	yield
	language(before)


def test_the_form_checks_the_settings_and_shows_what_is_missing(page, german):
	page.goto(f"/desk/business-document-settings/{quote('Kleinbetrieb Beispiel')}")
	button = page.get_by_role("button", name="Einstellungen prüfen")
	button.wait_for()
	button.click()
	dialog = page.locator(".modal.show")
	dialog.get_by_text("Kein Bankkonto gewählt").wait_for()
	assert dialog.get_by_text("Prüfung der Einstellungen").is_visible()


def test_a_company_with_an_account_hears_nothing_of_a_missing_one(page, german):
	page.goto(f"/desk/business-document-settings/{quote('Beispiel GmbH')}")
	page.get_by_role("button", name="Einstellungen prüfen").click()
	page.locator(".modal.show").get_by_text("Prüfung der Einstellungen").wait_for()
	assert "Kein Bankkonto gewählt" not in page.locator(".modal.show").inner_text()
