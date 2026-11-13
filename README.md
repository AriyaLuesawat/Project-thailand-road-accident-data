# Thailand Road Accident Data

Thai road-accident records for 2019–2025, translated into English, with the scripts that produce and check the translation. The records come from the Department of Highways, the Department of Rural Roads, and the Expressway Authority of Thailand.

**Dashboard:** <https://ariyaluesawat.github.io/Project-thailand-road-accident-data/Final%20Work/final.html> — Thailand road safety dashboard (maps, KPIs, and charts) built from `Final Work/Group 4.xlsx`.

The translation changes only the language. Row order, IDs, route codes, dates, times, numbers, and coordinates are the same as in the Thai source files.

## What's in the data

| File | Years | Rows | Columns |
| --- | --- | ---: | ---: |
| `accident2019_en.csv` | 2019 | 40,246 (19,194 with data) | 19 |
| `accident2020_en.csv` | 2020 | 21,239 | 38 |
| `accident2021_en.csv` | 2021 | 20,062 | 38 |
| `accident2022_en.csv` | 2022 | 20,566 | 38 |
| `accident2023_en.csv` | 2023 | 23,841 | 38 |
| `accident2024_en.csv` | 2024 | 23,952 | 38 |
| `accident2025_en.csv` | 2025 | 23,715 | 38 |
| `accident2020_2025_en.csv` | 2020–2025 | 133,375 | 38 |
| `accident2019_2025_en.csv` | 2019–2025 | 173,621 | 40 |

All files are in `Translated_data/`. Row counts exclude the header.

Rows by agency (2020–2025): Department of Highways 123,708, Department of Rural Roads 7,315, and Expressway Authority of Thailand 2,352.

### Columns (2020–2025)

| Group | Columns |
| --- | --- |
| When | `Accident_Year`, `Accident_Date`, `Accident_Time`, `Report_Date`, `Report_Time` |
| Where | `Agency`, `Agency_Road_Type`, `Route_Code`, `Road_Name`, `Kilometer`, `Province`, `Accident_Location`, `LATITUDE`, `LONGITUDE` |
| What happened | `ACC_CODE`, `First_Vehicle`, `Presumed_Cause`, `Accident_Type`, `Weather` |
| Vehicles | `Vehicles_Involved`, `Vehicles_and_People_Involved`, `Motorcycles`, `Motorized_Three_Wheelers`, `Private_Cars`, `Vans`, `Passenger_Pickups`, `Buses_Over_4_Wheels`, `Four_Wheel_Cargo_Pickups`, `Six_Wheel_Trucks`, `Trucks_Up_To_10_Wheels`, `Trucks_Over_10_Wheels`, `Farm_Vehicles`, `Other_Vehicles`, `Pedestrians` |
| Casualties | `Fatalities`, `Serious_Injuries`, `Minor_Injuries`, `Total_Injuries` |

The 2019 file uses an older 19-column layout. It has no vehicle-type counts, no `ACC_CODE`, no `Route_Code`, and no serious/minor injury split. It has `Accident_Location_Road_Geometry` and `Number_of_Vehicles_Involved` instead.

## Things to know before analysing

- **Date formats differ by year.** In 2019–2023, `Accident_Date` and `Report_Date` are day/month/year text, such as `1/1/2020` (2022 uses `01/01/2022`). In 2024–2025 they are Excel serial numbers, such as `45658` = 1 January 2025. Convert serials from 30 December 1899: `pd.to_datetime(s, unit="D", origin="1899-12-30")`.
- **2019 has 21,052 empty rows.** They have no year, date, province, or coordinates, so drop them first. They are also in `accident2019_2025_en.csv`.
- **Road names are transliterated, not translated.** `Road_Name` holds the Thai name in Latin script (for example `Noenmok - Plaengyao`), so names stay recognisable as official identifiers. `road_name_transliteration_map.json` maps each Thai name to its Latin form.
- **Encoding.** Files are UTF-8 with BOM so Excel shows them correctly. In pandas, use `encoding="utf-8-sig"`.

```python
import pandas as pd

df = pd.read_csv("Translated_data/accident2020_2025_en.csv", encoding="utf-8-sig")
```

## Repository layout

```
raw/                 Thai source CSVs, one per year (2019–2025)
Translated_data/     English CSVs, combined files, and JSON validation reports
Clean_data/          accident_2020-2025.xlsx — cleaned 2020–2025 workbook
Final Work/          Group 4.xlsx (cleaned data, data dictionary, KPI guide, work log)
                     final.html — road-safety dashboard (live link above)
```

## Reproducing the translation

Python 3 is required. Run the scripts in this order from the repository root:

```bash
python -m pip install -r requirements.txt   # pythainlp, tltk (for road-name transliteration)
python translate_accidents.py               # raw/ → Translated_data/accidentYYYY_en.csv
python transliterate_road_names.py          # Thai road names → Latin script
python combine_translated_years.py          # → Translated_data/accident2020_2025_en.csv
```

| Script | What it does | Report it writes |
| --- | --- | --- |
| `translate_accidents.py` | Translates headers and category values (agency, vehicle, cause, weather, …) | `translation_manifest.json` |
| `transliterate_road_names.py` | Transliterates `Road_Name` and checks that no other field changed | `road_name_transliteration_report.json`, `road_name_transliteration_map.json` |
| `combine_translated_years.py` | Joins 2020–2025, then checks columns, row counts, and years | `combined_file_report.json` |

Each report records row counts and SHA-256 hashes, so you can confirm a re-run matches the published files.

`accident2019_2025_en.csv` is not made by these scripts. It is `accident2019_en.csv` and `accident2020_2025_en.csv` stacked together. It has the 38 columns from 2020–2025 plus `Accident_Location_Road_Geometry` and `Number_of_Vehicles_Involved` from 2019.

## Notes

- The data files total about 245 MB, so cloning takes a while.
- The working Google Drive folder is [here](https://drive.google.com/drive/folders/1nARJRuXmP4n_WM8ztthTPTs9uaucvtBF).
- Check the source agencies' terms and attribution requirements before redistributing the data. Check important findings against the original Thai records in `raw/`.
