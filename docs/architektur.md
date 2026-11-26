# Architektur

Briefbote ist eine Frappe-App für ERPNext 16. Sie bringt Druckformate, ein gemeinsames Gestaltungssystem für sie und die Einstellungen, die ein Unternehmen dafür braucht. Sie setzt nur ERPNext voraus.

## Aufbau des Repositories

```text
briefbote/                         Repository
├── briefbote/                     Python-Paket der Frappe-App
│   ├── hooks.py                   App-Metadaten, setzt ERPNext voraus, Eintrag in der App-Übersicht, Symbol des Moduls, Fixture des Blocks „Über Briefbote“, Jinja-Methoden der Druckformate, Skript der Druckansicht
│   ├── permissions.py             wem die App-Übersicht Briefbote zeigt
│   ├── layout/                    Kern ohne Frappe-Import: das Gestaltungssystem
│   │   ├── din5008.py             Maße eines Briefs nach DIN 5008, Form A und B
│   │   ├── theme.py               Gestaltung je Unternehmen: Akzentfarbe und ihr lesbarer Ton für kleine Schrift, Logo, Schrift
│   │   ├── columns.py             Breiten der Spalten aus ihrem Inhalt
│   │   ├── status.py              Markierung von Entwurf und Storno
│   │   ├── logo.py                Größe eines Logos aus PNG, JPEG oder SVG und seine Fläche im Briefkopf
│   │   ├── metrics.py             Breite einer Zeile in Inter, aus den Maßen der Schrift
│   │   ├── medium.py              Weg eines Ausdrucks: PDF-Generator, Vorschau oder Druck des Browsers
│   │   └── letter.py              Rücksendeangabe, Anschrift, Angaben zum Unternehmen im Fuß
│   ├── invoice/                   Kern ohne Frappe-Import: die Ausgangsrechnung
│   │   ├── document.py            Art des Dokuments, Steuerfälle und ihre Hinweise, Leistungsdatum
│   │   ├── taxes.py               Steuersatz je Position, Bemessungsgrundlage je Steuerzeile, Entgelt ohne Umsatzsteuer
│   │   ├── completeness.py        Befunde eines unvollständigen Dokuments nach § 14 Abs. 4, § 14a UStG
│   │   └── self_billing.py        Gutschrift im Gutschriftsverfahren: Titel, Steuerfälle im Einkauf, Hinweise
│   ├── proof/                     Kern ohne Frappe-Import: die Prüfungen eines Ausdrucks
│   │   ├── pages.py               Seiten, Ränder, Überdruck, Tabellenkopf, Summen, Anschrift im Fenster, Informationsblock
│   │   └── raster.py              bemalte Fläche einer gerasterten Seite, etwa des Logos
│   ├── briefbote/                 Frappe-Modul „Briefbote“
│   │   ├── printing.py            liest Beleg, Stammdaten und Einstellungen für die Druckformate (Jinja-Methoden)
│   │   ├── about.py               Über Briefbote: Version, Lizenz, Links, ohne Frappe-Import
│   │   ├── about_block.py         gibt den Block dem Desk in der Sprache des Benutzers
│   │   ├── doctype/               Einstellungen Geschäftspost mit Bankkonten und Steuerfällen
│   │   ├── print_format/          die Druckformate, je eines mit .json und .html
│   │   ├── workspace/             Arbeitsbereich „Geschäftspost“
│   │   └── sidebar/               Seitenleiste des Moduls
│   ├── templates/includes/briefbote/
│   │   ├── style.html             das eine Stylesheet aller Druckformate
│   │   ├── first_page.html        Kopf der ersten Seite: Briefkopf, Anschriftfeld, Informationsblock, Marken
│   │   ├── findings.html          Befunde eines unvollständigen Dokuments
│   │   ├── positions.html         Betreff, Positionen, Summen, Hinweise, Zahlung, Bedingungen
│   │   └── footer.html            Fuß jeder Seite: Angaben zum Unternehmen, Dokument, „Seite n von N“
│   ├── public/                    Logo, Symbol des Moduls, Schriften (Inter mit SIL Open Font License), Skript der Druckansicht
│   ├── dock/                      Eintrag „Geschäftspost“ in der Leiste von ERPNext
│   ├── fixtures/                  Feld „Abrechnung im Gutschriftsverfahren“ der Eingangsrechnung, Block „Über Briefbote“
│   ├── translations/de.csv        deutsche Texte des Desks und, mit dem Kontext „Briefbote“, der Ausdrucke
│   └── tests/                     Tests der Dateien ohne Bench, Tests der Site, Belege und Nachweis der Ausdrucke, Browsertests (e2e)
├── scripts/build_fonts.py         baut die Schriften aus dem Release von Inter
├── docs/                          Dokumentation
└── .github/                       Workflows, Vorlagen für Issues und Pull Requests
```

## Kerne und Frappe-Schicht

Wie bei Steuerbote liegt jede Regel in einem Kern ohne Frappe-Import, getestet mit `pytest` ohne Bench und mit 100 % Abdeckung: welche Art von Dokument eine Rückgabe ist, welcher Hinweis zu welchem Steuerfall gehört, welches Datum die Leistung bekommt, wie der Fuß die Angaben eines Unternehmens ordnet, wo auf dem Blatt was steht. Die Frappe-Schicht (`briefbote/briefbote/printing.py`) liest Beleg, Stammdaten und Einstellungen, ruft die Kerne und gibt dem Druckformat fertige Zeilen, schon in der Sprache des Dokuments. Das Druckformat ordnet nur noch an.

Ein Druckformat ruft dafür zwei Jinja-Methoden:

- `briefbote_letter(doc, no_letterhead)`: der Rahmen jedes Briefs: Form und Maße, Papier, Rücksendeangabe, Anschrift des Empfängers (`dense`, wenn sie in 10 pt nicht in sechs Zeilen passt), Logo als Data-URL, Spalten des Fußes, Schriften, oberer und unterer Seitenrand.
- `briefbote_invoice(doc)`: was die Rechnung darüber hinaus druckt: Art, Titel, Betreff, Zeilen des Informationsblocks, Positionen mit ihrem Steuersatz, Summen, Hinweise, Zahlungsaufforderung, Geschäftsbedingungen.
- `briefbote_self_billing(doc)`: dasselbe für die [Gutschrift](gutschrift.md) aus einer Eingangsrechnung.
- `briefbote_quotation(doc)` und `briefbote_sales_order(doc)` in `briefbote/briefbote/sales.py`: dasselbe für [Angebot](angebot.md) und [Auftragsbestätigung](auftragsbestaetigung.md), mit den Kernen unter `briefbote/sales/`; `briefbote_delivery_letter(doc, no_letterhead)` und `briefbote_delivery_note(doc)` für den [Lieferschein](lieferschein.md), adressiert an die Lieferanschrift; `briefbote_dunning(doc)` in `briefbote/briefbote/dunning.py` für die [Mahnung](mahnung.md), mit den Kernen unter `briefbote/dunning/`; `briefbote_payment(doc, as_receipt)` in `briefbote/briefbote/receipt.py` für [Zahlungsbestätigung und Quittung](zahlungsbestaetigung.md) und `briefbote_remittance(doc)` daneben für das [Zahlungsavis](zahlungsavis.md), mit dem Kern `briefbote/purchase/remittance.py`; `briefbote_purchase_order(doc)` in `briefbote/briefbote/purchase.py` für die [Bestellung](bestellung.md), mit dem Kern unter `briefbote/purchase/`; daneben `briefbote_request_letter(doc, no_letterhead)` und `briefbote_request_for_quotation(doc)` für die [Anfrage](anfrage.md), adressiert an den Lieferanten, für den ERPNext sie druckt, und `briefbote_return_letter(doc, no_letterhead)` und `briefbote_purchase_return(doc)` für die [Lieferantenrücksendung](lieferantenruecksendung.md); `briefbote_packing_letter(doc, no_letterhead)` und `briefbote_packing_slip(doc)` in `briefbote/briefbote/sales.py` für die [Packliste](packliste.md), im Rahmen ihres Lieferscheins; `briefbote_business_letter_frame(doc, no_letterhead)` und `briefbote_business_letter(doc)` in `briefbote/briefbote/correspondence.py` für den [Geschäftsbrief](geschaeftsbrief-format.md), mit dem Kern unter `briefbote/correspondence/`. Anfrage, Lieferantenrücksendung und Packliste setzen ihre Positionen ohne Preise mit den Teilen des Lieferscheins (`delivery_positions.html`, `receipt.html`).

Ein neues Dokument bekommt eine eigene Methode nach diesem Muster und einen eigenen Kern, wo es eigene Regeln hat.

## Gestaltungssystem

Alle Druckformate teilen ein Stylesheet und zwei Teile:

- **Briefe** beginnen mit `first_page.html`: Briefkopf, Anschriftfeld, Informationsblock und Marken stehen absolut an ihren Stellen nach [DIN 5008](din-5008.md), Form A oder B nach den Einstellungen. Darauf folgen Betreff und Inhalt im Fluss, 25 mm vom linken und 10 mm vom rechten Rand, wo der Informationsblock endet: Logo, Informationsblock, Tabellen und Fuß haben eine rechte Kante.
- **Dokumente mit Positionen** setzen ihre Positionen in eine Tabelle, deren Kopf auf jeder Seite wiederkehrt (`thead` als `table-header-group`) und deren Zeilen nie brechen. Die Spalten der Zahlen, Einheiten und kurzen Angaben sind so breit wie ihr breitester Eintrag, gemessen mit den Maßen von Inter (`briefbote/layout/columns.py`); die Bezeichnung bekommt den Rest, rund die Hälfte der Breite. Die Summen beginnen an der Spalte der Menge, wenn ihre Bezeichnungen dort in eine Zeile passen, sonst weiter links. Der Leistungsnachweis misst Datum, Person, Projekt (höchstens 42 mm) und Stunden ebenso und gibt den Rest der Tätigkeit. Die letzte Position, die Summen, die Hinweise und die Zahlungsaufforderung stehen in einem Block, der nicht bricht, damit die Summen nie ohne Position auf einer Seite stehen. Eine Anlage wie ein Leistungsnachweis wird ein eigener Block mit eigener Tabelle; Listen über viele Seiten, etwa ein Kontoauszug, nutzen dieselbe Tabelle ohne Briefkopf.
- **Jede Seite** endet mit `footer.html`: ein Fuß fester Höhe mit den [Angaben zum Unternehmen](geschaeftsbrief.md#der-fuß) in bis zu vier gleich breiten Spalten (`foot_blocks` in `briefbote/layout/letter.py`) und der Seitenzeile mit Titel, Nummer des Dokuments und „Seite n von N“.

Die Gestaltung eines Unternehmens (`briefbote/layout/theme.py`) setzt Akzentfarbe, Schrift, Stellung und Höhe des Logos; jeder Wert wird geprüft, bevor er in das Stylesheet geht, so dass keine Einstellung eigenes CSS einschleusen kann. Die Klassen beginnen mit `bb-`, damit Frappes eigenes Druck-Stylesheet sie nicht trifft; das Stylesheet hängt nicht von Frappes Druckpaket ab.

## Entwurf und Storno

Ein Entwurf (docstatus 0 eines buchbaren Belegs) und ein stornierter Beleg (docstatus 2) tragen auf jeder Seite ein schräges Wasserzeichen, „ENTWURF“ oder „STORNIERT“ (englisch „DRAFT“, „CANCELLED“), hell genug, dass der Text lesbar bleibt, und kräftig genug für einen Schwarz-Weiß-Druck und eine Kopie, und dasselbe Wort in der Seitenzeile: „Rechnung RE-2026-0102 · Entwurf · Seite 1 von 3“. Ein Entwurf ist noch keine Rechnung und ein stornierter Beleg keine mehr; beide bitten nicht um Zahlung. Ob Frappe sie überhaupt druckt, entscheiden die Druckeinstellungen „Allow Print for Draft“ (Vorgabe an) und „Allow Print for Cancelled“ (Vorgabe aus; `validate_print_for_docstatus` in `frappe/www/printview.py`): Ist der Druck aus, bleibt es dabei; ist er an, tragen die Ausdrucke von Briefbote ihre Markierung, unabhängig von „Add Draft Heading“, das nur Frappes Standardformat betrifft. Andere Zustände wie bezahlt, überfällig oder teilweise bezahlt markiert Briefbote nicht: Sie ändern sich nach dem Druck, ein Ausdruck würde sie einfrieren. Ein Vermerk „bezahlt“ gehört auf die Zahlungsbestätigung, die ein eigenes Dokument ist. Eine App für E-Rechnungen kann auch in das PDF eines Entwurfs XML einbetten, siehe [Rechnung](rechnung.md#papierrechnung-und-e-rechnung); Briefbote markiert dieses PDF als Entwurf.

Die Markierung steht einmal für alle Formate in `style.html`, das jedes Druckformat zuerst einbindet: mit CSS gedreht, in durchscheinendem Grau über dem Text. Der Generator auf Chromium-Basis und der Druck des Browsers wiederholen ein fest positioniertes Element (`position: fixed`) auf jeder Seite. wkhtmltopdf tut das nicht und malt auch einen wiederholten Hintergrund nicht verlässlich auf jede Seite; mit wkhtmltopdf steht das Wasserzeichen deshalb nur auf der ersten Seite. Frappe führt wkhtmltopdf als veraltet, Vorgabe und Referenz ist der Generator auf Chromium-Basis. Auf jeder Seite steht das Wort zusätzlich gerahmt im Fuß (`footer.html`) und in der Seitenzeile. Der Nachweis prüft das Wasserzeichen als bemalte Fläche in der Mitte der gerasterten Seite und im Text der Seite, mit dem Generator auf Chromium-Basis auf jeder Seite, mit wkhtmltopdf auf der ersten, und mit beiden den gerahmten Vermerk und die Seitenzeile auf jeder Seite. Den Zustand liefert `briefbote_letter` (`status`, `mark`, `status_label`; Kern `briefbote/layout/status.py`). Ein neues Druckformat bekommt die Markierung, wenn es wie die vorhandenen `letter` mit `briefbote_letter(doc, no_letterhead)` setzt und `style.html` und `footer.html` einbindet; eine Zahlungsaufforderung druckt es nur, wenn `letter.status` leer ist. Der Nachweis der Ausdrucke prüft Entwurf und Storno von Rechnung, Gutschrift und einer Rechnung mit Leistungsnachweis über mehrere Seiten mit beiden Generatoren: das Wort auf jeder Seite, keine Zahlungsaufforderung und keine Markierung auf gebuchten Belegen.

## Die beiden PDF-Generatoren

Frappe 16 druckt PDFs mit wkhtmltopdf oder mit einem Generator auf Chromium-Basis; welcher druckt, sagen das Druckformat oder die Druckeinstellungen, deren Vorgabe Chromium ist (Frappe nennt wkhtmltopdf veraltet und will es mit Version 17 entfernen). Die Druckformate von Briefbote legen keinen Generator fest und drucken mit beiden denselben Inhalt mit denselben Regeln; nur die Seitenumbrüche langer Tabellen können mit wkhtmltopdf anders fallen (unten). Dafür gilt:

- **Seitenränder** stehen in der Regel `.print-format { margin-…: … }`, die beide Generatoren lesen (`read_options_from_html` in `frappe/utils/pdf.py`, `_parse_pdf_options_from_html` in `frappe/utils/pdf_generator/browser.py`); `@page` liest wkhtmltopdf nicht. Der untere Rand unterscheidet sich: wkhtmltopdf druckt den Fuß in den Rand, der Generator auf Chromium-Basis misst den Fuß und setzt den Rand darunter. `briefbote_letter` liest den Generator aus `frappe.form_dict.pdf_generator`, das `frappe.get_print` setzt, und gibt jedem seinen Rand.
- **Kopf und Fuß**: Der Fuß steht in `<div id="footer-html" class="visible-pdf">`; beide Generatoren drucken ihn auf jeder Seite und füllen die Spans `page` und `topage`. Einen laufenden Kopf haben die Briefe nicht: Der Generator auf Chromium-Basis gibt jeder Seite denselben Kopf, die erste Seite eines Briefs braucht aber den Briefkopf an seiner Stelle.
- **Nichts aus dem Netz**: wkhtmltopdf holt Adressen über die URL der Site, der Generator auf Chromium-Basis liest `/assets` und `/files` von der Platte. Briefbote braucht keins von beiden: Die Schriften stehen als Data-URL im Stylesheet, das Logo als Data-URL im Bild.
- **CSS**: wkhtmltopdf (QtWebKit) kennt weder Flexbox noch Grid noch `page-break-after: avoid`; das Stylesheet kommt mit Blöcken, Tabellen und absoluten Positionen aus und hält Zusammengehöriges mit `page-break-inside: avoid` zusammen. Linien und Marken sind mindestens ein Pixel hoch, weil QtWebKit dünnere nicht zeichnet.
- **Gleiche Seiten mit beiden Generatoren:** Der Generator auf Chromium-Basis misst den Fuß und setzt seinen Rand darunter, wkhtmltopdf druckt den Fuß in einen festen unteren Rand von 36 mm. Der Fuß ist deshalb auf jeder Seite gleich hoch, 87 Pixel (23,0 mm: Abstand, Linie, vier Zeilen der Blöcke, eine Zeile Abstand, Seitenzeile), und der Rand von Chromium der Rest der 36 mm, so dass beide dem Text dieselbe Höhe der Seite lassen und den Fuß an dieselbe Stelle setzen. wkhtmltopdf rundet Zeilenhöhen, Abstände und Linien auf ganze Pixel ab, Chromium nicht; gemessen an einer Rechnung mit 36 Positionen war eine Position mit Chromium 16,1 mm hoch, mit wkhtmltopdf 15,3 bis 15,5 mm, und der Fuß begann bei 268,5 statt 263 mm, so dass der Schlusssatz nur mit Chromium auf eine eigene Seite rutschte. Alle Höhen des fließenden Texts stehen deshalb in ganzen Pixeln; seitdem sind die Positionen mit beiden Generatoren gleich hoch. Es bleibt die bekannte Grenze von wkhtmltopdf (unten): Wo eine Seite in einer Tabelle bricht, setzt es manchmal Leerraum in eine Zeile, so dass seine Seiten eine Position früher brechen können; das kann ein Dokument um eine Seite länger oder kürzer machen als mit Chromium. Der Nachweis prüft mit beiden Generatoren, dass jede Seite eine Position oder die Summen hält, also nie ein Schlusstext allein steht, und dass die Seitenzahlen höchstens eine Seite auseinanderliegen; jeden Ausdruck, den die Generatoren verschieden brechen, nennt er im Bericht.
- **Schlusstexte:** Hinweise, Zahlungsaufforderung und Schluss einer Rechnung, einer Gutschrift, eines Angebots, einer Auftragsbestätigung, einer Bestellung oder einer Mahnung stehen im selben Block wie die letzte Position und die Summen, der nicht bricht (`positions.html`, `dunning_letter.html`; Lieferschein, Quittung und Zahlungsbestätigung hielten ihren Schluss schon so). Passen sie nicht mehr unter die Summen, rücken Summen und letzte Position mit ihnen auf die nächste Seite; keine Seite hält nur einen Schlusssatz. Bedingungen (Freitext) folgen danach und dürfen auf einer neuen Seite beginnen.
- **Bekannte Grenze von wkhtmltopdf:** wkhtmltopdf 0.12.6.1 (QtWebKit) setzt Leerraum in eine Tabellenzeile, über die eine Seite bricht, und zwar mehr, je weiter das Dokument reicht: Es schiebt einzelne Zeilen des Texts über den Umbruch, die ganze Zeile der Tabelle aber rückt erst danach auf die neue Seite und nimmt den Leerraum mit. Das zeigt schon eine Tabelle aus einfachen Zeilen ohne jedes Stylesheet von Briefbote; es tritt auch ohne `page-break-inside`, ohne wiederholten Tabellenkopf, ohne Linien und mit einer Schrift des Systems auf, und kein Stylesheet behebt es, das den wiederholten Tabellenkopf behält. Text fehlt nicht und überdeckt sich nicht, aber eine Seite kann eine Position weniger halten, und ein Dokument kann so eine Seite mehr brauchen als mit Chromium. Der Generator auf Chromium-Basis setzt die Seiten ohne den Leerraum. Weil Frappe wkhtmltopdf als veraltet führt, ist der Generator auf Chromium-Basis die Referenz für das Druckbild.

## Wege aufs Papier

Frappe 16 bringt ein Dokument auf mehreren Wegen auf Papier oder in eine Datei (`frappe/printing/page/print/print.js`, `frappe/utils/print_format.py`, `frappe/utils/print_utils.py`, `frappe/www/printview.py`, nachgelesen in v16.60.2 und im Zweig `version-16`). Nur der PDF-Generator füllt die Seitenzeile des Fußes und wiederholt ihn auf jeder Seite; deshalb führt Briefbote jeden Weg zum Generator oder, wo der Browser selbst druckt, zu einem Druck-Stylesheet mit Seitenzahlen.

| Weg | Was Frappe tut | Briefbote | Nachweis |
|---|---|---|---|
| Druckansicht, Knopf „Drucken“ und Strg+P dort; das Druckersymbol und Strg+P im Formular öffnen die Druckansicht | ohne weitere Einstellung: `/printview` in einem neuen Fenster, `window.print()` des Browsers | `public/js/print_view.js` (Hook `page_js` der Seite `print`): Für ein Druckformat des Moduls Briefbote holt „Drucken“ das PDF des Generators, lädt es in einen unsichtbaren Rahmen und öffnet den Druckdialog des Browsers darauf | Browsertest |
| Druckansicht mit der Druckeinstellung „PDF drucken“ (`print_generated_pdf`) | dasselbe mit Frappes eigenem `print_pdf()` | wie oben | wie oben |
| Druckansicht mit Druckserver oder zugeordnetem Drucker (QZ Tray, Rohdruck) | Frappe druckt über den Server (`print_by_server`, `frappe.get_print(as_pdf=True)`) oder roh | unverändert; der Server-Druck geht durch den Generator | – |
| Knopf „PDF“ | `download_pdf`, Generator | – | Nachweis der Ausdrucke |
| Listenansicht, „Drucken“ für mehrere Belege | `download_multi_pdf`, Generator | – | wie PDF |
| E-Mail mit Anhang | `attach_print`; mit „Ausdruck als PDF senden“ (Vorgabe an) der Generator | – | wie PDF |
| PDF beim Buchen (App pdf_on_submit) | `frappe.get_print(as_pdf=True)` | – | wie PDF |
| `/printview` direkt, vom Browser gedruckt | HTML im Browser | Druck-Stylesheet: A4, die Ränder der Generatoren, Seitenzeile „Seite n von N“ im Randfeld `@bottom-right` von `@page`, die Angaben zum Unternehmen einmal am Ende | Browsertest mit `page.pdf()` in Chromium |
| Vorschau der Druckansicht am Bildschirm | HTML im Rahmen | keine Seitenzeile, die dort nicht gefüllt würde | Browsertest |

`briefbote/layout/medium.py` erkennt den Weg am Pfad der Anfrage: die Vorschau an `frappe.www.printview.get_html_and_style`, den Druck des Browsers an `/printview`, alles andere geht durch einen Generator. Ein Druckformat anderer Apps behält Frappes Weg; das Skript greift nur, wenn das gewählte Format zum Modul Briefbote gehört und weder Druckserver noch Rohdruck eingestellt sind.

Die Browsertests (`briefbote/tests/e2e`, Playwright mit Chromium) klicken in der CI auf einer echten Site „Drucken“ für eine Rechnung mit 40 Positionen und eine mit Leistungsnachweis und prüfen das PDF, das gedruckt würde: mehrere Seiten, auf jeder „Seite n von N“ und der Tabellenkopf. Firefox und Safari prüft die CI nicht; „Drucken“ nutzt dort dieselbe Technik wie Frappes Einstellung „PDF drucken“. Das Randfeld von `@page` kennen Chromium-Browser; ein Browser ohne Randfelder druckt `/printview` mit Seitenumbrüchen und Tabellenköpfen, aber ohne Seitenzeile.

Der Generator auf Chromium-Basis der CI ist nicht der des Container-Images: Schrift und Laufweite können dort anders rendern. Für die ausgelieferte Umgebung ist der Test der Site im Image der Nachweis.

Frappe v16.60.2 rechnet im Generator auf Chromium-Basis den Abstand `header-spacing` als Zeichenkette zur Höhe eines laufenden Kopfs (`browser.py`, behoben in 16.61.0). Dieser Code läuft nur, wenn das HTML ein Element mit der ID `header-html` hat; kein Druckformat von Briefbote hat eines, gleich ob Briefpapier, Logo oder Anlage, und `briefbote/tests/test_templates.py` hält das fest.

## Schrift

Die Ausdrucke setzen Inter (Version 4.1), Regular und SemiBold, unter der SIL Open Font License 1.1, die das Bündeln mit Software erlaubt; Inter nennt keinen reservierten Schriftnamen. `scripts/build_fonts.py` baut aus dem geprüften Release eine Untermenge mit den lateinischen Buchstaben der EU-Sprachen, Satzzeichen und Symbolen behält Unterschneidung und die Features, die Glyphen zusammensetzen und an die Sprache anpassen, aber keines, das Buchstabenfolgen ersetzt (Ligaturen, kontextuelle Alternativen), damit „Nr.“ immer als Buchstaben druckt; `briefbote/tests/test_fonts.py` prüft das, und der Nachweis prüft, dass keine Seite „№“ druckt. Es legt die Ziffern auf die Tabellenziffern der Schrift, damit Beträge in ihrer Spalte untereinander stehen, auch mit wkhtmltopdf, das keine Schriftfeatures kennt. Die Dateien liegen mit der Lizenz unter `briefbote/public/fonts`. Eine eingebettete Schrift druckt auf jedem Image gleich; eine Schrift des Systems wie Nimbus Sans oder Liberation Sans ist nicht überall installiert und hat andere Maße, so dass Seitenumbrüche von Image zu Image wandern würden.

## Einstellungen

Je Unternehmen ein Satz „Einstellungen Geschäftspost“ (`Business Document Settings`) mit den Tabellen `Business Document Bank Account` und `Business Document Tax Case`, siehe [Einrichtung](einrichtung.md). Briefbote nutzt den Briefkopf von Frappe nicht; warum, steht dort.

## Platz im Desk

Der Arbeitsbereich „Geschäftspost“ führt zu den Einstellungen, zur Liste jedes Belegs, den ein Druckformat druckt (Angebote, Aufträge, Lieferscheine, Packzettel, Ausgangsrechnungen, Mahnungen, Zahlungen, Anfragen, Bestellungen, Wareneingänge, Eingangsrechnungen), und zu den Stammdaten, die die Druckformate lesen: Druckformate, Bankkonten, Vorlagen für Verkaufssteuern, Geschäftsbedingungen. Am Ende steht der Block „Über Briefbote“ mit Version, Lizenz, Haftungsausschluss und Links. Die Seitenleiste des Moduls führt zum Arbeitsbereich, zu den Einstellungen und in den Gruppen Verkaufsbelege, Zahlung und Mahnung sowie Einkaufsbelege zu denselben Belegen; `briefbote/tests/test_menu.py` prüft, dass jeder Beleg mit einem Druckformat von Briefbote in beiden steht, der Eintrag „Geschäftspost“ hängt in der Leiste von ERPNext. Kein Ausdruck nennt Briefbote: Ein Geschäftsdokument trägt keinen Hinweis auf die Software, die es gedruckt hat; `briefbote/tests/test_about_files.py` prüft das an jedem Teil der Druckformate.

## Zusammenspiel mit anderen Apps

Briefbote setzt nur ERPNext voraus und nutzt andere Apps, wenn sie da sind. Was die verbreiteten Apps für deutsche Unternehmen beim Drucken tun, steht im Code ihrer Releases, die erpnext_germanized bündelt:

- **ERPNext 16** bringt für die Belege des Verkaufs und Einkaufs Builder-Formate in vier Varianten ohne deutsche Pflichtangaben, siehe [Katalog](katalog.md), und eine deutsche Adressvorlage. Briefbote ersetzt diese Formate für deutsche Unternehmen; es ändert keine von ihnen.
- **erpnext_germany** (16.2.2) bringt keine Druckformate. Es gibt Unternehmen, Kunden und Lieferanten Felder für das Handelsregister (Registerart, Registernummer, Registergericht) und Angebot, Auftrag und Ausgangsrechnung das Feld `tax_exemption_reason` aus der Steuervorlage. Briefbote liest beide, wenn sie da sind: die Registerfelder des Unternehmens, wenn die Einstellungen keine haben, den Grund der Steuerbefreiung, wenn der Steuerfall keinen nennt. erpnext_germany bringt auch die DocTypes Business Letter und Business Letter Template ohne Druckformat; Briefbote druckt den Business Letter mit dem [Geschäftsbrief](geschaeftsbrief-format.md), den es nur auf einer Site mit erpnext_germany anlegt (`briefbote/briefbote/optional/`).
- **eu_einvoice** (16.4.0) erzeugt die E-Rechnung (XRechnung, ZUGFeRD) und bringt keine Druckformate. Es bettet sein XML in das PDF einer Ausgangsrechnung ein, das über den PDF-Download von Frappe (`frappe.utils.print_format.download_pdf`) entsteht, gleich mit welchem Druckformat; das gilt auch für die Formate von Briefbote. Nicht eingebettet wird es in PDFs der Builder-Formate, die einen anderen Endpunkt nutzen, und in Anhänge von E-Mails. Was Briefbote druckt, entspricht dem, was eu_einvoice ins XML schreibt: Rückgabe mit Bezug auf die Rechnung, Leistungszeitraum aus `from_date` und `to_date`.
- **pdf_on_submit** (16.3.1) hängt beim Buchen ein PDF an den Beleg, mit dem Druckformat und Briefkopf seiner Einstellungen, und bettet bei einer Ausgangsrechnung das XML von eu_einvoice ein. Mit „Rechnung“ als Druckformat entsteht so beim Buchen das PDF, das aufbewahrt wird.
- **Steuerbote** meldet die Steuern an ELSTER; die Rechnungen, die Briefbote druckt, sind die Belege, aus denen es meldet. Briefbote braucht Steuerbote nicht. Dass die Kontenzuordnung von Steuerbote den Steuerfall einer Rechnung liefert, steht in der [Roadmap](roadmap.md).
