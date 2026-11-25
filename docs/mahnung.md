# Zahlungserinnerung und Mahnung

Das Druckformat „Mahnung“ druckt eine Mahnung (Dunning) von ERPNext als Brief nach DIN 5008: je nach Mahnstufe als „Zahlungserinnerung“, „Mahnung“, „2. Mahnung“ oder „Letzte Mahnung“, mit dem Text der Stufe und einer Zahlungsfrist, der Liste der offenen Rechnungen mit Datum, Fälligkeit, Betrag, Bezahltem, Offenem und Tagen seit Fälligkeit, ihrer Summe, Verzugszinsen und Pauschale nur, wo sie rechtmäßig sind, der Bankverbindung und dem Tag, bis zu dem Zahlungen berücksichtigt sind.

Die Regeln stehen in `briefbote/dunning/interest.py` (Verzug, Verzugszinsen, Pauschale, Basiszinssatz) und `briefbote/dunning/letter.py` (Stufen, Texte, Frist, Prüfung der gebuchten Beträge), das Lesen des Belegs in `briefbote/briefbote/dunning.py` (`briefbote_dunning`), das Layout in `briefbote/briefbote/print_format/mahnung/mahnung.html` mit `dunning_letter.html`, dem gemeinsamen `findings.html` und den Regeln im gemeinsamen `style.html` unter `briefbote/templates/includes/briefbote/`.

Die Quellen sind das BGB in der Fassung von [gesetze-im-internet.de](https://www.gesetze-im-internet.de/), gelesen am 25.11.2026, die [Tabelle des Basiszinssatzes der Deutschen Bundesbank](https://www.bundesbank.de/de/bundesbank/organisation/agb-und-regelungen/basiszinssatz-607820), gelesen am 25.11.2026, und der UStAE im Stand vom 13.11.2026. Briefbote ist keine Rechtsberatung: Ob und in welcher Höhe eine Forderung besteht, verantwortet, wer mahnt (siehe [Haftungsausschluss](haftungsausschluss.md)).

## Keine Rechnung

Eine Mahnung bezieht sich ausschließlich auf den Zahlungsverkehr und ist keine Rechnung, auch wenn sie alle Angaben des § 14 Abs. 4 UStG enthielte (UStAE 14.1 Abs. 1 Satz 5). Sie trägt deshalb keine Rechnungsnummer und keine Umsatzsteuer; die Rechnungen nennt sie mit Nummer und Datum.

## Stufen

ERPNext zählt je Rechnung, wie viele gebuchte Mahnungen es zu ihr schon gibt, und gibt jeder Zeile ihre Mahnstufe (`dunning_level` der Overdue Payment, `set_dunning_level` in `erpnext/accounts/doctype/dunning/dunning.py`). Die Mahnung druckt nach der höchsten Stufe ihrer Zeilen:

| Stufe | Titel | Text (Vorgabe) | Frist |
|---|---|---|---|
| 1 | Zahlungserinnerung | „Nach unseren Unterlagen sind die folgenden Rechnungen noch offen. Bitte überweisen Sie den offenen Betrag bis zum …. Haben Sie inzwischen bezahlt, betrachten Sie dieses Schreiben bitte als gegenstandslos.“ | 10 Tage |
| 2 | Mahnung | „Trotz unserer Zahlungserinnerung sind die folgenden Rechnungen noch offen. Bitte überweisen Sie den offenen Betrag bis zum ….“ | 10 Tage |
| 3 | 2. Mahnung | „Die folgenden Rechnungen sind trotz unserer Mahnungen noch offen. Bitte überweisen Sie den offenen Betrag bis zum ….“ | 7 Tage |
| 4 und höher | Letzte Mahnung | „Die folgenden Rechnungen sind trotz mehrerer Mahnungen noch offen. Bitte überweisen Sie den offenen Betrag spätestens bis zum ….“ | 7 Tage |

Die Frist ist das Datum der Mahnung zuzüglich der Tage der Stufe. Die Texte drohen nichts an und kündigen keine Schritte an; wer mehr schreiben will, tut es selbst. In den Einstellungen Geschäftspost, Tabelle „Mahnstufen“, lassen sich Titel, Text und Zahlungsfrist jeder Stufe ersetzen; `{deadline}` im Text steht für die Frist. Ein Text der Einstellungen druckt, wie er dort steht, in jeder Sprache gleich. Die Texte der Mahnart in ERPNext (Dunning Letter Text, `body_text` und `closing_text` der Mahnung) druckt das Format nicht.

Die Zahlungserinnerung trägt weder Zinsen noch Gebühr. Ein Entwurf oder eine stornierte Mahnung trägt auf jeder Seite die Markierung „ENTWURF“ oder „STORNIERT“ und druckt keine Zahlungsaufforderung und keine Bankverbindung.

## Verzug

Verzugszinsen und Pauschale gibt es nur während des Verzugs. Briefbote bestimmt den ersten Tag des Verzugs je Rechnung so:

- **Durch Mahnung:** „Leistet der Schuldner auf eine Mahnung des Gläubigers nicht, die nach dem Eintritt der Fälligkeit erfolgt, so kommt er durch die Mahnung in Verzug.“ ([§ 286 Abs. 1 Satz 1 BGB](https://www.gesetze-im-internet.de/bgb/__286.html)). Als Mahnung zählt jede frühere gebuchte Mahnung zu dieser Rechnung, auch eine Zahlungserinnerung, deren Datum nach der Fälligkeit liegt; der Verzug beginnt am Tag nach ihrem Datum, weil ihr Zugang nicht bekannt ist.
- **Durch 30 Tage:** „Der Schuldner einer Entgeltforderung kommt spätestens in Verzug, wenn er nicht innerhalb von 30 Tagen nach Fälligkeit und Zugang einer Rechnung oder gleichwertigen Zahlungsaufstellung leistet; dies gilt gegenüber einem Schuldner, der Verbraucher ist, nur, wenn auf diese Folgen in der Rechnung oder Zahlungsaufstellung besonders hingewiesen worden ist.“ (§ 286 Abs. 3 Satz 1 BGB). Die Frist beginnt mit dem späteren von Fälligkeit und Rechnungsdatum; das Rechnungsdatum steht für den Zugang, der nicht früher sein kann. Der Tag des Ereignisses zählt nicht ([§ 187 Abs. 1 BGB](https://www.gesetze-im-internet.de/bgb/__187.html)), die Frist endet mit dem Ablauf ihres letzten Tages ([§ 188 Abs. 1 BGB](https://www.gesetze-im-internet.de/bgb/__188.html)), an einem Samstag oder Sonntag erst mit dem nächsten Werktag ([§ 193 BGB](https://www.gesetze-im-internet.de/bgb/__193.html)); der Verzug beginnt am Tag danach. Beispiel: fällig am 18.05.2026, 30. Tag 17.06.2026, Verzug ab 18.06.2026.
- **Verbraucher:** Gegenüber einem Kunden mit `customer_type` „Individual“ gilt die 30-Tage-Regel nur, wenn seine Rechnung den Hinweis trug. Das Druckformat [Rechnung](rechnung.md#steuerfälle-und-hinweise) druckt ihn jedem Verbraucher; Briefbote nimmt ihn deshalb an, wenn „Rechnung“ das Standard-Druckformat der Ausgangsrechnung ist, sonst nicht.
- **Kein Verzug durch das Fälligkeitsdatum allein:** Der Mahnung bedarf es nicht, wenn „für die Leistung eine Zeit nach dem Kalender bestimmt ist“ (§ 286 Abs. 2 Nr. 1 BGB). Das „Fällig am“ einer Rechnung setzt der Gläubiger allein; Briefbote behandelt es nicht als solche Zeit, auch wenn ein Vertrag den Zahlungstag festlegen kann. Wer einen vereinbarten Zahlungstag hat, kann Zinsen von diesem Tag an selbst fordern; das Format prüft sie dann gegen den späteren Beginn und zeigt einen Befund.

Bezahlt der Schuldner aus einem Grund nicht, den er nicht zu vertreten hat, kommt er nicht in Verzug (§ 286 Abs. 4 BGB); das kann Briefbote nicht wissen.

## Verzugszinsen

„Eine Geldschuld ist während des Verzugs zu verzinsen. Der Verzugszinssatz beträgt für das Jahr fünf Prozentpunkte über dem Basiszinssatz.“ ([§ 288 Abs. 1 BGB](https://www.gesetze-im-internet.de/bgb/__288.html)) „Bei Rechtsgeschäften, an denen ein Verbraucher nicht beteiligt ist, beträgt der Zinssatz für Entgeltforderungen neun Prozentpunkte über dem Basiszinssatz.“ (§ 288 Abs. 2 BGB)

Briefbote rechnet je Rechnung vom ersten Tag des Verzugs bis zum Datum der Mahnung, beide Tage gezählt, auf den offenen Betrag, mit 5 Prozentpunkten gegenüber Verbrauchern und 9 sonst, mit dem Basiszinssatz jedes Tages, also geteilt an jedem 1. Januar und 1. Juli, und mit 365 Tagen je Jahr wie ERPNext. Zinsen auf Zinsen gibt es nicht ([§ 289 BGB](https://www.gesetze-im-internet.de/bgb/__289.html)).

**Was gedruckt wird:** ERPNext rechnet die Zinsen einer Mahnung von der Fälligkeit an mit dem festen Zinssatz der Mahnart (`validate_overdue_payments` in `dunning.py`) und bucht sie. Briefbote rechnet nichts neu für die Bücher, sondern prüft:

- Liegen die gebuchten Zinsen höchstens beim rechtmäßigen Betrag, druckt das Format sie als „Verzugszinsen (§ 288 BGB) bis …“ mit dem gebuchten Betrag.
- Liegen sie darüber oder fehlt ein Basiszinssatz für einen Tag, druckt das Format statt der Forderung einen rot umrahmten Befund, nur die offenen Rechnungen, keine Zahlungsaufforderung und keine Bankverbindung. Eine solche Mahnung ist nicht zu versenden, sondern zu berichtigen.

## Pauschale

„Der Gläubiger einer Entgeltforderung hat bei Verzug des Schuldners, wenn dieser kein Verbraucher ist, außerdem einen Anspruch auf Zahlung einer Pauschale in Höhe von 40 Euro.“ (§ 288 Abs. 5 Satz 1 BGB) Sie gilt auch für Abschlags- und Ratenzahlungen (Satz 2) und wird auf Kosten der Rechtsverfolgung angerechnet (Satz 3).

Die Gebühr einer Mahnung (`dunning_fee`) druckt das Format als „Pauschale (§ 288 Abs. 5 BGB)“, wenn der Kunde kein Verbraucher ist, mindestens eine Rechnung der Mahnung in Verzug ist und die Gebühr 40 Euro je Rechnung in Verzug nicht übersteigt. Sonst druckt es einen Befund statt der Forderung, gegenüber einem Verbraucher immer.

## Basiszinssatz

Der Basiszinssatz ändert sich zum 1. Januar und 1. Juli; die Deutsche Bundesbank gibt ihn im Bundesanzeiger bekannt ([§ 247 BGB](https://www.gesetze-im-internet.de/bgb/__247.html)). Briefbote kennt keinen Satz im Code: Die Einstellungen Geschäftspost haben die Tabelle „Basiszinssätze“ (gültig ab, Satz), die neue Einstellungen und die Aktualisierung auf diese Version mit den Sätzen füllen, die die Bundesbank bis zum 25.11.2026 veröffentlicht hat:

| gültig ab | Basiszinssatz |
|---|---|
| 01.01.2023 | 1,62 % |
| 01.07.2023 | 3,12 % |
| 01.01.2024 | 3,62 % |
| 01.07.2024 | 3,37 % |
| 01.01.2025 | 2,27 % |
| 01.07.2025 | 1,27 % |
| 01.01.2026 | 1,27 % |
| 01.07.2026 | 1,52 % |

Zum 1. Januar und 1. Juli trägt das Unternehmen den neuen Satz aus der [Tabelle der Bundesbank](https://www.bundesbank.de/de/bundesbank/organisation/agb-und-regelungen/basiszinssatz-607820) ein, auch wenn er sich nicht ändert. Ohne Zeile für das Halbjahr eines Zinstags lassen sich die Zinsen nicht prüfen, und das Format zeigt den Befund; die Prüfung der Einrichtung (`check`, siehe [Einrichtung](einrichtung.md#prüfen-was-fehlt)) warnt, wenn für den heutigen Tag kein Satz eingetragen ist.

## Empfohlene Einrichtung: Mahnarten ohne Zinsen und Gebühr

Am einfachsten und sichersten sind Mahnarten (Dunning Type) mit Zinssatz 0 und Gebühr 0. Dann bucht ERPNext nichts, was nicht rechtmäßig wäre, und die Mahnung erinnert nur an die offenen Rechnungen. So ist es unter [Einrichtung](einrichtung.md#mahnungen) beschrieben.

Wer Verzugszinsen oder die Pauschale fordern will, kann

- die Zinsen in einer späteren Mahnung buchen, nachdem er den rechtmäßigen Betrag ermittelt hat: Die Mahnung druckt ihn, wenn er die Grenze dieser Seite nicht übersteigt; der gebuchte Betrag lässt sich vor dem Buchen im Feld „Interest“ der Zeilen anpassen;
- gegenüber Unternehmen eine Mahnart mit 40 Euro Gebühr für Mahnungen nehmen, deren Rechnungen schon in Verzug sind.

Eine Mahnart mit festem Zinssatz rechnet von der Fälligkeit an und liegt deshalb meist über dem rechtmäßigen Betrag; Briefbote zeigt das dann als Befund.

## Was ERPNext nicht abbildet

- **Zugang** der Rechnung und der Mahnung: unbekannt, Briefbote nimmt das Datum des Belegs.
- **Feiertage** am Leistungsort für § 193 BGB: unbekannt, nur Samstag und Sonntag verschieben das Fristende.
- **Vereinbarte Zahlungstage** nach § 286 Abs. 2 Nr. 1 BGB: kein Feld; siehe oben.
- **Verbraucher:** nur über `customer_type` „Individual“.

## Seiten

Jede Seite nennt im Fuß „Mahnung MZ-2026-0002 · Seite 1 von 2“; der Kopf der Liste der Rechnungen kehrt auf jeder Seite wieder, die letzte Rechnung steht mit den Summen auf einer Seite.

## Offen für die fachliche Prüfung

| Punkt | Was Briefbote tut | Frage |
|---|---|---|
| Zahlungserinnerung als Mahnung | jede frühere gebuchte Mahnung nach Fälligkeit setzt in Verzug, auch die Zahlungserinnerung | Genügt der Text der Zahlungserinnerung als Mahnung im Sinne des § 286 Abs. 1 BGB? |
| Beginn des Verzugs | Tag nach dem Datum der Mahnung; Rechnungsdatum als Zugang | Ist das vorsichtig genug, oder ist ein Zuschlag für den Zugang nötig? |
| Fälligkeitsdatum | kein Verzug nach § 286 Abs. 2 Nr. 1 BGB durch „Fällig am“ | Richtig so? |
| 30-Tage-Frist | § 187 Abs. 1, § 188 Abs. 1, § 193 BGB ohne Feiertage | Gilt § 193 BGB für die Frist des § 286 Abs. 3 BGB, und beginnen die Zinsen am Tag nach ihrem Ende? |
| Verbraucherhinweis | angenommen, wenn „Rechnung“ das Standard-Druckformat ist | Genügt das als Nachweis des Hinweises? |
| Zinsen | act/365, Basiszinssatz je Tag, beide Endtage gezählt, 9 Punkte für jede Rechnung an Unternehmen | Ist jede Rechnung eine Entgeltforderung, und ist die Zählweise richtig? |
| Pauschale | 40 Euro je Rechnung in Verzug, nie gegenüber Verbrauchern | Richtig je Rechnung? |
| Gebühr gegenüber Verbrauchern | stets ein Befund | Sind Mahnkosten als Verzugsschaden gegenüber Verbrauchern zulässig und wie hoch? |
| Texte | sachlich, ohne Androhung | Wortlaut der Stufen angemessen? |

## Nachweis

`briefbote/tests/print_documents_dunning.py` schreibt Rechnungen und Mahnungen, `briefbote/tests/print_proof_dunning.py` druckt und prüft sie mit beiden Generatoren:

- MZ-2026-0001: Zahlungserinnerung an ein Unternehmen, auf leerem und vorgedrucktem Papier;
- MZ-2026-0002: Mahnung an ein Unternehmen mit einer Rechnung in Verzug durch 30 Tage über den Wechsel des Basiszinssatzes am 01.07.2026, einer durch 30 Tage und einer durch die Zahlungserinnerung, mit rechtmäßigen Zinsen und Pauschale, auf leerem und vorgedrucktem Papier;
- MZ-2026-0003: Mahnung an eine Privatperson, in Verzug nur durch Mahnung, mit Zinsen, ohne Pauschale;
- MZ-2026-0005: 2. Mahnung mit Zinsen, wie ERPNext sie mit 12 % ab Fälligkeit bucht: Befund statt Forderung;
- MZ-2026-0006: Letzte Mahnung über 40 Rechnungen auf mehreren Seiten;
- MZ-2026-0007: englisch in die USA.
