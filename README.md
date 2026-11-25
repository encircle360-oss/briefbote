# <img src="briefbote/public/images/briefbote-logo.svg" alt="" width="32" height="32"> Briefbote

Druckformate für alle Geschäftsdokumente deutscher Unternehmen in ERPNext, nach DIN 5008 und mit den Angaben, die das Gesetz verlangt: vom Angebot über Auftragsbestätigung, Lieferschein, Rechnung, Rechnungskorrektur, Gutschrift, Zahlungserinnerung und Mahnung bis zur Anfrage und Bestellung, dazu Leistungsnachweise, Kontoauszüge, Belege und der freie Geschäftsbrief. Ziel ist alles, was ein deutsches Unternehmen aus ERPNext druckt oder versendet, in einem Gestaltungssystem: Briefe mit Anschriftfeld für den Fensterumschlag, Informationsblock und Pflichtangaben im Fuß, und Listen mit Positionstabellen über viele Seiten.

> **Status: in Entwicklung, noch nicht einsatzfähig.** Version 0.1.1 bringt die Druckformate [Rechnung](docs/rechnung.md) (Rechnung, Rechnungskorrektur, Stornorechnung und kaufmännische Gutschrift aus der Ausgangsrechnung), [Gutschrift](docs/gutschrift.md) (Gutschrift im Gutschriftsverfahren aus der Eingangsrechnung) und [Leistungsnachweis](docs/leistungsnachweis.md) (die Stunden einer Rechnung aus ihren Stundenzetteln), das Gestaltungssystem nach DIN 5008 mit der Gestaltung je Unternehmen und die Einrichtung ohne Oberfläche. „Drucken“ in der Druckansicht druckt dasselbe PDF wie „PDF“; Entwürfe und stornierte Belege tragen auf jeder Seite ihr Wasserzeichen, und ein Beleg, dem eine Pflichtangabe fehlt, sagt oben, was fehlt. Die Wortlaute der Pflichthinweise warten auf die Prüfung durch eine Steuerberatung (siehe „Offen für die fachliche Prüfung“ in der Dokumentation [Rechnung](docs/rechnung.md#offen-für-die-fachliche-prüfung)). Die übrigen Dokumente folgen in der Reihenfolge der [Roadmap](docs/roadmap.md); welche es geben soll, zählt der [Katalog](docs/katalog.md) auf.

## Was Briefbote macht

- **Ein Gestaltungssystem für alle Dokumente.** Ein Stylesheet und ein Satz Bausteine für Briefe nach DIN 5008, Form A und Form B, mit Anschriftfeld, Informationsblock, Betreff, Falz- und Lochmarken, und für Dokumente mit Positionstabellen, deren Kopf auf jeder Seite wiederkehrt, Summen, die bei ihrer Tabelle bleiben, Anlagen und „Seite n von N“.
- **Die Angaben, die das Gesetz verlangt.** Jedes Druckformat druckt die Pflichtangaben seines Dokuments, für die Rechnung die des § 14 Abs. 4 UStG mit den Hinweisen des § 14a UStG, und im Fuß jedes Briefs die Angaben zum Unternehmen nach § 35a GmbHG, § 37a HGB oder § 80 AktG. Jede Regel steht mit Quelle auf der Seite ihres Druckformats.
- **Mit und ohne Briefpapier.** Auf leeres Papier druckt Briefbote Kopf und Fuß selbst, auf vorgedrucktes Briefpapier nur den Inhalt an die Stellen der Norm.
- **Deutsch und Englisch.** Ein Dokument druckt in seiner Sprache, die Hinweise im Wortlaut, den das Gesetz vorgibt.
- **Nichts fest im Code, nichts aus dem Netz.** Was gedruckt wird, kommt aus dem Beleg, den Stammdaten und den Einstellungen Geschäftspost je Unternehmen. Ein Druckformat lädt nichts nach und druckt mit beiden PDF-Generatoren von Frappe gleich.
- **Bewiesen auf Papier.** Die CI druckt jedes Format mit beiden PDF-Generatoren für Belege, die das Layout fordern, und prüft jede Seite: Seitenzahlen, Ränder, nichts übereinander, Tabellenkopf wiederholt, Summen bei ihrer Tabelle, Pflichtangaben vorhanden, Anschrift im Fenster.

## Voraussetzungen

- Frappe und ERPNext ab Version 16. Unterstützt wird nur die jeweils aktuelle Hauptversion.
- Python 3.14.

## Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/encircle360-oss/briefbote
bench --site <site> install-app briefbote
```

Danach steht in der Leiste von ERPNext „Geschäftspost“ mit den Einstellungen je Unternehmen. Die Druckformate „Rechnung“, „Leistungsnachweis“ (Ausgangsrechnung), „Gutschrift“ (Eingangsrechnung), „Angebot“ (Angebot), „Auftragsbestätigung“ (Kundenauftrag) „Lieferschein“ (Lieferschein) „Mahnung“ (Mahnung), „Zahlungsbestätigung“ und „Quittung“ (Zahlungseingang) sowie „Bestellung“ (Bestellung) stehen zur Wahl; zum Standard macht sie erst, wer es einstellt. Wie das ohne Oberfläche geht, mit Steuerfällen nach Regel und der Prüfung, was einem Unternehmen fehlt, steht unter [Einrichtung](docs/einrichtung.md).

## Zusammenspiel

Briefbote setzt nur ERPNext voraus und ergänzt, was andere Apps für deutsche Unternehmen schon tun:

- **[Steuerbote](https://github.com/encircle360-oss/steuerbote)** meldet die Steuern an ELSTER. Beide Apps kommen von denselben Maintainern und folgen denselben Regeln; die Rechnungen, die Briefbote druckt, sind die Belege, aus denen Steuerbote meldet.
- **[erpnext_germanized](https://github.com/encircle360-oss/erpnext_germanized)** ist ein fertiges Container-Image mit ERPNext 16 und den gängigen deutschen Apps. Briefbote ist seit der Version 16.60.0-16 des Images darin enthalten.
- **E-Rechnung:** Die elektronische Rechnung (XRechnung, ZUGFeRD) erzeugt eine eigene App wie eu_einvoice; sie bettet ihr XML auch in das PDF eines Druckformats von Briefbote ein. Briefbote gestaltet das Dokument, das ein Mensch liest.
- **erpnext_germany:** Registerangaben des Unternehmens und den Grund einer Steuerbefreiung nimmt Briefbote von dort, wenn die App installiert ist. Was die Apps im Einzelnen tun, steht in der [Architektur](docs/architektur.md#zusammenspiel-mit-anderen-apps).

## Dokumentation

- [Katalog](docs/katalog.md): jedes Geschäftsdokument mit DocType, Stand in ERPNext, Anforderungen und Priorität
- [Roadmap](docs/roadmap.md): was es gibt, was als Nächstes kommt und wann ein Druckformat fertig ist
- [Einrichtung](docs/einrichtung.md): Einstellungen Geschäftspost, Druckformat wählen, was die Rechnung aus dem Beleg liest
- [Rechnung](docs/rechnung.md): Rechnung, Rechnungskorrektur, Stornorechnung und kaufmännische Gutschrift mit Pflichtangaben, Steuerfällen, Leistungsdatum und Quellen
- [Leistungsnachweis](docs/leistungsnachweis.md): die Stunden einer Rechnung aus ihren Stundenzetteln als Anlage oder eigenes Dokument, wie ERPNext Zeit und Rechnung verbindet und was eine fremde Zeiterfassung füllen muss
- [Angebot](docs/angebot.md): das Angebot mit Gültigkeit, Alternativen, Preisen je Einheit, Umsatzsteuer nach Satz und Annahme
- [Auftragsbestätigung](docs/auftragsbestaetigung.md): die Auftragsbestätigung mit Angebot, Bestellung des Kunden, Lieferterminen und Zahlungsbedingungen
- [Lieferschein](docs/lieferschein.md): der Lieferschein an die Lieferanschrift mit Lieferdatum, Seriennummern und Chargen, Preisen und Empfangsbestätigung nach den Einstellungen
- [Zahlungserinnerung und Mahnung](docs/mahnung.md): Mahnstufen, Verzug, Verzugszinsen und Pauschale nur, wo sie rechtmäßig sind, Basiszinssätze in den Einstellungen
- [Zahlungsbestätigung und Quittung](docs/zahlungsbestaetigung.md): der gebuchte Zahlungseingang eines Kunden mit den Belegen, auf die er angerechnet ist, als Bestätigung oder Quittung nach § 368 BGB
- [Bestellung](docs/bestellung.md): die Bestellung beim Lieferanten mit Lieferterminen, Lieferanschrift und der Umsatzsteuer des Lieferanten
- [Gutschrift](docs/gutschrift.md): die Gutschrift im Gutschriftsverfahren aus der Eingangsrechnung mit Pflichtangaben, Steuerfällen im Einkauf und Quellen
- [Geschäftsbrief](docs/geschaeftsbrief.md): Angaben zum Unternehmen nach Rechtsform, Fuß, Rücksendeangabe und Anschrift
- [DIN 5008](docs/din-5008.md): die Maße des Briefs und ihre Quellen
- [Architektur](docs/architektur.md): Kerne und Frappe-Schicht, Gestaltungssystem, die beiden PDF-Generatoren, Schrift, Zusammenspiel mit anderen Apps
- [Entwicklung](docs/entwicklung.md): Einrichtung, Tests, Nachweis der Ausdrucke, ein Druckformat hinzufügen, Stil und CI
- [Haftungsausschluss](docs/haftungsausschluss.md): ohne Gewähr, keine Rechts- oder Steuerberatung, Verantwortung für jedes Dokument
- [Mitwirken](CONTRIBUTING.md), [Hinweise für Coding-Agenten](AGENTS.md), [Sicherheit](SECURITY.md)

## Mitwirken und Community

### Beiträge sind willkommen

Briefbote lebt davon, dass Menschen mit unterschiedlichen Branchen, Dokumenten und Steuerfällen mitmachen. Du kannst

- **Maintainer werden**, für ein Dokument oder das ganze Projekt,
- **Pull Requests** für Fehlerbehebungen, Druckformate und Dokumentation stellen,
- **testen**, besonders mit anderen Steuerfällen, Sprachen und Briefpapieren als unseren,
- **Dokumentation und Beispiele** verbessern,
- **Fehler melden** oder Dokumente vorschlagen.

Jeder Beitrag zählt. Du musst kein Steuerprofi sein, wir helfen beim Einstieg.

### So geht es

1. Repository forken und einen Branch anlegen
2. Änderung samt Tests schreiben (Test zuerst, siehe [Mitwirken](CONTRIBUTING.md))
3. Lokal prüfen: `pre-commit run --all-files` und `pytest`
4. Pull Request mit kurzer Beschreibung und Quelle der fachlichen Regel stellen
5. Review gemeinsam durchgehen, bis es passt

### Maintainer werden

Wer dauerhaft Verantwortung übernehmen möchte, zeigt das am einfachsten durch Pull Requests und Hilfe in Issues und Discussions und schreibt dann an **oss@encircle360.com**. Ein Dokument reicht, es muss nicht das ganze Projekt sein.

## Support und professionelle Dienstleistungen

### Community-Support

- **Matrix:** [#oss:encircle360.com](https://matrix.to/#/#oss:encircle360.com) für den direkten Austausch mit Maintainern und Nutzern
- **Issues:** [Fehler und Wünsche zu Briefbote](https://github.com/encircle360-oss/briefbote/issues)
- **Discussions:** [Fragen und fachlicher Austausch](https://github.com/encircle360-oss/briefbote/discussions)
- **Fehler in ERPNext oder Frappe selbst** bitte beim jeweiligen Projekt melden: [frappe/erpnext](https://github.com/frappe/erpnext/issues), [frappe/frappe](https://github.com/frappe/frappe/issues)

### Professioneller Support

Für Einführung, Gestaltung nach dem eigenen Erscheinungsbild, Betrieb, Schulung oder die Abstimmung der Dokumente mit deiner Steuerberatung: **hello@encircle360.com**

## Haftungsausschluss

Briefbote wird ohne jede Gewährleistung und, soweit das Gesetz es erlaubt, ohne Haftung bereitgestellt (Abschnitte 15 und 16 der [Lizenz](LICENSE)). Briefbote ist Software, keine Rechts- oder Steuerberatung. Wer ein Dokument ausstellt, bleibt für seinen Inhalt verantwortlich und prüft die ersten Dokumente jedes Falls vor dem Versand. Was das im Einzelnen heißt, steht im [Haftungsausschluss](docs/haftungsausschluss.md).

Briefbote ist weder ein Angebot der Frappe Technologies Pvt. Ltd. noch des DIN Deutsches Institut für Normung e. V. ERPNext ist eine Marke der Frappe Technologies Pvt. Ltd. Briefbote steht mit keinem davon in Verbindung.

Für den Einsatz mit zugesichertem Support und Reaktionszeiten sprich uns an: **hello@encircle360.com**

## Lizenz

Briefbote steht unter der [GNU Affero General Public License v3.0 oder später](LICENSE) (AGPL-3.0-or-later). Sie ist mit der GPL-3.0 von ERPNext kompatibel.

## Maintainer

Briefbote wird von der **[encircle360 GmbH](https://encircle360.com/?ref=github-briefbote)** entwickelt und gepflegt, zusammen mit allen Mitwirkenden. Für Einführung, Betrieb und Unterstützung ist die encircle360 GmbH unter [encircle360.com](https://encircle360.com/?ref=github-briefbote) erreichbar. Briefbote sendet keine Telemetrie, und kein Ausdruck trägt einen Hinweis auf die Software.

## Credits und Mitwirkende

Danke an alle Mitwirkenden, Partner und die Open-Source-Community, insbesondere an das [Frappe/ERPNext-Projekt](https://github.com/frappe/erpnext), auf dem Briefbote aufsetzt. Alle Mitwirkenden stehen in der [Contributors-Liste](https://github.com/encircle360-oss/briefbote/graphs/contributors).
