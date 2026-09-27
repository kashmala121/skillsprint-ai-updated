# UI Upgrade & SRS Completion Notes

## 1. Premium UI theme (no more default blue/purple Streamlit look)

- `frontend/.streamlit/config.toml` — sets a charcoal + gold enterprise
  palette at the Streamlit engine level (this is what actually removes the
  default blue/purple).
- `frontend/utils/theme.py` — a shared design system: custom fonts
  (Playfair Display for headings, Inter for body), gold gradient buttons,
  bordered "card" containers, gold-accented metric cards, styled tabs/
  expanders/inputs/dataframes, a `hero()` banner component, and
  status-aware badges (green = Verified, gold = Warning, red = flagged).
- Every page (`app.py` + all 7 pages under `frontend/pages/`) now calls
  `theme.inject()` right after `st.set_page_config()` and uses `theme.hero()`,
  `theme.card_start()/card_end()`, and `theme.badge()` for a consistent,
  premium, non-templated look — closer to an enterprise SaaS dashboard than
  a default Streamlit app.
- Admin Dashboard now uses Plotly (donut chart + gauge) themed to match,
  instead of plain `st.metric` blocks only.

## 2. Remaining SRS requirements completed

- **Reports exportable in CSV, PDF, and Excel-compatible formats**
  (SRS Step 63 / §1.6 "Export"): previously only CSV existed.
  Added:
  - `GET /reports/coverage.xlsx` — styled Excel workbook (openpyxl)
  - `GET /reports/coverage.pdf` — formatted PDF table (reportlab)
  - `GET /reports/requirement-matrix.xlsx` — full Role Requirement Matrix export
  All three now have download buttons on the Admin Dashboard page.
- **Search and Filtering** (SRS Step 61 / §1.6 "Search and Filtering"):
  previously missing as a UI feature. Added live search/filter controls to:
  - Documents page (search by title/filename, filter by type/status)
  - Roles & Requirements page (search roles, search requirement text,
    filter by role and mandatory/optional)
  - Employees page (search by name, filter by role and training status)
  - Validation & Review page (search the audit trail)

## 3. Dependency notes

- `backend/requirements.txt` gained `openpyxl` and `reportlab` back
  (they are now genuinely used by the new export endpoints).
- No other backend logic changed — the GenAI pipeline, Python validation
  engine, comparison engine, and security scanner are untouched.
