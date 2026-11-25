# Entwicklung

Diese Seite beschreibt Einrichtung, Tests, Stil und CI. Wie ein Beitrag abläuft, steht in [CONTRIBUTING.md](../CONTRIBUTING.md), wie die Teile zusammenspielen, in der [Architektur](architektur.md).

## Einrichtung

Du brauchst Python 3.14 und eine Bench mit Frappe und ERPNext 16, dazu eine Site, auf der ERPNext installiert ist.

1. Klone deinen Fork und hol die App in die Bench:

   ```bash
   git clone https://github.com/<dein-konto>/briefbote.git ~/src/briefbote
   cd $PATH_TO_YOUR_BENCH
   bench get-app --soft-link ~/src/briefbote
   bench --site <site> install-app briefbote
   ```

   Mit `--soft-link` verlinkt bench den Checkout nach `apps/briefbote`. Änderungen im Checkout gelten damit sofort in der Bench.

2. Installiere die Entwicklungswerkzeuge im Checkout und richte die Git-Hooks ein:

   ```bash
   cd ~/src/briefbote
   python3.14 -m venv .venv
   . .venv/bin/activate
   pip install -r requirements-dev.txt
   pre-commit install
   ```

   `requirements-dev.txt` bringt coverage, pre-commit, pytest, pytest-cov, ruff und zizmor in festen Versionen. Der Hook `no-commit-to-branch` verhindert Commits direkt auf `main`.

## Tests

### Kern ohne Bench

```bash
pytest          # nur die reinen Module ohne Frappe
pytest --cov    # mit Abdeckung, wie in der CI
```

`pytest` sammelt nur die Tests, die ohne Frappe laufen (`testpaths` in `pyproject.toml`), und braucht weder Frappe noch eine Bench. `pytest --cov` misst dazu die Abdeckung der Kerne (`source` in `pyproject.toml`), Zeilen und Zweige. Unter 100 % schlägt der Lauf fehl.

### Frappe-Tests

Auf einer eigenen Testsite mit ERPNext und Briefbote, nie auf einer Site mit echten Daten:

```bash
bench --site <site> set-config allow_tests true
bench --site <site> run-tests --app briefbote
```

## Testgetrieben arbeiten

1. **Rot:** Schreib zuerst einen Test, der ohne die Änderung fehlschlägt, und sieh ihn fehlschlagen.
2. **Grün:** Schreib die kleinste Änderung, die ihn bestehen lässt.
3. **Aufräumen:** Verbessere Namen und Struktur, während alle Tests grün bleiben.

Kein bestehender Test wird abgeschwächt oder gelöscht, um grün zu werden. Testdaten sind erfunden. Testnamen beschreiben die Regel, etwa `test_names_the_invoice_a_correction_corrects`.

## Stil

- **ruff** mit der Konfiguration in `pyproject.toml`: Einrückung mit Tabs, Zeilen bis 110 Zeichen, doppelte Anführungszeichen, Python 3.14 als Ziel.
- **Regelgruppen:** F, E und W, I, UP, B, RUF, S, SIM, C4, T20. Ausgenommen sind E101 und W191 wegen der Tabs und E501, weil die Zeilenlänge der Formatierer setzt. In Tests ist `assert` erlaubt (S101).
- **pre-commit** führt `ruff check --fix` und `ruff format` aus. Außerdem prüft es Leerzeichen am Zeilenende (außer in Markdown), den Zeilenumbruch am Dateiende, Merge-Konflikte, Python-Syntax, JSON, TOML und YAML, große Dateien, vergessene Debug-Anweisungen und private Schlüssel, dazu die Workflows mit zizmor.
- **Englisch im Code**, auch in Kommentaren und Docstrings, deutsche Fachbegriffe, wo die Übersetzung fehlt.
- **Kommentare erklären das Warum**, nie das Was und nie die Geschichte einer Änderung.
- **Dokumentation auf Deutsch**, kurz und sachlich.

## CI

Alle drei Workflows laufen bei Pull Requests, bei Pushes auf `main` und von Hand, Security zusätzlich jeden Montag um 04:17 UTC. Sie lesen den Inhalt des Repositories nur (`contents: read`), lediglich CodeQL darf zusätzlich Sicherheitsbefunde schreiben. Ausgecheckt wird ohne gespeicherte Zugangsdaten (`persist-credentials: false`). Ein Pull Request wird erst gemergt, wenn alle Prüfungen grün sind.

| Workflow | Job | Was er tut |
|---|---|---|
| Tests | Core (without bench) | pytest mit Abdeckung auf Python 3.14, unter 100 % rot; legt `coverage.xml` als Artefakt ab. |
| Tests | Frappe site (ERPNext v16) | baut mit `frappe-bench` 5.31.1 eine Bench mit Frappe und ERPNext `version-16`, MariaDB 11.8 und Redis als Dienste, installiert ERPNext und Briefbote auf einer Testsite und führt `bench run-tests --app briefbote` aus. |
| Linters | pre-commit | alle Hooks auf allen Dateien, ohne `no-commit-to-branch`. |
| Linters | Frappe semgrep rules | semgrep 1.185.0 mit den Regeln aus `frappe/semgrep-rules` und `python/lang/correctness` aus `semgrep/semgrep-rules`, beide auf einen Commit gepinnt. |
| Security | Secret scan (gitleaks) | durchsucht die ganze Git-Historie nach Geheimnissen; gitleaks wird mit Prüfsumme geladen. |
| Security | Workflow audit (zizmor) | prüft die GitHub-Actions-Workflows auf Sicherheitsprobleme. |
| Security | Dependency audit (pip-audit) | prüft die Pakete aus `requirements-dev.txt` auf bekannte Schwachstellen. |
| Security | CodeQL | statische Analyse des Python-Codes, solange das Repository öffentlich ist. |

## Versionen

- **Frappe und ERPNext:** nur die aktuelle Hauptversion, derzeit 16 (`[tool.bench.frappe-dependencies]` in `pyproject.toml`, `required_apps` in `hooks.py`, `version-16` in der CI). Ältere Hauptversionen werden nicht unterstützt.
- **Python:** 3.14.
- **Entwicklungswerkzeuge** sind in `requirements-dev.txt` exakt gepinnt, die pre-commit-Hooks über `rev`, semgrep, pip-audit, frappe-bench, gitleaks und zizmor in den Workflows, jede Action und jedes andere Repository auf einen Commit; `briefbote/tests/test_workflows.py` prüft das. Dependabot meldet jede Woche neue Versionen für pip und GitHub Actions.

## Commits

- Commit-Nachrichten sind englisch, im Imperativ, klein geschrieben und vervollständigen den Satz „If applied, this commit will …“.
- Keine Ticket-Präfixe, keine Fußzeilen (Trailer).
- Branches heißen nach dem Thema. Auf `main` wird nicht direkt committet.
- Ein Thema pro Pull Request, die Dokumentation im selben Pull Request.
