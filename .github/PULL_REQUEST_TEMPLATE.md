## Was ändert sich?

<!-- Ein Thema pro Pull Request. Was ändert sich für Anwender, was intern? -->

## Quelle

<!-- Welche Quelle belegt eine fachliche Änderung? Gesetz, Verordnung, UStAE, BMF-Schreiben, DIN 5008, ERPNext-Code. -->

## Checkliste

- [ ] Tests zuerst: Jede Änderung hat einen Test, der ohne sie fehlschlägt. Kein Test wurde abgeschwächt.
- [ ] Die Dokumentation unter `docs/` und im README passt zum Code.
- [ ] Ein geändertes Druckformat ist im Artefakt `printouts` Seite für Seite angesehen, mit beiden PDF-Generatoren.
- [ ] Keine echten Rechnungen, Kundendaten, Bankverbindungen, Steuernummern oder Zugangsdaten in Code, Tests, Fixtures oder Screenshots.
- [ ] `pre-commit run --all-files` und `pytest` laufen lokal durch.
