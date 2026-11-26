# Saldenbestätigung

<a href="bilder/beispiele/saldenbestaetigung.png"><img src="bilder/beispiele/saldenbestaetigung.png" width="280" alt="Saldenbestätigung SB-2026-0002 an einen Lieferanten: Bitte um Bestätigung des Saldos zum Stichtag mit den offenen Posten, dem Saldo, der Bitte um Antwort bis zu einem Datum direkt an einen Abschlussprüfer und dem Antwortteil zum Ankreuzen mit Linien für Ort, Datum, Unterschrift, Name und Firmenstempel"></a>

Beispiel aus den erfundenen Daten des Nachweises: [Saldenbestätigung als PDF](beispiele/saldenbestaetigung.pdf).

Das Druckformat „Saldenbestätigung“ bittet einen Kunden oder Lieferanten, den Saldo seines Kontos zu einem Stichtag zu bestätigen. Es druckt die offenen Posten, aus denen der Saldo besteht, den Saldo und einen Antwortteil zum Zurücksenden:

- „Wir bestätigen den Saldo von … zum … zugunsten von …“ zum Ankreuzen,
- „Wir stellen folgende Abweichung fest:“ mit Linien zum Ausfüllen und „Unser Saldo laut unseren Büchern:“,
- Linien für Ort, Datum, Unterschrift sowie Name und Firmenstempel.

Es gehört zum selben DocType wie der [Kontoauszug](kontoauszug.md) (`Party Statement`), mit der Art „Saldenbestätigung“ und dem Nummernkreis SB-JJJJ-NNNN. Woher die Zahlen kommen, was ein Entwurf liest und was ein gebuchter Beleg behält, steht dort. Die Saldenbestätigung hat zwei Felder mehr: **Antwort bis** (eine Frist) und **Antwort an** (Name und Anschrift, an die die Antwort geht, etwa die des Abschlussprüfers; leer geht sie an das Unternehmen).

Die Regeln stehen in `briefbote/statement/statement.py`, das Lesen in `briefbote/briefbote/statement.py`, das Layout in `briefbote/briefbote/print_format/saldenbestätigung/` mit `payment_letter.html` und `confirmation_reply.html`.

## Was eine Saldenbestätigung ist

Eine Saldenbestätigung hat **keine gesetzlich vorgeschriebene Form**. Briefbote kennt kein Gesetz, das sie verlangt oder ihren Inhalt regelt. Sie ist ein Mittel der Abstimmung zwischen Geschäftspartnern und ein Prüfungsnachweis in der Abschlussprüfung. Als Brief an einen bestimmten Empfänger trägt sie die Angaben zum Unternehmen ([§ 35a Abs. 1 GmbHG](https://www.gesetze-im-internet.de/gmbhg/__35a.html), siehe [Geschäftsbrief](geschaeftsbrief.md)).

Für die Abschlussprüfung regeln die Prüfungsstandards die **Bestätigungen Dritter**. Was Briefbote davon nachlesen konnte:

- **ISA 505 „External Confirmations“** (IAASB), gelesen in der Fassung ISA (Ireland) 505 der irischen Aufsicht IAASA ([PDF](https://iaasa.ie/wp-content/uploads/2022/09/ISA505I.pdf)) am 26.11.2026; den Originaltext des IAASB hat Briefbote nicht abgeglichen:
  - Tz. 6(b) definiert die **positive Bestätigungsanfrage** („Positive confirmation request – A request that the confirming party respond directly to the auditor indicating whether the confirming party agrees or disagrees with the information in the request, or providing the requested information.“). Tz. 6(c) definiert die negative, auf die nur bei Widerspruch geantwortet wird.
  - Tz. 7 verlangt, dass der **Prüfer** die Anfragen steuert: was bestätigt wird, wer gefragt wird, die Gestaltung „including determining that requests are properly addressed and contain return information for responses to be sent directly to the auditor“, und den Versand.
  - Tz. A4 nennt als Gesichtspunkte der Gestaltung unter anderem „Management’s authorization or encouragement to the confirming parties to respond to the auditor“ und ob der Befragte einzelne Rechnungen oder nur den Gesamtsaldo bestätigen kann.
  - Tz. A5: Eine positive Anfrage kann den Betrag nennen oder ihn offen lassen, damit der Befragte ihn selbst einträgt. Die offene Form verringert das Risiko einer ungeprüften Zustimmung, kann aber die Antwortquote senken.
- **IDW PS 302 n.F. „Bestätigungen Dritter“**: Nach einer Meldung des Betriebs-Beraters vom 08.09.2014 ([Neufassung von IDW PS 302](https://betriebs-berater.ruw.de/bilanzrecht/nachrichten/Neufassung-von-IDW-PS-302-Bestaetigungen-Dritter-24427)) wurde er „an den einschlägigen ISA 505 „External Confirmations““ und an ISA 501 angepasst und in IDW-FN 9/2014 und im WPg-Supplement 3/2014 veröffentlicht. Den Text des Standards konnte Briefbote nicht einsehen, er ist nicht frei zugänglich.
- **ISA [DE]**: Nach der Wirtschaftsprüferkammer ([Anwendung der ISA in Deutschland](https://www.wpk.de/neu/anwendung-der-international-standards-on-auditing-isa-in-deutschland/)) ersetzen die ISA [DE] „mit Inkrafttreten … die korrespondierenden IDW PS“. Ob und ab welchem Zeitraum ISA [DE] 505 den IDW PS 302 n.F. ersetzt, hat Briefbote nicht nachgelesen (siehe unten).

## Wie Briefbote das umsetzt

| Punkt | Umsetzung | Grundlage |
|---|---|---|
| Art der Anfrage | positiv: Der Empfänger soll in jedem Fall antworten, zustimmend oder mit Abweichung | ISA 505 Tz. 6(b), A5 |
| Betrag | genannt, mit den offenen Posten; die Abweichung und „Unser Saldo laut unseren Büchern“ trägt der Empfänger selbst ein | ISA 505 Tz. A4, A5 |
| Antwort an | „Antwort an“ des Belegs, etwa der Abschlussprüfer, sonst das Unternehmen; der Brief bittet dann, direkt dorthin zu senden | ISA 505 Tz. 7(c) |
| Frist | „Antwort bis“, wenn gesetzt | – |
| Ermächtigung | Der Brief kommt vom Unternehmen selbst | ISA 505 Tz. A4 |
| Zugunsten von | Der Antwortteil nennt den Gläubiger beim Namen statt „zu unseren Gunsten“, weil der Empfänger die Antwort schreibt | – |
| Entwurf, Storno | Markierung, kein Antwortteil, keine Bitte um Antwort; ein Storno weist auch keinen Saldo aus | – |

Wie der Prüfer die Anfragen steuert, auswählt, versendet und Nichtbeantwortungen behandelt (ISA 505 ab Tz. 7), regelt die Prüfung, nicht das Druckformat. Ob eine Anfrage, die das Unternehmen mit Briefbote druckt, für eine Prüfung taugt, entscheidet der Prüfer.

## Offen für die fachliche Prüfung

| Punkt | Was Briefbote druckt | Frage |
|---|---|---|
| Geltender Standard | Verweise auf ISA 505 und IDW PS 302 n.F. | Gilt für deutsche Abschlussprüfungen heute ISA [DE] 505 statt IDW PS 302 n.F., und ab welchem Zeitraum? Weicht ISA [DE] 505 in den hier genutzten Punkten von ISA 505 ab? |
| Fassung des ISA 505 | Zitate aus ISA (Ireland) 505 | Stimmen die zitierten Textziffern mit ISA 505 des IAASB und mit ISA [DE] 505 überein? |
| Text des IDW PS 302 n.F. | nichts daraus | Den Text hat Briefbote nicht gelesen. Verlangt er Angaben, die die Anfrage nicht hat? |
| Positive Anfrage mit Betrag | Betrag genannt | Genügt das, oder soll es eine Variante ohne Betrag geben (ISA 505 Tz. A5)? |
| Antwort an den Prüfer | Feld „Antwort an“, Satz „Bitte senden Sie sie direkt an die Anschrift in der Antwort.“ | Genügt das, wenn der Prüfer die Anfrage steuern soll (ISA 505 Tz. 7), oder druckt der Prüfer die Anfragen selbst? |
| Angaben im Fuß | Angaben nach § 35a Abs. 1 GmbHG | Fällt eine Saldenbestätigung unter § 35a Abs. 2 GmbHG? |
| Wortlaut des Antwortteils | „Wir bestätigen den Saldo …“, „Wir stellen folgende Abweichung fest:“ | Ist der Wortlaut in der Praxis üblich und ausreichend? |

## Nachweis

`briefbote/tests/print_documents_statement.py` schreibt die Anfragen, `briefbote/tests/print_proof_statement.py` druckt sie mit beiden Generatoren:
- SB-2026-0001: Kunde mit 43 offenen Posten über mehrere Seiten, mit Frist, auf leerem und vorgedrucktem Papier; der Antwortteil steht ganz auf der letzten Seite.
- SB-2026-0002: Lieferant, Antwort direkt an einen erfundenen Abschlussprüfer.
- SB-2026-0003: englisch.
- SB-2026-0004: ausgeglichenes Konto.
- SB-2026-0001 als Entwurf, storniert und als Kontoauszug gedruckt; der Kontoauszug KA-2026-0001 als Saldenbestätigung gedruckt.

Geprüft werden außerdem die Linien für Ort, Datum, Unterschrift sowie Name und Firmenstempel als bemalte Fläche.
