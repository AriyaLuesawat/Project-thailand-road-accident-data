# Thailand Road Accident Data

This repository contains Thai road-accident datasets, English translations, cleaned workbooks, and the scripts used to validate and combine the data.

## Repository structure

- `raw/` — source CSV files for 2019–2025.
- `Translated_data/` — yearly English CSV files, combined datasets, translation manifests, checksums, and validation reports.
- `Clean_data/` — cleaned 2020–2025 Excel workbook.
- `Final Work/` — final workbook and HTML report.
- `translate_accidents.py` — translates headers and standardized categorical values while preserving identifiers, coordinates, row order, and numeric fields.
- `transliterate_road_names.py` — transliterates Thai road names into Latin script and validates that unrelated fields remain unchanged.
- `combine_translated_years.py` — combines the translated 2020–2025 files and validates schema, row counts, and year coverage.

## Reproducing the translated data

Python 3 is required. Install the optional transliteration dependencies, then run:

```bash
python -m pip install -r requirements.txt
python translate_accidents.py
python transliterate_road_names.py
python combine_translated_years.py
```

The translation and combination scripts write JSON reports containing row counts, hashes, and validation results to `Translated_data/`.

## Data notes

- CSV files use UTF-8 with BOM for spreadsheet compatibility.
- Proper identifiers, route codes, dates, times, numeric values, coordinates, and source row ordering are preserved during translation.
- The repository contains large data files; cloning may take some time.
- The working Google Drive folder is available [here](https://drive.google.com/drive/folders/1nARJRuXmP4n_WM8ztthTPTs9uaucvtBF).

## Usage

Review the source dataset's terms and attribution requirements before redistributing or using the data in production. Validate analytical conclusions against the original Thai records.
