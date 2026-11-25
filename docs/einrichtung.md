# Einrichtung

Nach der Installation steht in der Leiste von ERPNext der Eintrag „Geschäftspost“. Er öffnet den Arbeitsbereich mit den Einstellungen und den Belegen und Stammdaten, die die Druckformate lesen. Den Eintrag sehen Benutzer mit einer der Rollen Accounts User, Accounts Manager oder System Manager.

## Einstellungen Geschäftspost

Je Unternehmen gibt es einen Satz Einstellungen (DocType „Business Document Settings“, auf Deutsch „Einstellungen Geschäftspost“). Ohne ihn drucken die Formate mit den Vorgaben: Form B, leeres Papier, Falzmarken und Rücksendeangabe, ohne Logo, ohne Register- und Bankangaben. Ändern dürfen die Einstellungen Accounts Manager und System Manager, lesen auch Accounts User.

| Feld | Wofür |
|---|---|
| Unternehmen | für welches Unternehmen die Einstellungen gelten |
| Anschrift des Unternehmens | Anschrift für Rücksendeangabe und Fuß; leer: die Hauptanschrift des Unternehmens |
| Briefform | Form B (Anschriftfeld 45 mm unter der Oberkante) oder Form A (27 mm), siehe [DIN 5008](din-5008.md) |
| Papier | „Leeres Papier“: die Formate drucken Briefkopf und Fuß mit den Angaben zum Unternehmen. „Vorgedrucktes Briefpapier“: beides bleibt frei, der Inhalt steht an den Stellen der Norm |
| Logo | Bild im Briefkopf auf leerem Papier, höchstens 60 mm breit; ohne Logo steht dort der Name des Unternehmens |
| Falz- und Lochmarken drucken | die kurzen Striche am linken Rand |
| Rücksendeangabe drucken | das Unternehmen in einer Zeile über der Anschrift |
| Sitz, Registergericht, Registernummer, Geschäftsführer, Vorstand, Vorsitz des Aufsichtsrats | die Angaben nach § 35a GmbHG, § 80 AktG, §§ 37a, 125 HGB, siehe [Geschäftsbrief](geschaeftsbrief.md) |
| Steuernummer | die Steuernummer vom Finanzamt; die USt-IdNr. kommt aus dem Feld `tax_id` des Unternehmens |
| Bankkonten | Bankkonten des Unternehmens (DocType Bank Account mit `is_company_account`) für den Fuß und die Zahlungsaufforderung; IBAN aus dem Konto, Name und BIC aus der Bank |
| Kleinunternehmer (§ 19 UStG) | jede Rechnung sagt, dass keine Umsatzsteuer berechnet wird |
| Steuerfälle | je Vorlage für Verkaufssteuern ihr Steuerfall und bei „Steuerfrei“ der Grund der Befreiung, siehe [Rechnung](rechnung.md#steuerfälle-und-hinweise) |

Die Einstellungen nehmen nur Bankkonten des eigenen Unternehmens und Vorlagen des eigenen Unternehmens an, jede Vorlage einmal.

### Warum eigene Einstellungen und kein Briefkopf

ERPNext kennt den „Briefkopf“ (Letter Head): freies HTML für Kopf und Fuß. Briefbote nutzt ihn nicht, aus drei Gründen. Die Stellen von Anschriftfeld, Informationsblock und Marken hängen an der Form des Briefs, nicht an einem Bild; die Pflichtangaben zum Unternehmen müssen vollständig und in der Sprache des Dokuments gedruckt werden, was nur aus einzelnen Feldern geht; und der Nachweis der CI kann einzelne Felder prüfen, freies HTML nicht. Wer einen Briefkopf in ERPNext gewählt hat, sieht ihn auf den Formaten von Briefbote nicht; Logo und Angaben kommen aus den Einstellungen.

## Druckformat wählen

Die Druckformate von Briefbote stehen in der Liste „Druckformat“ mit dem Modul Briefbote. Briefbote macht sich nicht von selbst zum Standard: Wer „Rechnung“ zum Standard der Ausgangsrechnung machen will, setzt es über „Customize Form“ der Sales Invoice als Default Print Format. In der Druckansicht schaltet die Auswahl des Briefkopfs zwischen leerem und vorgedrucktem Papier um: Ohne Briefkopf (`no_letterhead`) druckt das Format wie auf vorgedrucktem Briefpapier.

Der PDF-Generator ist der der Druckeinstellungen von Frappe; die Formate von Briefbote drucken mit wkhtmltopdf und mit dem Generator auf Chromium-Basis gleich.

## Was die Rechnung aus dem Beleg liest

- **Leistungszeitraum:** `from_date` und `to_date` der Ausgangsrechnung (Abschnitt „Subscription“) oder `service_start_date` und `service_end_date` je Position; sonst Lieferschein oder Rechnungsdatum, siehe [Rechnung](rechnung.md#leistungsdatum).
- **Bestellnummer des Kunden:** `po_no` und `po_date`.
- **Kundennummer:** die ID des Kunden, wenn sie vom Namen abweicht.
- **Sprache:** das Feld `language` der Ausgangsrechnung.
- **Grund einer Steuerbefreiung:** aus der Zeile des Steuerfalls; fehlt er dort, das Feld `tax_exemption_reason`, das erpnext_germany der Ausgangsrechnung gibt.
- **Verbraucher:** Kunde mit `customer_type` „Individual“.
