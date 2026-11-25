# Zahlungsbestätigung und Quittung

Zwei Druckformate für einen Zahlungseingang (Payment Entry mit „Receive“ von einem Kunden):

- **Zahlungsbestätigung:** „Ihre Zahlung über … vom … ist eingegangen und wie folgt verrechnet.“, die Belege, auf die die Zahlung angerechnet ist, mit Datum, Fälligkeit, Betrag und angerechnetem Betrag, Abzüge wie Bankgebühren, der angerechnete Betrag und, was noch keiner Rechnung zugeordnet ist.
- **Quittung:** dasselbe mit „Den Betrag von … haben wir am … von … erhalten.“ und Linien für Ort, Datum und Unterschrift.

Die Regeln stehen in `briefbote/sales/receipt.py`, das Lesen des Belegs in `briefbote/briefbote/receipt.py` (`briefbote_payment`), das Layout in `briefbote/briefbote/print_format/zahlungsbestätigung/` und `briefbote/briefbote/print_format/quittung/` mit `payment_letter.html`.

Die Quellen sind das BGB in der Fassung von [gesetze-im-internet.de](https://www.gesetze-im-internet.de/), gelesen am 25.11.2026, und der UStAE im Stand vom 13.11.2026.

## Was eine Quittung ist

„Der Gläubiger hat gegen Empfang der Leistung auf Verlangen ein schriftliches Empfangsbekenntnis (Quittung) zu erteilen.“ ([§ 368 Satz 1 BGB](https://www.gesetze-im-internet.de/bgb/__368.html)) Die Kosten trägt der Schuldner, wenn nichts anderes vereinbart ist ([§ 369 Abs. 1 BGB](https://www.gesetze-im-internet.de/bgb/__369.html)). „Der Überbringer einer Quittung gilt als ermächtigt, die Leistung zu empfangen, …“ ([§ 370 BGB](https://www.gesetze-im-internet.de/bgb/__370.html)): Eine Quittung, die vor der Zahlung im Umlauf ist, kann jemanden zum Kassieren ermächtigen. Briefbote bestätigt deshalb nur einen **gebuchten** Zahlungseingang eines **Kunden**; ein Entwurf oder ein stornierter Beleg trägt die Markierung „ENTWURF“ oder „STORNIERT“, und er wie eine Zahlung an einen Lieferanten druckt den Befund „Dieses Dokument bestätigt nichts“ und bestätigt nichts.

Die Quittung trägt Linien für die Unterschrift: „schriftlich“ verlangt § 368 BGB; ob dafür die Schriftform mit eigenhändiger Unterschrift des § 126 BGB nötig ist, ist offen (siehe unten). Die Zahlungsbestätigung ist ein Schreiben ohne Unterschrift.

Keine der beiden ist eine Rechnung: Sie rechnen über keine Leistung ab ([§ 14 Abs. 1 Satz 1 UStG](https://www.gesetze-im-internet.de/ustg_1980/__14.html)), sondern beziehen sich auf den Zahlungsverkehr (vgl. UStAE 14.1 Abs. 1 Satz 5, der das für Mahnungen sagt).

## Angaben

| Angabe | Woher sie kommt |
|---|---|
| Nummer, Datum | Name und `posting_date` des Zahlungseingangs |
| Kundennummer | `party`, wenn sie vom Namen abweicht |
| Zahlungsweg | `mode_of_payment` |
| Referenz | `reference_no` und `reference_date` als „… vom …“, etwa die Kennung der Überweisung |
| Belege | Tabelle `references`: Art (Rechnung, Auftrag, Mahnung, sonst Beleg), Nummer, Datum des Belegs, `due_date`, `total_amount`, `allocated_amount` |
| Summen | `paid_amount` als Zahlungseingang, jede Zeile von `deductions` mit Beschreibung oder Konto, `total_allocated_amount` als angerechneter Betrag |
| nicht zugeordnet | `unallocated_amount`, als Satz unter den Summen |

Eine Angabe ohne Wert fehlt ganz.

## Was ERPNext nicht abbildet

- **Barzahlung in Teilen** oder mehrere Zahler: ein Zahlungseingang hat einen Zahler (`party_name`).
- **Ort** der Quittung: kein Feld; „Ort, Datum“ steht als Linie zum Ausfüllen.

## Offen für die fachliche Prüfung

| Punkt | Was Briefbote druckt | Frage |
|---|---|---|
| Quittung | „Den Betrag von … haben wir am … von … erhalten.“ mit Linien für Ort, Datum, Unterschrift | Genügt das als Quittung nach § 368 BGB, und braucht sie eine eigenhändige Unterschrift (§ 126 BGB)? |
| Zahlungsbestätigung | ohne Unterschrift | Ist sie ein Empfangsbekenntnis im Sinne des § 368 BGB, mit der Wirkung des § 370 BGB? |
| keine Rechnung | weder Steuer noch Rechnungsangaben | Folgt das aus UStAE 14.1 Abs. 1 Satz 5, der nur Mahnungen nennt? |

## Nachweis

`briefbote/tests/print_documents_payment.py` schreibt Zahlungseingänge, `briefbote/tests/print_proof_payment.py` druckt sie mit beiden Generatoren: ZE-2026-0001 Überweisung auf zwei Rechnungen mit einem nicht zugeordneten Rest, auf leerem und vorgedrucktem Papier; ZE-2026-0002 als Quittung einer Barzahlung einer Privatperson; ZE-2026-0003 englisch mit Bankgebühren; ZE-2026-0004 auf 40 Rechnungen über mehrere Seiten. Die Frappe-Tests prüfen zusätzlich, dass ein Entwurf und eine Zahlung an einen Lieferanten nichts bestätigen.
