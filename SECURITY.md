# Sicherheit

## Unterstützte Versionen

Sicherheitskorrekturen gibt es für den Branch `main` und die jeweils neueste Veröffentlichung. Ältere Stände werden nicht nachgepflegt.

## Sicherheitslücke melden

Bitte **nicht** als öffentliches Issue. Melde sie über die private Meldefunktion von GitHub: [„Report a vulnerability“](https://github.com/encircle360-oss/briefbote/security/advisories/new) unter *Security*. Die Meldung sehen nur du und die Maintainer des Repositorys. Ohne GitHub-Konto sende eine Beschreibung an **oss@encircle360.com**.

Hilfreich sind: betroffene Version, Schritte zum Nachstellen, mögliche Auswirkungen und, wenn vorhanden, ein Vorschlag zur Behebung. Keine echten Rechnungen, Kundendaten, Bankverbindungen oder Zugangsdaten mitschicken.

Wir bestätigen den Eingang so schnell wie möglich, in der Regel innerhalb weniger Werktage, und stimmen die Veröffentlichung einer Korrektur mit dir ab.

## Was Briefbote zusichert

- Ein Druckformat von Briefbote lädt nichts aus dem Netz: keine Schriften, Bilder, Stylesheets oder Skripte von fremden Servern und nichts über die Adresse der eigenen Site. Was es braucht, liegt in der App oder kommt aus der Datenbank der Site. Die CI druckt jedes Druckformat mit unerreichbarer Site-Adresse.
- Briefbote sendet keine Telemetrie und spricht mit keinem Server außer der eigenen ERPNext-Instanz.
- Abhängigkeiten, die Werkzeuge der CI und deren Regeln sind exakt gepinnt; Dependabot, `pip-audit`, Geheimnis-Scans, `zizmor`, die Frappe-`semgrep`-Regeln und CodeQL laufen in der CI.
