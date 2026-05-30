# Veervrat Content CMS

Internal dev tool for managing the Veervrat content database. Not for production.

## Stack

FastAPI · SQLite · Jinja2 · plain HTML/CSS

Database lives at `veervrat_cms.db` (single file, gitignore or commit as needed).

## Setup

```bash
# From repo root
source /Users/omc1/Documents/.venv/bin/activate.fish

cd data/cms
pip install -r requirements.txt

# First time only — init schema and seed from CSVs
python seed.py

# Start server
uvicorn main:app --port 8765 --reload
```

Open http://localhost:8765

## Pages

| URL | Purpose |
|-----|---------|
| `/` | Data model — ERD diagram + live row counts |
| `/virtues` | Virtues CRUD |
| `/subvirtues` | Subvirtues CRUD, linked to a virtue |
| `/weaknesses` | Weaknesses list; click to manage subvirtue links |
| `/sentences` | Sentences CRUD, filterable by subvirtue |
| `/plans` | Plans list — each plan holds exposures, resolutions, challenge |
| `/plans/{id}` | Full plan editor |

## Data model

```
virtue
  └── subvirtue (many per virtue)
        └── sentence (many per subvirtue)

weakness
  └── weakness_subvirtue (join table, with priority)
        └── subvirtue

plan (linked to virtue + optional weakness, has source_file for traceability)
  ├── exposure  (tier: local / national / international)
  ├── resolution (duration_weeks)
  └── challenge  (duration_days, one per plan)
```

## Seeding

`seed.py` imports from the CSV files one level up (`../`):

- `virtues.csv`
- `subvirtues.csv`
- `weakness.csv`
- `weakness_subvirtues.csv`
- `sentences.csv`

Re-running seed is safe — uses `INSERT OR IGNORE`.

## Source file traceability

Each plan has a `source_file` field. Point it to the original document in `../exposure-resolution-challenge/` (e.g. `Problem33_Initiative_Plan (1).pdf`). See `ANALYSIS.md` in that folder for a full inventory of what each file contains.

## Exporting

```bash
# Dump any table to CSV
sqlite3 -header -csv veervrat_cms.db "SELECT * FROM plan;" > plans_export.csv
```
