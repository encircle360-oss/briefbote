# Architektur

Briefbote ist eine Frappe-App für ERPNext 16. Sie bringt Druckformate, ein gemeinsames Gestaltungssystem für sie und die Einstellungen, die ein Unternehmen dafür braucht. Sie setzt nur ERPNext voraus.

## Aufbau des Repositories

```text
briefbote/                     Repository
├── briefbote/                 Python-Paket der Frappe-App
│   ├── hooks.py               App-Metadaten, setzt ERPNext voraus
│   ├── briefbote/             Frappe-Modul „Briefbote“
│   │   └── about.py           Über Briefbote: Version, Lizenz, Links, ohne Frappe-Import
│   ├── public/images/         Logo
│   ├── translations/de.csv    deutsche Texte der Oberfläche und der Ausdrucke
│   └── tests/                 Tests, die ohne Bench laufen, und Tests der Site
├── docs/                      Dokumentation
└── .github/                   Workflows, Vorlagen für Issues und Pull Requests
```
