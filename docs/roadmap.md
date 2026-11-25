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
- **Version 0.1.0:** Rechnung und Gutschrift, Gestaltung, Leistungsnachweis und Einrichtung, im Image erpnext_germanized seit 16.60.0-16. Veröffentlicht.
- **Version 0.1.1:** „Drucken“ gibt das PDF des Generators, Logo jeder Form, Rücksendeangabe, die in das Fenster passt, Steuerzeilen mit Bemessungsgrundlage auch bei den deutschen Steuervorlagen, Befunde bei fehlenden Pflichtangaben, Entwurf und Storno auf jeder Seite markiert, eine rechte Kante und Spalten nach Inhalt. Veröffentlicht.
- **Gestaltungssystem:** ein Stylesheet und die Teile eines Briefs nach [DIN 5008](din-5008.md) (Form A und B, Anschriftfeld, Informationsblock, Marken, Fuß mit den [Angaben zum Unternehmen](geschaeftsbrief.md), „Seite n von N“), Positionstabelle mit wiederholtem Kopf, Summen bei der letzten Position; [Einstellungen Geschäftspost](einrichtung.md) je Unternehmen. Da.
- **[Gutschrift](gutschrift.md):** Gutschrift im Gutschriftsverfahren aus der Eingangsrechnung mit Kennzeichen, Steuerfällen im Einkauf und Korrektur. Da; offen ist die Prüfung durch einen Menschen mit Fachkenntnis.
- **Gestaltung je Unternehmen:** Akzentfarbe, Stellung und Höhe des Logos, Spalten des Fußes, eingebettete Schrift oder Schrift des Systems in den Einstellungen Geschäftspost, siehe [Einrichtung](einrichtung.md#gestaltung-im-erscheinungsbild). Da.
- **[Leistungsnachweis](leistungsnachweis.md):** die Stunden einer Rechnung aus ihren Stundenzetteln als Anlage oder eigenes Dokument, mit Summen je Projekt und Person und dem Abgleich mit den Positionen. Da.
- **Einrichtung ohne Oberfläche:** Einstellungen über die API, Steuerfälle nach Regel, Prüfung je Unternehmen, siehe [Einrichtung](einrichtung.md#einrichtung-ohne-oberfläche). Da.
- **[Angebot](angebot.md) und [Auftragsbestätigung](auftragsbestaetigung.md):** aus Angebot und Kundenauftrag, mit Alternativen, Preisen je Einheit, Umsatzsteuer nach Satz und Bemessungsgrundlage aus den deutschen Vorlagen, Annahmefrist, Lieferterminen und Zahlungsbedingungen. Da; offen ist die Prüfung durch einen Menschen mit Fachkenntnis.
- **[Lieferschein](lieferschein.md):** an die Lieferanschrift, mit Datum und Lieferdatum, Seriennummern und Chargen, Preisen und Empfangsbestätigung nach den Einstellungen, Rücklieferschein. Da.
- **[Zahlungserinnerung und Mahnung](mahnung.md):** aus der Mahnung von ERPNext, Titel und Texte je Stufe, Verzug nach § 286 BGB, Verzugszinsen und Pauschale nur, wo sie rechtmäßig sind, sonst ein Befund; Basiszinssätze in den Einstellungen. Da; offen ist die Prüfung durch einen Menschen mit Fachkenntnis.
- **[Zahlungsbestätigung und Quittung](zahlungsbestaetigung.md):** aus dem gebuchten Zahlungseingang eines Kunden, mit den angerechneten Belegen, Abzügen und dem nicht zugeordneten Rest. Da; offen ist die Prüfung durch einen Menschen mit Fachkenntnis.
- **[Bestellung](bestellung.md):** an den Lieferanten mit Lieferterminen, Artikelnummern, Lieferanschrift und der Umsatzsteuer des Lieferanten. Da.
- **[Rechnung](rechnung.md):** Rechnung, Rechnungskorrektur, Stornorechnung und kaufmännische Gutschrift aus der Ausgangsrechnung. Da; offen ist die Prüfung durch einen Menschen mit Fachkenntnis (Schritt 5 oben).

## Als Nächstes

1. **Version 0.2.0:** Angebot, Auftragsbestätigung, Lieferschein, Zahlungserinnerung und Mahnung, Zahlungsbestätigung und Quittung, Bestellung; Basiszinssätze, Mahnstufen und Optionen des Lieferscheins in den Einstellungen. Vorbereitet; die Veröffentlichung löst der Maintainer aus.
2. **Proforma-Rechnung**, die ERPNext 16 aus dem Kundenauftrag druckt.
3. **Eventualpositionen im Angebot**, wenn ERPNext sie abbildet.
4. **Packliste** (Packing Slip) zum Lieferschein.
5. **Anzahlungs-, Abschlags- und Schlussrechnung:** Rechnung über eine noch nicht erbrachte Leistung (§ 14 Abs. 5 Satz 1 UStG) und Endrechnung, die die Teilentgelte mit ihrer Steuer absetzt (§ 14 Abs. 5 Satz 2 UStG), aus Anzahlungen gegen den Auftrag und der Tabelle `advances`.
6. **Kontoauszug und Offene-Posten-Liste** je Kunde, **Saldenbestätigung**.
7. **Geschäftsbrief** für freie Korrespondenz, als Format für den Business Letter von erpnext_germany oder mit einem eigenen schlichten DocType; Reklamation beim Lieferanten.
8. **Einkauf und Lager:** Anfrage, Zahlungsavis, Lieferantenrücksendung, Wareneingangsschein, Kommissionierliste.
9. **Buchhaltung und Personal:** Buchungsbeleg, Zahlungsbeleg, Anlagenkarte, Reisekosten- und Spesenabrechnung, Urlaubsantrag.

Zur Rechnung offen: der Hinweis auf die Aufbewahrungspflicht des Empfängers (§ 14 Abs. 4 Satz 1 Nr. 9 UStG), das innergemeinschaftliche Dreiecksgeschäft (§ 25b, § 14a Abs. 7 UStG), Rechnungen in Fremdwährung und Steuerfälle aus der Kontenzuordnung von Steuerbote, wenn Steuerbote installiert ist.

## Ideen für die Geschäftspost über Druckformate hinaus

Diese Punkte sind Ideen, nichts davon gibt es; ob und wie sie kommen, entscheidet sich, wenn die Druckformate stehen.

- **E-Mail-Vorlagen** für den Versand jedes Dokuments, deutsch und englisch, mit Anrede aus dem Kontakt und den Angaben zum Unternehmen in der Signatur, die § 35a GmbHG auch für E-Mails verlangt.
- **PDF und E-Rechnung zusammen versenden:** das PDF des Druckformats mit eingebettetem XML, wenn eine App für die E-Rechnung wie eu_einvoice da ist, oder beide als Anhänge einer E-Mail. Heute bettet eu_einvoice sein XML nur in PDFs ein, die über den PDF-Download von Frappe oder pdf_on_submit entstehen, nicht in Anhänge von E-Mails.
- **Archiv:** das versandte PDF unveränderlich am Beleg ablegen, damit es acht Jahre so reproduzierbar bleibt, wie es versandt wurde (§ 14b Abs. 1 UStG, § 147 AO).
- **Serienversand** von Mahnungen und Kontoauszügen.
- **Briefpapier-Vorlage:** ein PDF des Briefkopfs und Fußes zum Druck auf Vorrat, aus denselben Einstellungen.
