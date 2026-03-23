from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Literal


STOPWORDS_DE = {
    "aber","als","am","an","auch","auf","aus","bei","bin","bis","bist","da","dadurch","daher","darum",
    "das","dass","dein","deine","dem","den","der","des","dessen","deshalb","die","dies","dieser","dieses",
    "doch","dort","du","durch","ein","eine","einem","einen","einer","eines","er","es","euer","eure",
    "für","gegen","gewesen","hab","habe","haben","hat","hatte","hatten","hier","hin","hinter","ich","ihr","ihre",
    "im","in","ist","ja","jede","jedem","jeden","jeder","jedes","jetzt","kann","kannst","können","könnt",
    "machen","mehr","mein","meine","mit","muss","musst","müssen","müsst","nach","nicht","noch","nur","ob",
    "oder","ohne","sehr","sein","seine","sich","sie","sind","so","soll","sollen","sollst","sollt","sonst",
    "sowie","über","um","und","uns","unser","unsere","unter","vom","von","vor","wann","war","waren","was",
    "wegb","weil","weiter","welche","welcher","welches","wenn","wer","wie","wieder","wir","wird","wirst","wo",
    "wollen","wollt","zu","zum","zur","zwischen",
}


CTA_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("angebot", re.compile(r"\bangebot\b", re.I)),
    ("kostenlos", re.compile(r"\bkostenlos\b", re.I)),
    ("beratung", re.compile(r"\bberatung\b|\bberater\b", re.I)),
    ("termin", re.compile(r"\btermin\b|\bkalender\b|\bcall\b|\bgespr[aä]ch\b", re.I)),
    ("kontakt", re.compile(r"\bkontakt\b|\bmail\b|\be-?mail\b|\banrufen\b|\btelefon\b", re.I)),
    ("preis", re.compile(r"\bpreis\b|\beur\b|€|\bfestpreis\b|\bab\s*\d", re.I)),
    ("schnell", re.compile(r"\bschnell\b|\bsofort\b|\bin\s*\d+\s*(tage|wochen)\b", re.I)),
    ("audit", re.compile(r"\baudit\b|\bauditor\b", re.I)),
]


THEMES: list[tuple[str, re.Pattern[str]]] = [
    ("iso-9001", re.compile(r"\biso\s*9001\b|\b9001\b", re.I)),
    ("iso-14001", re.compile(r"\biso\s*14001\b|\b14001\b", re.I)),
    ("iso-27001", re.compile(r"\biso\s*27001\b|\b27001\b", re.I)),
    ("tisax", re.compile(r"\btisax\b", re.I)),
    ("iatf-16949", re.compile(r"\biatf\s*16949\b|\b16949\b", re.I)),
    ("dakkS", re.compile(r"\bdakks\b|\bakkreditier", re.I)),
    ("online", re.compile(r"\bonline\b|\bdigital\b|\bremote\b", re.I)),
    ("fixpreis", re.compile(r"\bfixpreis\b|\bfestpreis\b", re.I)),
    ("kleinbetrieb", re.compile(r"\bkleinbetrieb\b|\bkleine\s+(betriebe|unternehmen)\b|\bkm[uü]\b", re.I)),
    ("foerderung", re.compile(r"\bbafa\b|\bf[oö]rder", re.I)),
]

BRAND_TERMS = [
    "tüv", "tuv", "tuev", "dekra", "tüv süd", "tuv sud", "tüvsüd", "tuvsud", "din", "dqs",
]


TOKEN_RE = re.compile(r"[a-zA-ZäöüÄÖÜß0-9]+(?:-[a-zA-ZäöüÄÖÜß0-9]+)*")


@dataclass(frozen=True)
class AdRow:
    domain: str
    headline: str
    description: str
    landing_url: str | None = None
    first_seen: str | None = None
    last_seen: str | None = None
    country: str | None = None

    @property
    def text(self) -> str:
        return " ".join([self.headline or "", self.description or ""]).strip()


def _norm_domain(value: str) -> str:
    v = (value or "").strip().lower()
    v = v.replace("https://", "").replace("http://", "")
    v = v.split("/")[0]
    return v


def _tokenize(text: str) -> list[str]:
    tokens = [t.lower() for t in TOKEN_RE.findall(text or "")]
    tokens = [t for t in tokens if len(t) >= 2 and t not in STOPWORDS_DE]
    return tokens


def _ngrams(tokens: list[str], n: int) -> Iterable[str]:
    if n <= 1:
        return tokens
    return (" ".join(tokens[i : i + n]) for i in range(0, max(0, len(tokens) - n + 1)))


def _detect_flags(text: str) -> dict[str, bool]:
    t = (text or "").lower()
    return {
        "mentions_brand_term": any(bt in t for bt in BRAND_TERMS),
    }


def _detect_patterns(text: str, patterns: list[tuple[str, re.Pattern[str]]]) -> list[str]:
    hits: list[str] = []
    for name, rx in patterns:
        if rx.search(text or ""):
            hits.append(name)
    return hits


def _guess_columns(fieldnames: list[str]) -> dict[str, str]:
    if not fieldnames:
        raise ValueError("CSV has no header row")

    norm = {f: re.sub(r"[^a-z0-9]+", "_", f.strip().lower()) for f in fieldnames}

    def pick(*candidates: str) -> str | None:
        for original, n in norm.items():
            if n in candidates:
                return original
        return None

    mapping = {
        "domain": pick("domain", "advertiser_domain", "host", "seite", "website"),
        "headline": pick("headline", "title", "anzeigentitel", "titel"),
        "description": pick("description", "text", "anzeige", "body", "beschreibung"),
        "landing_url": pick("landing_url", "landing", "final_url", "ziel", "ziel_url", "url"),
        "first_seen": pick("first_seen", "firstseen", "start", "start_date"),
        "last_seen": pick("last_seen", "lastseen", "end", "end_date", "last"),
        "country": pick("country", "region", "land"),
    }

    missing = [k for k in ("domain", "headline", "description") if not mapping.get(k)]
    if missing:
        raise ValueError(
            "CSV missing required columns. Need at least: domain, headline, description. "
            f"Missing: {', '.join(missing)}. Found headers: {fieldnames}"
        )
    return mapping  # type: ignore[return-value]


def load_ads(csv_path: Path) -> list[AdRow]:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        mapping = _guess_columns(reader.fieldnames or [])

        out: list[AdRow] = []
        for row in reader:
            out.append(
                AdRow(
                    domain=_norm_domain(row.get(mapping["domain"], "")),
                    headline=(row.get(mapping["headline"], "") or "").strip(),
                    description=(row.get(mapping["description"], "") or "").strip(),
                    landing_url=(row.get(mapping.get("landing_url", ""), "") or "").strip() or None,
                    first_seen=(row.get(mapping.get("first_seen", ""), "") or "").strip() or None,
                    last_seen=(row.get(mapping.get("last_seen", ""), "") or "").strip() or None,
                    country=(row.get(mapping.get("country", ""), "") or "").strip() or None,
                )
            )

    out = [a for a in out if a.domain]
    if not out:
        raise ValueError("No rows loaded (domain empty in all rows?)")
    return out


def analyze(ads: list[AdRow], own_domain: str | None) -> dict:
    by_domain: dict[str, list[AdRow]] = defaultdict(list)
    for ad in ads:
        by_domain[ad.domain].append(ad)

    corpus_tokens = [_tokenize(ad.text) for ad in ads]
    corpus_unigrams = Counter(t for toks in corpus_tokens for t in toks)

    # Domain summaries
    domain_summaries = {}
    theme_matrix: dict[str, set[str]] = defaultdict(set)  # theme -> domains
    cta_matrix: dict[str, set[str]] = defaultdict(set)  # cta -> domains

    for domain, rows in sorted(by_domain.items(), key=lambda x: (-len(x[1]), x[0])):
        tokens = [_tokenize(r.text) for r in rows]
        uni = Counter(t for toks in tokens for t in toks)
        bi = Counter(g for toks in tokens for g in _ngrams(toks, 2))
        tri = Counter(g for toks in tokens for g in _ngrams(toks, 3))

        cta_hits = Counter()
        theme_hits = Counter()
        brand_flag = False

        for r in rows:
            ctas = _detect_patterns(r.text, CTA_PATTERNS)
            cta_hits.update(ctas)
            for c in ctas:
                cta_matrix[c].add(domain)

            themes = _detect_patterns(r.text, THEMES)
            theme_hits.update(themes)
            for th in themes:
                theme_matrix[th].add(domain)

            brand_flag = brand_flag or _detect_flags(r.text)["mentions_brand_term"]

        domain_summaries[domain] = {
            "ads": len(rows),
            "top_unigrams": [w for w, _ in uni.most_common(15)],
            "top_bigrams": [w for w, _ in bi.most_common(12)],
            "top_trigrams": [w for w, _ in tri.most_common(10)],
            "cta": dict(cta_hits.most_common()),
            "themes": dict(theme_hits.most_common()),
            "mentions_brand_term": brand_flag,
        }

    # Opportunity heuristics
    domains = list(by_domain.keys())
    crowded_themes = sorted(theme_matrix.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    rare_themes = sorted(theme_matrix.items(), key=lambda kv: (len(kv[1]), kv[0]))

    # Heuristic: "crowded" if >= 50% domains mention
    crowded = [
        {"theme": th, "domains": sorted(list(ds)), "coverage": len(ds) / max(1, len(domains))}
        for th, ds in crowded_themes
        if len(domains) and len(ds) / len(domains) >= 0.5
    ]

    rare = [
        {"theme": th, "domains": sorted(list(ds)), "coverage": len(ds) / max(1, len(domains))}
        for th, ds in rare_themes
        if len(domains) and 0 < len(ds) / len(domains) <= 0.25
    ]

    # Find domains that use brand terms (warning)
    brand_domains = [d for d, s in domain_summaries.items() if s.get("mentions_brand_term")]

    # Basic "chance" suggestions based on rare themes and CTAs
    suggestions = {
        "chancen": [],
        "lieber_nicht": [],
    }

    if rare:
        suggestions["chancen"].append(
            {
                "title": "Selten beworbene Themen (potenzielle Differenzierung)",
                "items": rare[:8],
                "note": "Selten heißt nicht automatisch hohe Nachfrage – aber oft weniger Konkurrenz im Messaging.",
            }
        )

    if crowded:
        suggestions["lieber_nicht"].append(
            {
                "title": "Sehr häufig beworbene Themen (stark umkämpft)",
                "items": crowded[:8],
                "note": "Hier brauchst du meistens klare USP (Preis/Speed/Nische), sonst gehst du im Vergleich unter.",
            }
        )

    if brand_domains:
        suggestions["lieber_nicht"].append(
            {
                "title": "Marken-/Brand-Begriffe in Anzeigen (Vorsicht)",
                "items": brand_domains,
                "note": "Begriffe wie TÜV/DEKRA etc. können markenrechtlich/Policy-relevant sein – im Zweifel vermeiden oder juristisch klären.",
            }
        )

    own = _norm_domain(own_domain or "") or None

    return {
        "meta": {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "rows": len(ads),
            "domains": len(domains),
            "own_domain": own,
        },
        "overall": {
            "top_terms": [w for w, _ in corpus_unigrams.most_common(30)],
            "domains": sorted(domains),
        },
        "by_domain": domain_summaries,
        "theme_matrix": {k: sorted(list(v)) for k, v in theme_matrix.items()},
        "cta_matrix": {k: sorted(list(v)) for k, v in cta_matrix.items()},
        "suggestions": suggestions,
    }


def _md_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    header = rows[0]
    sep = ["---"] * len(header)
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
    for r in rows[1:]:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def render_markdown(report: dict) -> str:
    meta = report["meta"]
    by_domain = report["by_domain"]

    lines: list[str] = []
    lines.append(f"# Google Ads Wettbewerbs-Report")
    lines.append("")
    lines.append(f"Stand: `{meta['generated_at']}` | Domains: **{meta['domains']}** | Ads: **{meta['rows']}**")
    if meta.get("own_domain"):
        lines.append(f"Eigene Domain: **{meta['own_domain']}**")
    lines.append("")

    lines.append("## Kurzüberblick")
    lines.append("")
    lines.append("Top Begriffe (gesamt):")
    lines.append("- " + ", ".join(report["overall"]["top_terms"][:20]))
    lines.append("")

    # Domain table
    dom_rows = [["Domain", "Ads", "Top-Themen", "Top-CTA"]]
    for dom, s in sorted(by_domain.items(), key=lambda kv: (-kv[1]["ads"], kv[0])):
        themes = ", ".join(list(s.get("themes", {}).keys())[:4]) or "–"
        ctas = ", ".join(list(s.get("cta", {}).keys())[:4]) or "–"
        dom_rows.append([dom, str(s["ads"]), themes, ctas])
    lines.append(_md_table(dom_rows))
    lines.append("")

    lines.append("## Was bewerben die? (pro Domain)")
    lines.append("")
    for dom, s in sorted(by_domain.items(), key=lambda kv: (-kv[1]["ads"], kv[0])):
        lines.append(f"### {dom}")
        lines.append("")
        if s.get("themes"):
            lines.append("Themen-Tags: " + ", ".join([f"`{k}`" for k in s["themes"].keys()]))
        if s.get("cta"):
            lines.append("CTA-Hinweise: " + ", ".join([f"`{k}`" for k in s["cta"].keys()]))
        lines.append("Top Phrasen:")
        lines.append("- 1-gram: " + ", ".join(s["top_unigrams"][:10]))
        lines.append("- 2-gram: " + ", ".join(s["top_bigrams"][:8]))
        lines.append("")

    lines.append("## Chancen & Risiken")
    lines.append("")

    sug = report["suggestions"]
    for block in sug.get("chancen", []):
        lines.append(f"### {block['title']}")
        lines.append("")
        items = block.get("items", [])
        if items and isinstance(items[0], dict):
            trows = [["Thema", "Abdeckung", "Domains"]]
            for it in items:
                trows.append([
                    it["theme"],
                    f"{int(round(it['coverage']*100))}%",
                    ", ".join(it["domains"][:6]) + (" …" if len(it["domains"]) > 6 else ""),
                ])
            lines.append(_md_table(trows))
        else:
            for it in items:
                lines.append(f"- {it}")
        if block.get("note"):
            lines.append("")
            lines.append(block["note"])
        lines.append("")

    for block in sug.get("lieber_nicht", []):
        lines.append(f"### {block['title']}")
        lines.append("")
        items = block.get("items", [])
        if items and isinstance(items[0], dict):
            trows = [["Thema", "Abdeckung", "Domains"]]
            for it in items:
                trows.append([
                    it["theme"],
                    f"{int(round(it['coverage']*100))}%",
                    ", ".join(it["domains"][:6]) + (" …" if len(it["domains"]) > 6 else ""),
                ])
            lines.append(_md_table(trows))
        else:
            for it in items:
                lines.append(f"- {it}")
        if block.get("note"):
            lines.append("")
            lines.append(block["note"])
        lines.append("")

    lines.append("## Nächste Schritte (praktisch)")
    lines.append("")
    lines.append("- Ergänze deine CSV um 10–30 Anzeigen pro Domain (Headline + Description + Landing URL).")
    lines.append("- Starte das Tool erneut und prüfe, ob sich die Themen/CTAs stabilisieren.")
    lines.append("- Wenn du deine eigenen USPs kennst (Preis, Speed, Online/Remote, Zielgruppe), kann man die ‘Chancen’ heuristischer priorisieren.")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="Analyze competitor Google Ads (from CSV import) and generate a report.")
    p.add_argument("--input", required=True, help="Path to ads CSV")
    p.add_argument("--own-domain", default=None, help="Your domain (for reference only)")
    p.add_argument("--out", required=True, help="Markdown output path")
    p.add_argument("--json-out", default=None, help="Optional JSON output path")

    args = p.parse_args()

    csv_path = Path(args.input).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    json_path = Path(args.json_out).expanduser().resolve() if args.json_out else None

    ads = load_ads(csv_path)
    report = analyze(ads, args.own_domain)

    out_path.write_text(render_markdown(report), encoding="utf-8")
    if json_path:
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote: {out_path}")
    if json_path:
        print(f"Wrote: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
