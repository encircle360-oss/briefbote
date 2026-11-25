# Angebot

Das Druckformat „Angebot“ druckt ein Angebot (Quotation) von ERPNext als Brief nach DIN 5008: Nummer, Datum und Gültigkeit im Informationsblock, die Positionen mit Alternativen und Preisen je Einheit, die Summen mit der Umsatzsteuer nach Satz und Bemessungsgrundlage wie auf der Rechnung, die Hinweise des Steuerfalls, die Zahlungsbedingungen, bis wann und wie der Kunde annimmt, und die Geschäftsbedingungen des Belegs.

Die Regeln stehen in `briefbote/sales/offer.py` und `briefbote/sales/taxes.py`, das Lesen des Belegs in `briefbote/briefbote/sales.py` (`briefbote_quotation`), das Layout in `briefbote/briefbote/print_format/angebot/angebot.html` mit den gemeinsamen Teilen unter `briefbote/templates/includes/briefbote/`.

Die Quellen sind Gesetz und Verordnung in der Fassung von [gesetze-im-internet.de](https://www.gesetze-im-internet.de/), gelesen am 25.11.2026, und der Umsatzsteuer-Anwendungserlass (UStAE) im Stand vom 13.11.2026.

## Was ein Angebot ist

Ein Angebot ist ein Antrag auf Abschluss eines Vertrags. Wer ihn macht, ist daran gebunden, „es sei denn, dass er die Gebundenheit ausgeschlossen hat“ ([§ 145 BGB](https://www.gesetze-im-internet.de/bgb/__145.html)). Setzt er eine Frist, kann der Kunde nur innerhalb der Frist annehmen ([§ 148 BGB](https://www.gesetze-im-internet.de/bgb/__148.html)); ohne Frist nur so lange, wie unter regelmäßigen Umständen mit einer Antwort zu rechnen ist ([§ 147 Abs. 2 BGB](https://www.gesetze-im-internet.de/bgb/__147.html)). Eine verspätete Annahme gilt als neues Angebot, eine Annahme mit Änderungen als Ablehnung mit neuem Angebot ([§ 150 BGB](https://www.gesetze-im-internet.de/bgb/__150.html)); darauf antwortet die [Auftragsbestätigung](auftragsbestaetigung.md).

Ein Angebot ist keine Rechnung: Rechnung ist ein Dokument, „mit dem über eine Lieferung oder sonstige Leistung abgerechnet wird“ ([§ 14 Abs. 1 Satz 1 UStG](https://www.gesetze-im-internet.de/ustg_1980/__14.html)). Das Angebot trägt deshalb keine Rechnungsnummer, kein Leistungsdatum, keine Fälligkeit und keine Bitte um Überweisung. Weil es für die Einordnung nicht auf die Bezeichnung ankommt (UStAE 14.1 Abs. 1 Satz 3 und 4), heißt es überall ausdrücklich „Angebot“.

## Angaben

Kein Gesetz schreibt den Inhalt eines Angebots vor. Briefbote druckt, was ein Angebot braucht, um angenommen zu werden, und nichts, was nicht im Beleg steht: Eine Angabe ohne Wert fehlt ganz, kein Feld steht leer.

| Angabe | Woher sie kommt | Wo sie steht | Quelle |
|---|---|---|---|
| Angaben zum Unternehmen | Unternehmen und Einstellungen Geschäftspost | Fuß jeder Seite auf leerem Papier | § 35a GmbHG, § 80 AktG, §§ 37a, 125 HGB, siehe [Geschäftsbrief](geschaeftsbrief.md) |
| Empfänger | `customer_name` und `customer_address`, auch für einen Interessenten (Lead) | Anschriftfeld | DIN 5008 |
| Angebotsnummer, Datum | Name des Belegs, `transaction_date` | Informationsblock, Betreff, Fuß | – |
| Kundennummer | `party_name`, wenn das Angebot an einen Kunden geht und die Nummer vom Namen abweicht | Informationsblock | – |
| Gültig bis | `valid_till` | Informationsblock und Schlusssatz | § 148 BGB |
| Positionen | Bezeichnung, Beschreibung, Menge, Einheit, Einzelpreis, Betrag | Positionstabelle | – |
| Alternativen | Positionen mit `is_alternative` | Positionstabelle mit Hinweis, nicht in den Summen | siehe unten |
| Preise je Einheit | Positionen mit Menge 0 | Positionstabelle ohne Menge und Betrag, mit Hinweis | siehe unten |
| Summen | Nettobetrag, Umsatzsteuer je Satz mit Bemessungsgrundlage, Gesamtbetrag | unter der letzten Position | § 3 PAngV für Verbraucher |
| Hinweise des Steuerfalls | Steuerfall der Vorlage für Verkaufssteuern in den Einstellungen | unter den Summen | wie auf der [Rechnung](rechnung.md#steuerfälle-und-hinweise) |
| Zahlungsbedingungen | Text oder Name der Zahlungsbedingung im Zahlungsplan | Schluss | – |
| Annahme | fester Satz, mit Frist, wenn `valid_till` gesetzt ist | Schluss | §§ 147, 148 BGB |
| Geschäftsbedingungen | `terms` des Belegs | Ende | – |

Der Schlusssatz lautet mit Frist „Dieses Angebot gilt bis zum 18.12.2026. Zur Annahme bestätigen Sie es uns bitte bis dahin schriftlich oder per E-Mail unter Angabe der Angebotsnummer.“ und ohne Frist „Zur Annahme bestätigen Sie uns dieses Angebot bitte schriftlich oder per E-Mail unter Angabe der Angebotsnummer.“ Wer anderes will, etwa ein freibleibendes Angebot, schreibt es in die Geschäftsbedingungen des Belegs.

## Alternativen und Preise je Einheit

ERPNext 16 kennt Alternativpositionen: Eine Position mit „Is Alternative“ steht hinter der Position, die sie ersetzen kann, und zählt nicht zu den Summen (`set_has_alternative_item` in `erpnext/selling/doctype/quotation/quotation.py`, `filter_rows` in `erpnext/controllers/taxes_and_totals.py`). Briefbote druckt sie mit ihrem Preis und dem Hinweis „Alternative zu Position 2, nicht im Gesamtbetrag enthalten.“; eine Alternative ganz oben ohne Position davor heißt „Alternativposition“. Sie bekommt keinen Steuersatz, weil ERPNext für sie keine Steuerdetails rechnet.

Erlauben die Selling Settings Angebote mit Menge 0 (`allow_zero_qty_in_quotation`), ist eine solche Position ein Preis je Einheit. Briefbote druckt dann weder Menge noch Betrag, sondern „Preis je Einheit, berechnet nach der gelieferten Menge, nicht im Gesamtbetrag enthalten.“

Eine Bedarfs- oder Eventualposition, die in den Gesamtbetrag nur auf Abruf eingeht, kennt ERPNext nicht. Sie lässt sich als Alternative oder als Preis je Einheit abbilden.

## Umsatzsteuer und Preisangaben

Die Summen zeigen die Umsatzsteuer wie die [Rechnung](rechnung.md): je Steuerzeile mit Satz und Bemessungsgrundlage, Positionen ohne Steuer neben besteuerten als „Entgelt ohne Umsatzsteuer“, die Spalte „USt.“, wenn die Positionen sich im Satz unterscheiden. Die Vorlagen, die der Einrichtungsassistent von ERPNext für Deutschland anlegt, haben Steuerzeilen mit dem Satz 0, und der Satz steht in der Artikelsteuervorlage jeder Position (`erpnext/setup/setup_wizard/data/country_wise_tax.json`); Briefbote nimmt Satz und Bemessungsgrundlage deshalb aus den Steuerdetails des Belegs (`item_wise_tax_details`), nicht aus der Steuerzeile.

Gegenüber Verbrauchern ist der Gesamtpreis anzugeben, der Preis einschließlich Umsatzsteuer ([§ 3 Abs. 1 PAngV](https://www.gesetze-im-internet.de/pangv_2022/__3.html), [§ 2 Nr. 3 PAngV](https://www.gesetze-im-internet.de/pangv_2022/__2.html)); wird ein Preis aufgegliedert, ist der Gesamtpreis hervorzuheben (§ 3 Abs. 3 PAngV). Der Gesamtbetrag steht fett und größer unter den Summen. Für Angebote an Unternehmer gilt die Preisangabenverordnung nicht ([§ 1 Abs. 1 PAngV](https://www.gesetze-im-internet.de/pangv_2022/__1.html)).

## Was ERPNext nicht abbildet

- **Bindung ausschließen:** Ein Feld für „freibleibend“ gibt es nicht; wer die Bindung ausschließen will, schreibt es in die Geschäftsbedingungen. Ob ein solches Wort die Bindung ausschließt, sagt das Gesetz nicht (siehe unten).
- **Eventualpositionen:** siehe oben.
- **Angebot an einen Interessenten:** Das Angebot an einen Lead druckt Name und Anschrift des Belegs, aber keine Kundennummer.

## Seiten

Jede Seite nennt im Fuß „Angebot AN-2026-0001 · Seite 1 von 2“. Der Kopf der Positionstabelle kehrt auf jeder Seite wieder, die letzte Position steht mit den Summen auf einer Seite.

## Offen für die fachliche Prüfung

| Punkt | Was Briefbote druckt | Frage |
|---|---|---|
| Schlusssatz mit Frist | „Dieses Angebot gilt bis zum …. Zur Annahme bestätigen Sie es uns bitte bis dahin schriftlich oder per E-Mail unter Angabe der Angebotsnummer.“ | Genügt der Satz als Annahmefrist nach § 148 BGB? Schränkt „schriftlich oder per E-Mail“ die Annahme unnötig ein? |
| Angebot ohne Frist | „Zur Annahme bestätigen Sie uns dieses Angebot bitte schriftlich oder per E-Mail …“ | Sollte ein Angebot ohne `valid_till` eine Frist nennen? |
| Freibleibende Angebote | nichts Eigenes; Text in den Geschäftsbedingungen | Schließt „freibleibend“ die Bindung nach § 145 BGB aus, und ist es gegenüber Verbrauchern ein Änderungsvorbehalt nach § 8 PAngV? |
| Preise an Verbraucher | Einzelpreise, wie der Beleg sie hat, netto oder brutto nach der Steuervorlage („im Druck enthalten“), Gesamtbetrag hervorgehoben | Genügt der hervorgehobene Gesamtbetrag nach § 3 PAngV, wenn die Einzelpreise netto sind? |
| Hinweise des Steuerfalls | dieselben Sätze wie auf der Rechnung, etwa zur Steuerschuldnerschaft des Leistungsempfängers | Sind sie auf einem Angebot richtig und nützlich? |
| Umsatzsteuer im Angebot | Steuer als Betrag je Satz | Kann ein angenommenes Angebot mit allen Angaben des § 14 Abs. 4 UStG als Rechnung gelten (UStAE 14.1 Abs. 17) und § 14c UStG auslösen? Das Angebot nennt kein Leistungsdatum. |

## Nachweis

Die CI schreibt mit `briefbote/tests/print_documents_sales.py` Angebote, wie ERPNext sie mit den deutschen Vorlagen bucht (Steuerzeilen mit Satz 0, Sätze in den Steuerdetails), und druckt sie mit `briefbote/tests/print_proof_sales.py` mit beiden PDF-Generatoren auf leerem und vorgedrucktem Papier, mit den Prüfungen der [Rechnung](entwicklung.md#ausdrucke-als-pdf): AN-2026-0001 mit Alternative, zwei Steuersätzen, Zahlungsbedingung und Geschäftsbedingungen; AN-2026-0002 mit 36 Positionen über mehrere Seiten; AN-2026-0003 an eine Privatperson ohne Frist mit einem Preis je Einheit; AN-2026-0004 englisch an ein Unternehmen in Österreich mit langem Namen; KA-2026-0001 eines Kleinunternehmers. Kein Ausdruck darf „Rechnungsdatum“, „Rechnungsnummer“, „Fällig am“, „Leistungsdatum“ oder „Bitte überweisen“ tragen.
