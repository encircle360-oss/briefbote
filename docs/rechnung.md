# Rechnung

Das Druckformat „Rechnung“ druckt eine Ausgangsrechnung (Sales Invoice) von ERPNext als Brief nach DIN 5008. Aus einer Vorlage entstehen vier Dokumente, je nachdem, was der Beleg ist:

| Beleg in ERPNext | Dokument | Titel |
|---|---|---|
| Ausgangsrechnung ohne `is_return` | Rechnung | „Rechnung“ |
| Rückgabe mit `return_against`, die die Rechnung vollständig aufhebt | Stornorechnung | „Stornorechnung … zur Rechnung … vom …“ |
| Rückgabe mit `return_against` über einen Teil | Rechnungskorrektur | „Rechnungskorrektur … zur Rechnung … vom …“ |
| Rückgabe ohne `return_against` | kaufmännische Gutschrift | „Kaufmännische Gutschrift“ |

Die Regeln stehen in `briefbote/invoice/document.py`, das Lesen des Belegs in `briefbote/briefbote/printing.py`, das Layout in `briefbote/briefbote/print_format/rechnung/rechnung.html` und den gemeinsamen Teilen unter `briefbote/templates/includes/briefbote/`. Was ein Unternehmen dafür einstellt, steht unter [Einrichtung](einrichtung.md).

Die Quellen auf dieser Seite sind Gesetz und Verordnung in der Fassung von [gesetze-im-internet.de](https://www.gesetze-im-internet.de/) und der [Umsatzsteuer-Anwendungserlass](https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Steuerarten/Umsatzsteuer/Umsatzsteuer-Anwendungserlass/Umsatzsteuer-Anwendungserlass-aktuell.pdf) (UStAE) im Stand vom 13.11.2026, der das BMF-Schreiben zur E-Rechnung vom 15.10.2026 schon enthält.

## Pflichtangaben

§ 14 Abs. 4 Satz 1 UStG zählt auf, was eine Rechnung enthalten muss. So erfüllt das Druckformat jede Angabe:

| Nr. | Angabe | Woher sie kommt | Wo sie steht |
|---|---|---|---|
| 1 | vollständiger Name und vollständige Anschrift des leistenden Unternehmers und des Leistungsempfängers | Unternehmen und seine Anschrift (Einstellungen, sonst Hauptanschrift); Kunde und Rechnungsanschrift des Belegs | Rücksendeangabe und Fuß; Anschriftfeld |
| 2 | Steuernummer oder USt-IdNr. des leistenden Unternehmers | USt-IdNr. des Unternehmens, Steuernummer aus den Einstellungen | Fuß, beide, wenn es beide gibt |
| 3 | Ausstellungsdatum | Buchungsdatum | Informationsblock „Rechnungsdatum“ |
| 4 | fortlaufende, einmalige Rechnungsnummer | Name des Belegs (Nummernkreis von ERPNext) | Betreff, Informationsblock, Fuß jeder Seite |
| 5 | Menge und handelsübliche Bezeichnung, Umfang und Art der Leistung | Positionen: Bezeichnung, Beschreibung, Menge, Einheit | Positionstabelle |
| 6 | Zeitpunkt der Lieferung oder Leistung | siehe [Leistungsdatum](#leistungsdatum) | Informationsblock, bei Positionen mit eigenem Zeitraum auch dort |
| 7 | Entgelt nach Steuersätzen und Steuerbefreiungen aufgeschlüsselt, vereinbarte Minderungen | Nettobetrag, je Steuerzeile ihre Bemessungsgrundlage, Rabatt, Skonto des Zahlungsplans | Summen, Zahlungsaufforderung |
| 8 | Steuersatz und Steuerbetrag oder Hinweis auf die Steuerbefreiung | Steuerzeilen des Belegs; Steuerfall der Vorlage | Summen („Umsatzsteuer 19 % auf …“); Hinweis unter den Summen |
| 9 | Hinweis auf die Aufbewahrungspflicht des Empfängers (§ 14b Abs. 1 Satz 5 UStG) | nicht umgesetzt | – |
| 10 | „Gutschrift“ bei Abrechnung durch den Leistungsempfänger | gilt nicht für die Ausgangsrechnung, siehe [Gutschrift im Gutschriftsverfahren](roadmap.md) | – |

Nr. 9 betrifft steuerpflichtige Werklieferungen und sonstige Leistungen im Zusammenhang mit einem Grundstück an Empfänger, die weder Unternehmer für ihr Unternehmen noch juristische Personen sind (§ 14 Abs. 2 Satz 2 Nr. 3, § 14b Abs. 1 Satz 5 UStG); Briefbote druckt diesen Hinweis noch nicht, die [Roadmap](roadmap.md) führt ihn.

Mehrere Steuersätze in einer Rechnung druckt das Format je Steuerzeile mit ihrer Bemessungsgrundlage (`net_amount` der Zeile in ERPNext), so dass das Entgelt nach Steuersätzen aufgeschlüsselt ist (Nr. 7): „Umsatzsteuer 19 % auf 5.292,00 €“. Unterscheiden sich die Positionen im Satz, bekommt jede Position eine Spalte „USt.“ mit ihrem Satz; den Satz je Position nimmt Briefbote aus der Tabelle `item_wise_tax_details` der Ausgangsrechnung (DocType Item Wise Tax Detail in ERPNext 16), bei einer Rechnung ohne diese Tabelle den einen Satz aller Steuerzeilen (`briefbote/invoice/taxes.py`). Positionen ohne Umsatzsteuer neben besteuerten stehen in den Summen als „Entgelt ohne Umsatzsteuer“, damit auch das Entgelt nach der Steuerbefreiung aufgeschlüsselt ist (Nr. 7 und 8); den Grund der Befreiung nennt die Position, etwa „steuerfrei nach § 4 Nr. 10 Buchst. a UStG“. Der Steuerbetrag ist der der Steuerzeile; gerundet hat ERPNext beim Buchen, auf den Cent genau, wie UStAE 14.5 Abs. 20 Satz 2 verlangt.

### Kleinbetragsrechnung und Kleinunternehmer

Eine Rechnung bis 250 Euro brutto braucht nach § 33 UStDV weniger Angaben, eine Rechnung eines Kleinunternehmers nach § 34a UStDV ebenfalls. Das Druckformat druckt trotzdem alle Angaben des § 14 Abs. 4 UStG: Sie schaden nicht, und § 33 Satz 3 UStDV schließt die Vereinfachung für innergemeinschaftliche Lieferungen und § 13b UStG ohnehin aus.

## Leistungsdatum

Die Rechnung nennt den Zeitpunkt der Lieferung oder Leistung immer ausdrücklich, als Datum oder Zeitraum (`document.service`), in dieser Reihenfolge:

1. **Leistungszeitraum der Rechnung:** die Felder `from_date` und `to_date` der Ausgangsrechnung. ERPNext 16 führt sie im Abschnitt „Subscription“; sie lassen sich auch nach dem Buchen setzen (`allow_on_submit`).
2. **Leistungszeiträume der Positionen:** Anfang und Ende der Leistung je Position (`service_start_date`, `service_end_date`), zusammen als Zeitraum vom frühesten Anfang bis zum spätesten Ende; jede Position druckt ihren Zeitraum zusätzlich.
3. **Lieferscheine:** das Datum des Lieferscheins der Positionen als „Lieferdatum“, bei mehreren als „Lieferzeitraum“.
4. **Rechnungsdatum:** sonst das Buchungsdatum als „Leistungsdatum“.

UStAE 14.5 Abs. 16 verlangt die Angabe auch, wenn das Leistungsdatum dem Rechnungsdatum entspricht. Ein Satz wie „Leistungsdatum entspricht Rechnungsdatum“ genügt nur bei Rechnungen, die keine E-Rechnung sind, und ersetzt in der E-Rechnung nicht das strukturierte Feld. Briefbote druckt deshalb stets das Datum selbst. Der ganze Leistungszeitraum genügt (UStAE 14.5 Abs. 16 Nr. 4), ebenso der Kalendermonat (§ 31 Abs. 4 UStDV).

## Steuerfälle und Hinweise

Welcher Steuerfall eine Rechnung ist, sagen die Einstellungen Geschäftspost: Jede Vorlage für Verkaufssteuern bekommt dort ihren Steuerfall. Eine Vorlage ohne Zeile ist ein im Inland steuerpflichtiger Umsatz. Der Hinweis steht fett unter den Summen, in der Sprache der Rechnung.

| Steuerfall | Hinweis (deutsch) | Quelle |
|---|---|---|
| Im Inland steuerpflichtig | keiner | – |
| Innergemeinschaftliche Lieferung | „Steuerfreie innergemeinschaftliche Lieferung (§ 4 Nr. 1 Buchst. b i. V. m. § 6a UStG).“ und beide USt-IdNrn. im Informationsblock | § 14 Abs. 4 Satz 1 Nr. 8, § 14a Abs. 3 UStG; UStAE 14a.1 Abs. 4 |
| Leistung an Unternehmen in einem anderen EU-Staat | „Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge). Die Leistung ist im Inland nicht steuerbar (§ 3a Abs. 2 UStG).“ und beide USt-IdNrn. | § 14a Abs. 1 UStG; UStAE 14a.1 Abs. 2 Satz 3, Abs. 6 Satz 2 |
| Steuerschuldnerschaft des Leistungsempfängers im Inland | „Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge, § 13b UStG).“ | § 13b Abs. 2, 5, § 14a Abs. 5 UStG; UStAE 13b.14 Abs. 1 |
| Ausfuhrlieferung | „Steuerfreie Ausfuhrlieferung (§ 4 Nr. 1 Buchst. a i. V. m. § 6 UStG).“ | § 14 Abs. 4 Satz 1 Nr. 8 UStG; UStAE 14.5 Abs. 20 |
| Leistung an Unternehmen außerhalb der EU | „Im Inland nicht steuerbare Leistung: Der Leistungsort liegt außerhalb der EU (§ 3a Abs. 2 UStG).“ | kein Pflichthinweis, siehe [Strittig](#strittig-und-vorsichtig-gelöst) |
| Steuerfrei | „Steuerfreie Leistung: “ und der Grund aus der Zeile des Steuerfalls oder dem Feld `tax_exemption_reason` des Belegs (erpnext_germany) | § 14 Abs. 4 Satz 1 Nr. 8 UStG; UStAE 14.5 Abs. 20 |
| Kleinunternehmer (Einstellung des Unternehmens) | „Gemäß § 19 UStG wird keine Umsatzsteuer berechnet (Steuerbefreiung für Kleinunternehmer).“, für jede Rechnung des Unternehmens | § 19 Abs. 1 UStG, § 34a Satz 1 Nr. 5 UStDV; UStAE 14.7a Abs. 1 |

Zum Wortlaut:

- **Steuerschuldnerschaft des Leistungsempfängers.** § 14a Abs. 1 und 5 UStG verlangen genau diese Angabe. Statt ihrer kommt die Formulierung der Amtssprache eines anderen Mitgliedstaats in Betracht, etwa „Reverse charge“ nach Art. 226 Nr. 11a der Mehrwertsteuer-Systemrichtlinie (UStAE 14a.1 Abs. 6 Satz 2, Anlage 8). Die deutsche Rechnung druckt beides, die englische „Reverse charge“ mit dem deutschen Begriff im Text. Eine Rechnung nach § 13b UStG weist keine Steuer aus; tut sie es, schuldet der leistende Unternehmer sie nach § 14c Abs. 1 UStG (UStAE 13b.14 Abs. 1). Der Nachweis der CI prüft, dass auf diesen Rechnungen kein Steuerbetrag steht.
- **Steuerbefreiungen.** Die Vorschrift muss nicht genannt werden, ein Hinweis in Worten genügt (UStAE 14.5 Abs. 20 Satz 4 bis 6). Briefbote nennt sie trotzdem, weil die Nennung den Grund eindeutig macht.
- **Beide USt-IdNrn.** verlangen § 14a Abs. 1 Satz 3 und Abs. 3 Satz 2 UStG bei der innergemeinschaftlichen Lieferung und der Leistung nach § 3a Abs. 2 UStG in einen anderen Mitgliedstaat. Der Informationsblock nennt dann „Ihre USt-IdNr.“ und „Unsere USt-IdNr.“; die USt-IdNr. des Kunden steht auch sonst dort, wenn der Beleg eine hat. Für einen Kleinunternehmer entfällt die Pflicht (§ 19 Abs. 1 Satz 2 UStG).
- **Verbraucher.** Ist der Kunde eine Privatperson (`customer_type` „Individual“), druckt die Rechnung den Hinweis des § 286 Abs. 3 Satz 1 BGB: „Zahlen Sie nicht innerhalb von 30 Tagen nach Fälligkeit und Zugang dieser Rechnung, kommen Sie auch ohne Mahnung in Verzug (§ 286 Abs. 3 BGB).“ Ohne ihn kommt ein Verbraucher nach dieser Vorschrift nicht in Verzug.

## Rechnungskorrektur, Stornorechnung, kaufmännische Gutschrift

- **Bezug auf die Rechnung.** Eine Berichtigung muss durch ein Dokument geschehen, das spezifisch und eindeutig auf die Rechnung bezogen ist (§ 31 Abs. 5 Satz 2 UStDV); das ist regelmäßig der Fall, wenn es die Nummer der ursprünglichen Rechnung nennt (UStAE 14.11 Abs. 1). Rechnungskorrektur und Stornorechnung nennen Nummer und Datum der Rechnung im Betreff und im Informationsblock („Rechnung: RE-… vom …“) und haben selbst eine eigene Nummer, die zulässig, aber nicht vorgeschrieben ist. Sie tragen alle Angaben des § 14 Abs. 4 UStG wie eine Rechnung (§ 31 Abs. 5 Satz 3 UStDV).
- **Kein „Gutschrift“ für Korrekturen.** Die im allgemeinen Sprachgebrauch so bezeichnete Stornierung oder Korrektur einer Rechnung ist keine Gutschrift (UStAE 14.3 Abs. 2 Satz 5). „Gutschrift“ ist nach § 14 Abs. 2 Satz 5 und Abs. 4 Satz 1 Nr. 10 UStG die Rechnung, die der Leistungsempfänger ausstellt. Briefbote nennt Korrekturen deshalb „Rechnungskorrektur“ und „Stornorechnung“. Die Stornorechnung ist die Rechnungskorrektur, die die ganze Rechnung aufhebt: Ihr Gesamtbetrag gleicht den der Rechnung auf den Cent aus.
- **Kaufmännische Gutschrift.** Eine Rückgabe ohne Bezug auf eine Rechnung, etwa ein Bonus oder ein Nachlass, heißt „Kaufmännische Gutschrift“ und sagt: „Diese Gutschrift mindert das Entgelt für frühere Lieferungen oder Leistungen (§ 17 UStG). Sie ist keine Gutschrift im Sinne des § 14 Abs. 2 Satz 5 UStG.“ Die Bezeichnung als „Gutschrift“ allein führt nicht zu § 14c UStG (UStAE 14c.1 Abs. 3 Satz 4); der Satz hält das Dokument trotzdem eindeutig vom Gutschriftsverfahren getrennt. Eine Minderung nach § 17 UStG, etwa durch Skonto oder Nachlass, braucht keine Rechnungsberichtigung (UStAE 14.11 Abs. 4).
- **Keine Zahlungsaufforderung und keine Geschäftsbedingungen** auf Korrekturen und Gutschriften; ihre Summe heißt „Korrekturbetrag“, „Stornierter Betrag“ oder „Gutgeschriebener Betrag“.

## Zahlung

Eine offene Rechnung schließt mit der Bitte, den Betrag bis zur Fälligkeit zu überweisen, auf das Konto im Fuß, wenn die Einstellungen eines nennen. Ein Zahlungsplan mit mehreren Raten druckt jede Rate mit ihrer Fälligkeit, ein Skonto als „2 % Skonto bei Zahlung bis zum …“; diese Angabe genügt für eine im Voraus vereinbarte Minderung des Entgelts (UStAE 14.5 Abs. 19). Anzahlungen, die ERPNext der Rechnung zugeordnet hat, stehen als „Abzüglich erhaltener Anzahlungen“ mit dem Betrag „Zu zahlen“ unter dem Gesamtbetrag. Die Geschäftsbedingungen des Belegs stehen am Ende.

## Sprache

Die Rechnung druckt in der Sprache, in der Frappe druckt: Die Druckansicht wählt die Sprache des Belegs (Feld `language` der Ausgangsrechnung), sonst die des Druckformats, sonst die des Benutzers (`set_default_print_language` in `frappe/printing/page/print/print.js` von Frappe 16); das Druckformat „Rechnung“ legt keine eigene Sprache fest. Briefbote bringt Deutsch und Englisch. Die Texte stehen englisch im Code und deutsch in `briefbote/translations/de.csv` mit dem Kontext „Briefbote“. Daten und Beträge formatiert Frappe nach den Systemeinstellungen, in beiden Sprachen gleich. Den Hinweis „Reverse charge“ lässt UStAE 14a.1 Abs. 6 Satz 2 ausdrücklich zu.

## Papierrechnung und E-Rechnung

Eine Rechnung auf Papier oder als PDF ist seit 2025 eine „sonstige Rechnung“. Für Umsätze zwischen inländischen Unternehmern ist sie nur noch im Übergang zulässig: für Umsätze bis zum 31.12.2026 allgemein, für Umsätze im Jahr 2027 nur, wenn der Gesamtumsatz des Ausstellers im Vorjahr 800.000 Euro nicht überstiegen hat (§ 27 Abs. 38 UStG). Danach ist im inländischen B2B-Verkehr die E-Rechnung die Rechnung, und das PDF ist eine lesbare Darstellung. Kleinbetragsrechnungen, Rechnungen von Kleinunternehmern und Rechnungen an Empfänger, die nicht im Inland ansässig sind, dürfen weiter sonstige Rechnungen sein (§ 33 Satz 4, § 34a Satz 4 UStDV; UStAE 14.1 Abs. 4). Briefbote erzeugt keine E-Rechnung; das tut eine App wie eu_einvoice, die ihr XML in das PDF des Druckformats einbetten kann, siehe [Architektur](architektur.md#zusammenspiel-mit-anderen-apps).

## Aufbewahrung

Eine Kopie jeder ausgestellten Rechnung bewahrt der Aussteller acht Jahre auf (§ 14b Abs. 1 UStG, § 147 Abs. 1 Nr. 4, Abs. 3 AO, § 257 HGB); nachträgliche Änderungen sind nicht zulässig (UStAE 14b.1 Abs. 5). Ein Druckformat druckt, was beim Drucken in ERPNext steht; ein später gedrucktes PDF kann von dem abweichen, das versandt wurde, etwa nach geänderten Einstellungen. Wer das versandte PDF aufbewahren muss, lässt es beim Buchen anhängen (zum Beispiel mit pdf_on_submit) oder archiviert die versandte E-Mail.

## Strittig und vorsichtig gelöst

- **Leistung an Unternehmen außerhalb der EU.** Kein Gesetz verlangt hier einen Hinweis: §§ 14, 14a UStG gelten für im Inland steuerbare Umsätze (UStAE 14.1 Abs. 20 Satz 1), § 14a Abs. 1 UStG nur für Leistungen in einen anderen Mitgliedstaat, und § 14 Abs. 4 Satz 1 Nr. 8 UStG für Steuerbefreiungen; ein nicht steuerbarer Umsatz ist keine. Briefbote druckt trotzdem einen Hinweis, damit die Rechnung erklärt, warum sie keine Steuer ausweist, und nennt die Leistung „nicht steuerbar“, nie „steuerfrei“. Ob der Staat des Kunden einen eigenen Hinweis verlangt, prüft das Unternehmen.
- **Bezeichnung der kaufmännischen Gutschrift.** Seit UStAE 14c.1 Abs. 3 Satz 4 ist das Wort „Gutschrift“ für sie steuerlich unschädlich; ältere Verwaltungsauffassung und Literatur sahen ein Risiko. Briefbote nennt sie „Kaufmännische Gutschrift“ und grenzt sie im Text ausdrücklich vom Gutschriftsverfahren ab.
- **Leistungsdatum gleich Rechnungsdatum.** Zulässig wäre bei sonstigen Rechnungen der Satz „Leistungsdatum entspricht Rechnungsdatum“ (UStAE 14.5 Abs. 16). Briefbote druckt stattdessen immer das Datum.
- **Angaben nach § 35a GmbHG auf Rechnungen.** Ob Rechnungen in einer bestehenden Geschäftsverbindung unter die Ausnahme für Vordrucke (§ 35a Abs. 2 GmbHG) fallen, ist umstritten. Briefbote druckt die Angaben auf jeder Seite jedes Dokuments auf leerem Papier, siehe [Geschäftsbrief](geschaeftsbrief.md).
- **Steuernummer und USt-IdNr.** § 14 Abs. 4 Satz 1 Nr. 2 UStG verlangt eine von beiden. Der Fuß druckt beide, wenn das Unternehmen beide hat.

## Was das Druckformat nicht kann

- Die Anzahlungsrechnung und die Endrechnung nach § 14 Abs. 5 UStG, siehe [Anzahlungen](#anzahlungen-und-endrechnung).
- Den Hinweis auf die Aufbewahrungspflicht des Empfängers (§ 14 Abs. 4 Satz 1 Nr. 9 UStG).
- Das innergemeinschaftliche Dreiecksgeschäft (§ 25b UStG, § 14a Abs. 7 UStG) und Differenzbesteuerung (§ 25a UStG): Diese Fälle haben noch keinen Steuerfall.
- Rechnungen in Fremdwährung druckt das Format mit den Beträgen des Belegs in seiner Währung; was eine solche Rechnung zusätzlich in Euro angeben sollte, ist noch nicht geprüft und nicht umgesetzt.

## Anzahlungen und Endrechnung

§ 14 Abs. 5 UStG: Wer ein Entgelt vor der Leistung vereinnahmt, rechnet darüber wie über eine Leistung ab (Satz 1), und die Rechnung macht kenntlich, dass über eine noch nicht erbrachte Leistung abgerechnet wird (UStAE 14.5 Abs. 16); die Endrechnung setzt die vor der Leistung vereinnahmten Teilentgelte und die Steuer darauf ab, wenn über sie Rechnungen ausgestellt wurden (Satz 2). So bildet ERPNext 16 das ab, gesehen im Code:

- Eine Anzahlung ist ein Zahlungseingang (Payment Entry) gegen den Auftrag. Er kann eine Steuer tragen (Tabelle `taxes`, DocType Advance Taxes and Charges mit Satz, Betrag und Bemessungsgrundlage `net_amount`); Anzahlungen lassen sich auf einem eigenen Konto buchen (`book_advance_payments_in_separate_party_account`).
- Die Ausgangsrechnung über die Leistung ordnet sich Anzahlungen in ihrer Tabelle `advances` zu (Sales Invoice Advance: `reference_type`, `reference_name`, `advance_amount`, `allocated_amount`, `remarks`); `total_advance` und `outstanding_amount` folgen daraus.
- Ein eigener Beleg „Anzahlungsrechnung“ fehlt. Die Proforma-Rechnung von ERPNext 16 ist eine Kopie des Auftrags und bucht nichts; der Zahlungseingang ist kein Dokument an den Kunden.

Briefbote druckt heute unter dem Gesamtbetrag „Abzüglich erhaltener Anzahlungen“ mit `total_advance` und „Zu zahlen“. Für eine Endrechnung nach § 14 Abs. 5 Satz 2 UStG fehlt je Anzahlung der Ausweis von Entgelt und Steuer; er ließe sich aus den Steuerzeilen der zugeordneten Zahlungseingänge lesen, aber nur, wenn jede Anzahlung mit Steuer gebucht ist und ihre Rechnung über die Anzahlung ausgestellt wurde. Für die Anzahlungsrechnung fehlt ein Beleg, aus dem sie druckt: ein Druckformat für den Zahlungseingang wäre keine Rechnung über eine noch nicht erbrachte Leistung, weil die Rechnung vor der Zahlung kommt. Beides bleibt offen, bis entschieden ist, aus welchem Beleg die Anzahlungsrechnung entsteht ([Roadmap](roadmap.md)).

## Seiten

Jede Seite nennt im Fuß das Dokument mit Nummer und Seite, „Rechnung RE-2026-0101 · Seite 1 von 2“, bei einer Korrektur „Rechnungskorrektur RE-… · Seite …“, damit eine lose Seite zuzuordnen ist.

## Offen für die fachliche Prüfung

Diese Formulierungen und Entscheidungen soll eine Steuerberatung oder ein Rechtsanwalt bestätigen, bevor Briefbote in Betrieb geht. Bis dahin gilt die vorsichtige Lösung, die die Seite beschreibt.

| Punkt | Was Briefbote druckt | Frage |
|---|---|---|
| Innergemeinschaftliche Lieferung | „Steuerfreie innergemeinschaftliche Lieferung (§ 4 Nr. 1 Buchst. b i. V. m. § 6a UStG).“ | Wortlaut ausreichend und richtig zitiert? |
| Leistung an Unternehmen in der EU | „Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge). Die Leistung ist im Inland nicht steuerbar (§ 3a Abs. 2 UStG).“ | Ist der zweite Satz richtig und nützlich? |
| § 13b UStG im Inland | „Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge, § 13b UStG).“ | Wortlaut ausreichend? |
| Ausfuhr | „Steuerfreie Ausfuhrlieferung (§ 4 Nr. 1 Buchst. a i. V. m. § 6 UStG).“ | Wortlaut ausreichend? |
| Leistung an Unternehmen außerhalb der EU | „Im Inland nicht steuerbare Leistung: Der Leistungsort liegt außerhalb der EU (§ 3a Abs. 2 UStG).“ | Kein Pflichthinweis; ist der Hinweis so richtig? |
| Steuerfrei | „Steuerfreie Leistung: “ mit dem Grund aus den Einstellungen | Genügt der Grund in Worten mit Vorschrift? |
| Kleinunternehmer | „Gemäß § 19 UStG wird keine Umsatzsteuer berechnet (Steuerbefreiung für Kleinunternehmer).“ | Wortlaut nach der Neufassung des § 19 UStG ab 2025 ausreichend? |
| Kaufmännische Gutschrift | Titel „Kaufmännische Gutschrift“ und „Diese Gutschrift mindert das Entgelt für frühere Lieferungen oder Leistungen (§ 17 UStG). Sie ist keine Gutschrift im Sinne des § 14 Abs. 2 Satz 5 UStG.“ | Titel und Satz so richtig, auch für Gutschriften, die keine Entgeltminderung sind? |
| Stornorechnung und Rechnungskorrektur | eigene Nummer, Bezug „zur Rechnung … vom …“, alle Angaben einer Rechnung | Genügt der Bezug nach § 31 Abs. 5 UStDV? |
| Verbraucher | „Zahlen Sie nicht innerhalb von 30 Tagen nach Fälligkeit und Zugang dieser Rechnung, kommen Sie auch ohne Mahnung in Verzug (§ 286 Abs. 3 BGB).“ | Genügt der Hinweis als „besonders hingewiesen“? |
| Positionen ohne Steuer | „Entgelt ohne Umsatzsteuer“ in den Summen, Grund an der Position | Genügt das für mehrere Befreiungen in einer Rechnung? |
| Angaben nach § 35a GmbHG | auf jeder Seite jedes Dokuments auf leerem Papier | Nötig auf Rechnungen in laufender Geschäftsverbindung? |
| Gutschrift im Gutschriftsverfahren | Titel „Gutschrift“, Satz „Abrechnung durch den Leistungsempfänger im Gutschriftsverfahren (§ 14 Abs. 2 Satz 5 UStG).“, Steuer als „Umsatzsteuer“ | Wortlaut richtig, siehe [Gutschrift](gutschrift.md)? |

## Nachweis

Die CI druckt jede Rechnung aus `briefbote/tests/print_documents.py` mit beiden PDF-Generatoren und prüft die Seiten, siehe [Entwicklung](entwicklung.md#ausdrucke-als-pdf). Die Prüfliste dieser Seite gilt als erfüllt, wenn für jeden Steuerfall und jede Art von Dokument ein Beleg des Nachweises die Angaben oben trägt und alle Ausdrucke ohne Problem sind.
