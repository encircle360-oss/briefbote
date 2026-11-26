# Kontoauszug

<a href="bilder/beispiele/kontoauszug.png"><img src="bilder/beispiele/kontoauszug.png" width="280" alt="Kontoauszug KA-2026-0004 an einen Lieferanten: offene Posten zum Stichtag mit seinen Rechnungsnummern, Datum, Fälligkeit, Betrag, Bezahltem und Offenem, dem Saldo unter der Spalte Offen und dem Satz, zu wessen Gunsten der Saldo steht"></a>

Beispiel aus den erfundenen Daten des Nachweises: [Kontoauszug als PDF](beispiele/kontoauszug.pdf).

Das Druckformat „Kontoauszug“ druckt die offenen Posten eines Kunden oder Lieferanten zu einem Stichtag (Offene-Posten-Liste) und den Saldo. Es gehört zum DocType **Kontoauszug** (`Party Statement`) von Briefbote, den es nur gibt, weil ein Druckformat in Frappe zu einem DocType gehört und ein Auszug „je Kunde zum Stichtag“ sonst keinen Beleg hätte (siehe [Warum ein eigener DocType](#warum-ein-eigener-doctype)). Aus demselben Beleg druckt die [Saldenbestätigung](saldenbestaetigung.md).

Die Regeln stehen in `briefbote/statement/statement.py`, das Lesen in `briefbote/briefbote/statement.py` (`briefbote_statement`), der DocType unter `briefbote/briefbote/doctype/party_statement/`, das Layout in `briefbote/briefbote/print_format/kontoauszug/` mit `payment_letter.html`, das auch Zahlungsbestätigung, Quittung und Zahlungsavis drucken.

Die Quellen sind das GmbHG in der Fassung von [gesetze-im-internet.de](https://www.gesetze-im-internet.de/), gelesen am 26.11.2026, und der Code von ERPNext und Frappe in den Zweigen `version-16` (ERPNext Commit `d770a3a`, Version 16.61.0; Frappe Commit `8b19f8c`), gelesen am 26.11.2026.

## So entsteht ein Kontoauszug

1. Im Desk unter Geschäftspost → Kontoauszüge einen neuen Kontoauszug anlegen: Art „Offene Posten“, Unternehmen, Datum, Stichtag, Kunde oder Lieferant.
2. Speichern: Der Entwurf liest die offenen Posten aus den Büchern und zeigt sie in der Tabelle; jedes Speichern und jeder Druck des Entwurfs liest neu.
3. Buchen: Der Kontoauszug behält die Zeilen und Salden, die er beim Buchen gelesen hat, und druckt von da an nur noch sie.
4. Drucken mit „Kontoauszug“.

Ein gebuchter Kontoauszug ändert sich nicht mehr, auch wenn später eine Buchung mit einem Datum vor dem Stichtag dazukommt: Was verschickt wurde, druckt wieder genau so. Wer den Stand von heute will, legt einen neuen Kontoauszug an oder storniert und berichtigt den alten. Ein **Entwurf ist live**: Er zeigt die Bücher, wie sie gerade sind, und trägt die Markierung „ENTWURF“. Ein stornierter Kontoauszug trägt „STORNIERT“ und den Befund „Dieses Dokument ist storniert.“, druckt seine Zeilen, aber weder den Satz über die offenen Posten noch den Saldo als Aussage.

## Woher die Zahlen kommen

Briefbote rechnet keine offenen Posten selbst aus. Die Zeilen sind die des Berichts **Accounts Receivable** (Kunde) oder **Accounts Payable** (Lieferant) von ERPNext für genau diese Partei zum Stichtag, aufgerufen wie ERPNexts Process Statement Of Accounts ihn aufruft (`execute` in `erpnext/accounts/report/accounts_receivable/accounts_receivable.py` und `accounts_payable/accounts_payable.py`):

- Der Bericht liest das Payment Ledger („This report is based on Payment Ledger Entries“, Kommentar am Kopf von `accounts_receivable.py`) bis einschließlich des Stichtags (`prepare_ple_query`: `posting_date` kleiner oder gleich `report_date`). Eine Zahlung nach dem Stichtag fehlt also, auch wenn sie schon gebucht ist.
- Je Beleg nimmt Briefbote Betrag (`invoiced`), Bezahlt (`paid` plus `credit_note`) und Offen (`outstanding`) des Berichts, dazu Datum, Fälligkeit und die eigene Nummer des Partners: bei Lieferanten `bill_no` der Eingangsrechnung, bei Kunden `po_no` der Ausgangsrechnung (`get_invoice_details`). Eine Zahlung, die keiner Rechnung zugeordnet ist, steht als eigene Zeile mit negativem offenem Betrag.
- Briefbote sortiert die Zeilen nach Datum und Nummer und addiert die offenen Beträge je Währung. Das ist dieselbe Summe, die der Bericht als Summenzeile bildet.

**Währung:** Briefbote ruft den Bericht mit `in_party_currency` auf. Dann stehen die Beträge in der Währung des Kontos der Partei (`amount_in_account_currency`, `set_party_details` setzt `currency` auf `account_currency`). Beträge verschiedener Währungen werden nie addiert: Jede Währung bekommt ihre eigene Saldozeile („Saldo in USD“) und ihren eigenen Satz. Gewöhnlich hat eine Partei ein Konto und eine Währung.

**Wer den Kontoauszug sehen darf:** Accounts User und Accounts Manager. Der Bericht Accounts Receivable ist für diese beiden Rollen freigegeben, Accounts Payable zusätzlich für Purchase User und Auditor (`accounts_receivable.json`, `accounts_payable.json`). Ein Kontoauszug kann beides zeigen, deshalb bekommen nur die Rollen Zugriff, die beide Berichte sehen dürfen. Benutzerrechte auf Kunden und Lieferanten wendet der Bericht selbst an (`add_user_permission_filters`).

## Angaben

| Angabe | Woher sie kommt |
|---|---|
| Nummer | Nummernkreis KA-JJJJ-NNNN |
| Datum, Stichtag | `posting_date`, `report_date` des Kontoauszugs |
| Kunden- oder Lieferantennummer | `party`, wenn sie vom Namen abweicht |
| Anschrift | Hauptanschrift der Partei (`customer_primary_address`, `supplier_primary_address`, sonst die Standardanschrift) |
| Beleg | Rechnung, Korrektur (Rückgabe), Zahlung, Buchung, sonst Beleg |
| Ihre Bestellung / Ihre Rechnung | `po_no` bzw. `bill_no`; die Spalte erscheint nur, wenn eine Zeile sie hat |
| Datum, Fällig am, Betrag, Bezahlt, Offen | Spalten des Berichts |
| Saldo | Summe der offenen Beträge je Währung, unter der Spalte Offen |
| Schlusssatz | „Zum … beträgt der Saldo … zu unseren Gunsten.“ (Forderung) oder „… zu Ihren Gunsten.“ (Verbindlichkeit, Guthaben des Kunden), „Zum … ist Ihr Konto ausgeglichen.“ |

Der Kontoauszug fordert nicht zur Zahlung auf. Dafür gibt es die [Mahnung](mahnung.md).

## Warum ein eigener DocType

Ein Druckformat gehört in Frappe zu einem DocType oder zu einem Bericht. Für einen Auszug je Partei zum Stichtag gab es drei Wege in ERPNext 16. Keiner erfüllt die Regeln von Briefbote:

| Weg | Was er kann | Was er nicht kann |
|---|---|---|
| Process Statement Of Accounts | eigene Vorlage als Berichtsformat (Jinja, `print_format` muss zum Bericht passen, `validate` in `process_statement_of_accounts.py`); Daten aus Accounts Receivable bzw. General Ledger | Die Vorlage bekommt keinen Beleg, nur Filter und Zeilen (`get_html`). Das PDF entsteht immer mit wkhtmltopdf (`get_report_pdf` ruft `frappe.utils.pdf.get_pdf`, das `pdfkit` nutzt). Kein Generator auf Chromium-Basis, keine Nummer, kein gebuchter Stand. |
| Berichtsformat für Accounts Receivable | Jinja-Berichtsformate gibt es in Frappe 16 (`render_report_jinja`, `download_report_pdf` in `frappe/utils/print_format.py`) | „Drucken“ setzt das HTML im Browser aus Zeilen, die der Browser schickt; „PDF“ druckt mit `get_pdf`, also wieder nur wkhtmltopdf. Kein Beleg, keine Nummer, kein gebuchter Stand. |
| Format auf dem Kunden | beide Generatoren über `get_print` | Kein Stichtag (die Druckansicht fragt kein Datum ab), also nur „heute“. Keine Nummer, kein Entwurf und kein Storno, weil ein Kunde nicht gebucht wird. |

Der DocType Kontoauszug gibt dem Auszug einen Beleg mit Nummer, Datum, Stichtag und Status. Er druckt mit beiden Generatoren über den normalen Druck von Frappe und hält fest, was verschickt wurde. Die Zahlen bleiben die des Berichts von ERPNext.

## Was nicht abgebildet ist

- **Kontobewegungen über einen Zeitraum** (Anfangssaldo, Buchungen, Endsaldo aus dem Hauptbuch): noch nicht. Der Kontoauszug zeigt die offenen Posten zum Stichtag.
- **Serienversand** an viele Kunden: Jeder Kontoauszug ist ein eigener Beleg. Process Statement Of Accounts von ERPNext bleibt für den Versand vieler Auszüge per E-Mail, mit seinen eigenen Vorlagen.
- **Altersstruktur** (30/60/90 Tage): Der Bericht rechnet sie, Briefbote druckt sie nicht.

## Offen für die fachliche Prüfung

| Punkt | Was Briefbote druckt | Frage |
|---|---|---|
| Form | Brief nach DIN 5008 mit den Angaben zum Unternehmen im Fuß | Ein Kontoauszug an einen Geschäftspartner hat nach Kenntnis von Briefbote keine gesetzlich vorgeschriebene Form. Stimmt das, und greift für ihn die Ausnahme des § 35a Abs. 2 GmbHG? |
| Gutschrift des Kunden | negativer offener Betrag, Satz „zu Ihren Gunsten“ | Ist die Bezeichnung des Saldos aus Sicht des Empfängers verständlich genug? |
| Stichtag | Ende des Stichtags, Buchungsdatum ≤ Stichtag | Genügt das Buchungsdatum, oder braucht ein Auszug zum Jahresende einen Hinweis auf noch nicht gebuchte Belege? |

## Nachweis

`briefbote/tests/print_documents_statement.py` schreibt für die Rechnungen und Zahlungen des Nachweises die Einträge des Payment Ledger, die ERPNext beim Buchen schriebe. Die Belege des Nachweises werden ohne Buchung geschrieben (siehe [Entwicklung](entwicklung.md#ausdrucke-als-pdf)), deshalb geht nur dieser Teil direkt in die Datenbank. Die Kontoauszüge legt das Modul danach mit allen Prüfungen an und bucht sie, so dass der Bericht von ERPNext ihre Zeilen liefert. `briefbote/tests/test_statement_printing.py` prüft, dass der Bericht genau die geschriebenen Posten zurückgibt.

`briefbote/tests/print_proof_statement.py` druckt mit beiden Generatoren:
- KA-2026-0001: Kunde mit 43 offenen Posten über mehrere Seiten, mit wiederholtem Tabellenkopf, einer teilweise bezahlten Rechnung und einer nicht zugeordneten Zahlung, auf leerem und vorgedrucktem Papier. Die Zahlung vom Tag nach dem Stichtag fehlt.
- KA-2026-0002: englisch.
- KA-2026-0003: ein Konto ohne offene Posten.
- KA-2026-0004: Lieferant mit seinen Rechnungsnummern.
- KA-2026-0005 und KA-2026-0006: ein gebuchter Kontoauszug, der nach einer später geschriebenen Buchung vor dem Stichtag seine Zeilen behält, neben einem Entwurf, der die Buchung zeigt.
- KA-2026-0001 storniert und als Saldenbestätigung gedruckt; die Saldenbestätigung SB-2026-0001 als Kontoauszug gedruckt.

Gemessen wird, dass der Saldo an der rechten Kante der Spalte „Offen“ endet.
