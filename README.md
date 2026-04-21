# CASENET
### Public Case Transparency Network

A public-facing visualization and aggregation tool for missing persons, unidentified remains, and unsolved homicides in the United States. Built to increase transparency, support families, and surface public-record data in a format accessible to anyone.

> **Prototype status.** Current case data is representative mock data structured to match real NamUs and MAP schemas. Live API integration is functional when hosted on HTTP/HTTPS. All prototype case IDs, names, and circumstances are illustrative only.

---

## Live Demo

[**casenet.untruesudo.github.io**](https://untruesudo.github.io/casenet) 

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
| **Murder Accountability Project (MAP)** | Unsolved homicides | [murderdata.org](https://www.murderdata.org) |
| **FBI Crime Data Explorer** | Aggregate crime statistics | [cde.ucr.cjis.fbi.gov](https://cde.ucr.cjis.fbi.gov) |

Map tiles © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, © [CARTO](https://carto.com/attributions).

### Live Data

When hosted on `http://` or `https://`, CASENET attempts to fetch live missing persons and unidentified remains data directly from the NamUs public API on load. Homicide data from MAP is currently mock/static pending MAP's own API availability.

When running from a local `file://` URL (e.g. opened directly in a browser), the live fetch is skipped automatically and prototype data is used instead. To test live data locally, serve the file with any static server:

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
├── index.html      # Entire application — all HTML, CSS, and JS
└── README.md       # This file
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

The geo-temporal pattern overlay surfaces cases where law enforcement or the Murder Accountability Project has formally noted potential linkage in official records. These flags are **not algorithmic inference** — CASENET does not generate its own linkage analysis. Sharing speculative public connections can compromise active investigations and harm families.

---

## Roadmap

- [ ] Backend proxy for NamUs API (removes CORS dependency)
- [ ] MAP live data integration
- [ ] Shareable case URLs (`?case=MP-2024-10847`)
- [ ] Case Index pagination for large datasets
- [ ] "Submit Tip to Agency" mailto flow
- [ ] Saved searches / bookmarks
- [ ] Print / PDF case report generation
- [ ] NamUs case submission guided form

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
