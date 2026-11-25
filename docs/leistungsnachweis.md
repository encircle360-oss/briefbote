# Leistungsnachweis

Der Leistungsnachweis zeigt die Zeit, die eine Ausgangsrechnung abrechnet, Eintrag für Eintrag: Datum, Person, Tätigkeit und Beschreibung, Projekt und Aufgabe, Stunden; danach die Stunden je Projekt, je Person und in Summe und die Positionen der Rechnung, die sie abrechnen. Er druckt als Anlage hinter der Rechnung oder als eigenes Dokument. Die Regeln stehen in `briefbote/annex/timesheets.py`, das Lesen in `briefbote/briefbote/annex.py`, das Layout in `briefbote/templates/includes/briefbote/annex.html`.

## Rechtlicher Rahmen

Eine Rechnung kann aus mehreren Dokumenten bestehen; das Dokument mit Entgelt und Steuer muss die anderen bezeichnen (§ 31 Abs. 1 UStDV). Die Rechnung von Briefbote ist für sich vollständig: Sie beschreibt Art und Umfang der Leistung in ihren Positionen und nennt den Leistungszeitraum. Der Leistungsnachweis belegt die abgerechneten Stunden; die Rechnung bezeichnet ihn trotzdem („Anlage: Leistungsnachweis mit 194,75 Stunden.“), damit klar ist, dass beide zusammengehören.

## Wie ERPNext Zeit und Rechnung verbindet

ERPNext 16 erfasst Zeit in Stundenzetteln (Timesheet) mit ihren Zeiteinträgen (Timesheet Detail: Tätigkeit, von, bis, Stunden, abrechenbare Stunden `billing_hours`, Projekt, Aufgabe, Beschreibung, abrechenbar, Ausgangsrechnung). Die Ausgangsrechnung führt die abgerechneten Einträge in ihrer Tabelle `timesheets` (Sales Invoice Timesheet: Stundenzettel `time_sheet`, Zeiteintrag `timesheet_detail`, `billing_hours`, `billing_amount`, `activity_type`, `description`, `from_time`, `to_time`, `project_name`). Gesehen im Code von ERPNext 16.60.0:

- „Rechnung erstellen“ am Stundenzettel (`make_sales_invoice` in `erpnext/projects/doctype/timesheet/timesheet.py`) übernimmt jeden abrechenbaren, noch nicht abgerechneten Zeiteintrag als Zeile und legt, wenn ein Artikel gewählt ist, eine Position mit den offenen Stunden als Menge an.
- Beim Speichern füllt die Rechnung Stunden und Betrag einer Zeile aus ihrem Zeiteintrag (`set_billing_hours_and_amount` in `sales_invoice.py`); eine Zeile, die nur den Stundenzettel nennt, wird durch dessen offene Zeiteinträge ersetzt.
- Beim Buchen trägt die Rechnung sich in jeden ihrer Zeiteinträge ein (`update_time_sheet_detail`); ein Zeiteintrag wird damit ganz abgerechnet, nie zum Teil. Ein Stundenzettel, dessen Einträge auf mehrere Rechnungen verteilt sind, ist „teilweise abgerechnet“; jede Rechnung zeigt nur ihre Einträge.
- Abrechenbare Stunden (`billing_hours`) können von den gearbeiteten Stunden (`hours`) abweichen. Der Leistungsnachweis zeigt die abrechenbaren Stunden der Rechnung, weil sie es sind, die die Rechnung in Rechnung stellt.

## Was jede Spalte zeigt

| Spalte | Woher sie kommt |
|---|---|
| Datum | `from_time` der Zeile der Rechnung, ohne sie das Rechnungsdatum |
| Person | `employee_name` des Stundenzettels der Zeile, je nach Einstellung als Name, Initialen ohne Titel („EM“) oder Funktion (`designation` des Mitarbeiters); bei „Keine“ entfällt die Spalte |
| Tätigkeit | `activity_type` und `description` der Zeile |
| Projekt und Aufgabe | `project_name` der Zeile, sonst das Projekt des Zeiteintrags; die Aufgabe (`task`) des Zeiteintrags mit ihrem Betreff |
| Stunden | `billing_hours` der Zeile |

## Abgleich mit der Rechnung

Die Summe der Stunden muss der Menge der Positionen entsprechen, die die Rechnung nach Zeit abrechnet: der Positionen in der Zeiteinheit der Einstellungen (Feld „Zeiteinheit“, etwa „Hour“; leer heißt: kein Vergleich). Der Leistungsnachweis druckt die Summe und darunter „Abgerechnet in Position 1, 2“ mit der Menge dieser Positionen, so dass Kunde und Unternehmen beides vergleichen. Stimmen sie nicht überein, warnt die Rechnung beim Speichern; gespeichert wird sie trotzdem. Der Nachweis der CI prüft für seine Rechnung, dass beide gleich sind.

## Einstellungen

| Feld | Wofür |
|---|---|
| Leistungsnachweis drucken | „Mit der Rechnung“: auf eigenen Seiten hinter der Rechnung, nach einem Seitenumbruch, jede Seite mit dem Titel „Leistungsnachweis zur Rechnung … vom …“ im Kopf der Tabelle und im Fuß „Rechnung … · Seite n von N“ über alle Seiten. „Als eigenes Dokument“: nur mit dem Druckformat „Leistungsnachweis“. „Nicht drucken“: weder Anlage noch Hinweis auf der Rechnung |
| Person nennen mit | Name, Initialen, Funktion oder keine Person |
| Zeiteinheit | die Einheit der Positionen, die nach Zeit abrechnen |

Das Druckformat „Leistungsnachweis“ druckt den Nachweis einer Ausgangsrechnung als Brief nach DIN 5008 mit dem Informationsblock der Rechnung, gleich, was die Einstellung sagt.

## Zeit aus einer anderen Zeiterfassung

Wer die Zeit außerhalb von ERPNext erfasst und einspielt, muss für den Leistungsnachweis mindestens die Tabelle `timesheets` der Ausgangsrechnung füllen: je Eintrag `from_time` (Datum), `billing_hours`, `activity_type` (eine Activity Type, die es gibt), `description` und `project_name`. Für die Spalte Person und die Aufgabe braucht es dazu Stundenzettel mit Mitarbeiter (`employee`, `employee_name`) und Zeiteinträgen mit `task`, auf die die Zeilen mit `time_sheet` und `timesheet_detail` verweisen; der Zeiteintrag sollte `is_billable` gesetzt haben und mit `sales_invoice` auf die Rechnung zeigen, wie ERPNext es beim Buchen selbst tut. Die Positionen, die die Zeit abrechnen, tragen die Zeiteinheit der Einstellungen und als Menge die Summe der Stunden.
