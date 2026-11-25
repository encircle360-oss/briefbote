# Roadmap

Ziel von Briefbote sind Druckformate für alle Geschäftsdokumente, die ein deutsches Unternehmen aus ERPNext druckt oder versendet; der [Katalog](katalog.md) zählt sie auf. Diese Seite ordnet sie zu Schritten, nach dem, was ein kleines Dienstleistungs- oder Handelsunternehmen zuerst braucht.

## Wann ein Schritt fertig ist

Ein Druckformat ist fertig, wenn

1. seine Seite unter `docs/` die Rechtsgrundlage jeder Angabe mit Quelle nennt, eine Prüfliste der Pflichtangaben hat und sagt, was strittig ist und wie Briefbote es löst;
2. der Nachweis der CI es für Belege druckt, die jeden Fall der Seite und das Layout fordern (eine Position, viele Positionen über mehrere Seiten, lange Texte und Namen, Anschrift im Ausland), mit beiden PDF-Generatoren, auf leerem und auf vorgedrucktem Papier, und alle Prüfungen grün sind: Seitenzahlen, Ränder, nichts übereinander, Tabellenkopf wiederholt, Summen bei ihrer Tabelle, Pflichtangaben vorhanden, Anschrift im Fenster;
3. jemand jede Seite des Artefakts `printouts` angesehen hat;
4. es deutsch und englisch druckt, jeder Text in `de.csv`;
5. ein Mensch mit Fachkenntnis Pflichtangaben und Hinweise geprüft hat.

## Stand

- **Fundament:** App, Tests, CI, Regeln für Beiträge. Fertig.
- **Gestaltungssystem:** ein Stylesheet und die Teile eines Briefs nach [DIN 5008](din-5008.md) (Form A und B, Anschriftfeld, Informationsblock, Marken, Fuß mit den [Angaben zum Unternehmen](geschaeftsbrief.md), „Seite n von N“), Positionstabelle mit wiederholtem Kopf, Summen bei der letzten Position; [Einstellungen Geschäftspost](einrichtung.md) je Unternehmen. Da.
- **[Gutschrift](gutschrift.md):** Gutschrift im Gutschriftsverfahren aus der Eingangsrechnung mit Kennzeichen, Steuerfällen im Einkauf und Korrektur. Da; offen ist die Prüfung durch einen Menschen mit Fachkenntnis.
- **[Leistungsnachweis](leistungsnachweis.md):** die Stunden einer Rechnung aus ihren Stundenzetteln als Anlage oder eigenes Dokument, mit Summen je Projekt und Person und dem Abgleich mit den Positionen. Da.
- **[Rechnung](rechnung.md):** Rechnung, Rechnungskorrektur, Stornorechnung und kaufmännische Gutschrift aus der Ausgangsrechnung. Da; offen ist die Prüfung durch einen Menschen mit Fachkenntnis (Schritt 5 oben).

## Als Nächstes

1. **Gestaltung je Unternehmen:** Akzentfarbe für Tabellenköpfe und Linien, Logo links oder rechts und seine Größe, Spalten des Fußes und ihre Reihenfolge, eingebettete Schrift oder Schrift des Systems, in den Einstellungen Geschäftspost, ohne Vorlagen zu ändern; der Nachweis druckt zwei verschiedene Gestaltungen.
2. **Einrichtung ohne Oberfläche:** alle Einstellungen über die API, Steuerfälle aus den Namen der Steuervorlagen nach einer beschriebenen Regel, eine Prüfung, die sagt, was einem Unternehmen fehlt.
3. **Version 0.1.0** mit Rechnung und Gutschrift, Gestaltung, Leistungsnachweis und Einrichtung, gebündelt mit dem Image erpnext_germanized.
4. **Zahlungserinnerung und Mahnung** aus dem Mahnwesen von ERPNext (Dunning, Dunning Type): Stufen als Mahnarten, Gebühr, Verzugszinsen nach § 288 BGB mit dem Basiszinssatz als datierte Tabelle (§ 247 BGB; 1,27 % ab 01.01.2026, 1,52 % ab 01.07.2026), die Pauschale von 40 Euro nur gegenüber Unternehmern (§ 288 Abs. 5 BGB), die überfälligen Rechnungen als Tabelle, die Texte der Mahnart in der Sprache des Kunden.
5. **Zahlungsbestätigung** aus dem Zahlungseingang (Payment Entry): Quittung mit Betrag, Datum, Zahlungsweg und den beglichenen Rechnungen.
6. **Angebot** (Quotation): Gültigkeit, Zahlungsbedingungen, optionale Positionen.
7. **Auftragsbestätigung** (Sales Order): Liefertermin, Bestellnummer des Kunden, Zahlungsplan; dazu die Proforma-Rechnung, die ERPNext 16 aus dem Auftrag druckt.
8. **Lieferschein** (Delivery Note): mit und ohne Preise, mit eigenem Leistungsdatum, damit eine Rechnung auf ihn verweisen kann (UStAE 14.5 Abs. 16); Packliste.
9. **Bestellung** (Purchase Order): Bestellschein mit den Angaben zum Unternehmen (§ 35a Abs. 3 GmbHG), Lieferanschrift und Liefertermin.
10. **Anzahlungs-, Abschlags- und Schlussrechnung:** Rechnung über eine noch nicht erbrachte Leistung (§ 14 Abs. 5 Satz 1 UStG) und Endrechnung, die die Teilentgelte mit ihrer Steuer absetzt (§ 14 Abs. 5 Satz 2 UStG), aus Anzahlungen gegen den Auftrag und der Tabelle `advances`.
11. **Kontoauszug und Offene-Posten-Liste** je Kunde, **Saldenbestätigung**.
12. **Geschäftsbrief** für freie Korrespondenz, als Format für den Business Letter von erpnext_germany oder mit einem eigenen schlichten DocType; Reklamation beim Lieferanten.
13. **Einkauf und Lager:** Anfrage, Zahlungsavis, Lieferantenrücksendung, Wareneingangsschein, Kommissionierliste.
14. **Buchhaltung und Personal:** Buchungsbeleg, Zahlungsbeleg, Anlagenkarte, Reisekosten- und Spesenabrechnung, Urlaubsantrag.

Zur Rechnung offen: der Hinweis auf die Aufbewahrungspflicht des Empfängers (§ 14 Abs. 4 Satz 1 Nr. 9 UStG), das innergemeinschaftliche Dreiecksgeschäft (§ 25b, § 14a Abs. 7 UStG), Rechnungen in Fremdwährung und Steuerfälle aus der Kontenzuordnung von Steuerbote, wenn Steuerbote installiert ist.

## Ideen für die Geschäftspost über Druckformate hinaus

Diese Punkte sind Ideen, nichts davon gibt es; ob und wie sie kommen, entscheidet sich, wenn die Druckformate stehen.

- **E-Mail-Vorlagen** für den Versand jedes Dokuments, deutsch und englisch, mit Anrede aus dem Kontakt und den Angaben zum Unternehmen in der Signatur, die § 35a GmbHG auch für E-Mails verlangt.
- **PDF und E-Rechnung zusammen versenden:** das PDF des Druckformats mit eingebettetem XML, wenn eine App für die E-Rechnung wie eu_einvoice da ist, oder beide als Anhänge einer E-Mail. Heute bettet eu_einvoice sein XML nur in PDFs ein, die über den PDF-Download von Frappe oder pdf_on_submit entstehen, nicht in Anhänge von E-Mails.
- **Archiv:** das versandte PDF unveränderlich am Beleg ablegen, damit es acht Jahre so reproduzierbar bleibt, wie es versandt wurde (§ 14b Abs. 1 UStG, § 147 AO).
- **Serienversand** von Mahnungen und Kontoauszügen.
- **Briefpapier-Vorlage:** ein PDF des Briefkopfs und Fußes zum Druck auf Vorrat, aus denselben Einstellungen.
