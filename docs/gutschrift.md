# Gutschrift

Das Druckformat „Gutschrift“ druckt eine Eingangsrechnung (Purchase Invoice) als Gutschrift im Sinne des § 14 Abs. 2 Satz 5 UStG: Das Unternehmen rechnet eine Lieferung oder Leistung, die es empfangen hat, mit dem Lieferanten durch ein Dokument ab, das es selbst ausstellt. Das ist nur zulässig, wenn es vorher mit dem Lieferanten vereinbart wurde; widerspricht der Lieferant dem Dokument, verliert es die Wirkung einer Rechnung (§ 14 Abs. 2 Satz 6 UStG). Die Regeln stehen in `briefbote/invoice/self_billing.py`, das Lesen des Belegs in `briefbote_self_billing` in `briefbote/briefbote/printing.py`, das Layout in `briefbote/briefbote/print_format/gutschrift/gutschrift.html` mit denselben Teilen wie die [Rechnung](rechnung.md).

## Kennzeichen an der Eingangsrechnung

Briefbote gibt der Eingangsrechnung das Feld „Abrechnung im Gutschriftsverfahren“ (`self_billing`, nach „Ist Rückgabe“, auch nach dem Buchen änderbar). ERPNext 16 hat kein eigenes Kennzeichen dafür. Das Druckformat druckt nur eine so gekennzeichnete Eingangsrechnung; jede andere druckt statt der Gutschrift einen Satz, dass sie nicht gekennzeichnet ist. So wird eine Rechnung des Lieferanten nicht versehentlich zu einer Gutschrift des Unternehmens.

## Pflichtangaben

Eine Gutschrift ist eine Rechnung des Lieferanten und trägt alle Angaben des § 14 Abs. 4 UStG, siehe [Rechnung](rechnung.md#pflichtangaben). Was sich ändert:

| Angabe | Woher sie kommt | Wo sie steht |
|---|---|---|
| Name und Anschrift des leistenden Unternehmers, des Lieferanten (Nr. 1) | Lieferant und seine Anschrift (`supplier_address`) | Anschriftfeld |
| Name und Anschrift des Leistungsempfängers, des Unternehmens (Nr. 1) | Unternehmen und seine Anschrift | Rücksendeangabe und Fuß |
| Steuernummer oder USt-IdNr. des leistenden Unternehmers (Nr. 2) | `tax_id` der Eingangsrechnung, sonst des Lieferanten | Informationsblock „Ihre Steuernummer oder USt-IdNr.“ |
| Nummer (Nr. 4) | Name des Belegs, vom Unternehmen vergeben | Betreff, Informationsblock, Fuß jeder Seite |
| Steuersatz und Steuerbetrag (Nr. 8) | Steuerzeilen der Eingangsrechnung, die Steuer hinzufügen | Summen als „Umsatzsteuer 19 % auf …“ |
| „Gutschrift“ (Nr. 10) | – | Titel und Betreff, Fuß jeder Seite |

Die Steuer heißt „Umsatzsteuer“, nicht „Vorsteuer“: Es ist die Steuer, die der Lieferant schuldet; dass das Unternehmen sie als Vorsteuer abzieht, steht nicht auf dem Dokument. Die Beschreibung der Steuerzeile in ERPNext („Vorsteuer 19 %“) druckt das Format deshalb nicht. Statt „Gutschrift“ wäre auch die Bezeichnung einer anderen Amtssprache nach Art. 226 Nr. 10a der Mehrwertsteuer-Systemrichtlinie zulässig, etwa „Self-billing“ (UStAE 14.5 Abs. 24); die deutsche Gutschrift trägt „Gutschrift“, die englische „Self-Billing Invoice“.

Unter den Summen steht „Abrechnung durch den Leistungsempfänger im Gutschriftsverfahren (§ 14 Abs. 2 Satz 5 UStG).“ und, wenn der Beleg offen ist, „Den Betrag von … überweisen wir bis zum … auf Ihr Konto.“

## Steuerfälle im Einkauf

Die Einstellungen Geschäftspost geben jeder Vorlage für Einkaufssteuern ihren Steuerfall; eine Vorlage ohne Zeile ist ein im Inland steuerpflichtiger Umsatz.

| Steuerfall | Summen | Hinweis | Quelle |
|---|---|---|---|
| Im Inland steuerpflichtig | Umsatzsteuer je Satz mit Bemessungsgrundlage | keiner | § 14 Abs. 4 Satz 1 Nr. 8 UStG |
| Steuerschuldnerschaft des Leistungsempfängers im Inland | keine Steuer | „Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge, § 13b UStG).“ | § 13b, § 14a Abs. 5 UStG |
| Lieferant ist Kleinunternehmer | keine Steuer | „Gemäß § 19 UStG wird keine Umsatzsteuer berechnet (Steuerbefreiung für Kleinunternehmer).“ | § 19 Abs. 1 UStG, § 34a UStDV |
| Steuerfrei | keine Steuer | „Steuerfreie Leistung: “ und der Grund aus der Zeile | § 14 Abs. 4 Satz 1 Nr. 8 UStG |

ERPNext bucht die Steuer nach § 13b UStG mit einer Vorlage, die sie hinzufügt und wieder abzieht. Das ist die Steuer des Unternehmens, nicht des Lieferanten; das Format druckt bei diesen Fällen keine Steuerzeile.

## Korrektur

Eine Rückgabe gegen eine Gutschrift druckt als „Korrektur der Gutschrift … zur Gutschrift … vom …“ oder, wenn sie die ganze Gutschrift aufhebt, als „Stornierung der Gutschrift“, mit Nummer und Datum der ursprünglichen Gutschrift (§ 31 Abs. 5 UStDV), ohne Zahlungssatz.

## Was das Druckformat nicht kann

- Gutschriften an Lieferanten in einem anderen Mitgliedstaat: Für sie gelten die Rechnungsvorschriften des Staats des Lieferanten (Art. 219a der Mehrwertsteuer-Systemrichtlinie). Briefbote hat dafür keine Steuerfälle.
- Gutschriften an Lieferanten im Drittland.
