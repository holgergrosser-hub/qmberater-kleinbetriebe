# Ads Competitor Analyzer (Google Ads – Konkurrenz schnell auswerten)

Dieses Tool wertet **manuell erfasste** Google-Ads-Anzeigen (z.B. aus dem Google Ads Transparency Center) aus.

Wichtig: Es gibt **kein Scraping**. Du gibst die Anzeigen entweder über einen Assistenten ein oder per CSV.

## Quickstart (am einfachsten)

1) Öffne den Ordner `tools/ads_competitor_analyzer/`
2) Starte den Assistenten:
	- per Doppelklick: `run_wizard.cmd`
	- per PowerShell: `./run_wizard.ps1`
	- oder direkt: `python ./wizard.py`
3) Gib pro Anzeige `Domain`, `Headline`, `Description` ein → der Report wird automatisch erstellt.

Outputs liegen danach direkt im Ordner:
- `ads.csv` (deine Eingaben)
- `ads_report.md`
- `ads_report.json`

## Alternative: CSV-Import

Wenn du lieber in Excel/Sheets arbeitest: nutze `ads_template.csv` als Vorlage.

Empfohlene Spalten:
- `domain` – z.B. `tuvsud.com`
- `headline` – Anzeigentitel
- `description` – Beschreibung/Body
- `landing_url` – Ziel-URL (optional)
- optional: `first_seen`, `last_seen`, `country`

Ausführen:

```bash
python .\ads_analyzer.py --input .\ads.csv --own-domain 9001-zertifikat.qmberater.info --out .\ads_report.md --json-out .\ads_report.json
```

## 4) Was das Tool liefert

- „Was bewerben die?“: Top-Themen, häufigste Begriffe/Claims/CTAs je Domain
- „Wo habe ich Chancen?“: seltene Themen (wenige Domains), Differenzierungsideen aus den Daten
- „Was lieber nicht?“: stark umkämpfte Themen (viele Domains), mögliche Marken-/Brand-Begriffe (TÜV/DEKRA etc.) als Warnhinweis

## Hinweis zu Recht/Compliance
Bitte prüfe selbst, dass deine Datensammlung mit den Bedingungen der jeweiligen Plattform (Google) und deinem rechtlichen Rahmen kompatibel ist. Das Tool ist bewusst auf **Import** ausgelegt, nicht auf Crawling.
