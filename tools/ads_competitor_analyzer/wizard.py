from __future__ import annotations

import csv
from pathlib import Path

from ads_analyzer import AdRow, analyze, load_ads, render_markdown


def prompt(msg: str) -> str:
    return input(msg).strip()


def main() -> int:
    here = Path(__file__).resolve().parent

    print("Google Ads Wettbewerbs-Report – Assistent (ohne CSV-Gefrickel)")
    print("Tipp: Du kannst Text einfach kopieren und hier einfügen.")
    print("")

    own_domain = prompt("Eigene Domain (optional, Enter = überspringen): ") or None

    rows: list[AdRow] = []
    print("")
    print("Jetzt pro Anzeige 3 Felder eingeben: Domain, Headline, Description.")
    print("Zum Beenden bei Domain einfach 'fertig' eingeben.")
    print("")

    while True:
        domain = prompt("Domain (oder 'fertig'): ")
        if not domain:
            print("Bitte eine Domain eingeben (oder 'fertig').")
            continue
        if domain.lower() in {"fertig", "done", "ende", "exit", "quit"}:
            break

        headline = prompt("Headline: ")
        if not headline:
            print("Headline ist leer – bitte nochmal.")
            continue

        description = prompt("Description: ")
        if not description:
            print("Description ist leer – bitte nochmal.")
            continue

        landing_url = prompt("Landing-URL (optional): ") or None

        rows.append(
            AdRow(
                domain=domain,
                headline=headline,
                description=description,
                landing_url=landing_url,
            )
        )
        print("✓ gespeichert\n")

    if not rows:
        print("Keine Anzeigen eingegeben – Abbruch.")
        return 2

    csv_path = here / "ads.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "domain",
                "headline",
                "description",
                "landing_url",
                "first_seen",
                "last_seen",
                "country",
            ],
        )
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    "domain": r.domain,
                    "headline": r.headline,
                    "description": r.description,
                    "landing_url": r.landing_url or "",
                    "first_seen": r.first_seen or "",
                    "last_seen": r.last_seen or "",
                    "country": r.country or "",
                }
            )

    ads = load_ads(csv_path)
    report = analyze(ads, own_domain)

    md_out = here / "ads_report.md"
    json_out = here / "ads_report.json"

    md_out.write_text(render_markdown(report), encoding="utf-8")
    import json

    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Fertig!")
    print(f"- Daten: {csv_path}")
    print(f"- Report (Markdown): {md_out}")
    print(f"- Report (JSON): {json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
