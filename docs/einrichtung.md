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
| Logo | Bild im Briefkopf auf leerem Papier: PNG, JPEG oder SVG; ein SVG mit viewBox oder mit Breite und Höhe, auch so, wie ein Zeichenprogramm es exportiert. Es druckt in der Höhe der Einstellung und so breit, wie seine Proportionen es verlangen, höchstens so breit wie der Informationsblock (75 mm). Ohne Logo, oder wenn sich die Datei nicht lesen lässt, steht dort der Name des Unternehmens; die Prüfung der Einstellungen warnt dann |
| Falz- und Lochmarken drucken | die kurzen Striche am linken Rand |
| Rücksendeangabe drucken | das Unternehmen in einer Zeile über der Anschrift |
| Akzentfarbe | Farbe der Linien und, wo sie gegen Weiß gut lesbar ist, der Tabellenköpfe, als `#RRGGBB`; leer oder ungültig: Schwarz. Eine helle Akzentfarbe mit einem Kontrast unter 4,5 : 1 gegen Weiß (WCAG 2.2) bleibt für Linien und Marken; kleine Schrift wie die Tabellenköpfe bekommt einen dunkleren Ton derselben Farbe, der den Kontrast erreicht (`text_colour` in `briefbote/layout/theme.py`) |
| Schrift | „Inter (eingebettet)“ druckt auf jedem Server gleich; „Serifenlose Schrift des Systems“ nimmt Nimbus Sans, Liberation Sans, Arial oder Helvetica, was der Server hat |
| Stellung des Logos, Höhe des Logos (mm) | Logo rechts (Vorgabe) oder links im Briefkopf; die Höhe reicht höchstens bis 4 mm über das Anschriftfeld, bei Form B also 29 mm, bei Form A 11 mm |
| Spalten des Fußes | welche Blöcke (Unternehmen und Kontakt, Register und Leitung, Steuernummern, Bankkonten) in welcher Spalte stehen, mehrere Blöcke einer Spalte untereinander in der Reihenfolge der Tabelle; leer: vier Spalten. Ein Block, der in der Tabelle fehlt, wird nicht gedruckt |
| Sitz, Registergericht, Registernummer, Geschäftsführer, Vorstand, Vorsitz des Aufsichtsrats | die Angaben nach § 35a GmbHG, § 80 AktG, §§ 37a, 125 HGB, siehe [Geschäftsbrief](geschaeftsbrief.md) |
| Steuernummer | die Steuernummer vom Finanzamt; die USt-IdNr. kommt aus dem Feld `tax_id` des Unternehmens |
| Bankkonten | Bankkonten des Unternehmens (DocType Bank Account mit `is_company_account`) für den Fuß und die Zahlungsaufforderung; IBAN aus dem Konto, Name und BIC aus der Bank |
| Kleinunternehmer (§ 19 UStG) | jede Rechnung sagt, dass keine Umsatzsteuer berechnet wird |
| Steuerfälle | je Vorlage für Verkaufssteuern ihr Steuerfall und bei „Steuerfrei“ der Grund der Befreiung, siehe [Rechnung](rechnung.md#steuerfälle-und-hinweise) |

Die Einstellungen nehmen nur Bankkonten des eigenen Unternehmens und Vorlagen des eigenen Unternehmens an, jede Vorlage einmal.

### Gestaltung im Erscheinungsbild

Akzentfarbe, Schrift, Logo und Spalten des Fußes passen die Ausdrucke an das Erscheinungsbild eines Unternehmens an, ohne eine Vorlage zu ändern. Ein Beispiel: Logo rechts, 18 mm hoch, Akzentfarbe für die Spaltenköpfe, Fuß in drei Spalten mit Unternehmen und Kontakt in der ersten, Register und Leitung über den Steuernummern in der zweiten und den Bankkonten in der dritten:

| Spalte | Block |
|---|---|
| 1 | Unternehmen und Kontakt |
| 2 | Register und Leitung |
| 2 | Steuernummern |
| 3 | Bankkonten |

Die Werte gehen geprüft in das Stylesheet (`briefbote/layout/theme.py`): Eine Farbe, die keine Hexadezimalfarbe ist, wird Schwarz, eine Logohöhe außerhalb des Briefkopfs wird begrenzt. Die Pflichtangaben im Fuß bleiben, was die [Geschäftsbrief](geschaeftsbrief.md)-Seite verlangt: Wer einen Block weglässt, lässt auch seine Angaben weg.

### Warum eigene Einstellungen und kein Briefkopf

ERPNext kennt den „Briefkopf“ (Letter Head): freies HTML für Kopf und Fuß. Briefbote nutzt ihn nicht, aus drei Gründen. Die Stellen von Anschriftfeld, Informationsblock und Marken hängen an der Form des Briefs, nicht an einem Bild; die Pflichtangaben zum Unternehmen müssen vollständig und in der Sprache des Dokuments gedruckt werden, was nur aus einzelnen Feldern geht; und der Nachweis der CI kann einzelne Felder prüfen, freies HTML nicht. Wer einen Briefkopf in ERPNext gewählt hat, sieht ihn auf den Formaten von Briefbote nicht; Logo und Angaben kommen aus den Einstellungen.

## Einrichtung ohne Oberfläche

Wer eine Site mit Skripten einrichtet, setzt Briefbote über die REST-API von Frappe. Jedes Feld der Einstellungen ist über die API setzbar; die Tabellen gehen als Listen mit:

```bash
curl -X POST https://<site>/api/resource/Business%20Document%20Settings \
  -H "Authorization: token <api-key>:<api-secret>" -H "Content-Type: application/json" \
  -d '{
    "company": "Beispiel GmbH",
    "letter_form": "B",
    "stationery": "Blank paper",
    "logo": "/files/logo.svg",
    "accent_color": "#0B6E99",
    "font": "Inter (embedded)",
    "logo_position": "Right",
    "logo_height": 18,
    "footer_layout": [
      {"column": 1, "block": "Company and Contact"},
      {"column": 2, "block": "Register and Management"},
      {"column": 2, "block": "Tax Numbers"},
      {"column": 3, "block": "Bank Accounts"}
    ],
    "registered_office": "Musterstadt",
    "register_court": "Amtsgericht Musterstadt",
    "register_number": "HRB 99999",
    "managing_directors": "Erika Mustermann\nMax Mustermann",
    "tax_number": "12/345/67890",
    "bank_accounts": [{"bank_account": "Geschäftskonto - Beispielbank"}],
    "timesheet_annex": "With the invoice",
    "person_display": "Name",
    "time_unit": "Hour"
  }'
```

Die Werte der Auswahlfelder sind die englischen Werte der Tabelle oben („Blank paper“, „Pre-printed letter paper“, „Right“, „Left“, „Inter (embedded)“, „System sans-serif“, „With the invoice“, „Separate document“, „Not printed“, „Name“, „Initials“, „Role“, „None“); das Logo ist die Adresse einer Datei der Site (`file_url` eines File). Ändern geht mit `PUT /api/resource/Business%20Document%20Settings/<Unternehmen>`.

### Steuerfälle nach Regel

`apply_tax_cases` gibt jeder Steuervorlage des Unternehmens, die noch keinen Steuerfall hat, den Fall, den die Regel für ihren Titel kennt, und legt die Einstellungen an, wo es keine gibt; vorhandene Zeilen bleiben, wie sie sind:

```bash
curl -X POST https://<site>/api/method/briefbote.briefbote.setup.apply_tax_cases \
  -H "Authorization: token <api-key>:<api-secret>" -d "company=Beispiel GmbH"
```

Die Regel (`briefbote/setup/tax_cases.py`) kennt die Titel, die der Einrichtungsassistent von ERPNext 16 einem Unternehmen in Deutschland gibt, für SKR03, SKR04 und den Standard-Kontenrahmen gleich (`erpnext/setup/setup_wizard/data/country_wise_tax.json`):

| Vorlage für Verkaufssteuern | Steuerfall |
|---|---|
| Lieferung oder sonstige Leistung im Inland | Im Inland steuerpflichtig |
| Lieferung an Unternehmen in der EU | Innergemeinschaftliche Lieferung |
| Sonstige Leistung an Unternehmen in der EU | Leistung an Unternehmen in einem anderen EU-Staat |
| Lieferung oder sonstige Leistung an nicht-Unternehmen in der EU | Im Inland steuerpflichtig |
| Lieferung in Drittland | Ausfuhrlieferung |
| Sonstige Leistung an Unternehmen in Drittland | Leistung an Unternehmen außerhalb der EU |
| Sonstige Leistung an nicht-Unternehmen in Drittland | Im Inland steuerpflichtig |
| Bauleistungen nach § 13b UStG | Steuerschuldnerschaft des Leistungsempfängers im Inland |

| Vorlage für Einkaufssteuern | Steuerfall |
|---|---|
| Lieferung aus dem Inland | Im Inland steuerpflichtig |
| Sonstige Leistung aus dem Inland | Im Inland steuerpflichtig |
| Bauleistungen nach § 13b UStG | Steuerschuldnerschaft des Leistungsempfängers im Inland |

Bewusst ohne Fall bleiben „Nullsteuersatz nach § 12 Abs. 3 UStG“ (ein steuerpflichtiger Umsatz zum Satz von 0 %, dessen Rechnung den Satz nennen muss; Briefbote druckt diesen Fall noch nicht eigens) und die Einkäufe aus der EU und aus Drittländern (eine Gutschrift an einen Lieferanten im Ausland folgt den Vorschriften seines Staats). Eine eigene Vorlage bekommt ihren Fall als Zeile der Einstellungen.

### Prüfen, was fehlt

`check` sagt, was einem Unternehmen für seine Ausdrucke fehlt: Einstellungen, Anschrift, USt-IdNr. oder Steuernummer (Fehler), Sitz, Registergericht und -nummer, Geschäftsführung, Bankkonto, Steuervorlagen ohne Fall (Warnung), Logo, Einkaufsvorlagen ohne Fall (Hinweis). Eine leere Liste heißt: nichts fehlt.

```bash
curl -X POST https://<site>/api/method/briefbote.briefbote.setup.check \
  -H "Authorization: token <api-key>:<api-secret>" -d "company=Beispiel GmbH"
# {"message": [{"level": "warning", "message": "No bank account is chosen; invoices ask for payment without one."}]}
```

Beide Methoden verlangen die Rolle Accounts Manager oder System Manager; die Meldungen kommen in der Sprache des Benutzers.

## Druckformat wählen

Die Druckformate von Briefbote stehen in der Liste „Druckformat“ mit dem Modul Briefbote: „Rechnung“ und „Leistungsnachweis“ für die Ausgangsrechnung, „Gutschrift“ für die Eingangsrechnung, „Angebot“ für das Angebot (Quotation) und „Auftragsbestätigung“ für den Kundenauftrag (Sales Order). Briefbote macht sich nicht von selbst zum Standard. Im Desk setzt man das Standard-Druckformat über „Customize Form“ der Sales Invoice bzw. der Purchase Invoice (Feld Default Print Format). Ohne Oberfläche legt man dafür einen Property Setter an, wie es auch „Customize Form“ tut:

```bash
curl -X POST https://<site>/api/resource/Property%20Setter \
  -H "Authorization: token <api-key>:<api-secret>" -H "Content-Type: application/json" \
  -d '{"doctype_or_field": "DocType", "doc_type": "Sales Invoice", "property": "default_print_format",
       "property_type": "Data", "value": "Rechnung"}'
```

Für die Gutschrift ebenso mit `"doc_type": "Purchase Invoice"` und `"value": "Gutschrift"`; dann druckt jede Eingangsrechnung standardmäßig mit „Gutschrift“, und nur eine als Gutschrift gekennzeichnete druckt den Inhalt. Wer das nicht will, wählt „Gutschrift“ beim Drucken einer gekennzeichneten Eingangsrechnung. In einer App oder einem Skript auf der Site selbst tut es `frappe.make_property_setter({"doctype": "Sales Invoice", "doctype_or_field": "DocType", "property": "default_print_format", "value": "Rechnung", "property_type": "Data"})`. In der Druckansicht schaltet die Auswahl des Briefkopfs zwischen leerem und vorgedrucktem Papier um: „Kein Briefkopf“ (`no_letterhead`) druckt das Format wie auf vorgedrucktem Briefpapier, aber nur, wenn die Site Briefköpfe zur Auswahl hat. Hat sie keinen, ist das Feld leer und Frappe meldet trotzdem „Kein Briefkopf“; dann bleibt es beim Papier der Einstellungen, und Vorschau, PDF und Druck zeigen Logo und Angaben zum Unternehmen.

Der PDF-Generator ist der der Druckeinstellungen von Frappe; die Formate von Briefbote drucken mit wkhtmltopdf und mit dem Generator auf Chromium-Basis gleich.

### Drucken aus der Druckansicht

„Drucken“ in der Druckansicht (auch Strg+P dort und das Druckersymbol im Formular, das die Druckansicht öffnet) druckt bei den Formaten von Briefbote dasselbe PDF wie der Knopf „PDF“: mit Seitenumbrüchen, dem Tabellenkopf auf jeder Seite und „Seite n von N“. Während der Generator rechnet, zeigt der Desk „Das PDF wird für den Druck vorbereitet …“; dann öffnet sich der Druckdialog des Browsers. Es öffnet sich kein neues Fenster, ein Pop-up-Blocker greift also nicht. Gelingt der Druck nicht, sagt der Desk, dass man das PDF mit „PDF“ herunterladen und von dort drucken kann. Ein Druckserver und der Rohdruck in den Druckeinstellungen gehen vor und bleiben, wie Frappe sie vorsieht. Die Vorschau am Bildschirm zeigt keine Seitenzeile; Seitenzahlen gibt es erst auf Papier. Welche Wege es gibt und welche nachgewiesen sind, steht in der [Architektur](architektur.md#wege-aufs-papier).

## Was die Rechnung aus dem Beleg liest

- **Leistungszeitraum:** `from_date` und `to_date` der Ausgangsrechnung (Abschnitt „Subscription“) oder `service_start_date` und `service_end_date` je Position; sonst Lieferschein oder Rechnungsdatum, siehe [Rechnung](rechnung.md#leistungsdatum).
- **Bestellnummer des Kunden:** `po_no` und `po_date`.
- **Kundennummer:** die ID des Kunden, wenn sie vom Namen abweicht.
- **Sprache:** das Feld `language` der Ausgangsrechnung.
- **Grund einer Steuerbefreiung:** aus der Zeile des Steuerfalls; fehlt er dort, das Feld `tax_exemption_reason`, das erpnext_germany der Ausgangsrechnung gibt.
- **Verbraucher:** Kunde mit `customer_type` „Individual“.
