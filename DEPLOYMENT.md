# Deployment: 9001-zertifikat.qmberater.info

## Übersicht

| | |
|---|---|
| **Subdomain** | 9001-zertifikat.qmberater.info |
| **Netlify Site** | qmberater-kleinbetriebe.netlify.app |
| **GitHub Repo** | qmberater-kleinbetriebe |
| **Build** | `npm install && npm run build` |
| **Publish dir** | `dist` |
| **Stand** | 2026-03-22 |

---

## Vor dem ersten Deploy

Alles ist bereits fertig — kein Bild-Upload nötig, kein Platzhalter mehr offen.

**Checkliste:**
- [x] Foto Holger Grosser — Base64 eingebettet
- [x] E-Mail — Holger.grosser@qmberater.info
- [x] KI-Berater — https://iso9001.qm-guru.de/
- [x] Impressum — https://qm-guru.de/impressum/
- [x] Datenschutz — https://qm-guru.de/sonstiges/datenschutz/
- [x] Angebot QM-Beratung — https://angebot.qmberater.info/
- [x] Angebot OnlineCert — https://onlinecert.info/angebot-fuer-nicht-akkreditierte-zertifizierung/
- [x] Termin — https://calendly.com/grosser-qmguru/iso-9001-zertifikat-fuer-kleinbetriebe
- [x] SEO Meta, Schema.org, Open Graph vollstaendig
- [x] Mobile optimiert, Sticky CTA aktiv

---

## GitHub -> Netlify -> Cloudflare

### 1. GitHub Repo erstellen
```bash
cd qmberater-kleinbetriebe
git init
git add .
git commit -m "Initial: ISO 9001 Landingpage Kleinbetriebe"
gh repo create qmberater-kleinbetriebe --public --source=. --push
```

### 2. Netlify
- netlify.com -> "Add new site" -> "Import from Git"
- Repo: qmberater-kleinbetriebe
- Build command: npm install && npm run build
- Publish directory: dist
- Deploy

### 3. Cloudflare DNS (qmberater.info)
```
Type:   CNAME
Name:   9001-zertifikat
Value:  qmberater-kleinbetriebe.netlify.app
Proxy:  DNS only (graue Wolke)
```

### 4. Netlify Custom Domain
- Netlify -> Site -> Domain management
- "Add custom domain": 9001-zertifikat.qmberater.info
- SSL wird automatisch ausgestellt (Let's Encrypt)

---

## Alle Links in der Seite

| Link | Zweck |
|------|-------|
| https://angebot.qmberater.info/ | Primaerer CTA (Hero + Sticky + Kontakt) |
| https://onlinecert.info/angebot-fuer-nicht-akkreditierte-zertifizierung/ | Angebot Zertifizierung |
| https://calendly.com/grosser-qmguru/iso-9001-zertifikat-fuer-kleinbetriebe | Termin vereinbaren |
| https://iso9001.qm-guru.de/ | KI-Berater |
| mailto:Holger.grosser@qmberater.info | E-Mail |
| https://qm-guru.de/impressum/ | Impressum |
| https://qm-guru.de/sonstiges/datenschutz/ | Datenschutz |
| https://qmberater.info | Hauptdomain |
| https://qm-guru.de | Netzwerk |
| https://onlinecert.info | Netzwerk |
| https://iso9001.info | Netzwerk |
| https://www.google.com/maps/place/Holger+Grosser+QM+Dienstleistungen | Google Bewertungen |

---

## Post-Deployment Checkliste

- [ ] Seite erreichbar unter https://9001-zertifikat.qmberater.info
- [ ] SSL-Zertifikat gueltig (kein Browser-Warning)
- [ ] Kein HTTP->HTTPS Redirect-Loop
- [ ] Alle Links geprueft (Angebot, KI-Berater, Termin, E-Mail)
- [ ] Sitemap bei Google Search Console eingereicht:
      https://9001-zertifikat.qmberater.info/sitemap.xml
- [ ] Mobile-Ansicht geprueft (Sticky CTA erscheint nach Hero-Scroll)
