"""Fixtures of the browser tests: Chromium and the desk of the Administrator on a site with the documents of
print_documents.py.

	pytest briefbote/tests/e2e --base-url http://localhost:8000 --output <directory>

The test modules import neither pytest nor Playwright, because bench run-tests imports every test_*.py of the app in
the environment of the bench, which has neither; they take what they need from these fixtures. A test fails when its
page saw a JavaScript error or a response with a status of 500 or more. The tests leave every PDF they check under
--output.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page, Playwright, StorageState, sync_playwright

TIMEOUT_MS = 60_000
FIRST_DESK_TIMEOUT_MS = 180_000
ADMINISTRATOR = "Administrator"


def pytest_addoption(parser: pytest.Parser) -> None:
	group = parser.getgroup("briefbote", "browser tests of Briefbote")
	group.addoption(
		"--base-url", default="http://localhost:8000", help="the site with the documents of the proof"
	)
	group.addoption("--admin-password", default="admin", help="the password of the Administrator of the site")
	group.addoption("--output", default="test-results", help="where the tests leave the PDFs they check")


@pytest.fixture(scope="session")
def base_url(pytestconfig: pytest.Config) -> str:
	return pytestconfig.getoption("base_url").rstrip("/")


@pytest.fixture(scope="session")
def output(pytestconfig: pytest.Config) -> Path:
	path = Path(pytestconfig.getoption("output"))
	path.mkdir(parents=True, exist_ok=True)
	return path


@pytest.fixture(scope="session")
def playwright() -> Iterator[Playwright]:
	with sync_playwright() as playwright:
		yield playwright


@pytest.fixture(scope="session")
def browser(playwright: Playwright) -> Iterator[Browser]:
	browser = playwright.chromium.launch()
	yield browser
	browser.close()


@pytest.fixture(scope="session")
def session(playwright: Playwright, base_url: str, pytestconfig: pytest.Config) -> StorageState:
	"""A session of the Administrator, whose desk the server has built once."""
	api = playwright.request.new_context(base_url=base_url)
	try:
		login = api.post(
			"/api/method/login", form={"usr": ADMINISTRATOR, "pwd": pytestconfig.getoption("admin_password")}
		)
		assert login.ok, login.text()
		assert api.get("/desk", timeout=FIRST_DESK_TIMEOUT_MS).ok
		return api.storage_state()
	finally:
		api.dispose()


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> pytest.TestReport:
	"""Keep the report of each phase on the test, so that the fixture page can leave a screenshot of a failure."""
	report = yield
	setattr(item, f"report_{report.when}", report)
	return report


@pytest.fixture
def page(
	browser: Browser, base_url: str, session: StorageState, output: Path, request: pytest.FixtureRequest
) -> Iterator[Page]:
	context = browser.new_context(
		base_url=base_url, storage_state=session, viewport={"width": 1440, "height": 900}, locale="de-DE"
	)
	context.set_default_timeout(TIMEOUT_MS)
	page = context.new_page()
	problems: list[str] = []
	page.on("pageerror", lambda error: problems.append(f"JavaScript error: {error}"))
	page.on(
		"response",
		lambda response: (
			problems.append(f"HTTP {response.status}: {response.url}") if response.status >= 500 else None
		),
	)
	try:
		yield page
		failed = getattr(request.node, "report_call", None)
		if failed is not None and failed.failed:
			page.screenshot(path=output / f"{request.node.name}.png", full_page=True)
		assert not problems, "the browser saw errors:\n" + "\n".join(problems)
	finally:
		context.close()


@pytest.fixture
def german(page: Page) -> Iterator[None]:
	"""The desk in German for the user of the tests, as a German company runs it, set through the desk itself so that
	the request carries its token."""
	page.goto("/desk/user", wait_until="domcontentloaded")
	page.wait_for_function("() => window.frappe && frappe.xcall && frappe.session && frappe.session.user")

	def language(value: str) -> None:
		page.evaluate(
			"(value) => frappe.xcall('frappe.client.set_value', "
			"{doctype: 'User', name: frappe.session.user, fieldname: 'language', value})",
			value,
		)

	before = page.evaluate(
		"() => frappe.xcall('frappe.client.get_value', "
		"{doctype: 'User', filters: frappe.session.user, fieldname: 'language'}).then((row) => row.language || '')"
	)
	language("de")
	yield
	page.goto("/desk/user", wait_until="domcontentloaded")
	page.wait_for_function("() => window.frappe && frappe.xcall")
	language(before)
