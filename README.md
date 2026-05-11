# lvgd.github.io

Personal site for Weitong Cai (蔡卫彤), served via GitHub Pages with the
custom domain [weitongcai.com](https://weitongcai.com).

## Sections

| Path | What it is |
|---|---|
| `index.html` | Homepage |
| `Ww/` | "W with w" — joint analytics dashboard for two Scholar profiles |
| `Job-W/` | Daily UK research-job tracker (digest archive + dashboard) |
| `ColorTrigger/` | Project page for ColorTrigger (CVPR 2026) |
| `data/citations.json` | Scholar snapshot history (powers `Ww/`) |
| `scripts/fetch_scholar.py` | Stdlib-only scraper for Google Scholar metrics |
| `.github/workflows/scrape-scholar.yml` | Manual fallback workflow for the scraper |

## Daily data refresh

`data/citations.json` is refreshed by a local LaunchAgent on a Mac mini
(residential IP — Scholar doesn't CAPTCHA it the way it does GitHub's
data-center IPs). The GitHub Action is kept for manual fallback only.
