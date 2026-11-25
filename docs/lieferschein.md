# Lieferschein

Das Druckformat „Lieferschein“ druckt einen Lieferschein (Delivery Note) von ERPNext als Brief nach DIN 5008 an die Anschrift, an die die Ware geht: Nummer, Datum und Lieferdatum, die Bestellung des Kunden und unsere Aufträge im Informationsblock, die Positionen mit Menge, Einheit, Seriennummern und Chargen, das Nettogewicht und eine Empfangsbestätigung zum Unterschreiben. Preise druckt es nur, wenn die Einstellungen Geschäftspost es verlangen.

Die Regeln stehen in `briefbote/sales/delivery.py`, das Lesen des Belegs in `briefbote/briefbote/sales.py` (`briefbote_delivery_letter`, `briefbote_delivery_note`), das Layout in `briefbote/briefbote/print_format/lieferschein/lieferschein.html` mit den Teilen `delivery_positions.html` und `receipt.html` und den Regeln im gemeinsamen `style.html` unter `briefbote/templates/includes/briefbote/`.

Die Quellen sind Gesetz und Verordnung in der Fassung von [gesetze-im-internet.de](https://www.gesetze-im-internet.de/), gelesen am 25.11.2026, und der UStAE im Stand vom 13.11.2026.

## Was ein Lieferschein ist

Kein Gesetz schreibt den Inhalt eines Lieferscheins vor. Er begleitet die Ware und ist keine Rechnung, weil er über nichts abrechnet ([§ 14 Abs. 1 Satz 1 UStG](https://www.gesetze-im-internet.de/ustg_1980/__14.html)). Wichtig wird er, wenn eine Rechnung, die keine E-Rechnung ist, auf ihn verweist: Eine Rechnung kann aus mehreren Dokumenten bestehen ([§ 31 Abs. 1 UStDV](https://www.gesetze-im-internet.de/ustdv_1980/__31.html)), und der Zeitpunkt der Lieferung darf dann im Lieferschein stehen, wenn die Rechnung ihn bezeichnet und er „neben dem Lieferscheindatum eine gesonderte Angabe des Leistungsdatums enthält“ (UStAE 14.5 Abs. 16 Satz 6 und 7). Ebenso darf die Rechnung für die Bezeichnung der Ware auf ihn verweisen (UStAE 14.5 Abs. 1 Satz 19). Für eine E-Rechnung ersetzt der Verweis die strukturierten Angaben nicht (UStAE 14.5 Abs. 16 Satz 4).

Briefbote druckt deshalb immer beides, „Datum“ und „Lieferdatum“, auch wenn ERPNext für beides nur das Buchungsdatum kennt, damit eine Rechnung eines anderen Systems auf ihn verweisen kann. Die [Rechnung](rechnung.md#leistungsdatum) von Briefbote druckt das Lieferdatum aus den Lieferscheinen ihrer Positionen selbst und braucht den Verweis nicht.

## Angaben

| Angabe | Woher sie kommt | Wo sie steht |
|---|---|---|
| Angaben zum Unternehmen | Unternehmen und Einstellungen Geschäftspost | Fuß jeder Seite auf leerem Papier, siehe [Geschäftsbrief](geschaeftsbrief.md) |
| Empfänger | Lieferanschrift `shipping_address_name`, sonst die Anschrift des Kunden | Anschriftfeld |
| Lieferscheinnummer | Name des Belegs | Informationsblock, Betreff, Fuß |
| Datum und Lieferdatum | `posting_date` | Informationsblock |
| Kundennummer, Ihre Bestellung | `customer`, `po_no` und `po_date` | Informationsblock |
| Unser Auftrag | die Kundenaufträge der Positionen (`against_sales_order`) mit ihrem Datum | Informationsblock |
| Positionen | Bezeichnung, Beschreibung, Menge, Einheit | Positionstabelle |
| Seriennummern, Chargen | Serien- und Chargenbündel der Position (Serial and Batch Bundle), sonst die Felder `serial_no` und `batch_no` | unter der Position; mehrere Chargen mit ihrer Menge |
| Nettogewicht | `total_net_weight`, wenn alle Positionen mit Gewicht dieselbe Gewichtseinheit haben | unter der letzten Position |
| Empfangsbestätigung | „Ware erhalten:“ mit Linien für Datum, Unterschrift und Name in Druckbuchstaben | am Schluss, mit der letzten Position auf einer Seite |
| Preise und Summen | nur mit der Einstellung, siehe unten | wie auf dem [Angebot](angebot.md#umsatzsteuer-und-preisangaben) |

Eine Angabe ohne Wert fehlt ganz, kein Feld steht leer. Ein Rücklieferschein (`is_return`) heißt „Rücklieferschein“, nennt im Betreff und im Informationsblock den Lieferschein, auf den er sich bezieht („Rücklieferschein LS-2026-0004 zum Lieferschein LS-2026-0001 vom 23.11.2026“), und druckt die Menge, die zurückkommt, positiv, auch wenn ERPNext sie negativ führt.

## Einstellungen

In den Einstellungen Geschäftspost, Abschnitt „Lieferschein“:

| Feld | Vorgabe | Wirkung |
|---|---|---|
| Preise auf Lieferscheinen drucken | aus | Einzelpreise, Beträge und Summen wie auf dem Angebot. Ein Lieferschein mit „Print Without Amount“ druckt auch dann keine. |
| Empfangsbestätigung zum Unterschreiben drucken | an | „Ware erhalten:“ mit Linien für Datum, Unterschrift und Name. |

Ein Lieferschein, der noch nicht gebucht oder storniert ist, trägt die Markierung „ENTWURF“ oder „STORNIERT“ und druckt keine Empfangsbestätigung: Er bittet niemanden, einen Empfang zu bestätigen.

Für ein Dienstleistungsunternehmen genügt oft der Leistungsnachweis zur Rechnung; der Lieferschein bleibt dafür schlicht.

## Was ERPNext nicht abbildet

- **Ein eigenes Leistungsdatum:** ERPNext kennt nur das Buchungsdatum des Lieferscheins. Briefbote druckt es als Datum und als Lieferdatum. Weicht der Tag der Lieferung ab, ist der Lieferschein an diesem Tag zu buchen.
- **Packstücke:** Die Packliste (Packing Slip) ist ein eigenes Dokument der [Roadmap](roadmap.md).
- **Zustand der Ware:** Die Empfangsbestätigung sagt nur, dass die Ware erhalten wurde, nichts über ihren Zustand.

## Seiten

Jede Seite nennt im Fuß „Lieferschein LS-2026-0001 · Seite 1 von 2“; der Kopf der Positionstabelle kehrt auf jeder Seite wieder.

## Offen für die fachliche Prüfung

| Punkt | Was Briefbote druckt | Frage |
|---|---|---|
| Lieferdatum | „Datum“ und „Lieferdatum“, beide aus dem Buchungsdatum | Genügt das als gesonderte Angabe des Leistungsdatums nach UStAE 14.5 Abs. 16 Satz 7? |
| Empfangsbestätigung | „Ware erhalten:“, Datum, Unterschrift, Name in Druckbuchstaben | Reicht der Wortlaut, oder soll er Menge oder Zustand einschließen? |
| Preise | auf Wunsch wie auf dem Angebot, mit Umsatzsteuer | Kann ein Lieferschein mit Preisen und Umsatzsteuer als Rechnung gelten (§ 14 Abs. 1 Satz 1 UStG)? Briefbote druckt dann keine Zahlungsaufforderung und kein Leistungsdatum als Rechnungsangabe. |

## Nachweis

`briefbote/tests/print_documents_sales.py` schreibt Lieferscheine, `briefbote/tests/print_proof_sales.py` druckt und prüft sie mit beiden Generatoren: LS-2026-0001 an eine abweichende Lieferanschrift mit Seriennummern, zwei Chargen, Gewicht und Empfangsbestätigung, auf leerem und vorgedrucktem Papier; LS-2026-0002 mit 40 Positionen über mehrere Seiten; LS-2026-0003 englisch in die USA; der Rücklieferschein LS-2026-0004; KL-2026-0001 eines Unternehmens, das Preise und keine Empfangsbestätigung druckt. Kein Ausdruck ohne Preise darf einen Betrag tragen.
