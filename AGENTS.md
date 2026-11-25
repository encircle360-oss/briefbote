# Hinweise für Coding-Agenten

Der Einsatz von KI-Werkzeugen und Coding-Agenten ist in diesem Projekt ausdrücklich erlaubt, für Maintainer wie für Mitwirkende. Verantwortlich bleibt immer der Mensch, der den Pull Request stellt und die Änderung versteht. Diese Datei ist der Einstieg. Die Regeln stehen in [CONTRIBUTING.md](CONTRIBUTING.md) und [docs/entwicklung.md](docs/entwicklung.md) und gelten für Menschen und Agenten gleichermaßen.

## Was ein Agent wissen muss

- **Projekt:** Frappe-App für ERPNext, nur die aktuelle Hauptversion (derzeit 16), Python 3.14, Tabs, `ruff`. Briefbote druckt die Geschäftsdokumente deutscher Unternehmen nach DIN 5008: Ziel ist jedes Dokument, das ein Unternehmen aus ERPNext druckt oder versendet; was es heute gibt und was als Nächstes kommt, steht in der [Roadmap](docs/roadmap.md).
- **Struktur:** Wie die Teile zusammenspielen, beschreibt [docs/architektur.md](docs/architektur.md).
- **Sprache:** Code, Kommentare und Commits englisch, Fachbegriffe deutsch (Rechnungskorrektur, Gutschrift, Leistungszeitraum, Steuerschuldnerschaft, Pflichtangabe). Dokumentation, Issues und Pull Requests deutsch. Die Texte der Ausdrucke stehen englisch im Code und deutsch in `briefbote/translations/de.csv`, damit ein Dokument in seiner Sprache druckt. Commits im Imperativ, klein geschrieben, ohne Präfixe und Fußzeilen ([Commits](CONTRIBUTING.md#commits)).
- **Quellen:** Jede Pflichtangabe, jeder Hinweis und jedes Maß hat eine Quelle: Gesetz (UStG, UStDV, HGB, GmbHG, AktG, BGB), Umsatzsteuer-Anwendungserlass, BMF-Schreiben, DIN 5008. Die Quelle steht im Code und auf der Seite des Druckformats unter `docs/`. Was dort nicht steht, wird nicht aus dem Gedächtnis ergänzt, sondern nachgeschlagen. Wie ERPNext sich verhält, wird im Code von ERPNext 16 nachgesehen, nicht vermutet.

## Leitplanken

1. **Test zuerst, sichtbar in der Historie.** Erst ein Commit mit dem Test, der fehlschlägt, dann der Commit, der ihn grün macht. Kein Test wird abgeschwächt, übersprungen oder gelöscht, um grün zu werden. Die Kerne haben 100 % Abdeckung, und das bleibt so.
2. **Quelle im Code.** Jede rechtliche oder normative Regel nennt ihre Quelle.
3. **Nichts aus dem Netz.** Ein Druckformat lädt nichts nach, auch nicht über die Adresse der eigenen Site, und druckt mit wkhtmltopdf und mit dem Generator auf Chromium-Basis gleich. Der Nachweis der Ausdrucke in der CI prüft beides.
4. **Nichts fest für ein Unternehmen.** Was ein Ausdruck zeigt, kommt aus Beleg, Stammdaten oder den Einstellungen Geschäftspost. Kein Name, keine Anschrift, keine Bankverbindung im Code.
5. **Kein Hinweis auf die Software auf dem Papier.** Ein Geschäftsdokument trägt keinen Vermerk über Briefbote; „Über Briefbote“ steht nur im Desk.
6. **Keine echten Daten.** Keine echten Firmen, Anschriften, Bankverbindungen, Steuernummern oder USt-IdNrn. in Code, Tests, Fixtures, Logs, Issues oder Commits. Testdaten sind erfunden: „Beispiel GmbH“, erfundene Anschriften, formal gültige, aber erkennbar erfundene IBANs und USt-IdNrn.
7. **Ein Pull Request, ein Thema.** Dokumentation im selben Pull Request. Kleine Schritte.
8. **Sehen, nicht nur prüfen.** Wer ein Druckformat ändert, lädt das Artefakt `printouts` des Laufs herunter und sieht sich jede Seite an. Die automatischen Prüfungen finden vieles, aber nicht alles.
9. **Alles im Menü, mit Symbol.** Jeder DocType, der keine Tabelle ist, steht in der Seitenleiste; jeder Eintrag außerhalb einer Gruppe und jede Gruppe trägt ein Symbol, das der Desk hat.
10. **Nichts Ungeprüftes nach `main`.** Ein Mensch mit Fachkenntnis prüft Pflichtangaben und Steuerhinweise vor dem Merge. Die CI muss grün sein.
11. **Keine neuen Abhängigkeiten ohne Grund.** Was dazukommt, wird exakt gepinnt und begründet. Briefbote setzt nur ERPNext voraus; andere Apps wie Steuerbote, erpnext_germany oder eu_einvoice nutzt es, wenn sie da sind, und braucht sie nie.
12. **Nichts Fremdes übernehmen oder nennen.** Andere Projekte dürfen inspirieren. Code wird eigenständig für ERPNext geschrieben; genannt wird nur, was Briefbote nutzt, ergänzt oder als Quelle zitiert, kein anderes Produkt, Projekt oder Netzwerk.
13. **Kein Vermerk über KI.** Code, Dokumentation, Commits und Pull Requests nennen keine KI-Werkzeuge, Coding-Agenten oder Assistenten, die an einem Beitrag mitgearbeitet haben, auch nicht in Fußzeilen.
14. **Prüfen, was sicher prüfbar ist:** `pre-commit run --all-files`, `pytest --cov`, bei Frappe-Änderungen `bench --site <site> run-tests --app briefbote` und der Nachweis der Ausdrucke (siehe [Entwicklung](docs/entwicklung.md)).
