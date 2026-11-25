# Geschäftsbrief

Jedes Dokument, das Briefbote druckt, ist ein Geschäftsbrief: Rechnung, Mahnung, Angebot, Bestellung. Was ein Geschäftsbrief über das Unternehmen angeben muss, hängt von der Rechtsform ab. Briefbote druckt diese Angaben auf leerem Papier im Fuß jeder Seite (`briefbote/layout/letter.py`), aus dem Unternehmen und den [Einstellungen Geschäftspost](einrichtung.md).

## Pflichtangaben nach Rechtsform

| Rechtsform | Vorschrift | Angaben |
|---|---|---|
| GmbH, UG (haftungsbeschränkt) | [§ 35a Abs. 1 GmbHG](https://www.gesetze-im-internet.de/gmbhg/__35a.html) | Rechtsform, Sitz, Registergericht des Sitzes, Registernummer, alle Geschäftsführer, bei einem Aufsichtsrat mit Vorsitzendem dieser, jeweils mit Familiennamen und mindestens einem ausgeschriebenen Vornamen |
| AG | [§ 80 Abs. 1 AktG](https://www.gesetze-im-internet.de/aktg/__80.html) | Rechtsform, Sitz, Registergericht, Registernummer, alle Vorstandsmitglieder, der Vorsitzende des Vorstands als solcher bezeichnet, der Vorsitzende des Aufsichtsrats |
| Einzelkaufmann (e. K.) | [§ 37a Abs. 1 HGB](https://www.gesetze-im-internet.de/hgb/__37a.html) | Firma mit der Bezeichnung „eingetragener Kaufmann“ oder einer Abkürzung, Ort der Handelsniederlassung, Registergericht, Registernummer |
| OHG, KG | [§ 125 Abs. 1 HGB](https://www.gesetze-im-internet.de/hgb/__125.html) | Firma, Sitz, Registergericht, Registernummer; ist kein Gesellschafter eine natürliche Person (etwa GmbH & Co. KG), auch die Firmen der Gesellschafter mit deren Angaben nach § 35a GmbHG oder § 80 AktG |

Seit dem 1.1.2024 steht die Vorschrift für OHG und KG in § 125 HGB; der frühere § 125a HGB ist entfallen. Die Pflicht gilt für Geschäftsbriefe gleich welcher Form, die an einen bestimmten Empfänger gerichtet sind, also auch für E-Mails. Macht ein Brief Angaben zum Kapital, muss er das Stamm- oder Grundkapital und ausstehende Einlagen nennen (§ 35a Abs. 1 Satz 2 GmbHG, § 80 Abs. 1 Satz 3 AktG); Briefbote druckt kein Kapital.

Ausgenommen sind nach § 35a Abs. 2 GmbHG Mitteilungen in einer bestehenden Geschäftsverbindung, für die üblicherweise Vordrucke verwendet werden; Bestellscheine sind immer Geschäftsbriefe (Abs. 3). Ob Rechnungen unter die Ausnahme fallen, ist umstritten; die IHK zählt Rechnungen und Quittungen zu den Geschäftsbriefen ([IHK Karlsruhe](https://www.ihk.de/karlsruhe/fachthemen/recht/gesellschaftsrecht-handelsrecht/handelsrecht/pflichtangaben-auf-geschaeftsbriefen-2459134)). Briefbote druckt die Angaben deshalb auf jedem Dokument.

## Der Fuß

Der Fuß hat bis zu vier Spalten; eine Spalte ohne Inhalt entfällt.

1. **Unternehmen:** Name (mit Rechtsform), Anschrift, Telefon, E-Mail, Website aus dem Unternehmen und seiner Anschrift.
2. **Register und Leitung:** „Sitz: …“, Registergericht und Registernummer in einer Zeile („Amtsgericht Musterstadt, HRB 12345“), „Geschäftsführer: …“, „Vorstand: …“, „Vorsitz des Aufsichtsrats: …“ aus den Einstellungen. Hat das Unternehmen die Registerfelder von erpnext_germany (Registerart, Registernummer, Registergericht) und lassen die Einstellungen sie leer, nimmt Briefbote diese.
3. **Steuern:** „USt-IdNr.: …“ aus dem Unternehmen und „Steuernummer: …“ aus den Einstellungen, beide, wenn es beide gibt. Eine Rechnung braucht eine von beiden ([§ 14 Abs. 4 Satz 1 Nr. 2 UStG](https://www.gesetze-im-internet.de/ustg_1980/__14.html)); die Angabe des Finanzamts ist nicht nötig (UStAE 14.5 Abs. 5).
4. **Bank:** Name der Bank, IBAN in Vierergruppen, BIC aus den Bankkonten der Einstellungen.

Auf vorgedrucktem Briefpapier bleibt der Fuß bis auf Titel, Nummer und Seite leer: Die Angaben stehen dann auf dem Papier.

## Rücksendeangabe und Anschrift

Die Rücksendeangabe steht in einer Zeile in 7 pt unten in der Zusatz- und Vermerkzone: Name, Straße, Postleitzahl und Ort des Unternehmens. Die Anschrift des Empfängers folgt aus dem Beleg: Name, Ansprechpartner, wenn er vom Namen abweicht, die Zeilen der Anschrift, Postleitzahl und Ort und bei einer Anschrift im Ausland der Staat in Großbuchstaben. Sind es mehr als sechs Zeilen, rücken die beiden Straßenzeilen in eine.
