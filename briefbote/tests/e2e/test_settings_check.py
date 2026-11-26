"""The check of the Einstellungen Geschäftspost from their form: a user who sets up a company runs it with a button
and reads what is missing, in German (the fixture german of conftest.py), without the REST API."""

from urllib.parse import quote


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
