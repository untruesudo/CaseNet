# CASENET
### Public Case Transparency Network

A public-facing visualization and aggregation tool for missing persons, unidentified remains, and unsolved homicides in the United States. Built to increase transparency, support families, and surface public-record data in a format accessible to anyone.

> **Prototype status.** Homicide data (Washington Post, historical 2007–2017) and unidentified-remains data (NamUs, manually exported) are real and refreshed automatically — see [Data Pipeline](#data-pipeline) below. Missing-persons data is real once a NamUs export has been supplied the same way (see below); until then it falls back to illustrative mock data. There is no live in-browser API fetch — NamUs blocks unauthenticated requests, so a real backend proxy is still on the [Roadmap](#roadmap).

---

## Live Demo

[**CaseNet.untruesudo.github.io**](https://untruesudo.github.io/CaseNet) 

---

## What It Does

| Tab | Description |
|-----|-------------|
| **Map View** | Interactive Leaflet map with case dots color-coded by type. Zoom, pan, click any case to open its detail panel. Pulses indicate active missing persons. Geo-temporal pattern overlay surfaces officially-noted case linkages. |
| **Case Index** | Full sortable, searchable table of all cases. Sort by any column. Export filtered results as CSV. Click any row to fly to that case on the map. |
| **Analytics** | Live charts derived from the current filtered dataset — cases by year, type breakdown, cases by state, status, data sources, and lead agencies. Updates in real time as filters change. |
| **About** | Mission, data sources, responsible use guidelines, pattern flag explanation, and legal disclaimers. |

**Filters** (sidebar, all views): case type, time range, free-text search by name / city / state / case ID, geo-temporal pattern overlay toggle.

---

## Data Sources

| Source | Type | URL |
|--------|------|-----|
| **NamUs** | Missing persons, unidentified remains | [namus.gov](https://www.namus.gov) |
| **Washington Post** ("Murder with Impunity") | Unsolved homicides, 2007–2017 (historical) | [github.com/washingtonpost/data-homicides](https://github.com/washingtonpost/data-homicides) |
| **Murder Accountability Project (MAP)** | Unsolved homicides, official case linkages | [murderdata.org](https://www.murderdata.org) |
| **FBI Crime Data Explorer** | Aggregate crime statistics | [cde.ucr.cjis.fbi.gov](https://cde.ucr.cjis.fbi.gov) |

Map tiles © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, © [CARTO](https://carto.com/attributions).

### Data Pipeline

CASENET has no live in-browser API fetch — NamUs's public API blocks unauthenticated requests, and routing that through a public third-party CORS relay isn't something we're willing to ship for a tool handling this kind of data. Instead, data is generated ahead of time and committed to the repo:

| File | How it's generated | Refresh |
|------|---------------------|---------|
| `data/homicides.json` | `scripts/fetch_homicides.py` pulls the WaPo CSV directly (no auth needed) | Automatic, weekly (GitHub Action) |
| `data/unidentified.json` | Export a CSV from [namus.gov/UnidentifiedPersons/Search](https://www.namus.gov/UnidentifiedPersons/Search) → save as `data/namus_unidentified_raw.csv` → `scripts/convert_namus_csv.py` | Manual export, converted automatically once the CSV is committed |
| `data/missing.json` | Export a CSV from [namus.gov/MissingPersons/Search](https://www.namus.gov/MissingPersons/Search) → save as `data/namus_missing_raw.csv` → `scripts/convert_namus_missing_csv.py` | Manual export, converted automatically once the CSV is committed |

The weekly Action (`.github/workflows/update-data.yml`) re-runs the homicide fetch and re-converts whichever raw CSVs are present, committing the result. Any data file with no export supplied yet falls back to the mock cases baked into `index.html`.

To preview locally, serve the folder with any static server (opening `index.html` directly via `file://` also works, using whatever data files are already committed):

```bash
# Python
python3 -m http.server 8080

# Node
npx serve .
```

Then open `http://localhost:8080`.

---

## Tech Stack

Pure HTML/CSS/JS — no build tools, no framework, no package manager.

| Library | Purpose | Loaded |
|---------|---------|--------|
| [Leaflet 1.9.4](https://leafletjs.com) | Interactive map | Dynamic (CDN) |
| [Leaflet.MarkerCluster 1.5.3](https://github.com/Leaflet/Leaflet.markercluster) | Marker clustering | Dynamic (CDN) |
| [Chart.js 4.4.0](https://www.chartjs.org) | Analytics charts | Lazy (CDN, Analytics tab only) |
| [Barlow Condensed + IBM Plex Mono](https://fonts.google.com) | Typography | Google Fonts |
| [CartoDB Basemaps](https://carto.com/basemaps) | Map tiles (light + dark) | Tile server |

Everything else is vanilla JS. The entire application is a single `index.html` file.

---

## Deploying to GitHub Pages

1. Fork or clone this repository
2. Ensure the main file is named `index.html`
3. Go to **Settings → Pages**
4. Set Source to **Deploy from a branch**, branch `main`, folder `/`
5. Save — your site will be live at `https://yourusername.github.io/casenet` within ~2 minutes

No build step required.

### Custom Domain

To use a custom domain (e.g. `casenet.io`):
1. Add a `CNAME` file to the repo root containing your domain
2. Configure your DNS with a CNAME record pointing to `yourusername.github.io`
3. Set the custom domain in GitHub Pages settings and enable HTTPS

---

## Project Structure

```
casenet/
├── index.html                          # Entire application — all HTML, CSS, and JS
├── data/
│   ├── homicides.json                  # Generated by scripts/fetch_homicides.py
│   ├── unidentified.json               # Generated by scripts/convert_namus_csv.py
│   ├── namus_unidentified_raw.csv      # Manually exported from namus.gov
│   └── missing.json                    # Generated by scripts/convert_namus_missing_csv.py (once a raw CSV is supplied)
├── scripts/
│   ├── fetch_homicides.py              # Pulls the WaPo homicide dataset
│   ├── convert_namus_csv.py            # Converts a NamUs unidentified-persons export
│   └── convert_namus_missing_csv.py    # Converts a NamUs missing-persons export
├── .github/workflows/update-data.yml   # Weekly data refresh
└── README.md                           # This file
```

---

## Responsible Use

**This tool aggregates public records. It is not an official law enforcement system.**

- CASENET is not affiliated with any government agency
- It does not have access to restricted law enforcement databases (ViCAP, NCIC, etc.)
- Case data may be incomplete, outdated, or contain errors inherited from source databases
- Always verify information directly with the lead agency before acting on it

### For Researchers & Journalists

Attribution to the originating database (NamUs, MAP, FBI CDE) is required when publishing. Do not republish personally identifiable information beyond what appears in the public record. Contact the lead agency before publishing details of active investigations.

### For Families

If you have information about a case, contact the lead agency listed in the case record directly. To submit or update a missing person record, contact NamUs at **1-833-526-2887** or visit [namus.gov](https://www.namus.gov). CASENET is not a substitute for working directly with law enforcement.

### Pattern Flags

The geo-temporal pattern overlay surfaces cases where law enforcement or the Murder Accountability Project has formally noted potential linkage in official records. These flags are **not CASENET's own algorithmic inference** — CASENET does not compute or generate its own linkage analysis; it only displays a linkage that was already noted in the source record. Sharing speculative public connections can compromise active investigations and harm families.

---

## Roadmap

- [x] Shareable case URLs (`?case=MP-2024-10847`)
- [x] Case Index pagination for large datasets
- [x] Real missing-persons data pipeline (NamUs CSV export → `data/missing.json`)
- [ ] Backend proxy for NamUs API — not started. The previous in-browser attempt (routing through public third-party CORS relays) was removed: it hit NamUs's auth wall regardless, and wasn't something worth shipping for data like this. A real fix needs a first-party backend holding its own NamUs session.
- [ ] MAP live data integration — not started; MAP has no public API today.
- [ ] "Submit Tip to Agency" mailto flow
- [ ] Saved searches / bookmarks
- [ ] Print / PDF case report generation
- [ ] NamUs case submission guided form
- [ ] Accessibility pass (`aria-*`, `alt`, keyboard navigation — currently absent throughout)
- [ ] CI failure alerting for the weekly data-refresh Action (currently fails silently to the Actions tab only)

---

## Contributing

Pull requests welcome. Please open an issue first to discuss significant changes.

When contributing case data, pattern flags, or agency information, ensure the source is a publicly accessible official record and include the source URL in your PR description.

---

## License

MIT — see [LICENSE](LICENSE) for details.

Data sourced from NamUs and MAP is subject to each database's own terms of use. NamUs data is a federal government resource — attribution required, commercial use restricted. MAP data is publicly available for non-commercial research and journalism.

---

> *Every unsolved case is someone waiting for an answer.*
