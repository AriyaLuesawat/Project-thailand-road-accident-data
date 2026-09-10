#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Combine translated 2020–2025 CSVs into one validated CSV."""

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "Translated_data"
OUTPUT = DATA / "accident2020_2025_en.csv"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    paths = [DATA / f"accident{year}_en.csv" for year in range(2020, 2026)]
    headers = {}
    counts = {}
    for path in paths:
        with path.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.reader(source)
            headers[path] = next(reader)

    # Use the current 38-column schema first, then retain any legacy-only field.
    combined_header = list(headers[paths[1]])
    for path in paths:
        for column in headers[path]:
            if column not in combined_header:
                combined_header.append(column)

    total_rows = 0
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=combined_header, extrasaction="raise")
        writer.writeheader()
        for path in paths:
            count = 0
            with path.open(encoding="utf-8-sig", newline="") as source:
                reader = csv.DictReader(source)
                for row in reader:
                    writer.writerow(row)
                    count += 1
            counts[path.name] = count
            total_rows += count

    # Validate header, row count, year coverage, and column width by reading back.
    years = set()
    blank_year_rows = 0
    validated_rows = 0
    with OUTPUT.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source)
        output_header = next(reader)
        if output_header != combined_header:
            raise AssertionError("Combined header mismatch")
        year_index = output_header.index("Accident_Year")
        for validated_rows, row in enumerate(reader, 1):
            if len(row) != len(combined_header):
                raise AssertionError(f"Column mismatch at combined row {validated_rows + 1}")
            if row[year_index]:
                years.add(row[year_index])
            else:
                blank_year_rows += 1

    if validated_rows != total_rows:
        raise AssertionError("Combined row count mismatch")
    expected_years = {str(year) for year in range(2020, 2026)}
    if years != expected_years:
        raise AssertionError(f"Unexpected year coverage: {sorted(years)}")

    report = {
        "output": OUTPUT.name,
        "rows": total_rows,
        "columns": len(combined_header),
        "years": sorted(years),
        "blank_accident_year_rows_preserved": blank_year_rows,
        "source_rows": counts,
        "sha256": sha256(OUTPUT),
        "bytes": OUTPUT.stat().st_size,
        "validated": True,
    }
    (DATA / "combined_file_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
