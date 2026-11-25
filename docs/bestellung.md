# Bestellung

Das Druckformat „Bestellung“ druckt eine Bestellung (Purchase Order) von ERPNext als Brief nach DIN 5008 an den Lieferanten: Bestellnummer, Datum, Lieferantennummer und Liefertermin im Informationsblock, die Positionen mit der Artikelnummer des Lieferanten, die Summen mit der Umsatzsteuer des Lieferanten nach Satz und Bemessungsgrundlage, wo die Lieferung im Inland steuerpflichtig ist, die Zahlungsbedingungen, die Bitte um Bestätigung, die Lieferanschrift und die Einkaufsbedingungen des Belegs.

Die Regeln stehen in `briefbote/purchase/order.py`, das Lesen des Belegs in `briefbote/briefbote/purchase.py` (`briefbote_purchase_order`), das Layout in `briefbote/briefbote/print_format/bestellung/bestellung.html` mit den gemeinsamen Teilen. Positionen, Summen und Liefertermine liest es wie die [Auftragsbestätigung](auftragsbestaetigung.md).

## Ein Bestellschein ist immer ein Geschäftsbrief

„Bestellscheine sind Geschäftsbriefe im Sinne des Absatzes 1.“ ([§ 35a Abs. 3 Satz 1 GmbHG](https://www.gesetze-im-internet.de/gmbhg/__35a.html), ebenso [§ 80 Abs. 3 AktG](https://www.gesetze-im-internet.de/aktg/__80.html)); die Ausnahme für Mitteilungen in einer bestehenden Geschäftsverbindung gilt für sie nicht. Auf leerem Papier druckt der Fuß jeder Seite die Angaben zum Unternehmen, siehe [Geschäftsbrief](geschaeftsbrief.md); auf vorgedrucktem Briefpapier müssen sie auf dem Papier stehen.

## Angaben

| Angabe | Woher sie kommt |
|---|---|
| Lieferant | `supplier_name`, `supplier_address` |
| Bestellnummer, Datum | Name, `transaction_date` |
| Lieferantennummer | `supplier`, wenn sie vom Namen abweicht |
| Liefertermin | `schedule_date` der Positionen: ein Termin, sonst „Liefertermine“ als Spanne und der Termin an jeder Position; sonst `schedule_date` der Bestellung |
| Positionen | Bezeichnung, Beschreibung, „Ihre Artikelnummer …“ aus `supplier_part_no`, Menge, Einheit, Einzelpreis, Betrag |
| Umsatzsteuer | Steuerzeilen mit Satz und Bemessungsgrundlage aus den Steuerdetails, nur im Steuerfall „Im Inland steuerpflichtig“ der Vorlage für Einkaufssteuern (Einstellungen Geschäftspost) |
| Hinweis | bei Leistungen nach § 13b UStG „Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge, § 13b UStG).“ |
| Zahlungsbedingungen | wie auf der [Auftragsbestätigung](auftragsbestaetigung.md#zahlungsbedingungen) |
| Bitte um Bestätigung | „Bitte bestätigen Sie uns diese Bestellung unter Angabe der Bestellnummer.“, nur auf einer gebuchten Bestellung |
| Lieferanschrift | `shipping_address` |
| Einkaufsbedingungen | `terms` |

Die Steuer einer Vorlage nach § 13b UStG bucht ERPNext als Zeile, die hinzugefügt und wieder abgezogen wird; sie ist die Steuer des bestellenden Unternehmens und keine Zeile der Bestellung (wie bei der [Gutschrift](gutschrift.md)). Bei einem Lieferanten, der Kleinunternehmer ist, zeigt die Bestellung keine Steuer.

## Was ERPNext nicht abbildet

- **Angebotsnummer des Lieferanten:** Das Lieferantenangebot (Supplier Quotation) hat keine Nummer des Lieferanten; die Bestellung nennt es nicht.
- **Streckengeschäft:** Eine Bestellung mit Lieferung an den Kunden (`customer`) druckt die Lieferanschrift der Bestellung; den Kunden nennt sie nicht.

## Offen für die fachliche Prüfung

| Punkt | Was Briefbote druckt | Frage |
|---|---|---|
| Umsatzsteuer | Steuer des Lieferanten nur bei im Inland steuerpflichtigen Lieferungen | Richtig für alle Steuerfälle im Einkauf? |
| § 13b UStG | Hinweis auf die Steuerschuldnerschaft des Leistungsempfängers | Ist der Hinweis auf einer Bestellung nützlich? |

## Nachweis

`briefbote/tests/print_documents_purchase.py` schreibt Bestellungen mit den deutschen Vorlagen für Einkaufssteuern, `briefbote/tests/print_proof_purchase.py` druckt sie mit beiden Generatoren: BE-2026-0001 mit zwei Steuersätzen, Artikelnummern, Zahlungsbedingung und Lieferanschrift auf leerem und vorgedrucktem Papier; BE-2026-0002 mit 36 Positionen und drei Lieferterminen; BE-2026-0003 nach § 13b UStG; BE-2026-0004 englisch an einen Kleinunternehmer.
