# Mitwirken an Briefbote

Issues und Pull Requests sind willkommen. Briefbote ist eine Frappe-App für ERPNext mit Druckformaten für die Geschäftsdokumente deutscher Unternehmen nach DIN 5008. Diese Seite beschreibt, wie ein Beitrag abläuft und welche Regeln gelten. Die Regeln gelten für Menschen und für Coding-Agenten gleichermaßen, siehe [AGENTS.md](AGENTS.md).

## Fehler und Wünsche melden

Bitte ein [Issue über die Vorlagen](https://github.com/encircle360-oss/briefbote/issues/new/choose) anlegen. Vorher lohnt ein Blick in die [Roadmap](docs/roadmap.md) und die offenen Issues. Fragen und fachlicher Austausch gehen in die [Discussions](https://github.com/encircle360-oss/briefbote/discussions) oder auf [Matrix](https://matrix.to/#/#oss:encircle360.com).

**Keine echten Rechnungen, Kunden- oder Lieferantendaten, Bankverbindungen, Steuernummern oder Zugangsdaten** in Issues, Screenshots, PDFs, Logs oder Pull Requests. Ein Druckbild zeigt man mit erfundenen Daten, etwa mit den Belegen des Nachweises der CI. Sicherheitslücken bitte nicht öffentlich melden, sondern wie in [SECURITY.md](SECURITY.md) beschrieben.

## Ein Pull Request

1. **Fork und Branch.** Branches heißen nach dem Thema, etwa `mahnung-verzugszinsen`.
2. **Test zuerst.** Jede Änderung beginnt mit einem Test, der ohne sie fehlschlägt. Kein bestehender Test wird abgeschwächt oder gelöscht, um grün zu werden. Die Kerne haben 100 % Testabdeckung, und das bleibt so.
3. **Quelle nennen.** Jede rechtliche oder normative Regel (Pflichtangabe, Steuerhinweis, Wortlaut, Maß nach DIN 5008) braucht eine Quelle: Gesetz, Verordnung, Umsatzsteuer-Anwendungserlass, BMF-Schreiben, Norm. Die Quelle steht im Code und auf der Seite des Druckformats unter `docs/`, nicht nur im Pull Request.
4. **Ein Thema pro Pull Request**, Dokumentation im selben Pull Request. Kleine Schritte sind leichter zu prüfen.
5. **Lokal prüfen:** `pre-commit run --all-files` und `pytest`. Wer Frappe-Teile oder ein Druckformat ändert, lässt zusätzlich die Tests der Site und den Nachweis der Ausdrucke laufen, siehe [Entwicklung](docs/entwicklung.md).
6. **Pull Request stellen.** Die Vorlage fragt nach Änderung, Quelle und Checkliste. Die CI muss grün sein; bei einem Druckformat gehört ein Blick auf die Seiten im Artefakt `printouts` dazu.
7. **Review.** Pflichtangaben und Steuerhinweise werden erst gemergt, wenn ein Mensch mit Fachkenntnis sie geprüft hat. Rückfragen im Review sind normal und kein Urteil über den Beitrag.

## Regeln im Code

- **Nur die aktuelle Hauptversion** von Frappe und ERPNext (derzeit 16). Keine Kompatibilitätsschichten für ältere Versionen.
- **Nichts aus dem Netz.** Ein Druckformat lädt keine Schrift, kein Bild, kein Stylesheet und kein Skript, auch nicht von der eigenen Site, und druckt mit beiden PDF-Generatoren von Frappe gleich.
- **Nichts für ein Unternehmen fest im Code.** Was ein Druckformat druckt, kommt aus dem Beleg, den Stammdaten oder den Einstellungen Geschäftspost.
- **Englisch im Code**, deutsch in der Dokumentation und auf den Ausdrucken. Fachbegriffe ohne gute Übersetzung bleiben deutsch: Rechnungskorrektur, Gutschrift, Leistungszeitraum, Steuerschuldnerschaft. Die Texte der Ausdrucke stehen englisch im Code und deutsch in `briefbote/translations/de.csv`; ein Dokument druckt in seiner Sprache.
- **Kommentare erklären das Warum**, nie das Was und nie die Geschichte einer Änderung. Eine bessere Benennung schlägt einen Kommentar.
- **Keine neuen Abhängigkeiten ohne Grund.** Was dazukommt, wird exakt gepinnt und im Pull Request begründet.
- **Kein fremder Code.** Andere Projekte dürfen inspirieren; Briefbote wird eigenständig für ERPNext geschrieben.
- **Stil:** `ruff` mit der Konfiguration in `pyproject.toml` (Tabs, 110 Zeichen, doppelte Anführungszeichen), wie im Frappe-Ökosystem üblich.

## Commits

Commit-Nachrichten sind englisch, im Imperativ, klein geschrieben und vervollständigen den Satz „If applied, this commit will …“: `print the service period of each position`, `keep the totals with the last position`. Keine Ticket-Präfixe, keine Fußzeilen. Eine Nachricht beschreibt, was sich ändert und warum, wenn das Warum nicht offensichtlich ist.

## Umgangston

Wir gehen respektvoll miteinander um, nehmen Kritik an der Sache an und nicht persönlich, und gehen davon aus, dass alle ihr Bestes geben. Wer das nicht einhält, wird von den Maintainern angesprochen und notfalls ausgeschlossen.

## Lizenz der Beiträge

Mit deinem Beitrag stimmst du zu, dass er unter der [AGPL-3.0-or-later](LICENSE) veröffentlicht wird, und bestätigst, dass du das Recht hast, ihn unter dieser Lizenz beizusteuern.
