# Katalog der Geschäftsdokumente

Ziel von Briefbote ist jedes Dokument, das ein deutsches Unternehmen aus ERPNext druckt oder versendet. Diese Seite zählt sie auf, mit dem DocType, aus dem das Dokument entsteht, dem, was ERPNext 16 heute dafür mitbringt, dem, was die deutsche Fassung verlangt, und der Priorität. Die [Roadmap](roadmap.md) ordnet sie zu Schritten.

**Stand der Prüfung:** ERPNext und HRMS in Version 16.60.0, Frappe 16.61.0, gelesen im Code der Releases. Kein DocType von ERPNext oder HRMS setzt ein Standard-Druckformat; ohne eigenes Format druckt Frappe das generische Format „Standard“. Die mitgelieferten Formate von Angebot, Auftrag, Lieferschein, Ausgangs- und Eingangsrechnung, Bestellung und Anfrage sind Formate des Print Format Builder in vier Varianten (Classic, Modern, Bordered, Modern with Images). Keines druckt die USt-IdNr. oder Steuernummer des Unternehmens, den Leistungszeitraum, die Bankverbindung, den Zahlungsplan oder die Stundenzettel einer Rechnung, und ihre Texte in eigenen HTML-Blöcken sind englisch. Die deutsche Übersetzung von ERPNext nennt die Rückgabe einer Ausgangsrechnung („Credit Note“) „Gutschrift“, was im Umsatzsteuerrecht das Gutschriftsverfahren bezeichnet (UStAE 14.3 Abs. 2 Satz 5).

**Für jedes Dokument gilt:** Es ist ein Geschäftsbrief, sobald es an einen bestimmten Empfänger außerhalb des Unternehmens geht, und trägt dann die Angaben nach § 35a GmbHG, § 80 AktG oder §§ 37a, 125 HGB; Bestellscheine immer (§ 35a Abs. 3 GmbHG, § 80 Abs. 3 AktG), siehe [Geschäftsbrief](geschaeftsbrief.md). Briefe folgen DIN 5008 ([DIN 5008](din-5008.md)). Ein Buchungsbeleg und ein versandter Handels- oder Geschäftsbrief werden aufbewahrt (§ 147 Abs. 1, 3 AO; § 257 HGB), eine Rechnung acht Jahre (§ 14b Abs. 1 UStG).

Priorität: **1** braucht fast jedes kleine Unternehmen von Anfang an, **2** braucht ein Dienstleister oder Händler bald, **3** braucht ein Teil der Unternehmen, **4** ist intern oder selten.

## Verkauf

| Dokument | DocType (App) | ERPNext 16 heute | Was die deutsche Fassung verlangt | Priorität |
|---|---|---|---|---|
| Rechnung | Sales Invoice (ERPNext) | vier Builder-Formate, „Sales Invoice Return“, „Sales Auditing Voucher“ | § 14 Abs. 4 UStG, Hinweise nach § 14a UStG, Leistungsdatum (UStAE 14.5 Abs. 16), Verbraucherhinweis nach § 286 Abs. 3 BGB, siehe [Rechnung](rechnung.md). **Da: Druckformat „Rechnung“** | 1 |
| Rechnungskorrektur, Stornorechnung | Sales Invoice mit `is_return` und `return_against` | Builder-Formate mit dem Titel „Credit Note“, deutsch „Gutschrift“ | Bezug auf die Rechnung nach § 31 Abs. 5 UStDV, UStAE 14.11 Abs. 1; nicht „Gutschrift“ (UStAE 14.3 Abs. 2 Satz 5). **Da: Druckformat „Rechnung“** | 1 |
| Kaufmännische Gutschrift | Sales Invoice mit `is_return` ohne `return_against` | wie oben | Abgrenzung vom Gutschriftsverfahren (UStAE 14c.1 Abs. 3 Satz 4). **Da: Druckformat „Rechnung“** | 1 |
| Leistungsnachweis, Stundennachweis | Sales Invoice, Tabelle `timesheets` (Sales Invoice Timesheet: Tätigkeit, Beschreibung, von, bis, Stunden, Betrag, Projekt); Timesheet | kein Format für Timesheet, keines der Rechnungsformate druckt die Stunden | Anlage zur Rechnung: eine Rechnung kann aus mehreren Dokumenten bestehen, wenn das Dokument mit Entgelt und Steuer die anderen bezeichnet (§ 31 Abs. 1 UStDV) | 1 |
| Abschlags- und Anzahlungsrechnung | kein eigener DocType: Anzahlung als Payment Entry gegen den Auftrag mit „Advance Taxes and Charges“; neu in 16 der DocType Proforma Invoice | kein Format | Rechnung über eine noch nicht erbrachte Leistung, als solche kenntlich (§ 14 Abs. 5 Satz 1 UStG, UStAE 14.5 Abs. 16) | 2 |
| Teil- und Schlussrechnung | Sales Invoice aus Teilmengen des Auftrags; Anzahlungen in der Tabelle `advances` | kein Format druckt `advances` | Endrechnung setzt vereinnahmte Teilentgelte mit ihrer Steuer ab (§ 14 Abs. 5 Satz 2 UStG) | 2 |
| Proforma-Rechnung | Proforma Invoice (ERPNext 16, in den Selling Settings einzuschalten); druckt eine Kopie des Auftrags, das Format gehört deshalb zum Sales Order | „Proforma Invoice“ (Sales Order), Überschrift „PROFORMA INVOICE“ ohne Übersetzung | keine Rechnung, als solche deutlich zu kennzeichnen; was sie steuerlich bedeutet, ist vor dem Format zu prüfen | 3 |
| Angebot | Quotation | vier Builder-Formate | Gültigkeit (`valid_till`) und Annahmefrist (§ 148 BGB), Gesamtpreis gegenüber Verbrauchern (§ 3 PAngV), keine Rechnung (§ 14 Abs. 1 UStG); siehe [Angebot](angebot.md). **Da: Druckformat „Angebot“** | 1 |
| Auftragsbestätigung | Sales Order | vier Builder-Formate | Liefertermin, Bestellnummer des Kunden, Angebot, Zahlungsbedingungen; keine Rechnung (UStAE 14.1 Abs. 17); siehe [Auftragsbestätigung](auftragsbestaetigung.md). **Da: Druckformat „Auftragsbestätigung“** | 2 |
| Lieferschein | Delivery Note | vier Builder-Formate; `print_without_amount` blendet Preise aus | wird er für das Leistungsdatum einer Rechnung herangezogen, braucht er neben dem Lieferscheindatum ein eigenes Leistungsdatum (UStAE 14.5 Abs. 16); siehe [Lieferschein](lieferschein.md). **Da: Druckformat „Lieferschein“** | 2 |
| Packliste | Packing Slip | kein Format | Packstücke, Netto- und Bruttogewicht | 3 |
| Zahlungserinnerung, Mahnung (Stufen) | Dunning, Dunning Type (Gebühr, Zinssatz, Text je Sprache) | „Dunning Letter“, ohne Angaben zum Unternehmen und ohne Bank | Verzug (§ 286 BGB), Verzugszinsen 5 bzw. 9 Prozentpunkte über dem Basiszinssatz (§ 288 Abs. 1, 2 BGB, § 247 BGB; 1,52 % ab 01.07.2026), Pauschale 40 Euro gegenüber Unternehmern (§ 288 Abs. 5 BGB); eine Mahnung ist keine Rechnung (UStAE 14.1 Abs. 1 Satz 5); siehe [Mahnung](mahnung.md). **Da: Druckformat „Mahnung“** | 1 |
| Zahlungsbestätigung, Quittung | Payment Entry (Eingang) | „Bank and Cash Payment Voucher“, englisch, Buchungssicht | Empfänger, Betrag, Datum, Bezug auf die Rechnungen; Quittung nach § 368 BGB nur für gebuchte Zahlungen (§ 370 BGB); siehe [Zahlungsbestätigung](zahlungsbestaetigung.md). **Da: Druckformate „Zahlungsbestätigung“ und „Quittung“** | 2 |
| Kontoauszug, Offene-Posten-Liste | Process Statement Of Accounts; Berichte Accounts Receivable und General Ledger; Kontoauszug (Party Statement, Briefbote) | eigene Vorlagen, immer mit wkhtmltopdf; Berichtsformate „Statement of Account“, „Accounts Receivable Standard“ | Fälligkeiten, Bezug auf Rechnungen; DIN 5008; keine gesetzlich vorgeschriebene Form bekannt; siehe [Kontoauszug](kontoauszug.md). **Da: Druckformat „Kontoauszug“** (offene Posten zum Stichtag) aus dem DocType Kontoauszug | 2 |
| Saldenbestätigung | Bericht Accounts Receivable bzw. Accounts Payable; Kontoauszug (Party Statement, Briefbote) | Berichtsformate „Customer/Supplier Balance Confirmation“ (indische Vorlage) | Saldo zum Stichtag, Bitte um Bestätigung; keine gesetzliche Form, Bestätigungen Dritter nach ISA 505 und IDW PS 302 n.F.; siehe [Saldenbestätigung](saldenbestaetigung.md). **Da: Druckformat „Saldenbestätigung“** mit Antwortteil | 3 |
| Kassenbon | POS Invoice | sechs Formate | Kleinbetragsrechnung (§ 33 UStDV) | 4 |

## Einkauf

| Dokument | DocType | ERPNext 16 heute | Was die deutsche Fassung verlangt | Priorität |
|---|---|---|---|---|
| Gutschrift im Gutschriftsverfahren | Purchase Invoice; ERPNext 16 hat kein Kennzeichen dafür | vier Builder-Formate der Eingangsrechnung | Angabe „Gutschrift“ (§ 14 Abs. 4 Satz 1 Nr. 10 UStG) oder „Self-billing“ (UStAE 14.5 Abs. 24), vorherige Vereinbarung (§ 14 Abs. 2 Satz 5 UStG), Steuernummer oder USt-IdNr. des leistenden Lieferanten (§ 14 Abs. 4 Satz 1 Nr. 2 UStG); Widerspruch nimmt ihr die Wirkung (§ 14 Abs. 2 Satz 6 UStG). **Da: Druckformat „Gutschrift“** | 1 |
| Bestellung | Purchase Order | vier Builder-Formate, „Drop Shipping Format“ | Bestellschein: Angaben zum Unternehmen immer (§ 35a Abs. 3 GmbHG); Lieferanschrift, Liefertermin; siehe [Bestellung](bestellung.md). **Da: Druckformat „Bestellung“** | 2 |
| Anfrage | Request for Quotation | vier Builder-Formate | Positionen ohne Preise, Antwortfrist | 3 |
| Zahlungsavis | Payment Entry (Ausgang), Payment Order | kein Format für Payment Order; Payment Entry nur Buchungssicht | Bezug auf die bezahlten Rechnungen des Lieferanten (`bill_no`), Skonto je Rechnung; keine Vorschrift für Form oder Inhalt bekannt; siehe [Zahlungsavis](zahlungsavis.md). **Da: Druckformat „Zahlungsavis“** aus dem Zahlungsausgang | 3 |
| Reklamation | kein DocType für Reklamationen beim Lieferanten (Non Conformance und Quality Feedback sind intern, Warranty Claim gilt dem Kunden) | – | als [Geschäftsbrief](#allgemein) | 3 |
| Lieferantenrücksendung | Purchase Receipt mit `is_return` | nur das Format für Serien und Chargen | Bezug auf den Wareneingang | 3 |

## Lager

| Dokument | DocType | ERPNext 16 heute | Was die deutsche Fassung verlangt | Priorität |
|---|---|---|---|---|
| Wareneingangsschein | Purchase Receipt | „Purchase Receipt Serial and Batch Bundle Print“, englische Spalten | intern; Lieferschein des Lieferanten (`supplier_delivery_note`) | 4 |
| Kommissionierliste | Pick List | „Pick List“, englische Überschrift | intern | 4 |
| Lagerbuchung | Stock Entry | kein Format | intern | 4 |
| Versandauftrag | Shipment | kein Format | Absender, Empfänger, Pakete, Warenwert | 4 |

## Projekte und Dienstleistung

| Dokument | DocType | ERPNext 16 heute | Was die deutsche Fassung verlangt | Priorität |
|---|---|---|---|---|
| Stundenzettel | Timesheet | kein Format | Abnahme durch den Kunden, wo vereinbart; als Anlage zur Rechnung siehe oben | 2 |
| Wartungs- oder Einsatzbericht | Maintenance Visit | kein Format | Leistungsnachweis beim Kunden | 3 |
| Installations- oder Abnahmeprotokoll | Installation Note | kein Format | Abnahme | 3 |
| Vertrag | Contract | kein Format | Vertragstext aus Contract Template, Unterschriften | 3 |

## Buchhaltung

| Dokument | DocType | ERPNext 16 heute | Was die deutsche Fassung verlangt | Priorität |
|---|---|---|---|---|
| Buchungsbeleg | Journal Entry | „Journal Auditing Voucher“ (englische Texte), „Credit Note“, „Payment Receipt Voucher“, Scheckformat | Belegfunktion und Aufbewahrung (§ 147 Abs. 1 Nr. 4, Abs. 3 AO; § 257 HGB) | 3 |
| Zahlungsbeleg | Payment Entry | „Bank and Cash Payment Voucher“ | wie Buchungsbeleg | 3 |
| Anlagenkarte | Asset | kein Format | Anschaffung, Nutzungsdauer, Abschreibung | 4 |
| Zahlungsanforderung | Payment Request | kein Format; der DocType hat ein Feld für sein Druckformat | IBAN, Verwendungszweck | 3 |

## Personal (HRMS)

Die Lohnabrechnung läuft in deutschen Unternehmen in der Regel außerhalb von ERPNext; die Gehaltsabrechnung von HRMS (Salary Slip) ist auf ein anderes Lohnsteuerrecht zugeschnitten und gehört nicht zum Ziel von Briefbote.

| Dokument | DocType | HRMS 16 heute | Was die deutsche Fassung verlangt | Priorität |
|---|---|---|---|---|
| Reisekosten- und Spesenabrechnung | Expense Claim | kein Format | Belege, Vorsteuer aus den Belegen, Erstattung | 3 |
| Vorschuss | Employee Advance | kein Format | Betrag, Verrechnung | 4 |
| Dienstreiseantrag | Travel Request | kein Format | intern | 4 |
| Urlaubsantrag | Leave Application | kein Format | intern | 4 |
| Einstellungszusage, Angebot an Bewerber | Job Offer | drei Formate mit festem englischem Text | Brief nach DIN 5008 | 4 |
| Arbeitszeugnis | kein DocType in HRMS 16 | – | – | – |

## Allgemein

| Dokument | DocType | ERPNext 16 heute | Was die deutsche Fassung verlangt | Priorität |
|---|---|---|---|---|
| Geschäftsbrief | kein DocType in Frappe, ERPNext oder HRMS; erpnext_germany bringt die DocTypes Business Letter und Business Letter Template ohne Druckformat | – | DIN 5008, Angaben zum Unternehmen | 2 |

Der Geschäftsbrief bekommt ein Format für den Business Letter von erpnext_germany, wenn die App da ist; ohne sie braucht Briefbote einen eigenen schlichten DocType für freie Briefe. Das entscheidet der Schritt der Roadmap.
