# Entwicklung

Diese Seite beschreibt Einrichtung, Tests, den Nachweis der Ausdrucke, wie ein Druckformat dazukommt, Stil und CI. Wie ein Beitrag abläuft, steht in [CONTRIBUTING.md](../CONTRIBUTING.md), wie die Teile zusammenspielen, in der [Architektur](architektur.md).

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

   `requirements-dev.txt` bringt coverage, fonttools (nur für `scripts/build_fonts.py`), pre-commit, pytest, pytest-cov, ruff und zizmor in festen Versionen. Der Hook `no-commit-to-branch` verhindert Commits direkt auf `main`.

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

### Ausdrucke als PDF

Die Vorschau im Browser zeigt keine Seitenumbrüche. Deshalb druckt der Job „Frappe site“ zum Schluss jedes Druckformat als PDF, so wie eine Site es druckt, mit beiden PDF-Generatoren, die Frappe anbietet: wkhtmltopdf 0.12.6.1 mit gepatchtem Qt aus den Paketen des wkhtmltopdf-Projekts, dessen SHA-256-Summe der Job prüft, und dem Generator auf Chromium-Basis mit dem Chrome des Runners. Die Adresse der Site zeigt dabei auf einen Host, den es nicht gibt: Ein Druckformat darf nichts nachladen. wkhtmltopdf bekommt das HTML ohne den Verweis auf Frappes Druckpaket, den Frappe jedem Druckformat beifügt; jede andere Adresse im HTML, die keine Data-URL ist, lässt den Ausdruck scheitern.

- `briefbote/tests/print_documents.py` schreibt die Belege des Nachweises in die Testsite: zwei erfundene Unternehmen (eine GmbH mit Logo, Form B, Register- und Bankangaben und je Steuerfall einer Vorlage; ein Kleinunternehmer mit Form A ohne Logo), Kunden im Inland, in Österreich und in den USA, eine Privatperson und Rechnungen, die das Layout und jeden Fall fordern: eine Position, 40 Positionen mit langen Beschreibungen und zwei Steuersätzen, ein sehr langer Kundenname mit zweiter Anschriftzeile im Ausland, jeder Steuerfall, Rechnungskorrektur, Stornorechnung, kaufmännische Gutschrift, Verbraucher mit Skonto, Kleinunternehmer, eine Rechnung mit einer steuerfreien Position neben besteuerten; dazu Lieferanten, Vorlagen für Einkaufssteuern und vier Eingangsrechnungen, die als Gutschrift drucken: im Inland steuerpflichtig, nach § 13b UStG, vom Kleinunternehmer und eine Korrektur.
- `briefbote/tests/print_proof.py` druckt jede Rechnung mit „Rechnung“ und jede Gutschrift mit „Gutschrift“ auf Deutsch mit beiden Generatoren, auf leerem Papier und, für die ersten beiden, auf vorgedrucktem Briefpapier, liest die Wörter jeder Seite mit `pdftotext -bbox` von Poppler und prüft sie mit `briefbote/proof/pages.py`: die Zahl der Seiten, „Seite n von N“ und die Nummer des Belegs auf jeder Seite, kein Wort über den Rand, keine zwei Wörter übereinander, keine letzte Seite mit weniger als sechs Zeilen, der Tabellenkopf auf jeder Seite bis zu den Summen, die letzte Position auf der Seite der Summen, jeder Block, der nicht brechen darf, ganz auf einer Seite (die Summen einer Rechnung oder Gutschrift vom Nettobetrag bis zum Gesamtbetrag, die Zusammenfassung des Leistungsnachweises mit jeder Zeile je Projekt und je Person), die Pflichtangaben und Hinweise des Falls im Ausdruck, kein englisches Wort, das eine fehlende Übersetzung druckt, kein „№“, das eine Ligatur für „Nr.“ druckt, nur die Schrift Inter (pdffonts), die Anschrift im Rechteck der Anschriftzone und die Rücksendeangabe in der Vermerkzone nach DIN 5008, gerechnet aus den Positionen der Wörter.

Hat ein Ausdruck ein Problem, wird der Job rot. Das Artefakt `printouts` hält nach jedem Lauf die PDFs, das HTML, das jeder Generator bekam, die Wörter der Seiten und `report.md` mit Seiten und Problemen jedes Ausdrucks. Was die Prüfungen nicht sehen, zeigt der Blick auf die Seiten: Wer ein Druckformat ändert, lädt das Artefakt herunter und sieht sich jede Seite an. Lokal, gegen eine Bench mit wkhtmltopdf, Chrome und Poppler:

```bash
bench --site <site> execute briefbote.tests.print_documents.run
bench --site <site> execute briefbote.tests.print_proof.run --kwargs "{'directory': '/tmp/ausdrucke'}"
```

### Beispiele im README

`briefbote/tests/print_examples.py` druckt aus den Fällen des Nachweises die Beispiele, die das README und die Seite jedes Druckformats zeigen: je Druckformat einen Beleg, dazu eine Rechnung als Entwurf, die zweite Seite einer langen Rechnung und eine englische Rechnung, mit dem Generator auf Chromium-Basis auf leerem Papier. Es schreibt `docs/beispiele/<name>.pdf` und die gezeigte Seite als `docs/bilder/beispiele/<name>.png` (115 dpi, 64 Farben) und vergleicht sie mit den Dateien im Repository: Zahl der Seiten, Wörter jeder Seite und das Bild, grob in Zellen von 8 Pixeln, denn das Chromium des Runners zeichnet die Kanten der Buchstaben nach jedem Update etwas anders. Der Schritt der CI schlägt fehl, wenn ein Beispiel fehlt oder abweicht; das Artefakt `beispiele` hat die neuen Dateien an ihren Pfaden im Repository und wird zum Aktualisieren in dessen Wurzel entpackt. Vorher jedes Bild in voller Größe ansehen.

## Ein Druckformat hinzufügen

1. **Katalog und Quelle:** Das Dokument steht im [Katalog](katalog.md). Eine Seite unter `docs/` nennt für jede Pflichtangabe und jeden Hinweis die Quelle, sagt, was strittig ist, und hat eine Prüfliste; die [Roadmap](roadmap.md#wann-ein-schritt-fertig-ist) sagt, wann das Format fertig ist.
2. **Kern zuerst:** Regeln des Dokuments, etwa die Stufen einer Mahnung oder die Zinsen, kommen als reines Python unter `briefbote/<dokument>/` mit Tests und 100 % Abdeckung; `testpaths` und `source` in `pyproject.toml` bekommen das Paket.
3. **Lesen:** Eine Jinja-Methode in `briefbote/briefbote/printing.py` (oder einem Modul daneben) liest Beleg und Stammdaten und gibt dem Format fertige Zeilen in der Sprache des Dokuments; sie steht in `jinja` in `hooks.py`. Jeder Text geht durch `t()` und steht in `de.csv` mit dem Kontext „Briefbote“.
4. **Format:** `briefbote/briefbote/print_format/<name>/<name>.json` und `.html`; das HTML setzt `letter` mit `briefbote_letter`, bindet `style.html`, `first_page.html` und `footer.html` ein und nutzt die Klassen des Stylesheets. Neue Bausteine kommen in das gemeinsame Stylesheet, nicht in das Format.
5. **Nachweis:** Belege für jeden Fall in `print_documents.py`, Erwartungen in `print_proof.py`; dann die Seiten im Artefakt ansehen.
6. **Beispiel:** ein Eintrag in `EXAMPLES` von `print_examples.py`, das Bild im README und oben auf der Seite des Formats; ein Test verlangt beides für jedes Format.

## Schriften

`scripts/build_fonts.py` baut `briefbote/public/fonts/Inter-Regular.ttf` und `Inter-SemiBold.ttf` aus dem Release Inter 4.1 (`Inter-4.1.zip` von github.com/rsms/inter, SHA-256 im Skript) und legt `OFL.txt` daneben; zweimal gebaut entstehen dieselben Dateien. Eine neue Version von Inter ist eine neue Summe im Skript und ein neuer Lauf.

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
| Tests | Frappe site (ERPNext v16) | baut mit `frappe-bench` 5.31.1 eine Bench mit Frappe und ERPNext `version-16`, MariaDB 11.8 und Redis als Dienste, installiert ERPNext und Briefbote auf einer Testsite und führt `bench run-tests --app briefbote` aus. Danach schreibt er die Belege des Nachweises, druckt jedes Druckformat mit beiden PDF-Generatoren und prüft die Seiten (siehe [Ausdrucke als PDF](#ausdrucke-als-pdf); Artefakt `printouts`). |
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
