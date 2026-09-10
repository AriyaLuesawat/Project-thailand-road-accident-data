#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replace Road_Name values with Latin-script RTGS-style transliterations."""

import csv
import hashlib
import json
import os
import re
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import tltk
from pythainlp.transliterate import romanize as pythai_romanize

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "Translated_data"
THAI_RUN = re.compile(r"[\u0E00-\u0E7F]+")
THAI_ANY = re.compile(r"[\u0E00-\u0E7F]")
THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
OVERRIDES = {
    "กม": "km",
    "ตชด": "TCHD",
}
THAI_INITIALS = {
    "ก":"K","ข":"Kh","ฃ":"Kh","ค":"Kh","ฅ":"Kh","ฆ":"Kh","ง":"Ng",
    "จ":"Ch","ฉ":"Ch","ช":"Ch","ซ":"S","ฌ":"Ch","ญ":"Y","ฎ":"D",
    "ฏ":"T","ฐ":"Th","ฑ":"Th","ฒ":"Th","ณ":"N","ด":"D","ต":"T",
    "ถ":"Th","ท":"Th","ธ":"Th","น":"N","บ":"B","ป":"P","ผ":"Ph",
    "ฝ":"F","พ":"Ph","ฟ":"F","ภ":"Ph","ม":"M","ย":"Y","ร":"R",
    "ล":"L","ว":"W","ศ":"S","ษ":"S","ส":"S","ห":"H","ฬ":"L",
    "อ":"O","ฮ":"H",
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def romanize_run(text):
    if text in OVERRIDES:
        return OVERRIDES[text]
    try:
        result = tltk.nlp.th2roman(text).replace("<s/>", "").strip()
    except Exception:
        result = ""
    if not result:
        result = pythai_romanize(text, engine="royin").strip()
    if not result and all(char in THAI_INITIALS for char in text):
        result = "".join(THAI_INITIALS[char] for char in text)
    if not result or THAI_ANY.search(result):
        raise ValueError(f"Failed to transliterate Thai segment: {text!r} -> {result!r}")
    return result[0].upper() + result[1:]


def transliterate(text, cache):
    if text in cache:
        return cache[text]
    text = text.translate(THAI_DIGITS)
    result = THAI_RUN.sub(lambda match: romanize_run(match.group(0)), text)
    result = re.sub(r"[ \t]+", " ", result).strip()
    if THAI_ANY.search(result):
        raise ValueError(f"Thai remains in road name: {text!r} -> {result!r}")
    cache[text] = result
    return result


def process(path, cache):
    temp = path.with_suffix(".tmp.csv")
    before_hash = sha256(path)
    rows = changed = 0
    with path.open(encoding="utf-8-sig", newline="") as source, temp.open(
        "w", encoding="utf-8-sig", newline=""
    ) as target:
        reader = csv.reader(source)
        writer = csv.writer(target)
        header = next(reader)
        if "Road_Name" not in header:
            raise ValueError(f"Road_Name column not found in {path.name}")
        road_index = header.index("Road_Name")
        writer.writerow(header)
        for row in reader:
            original = list(row)
            row[road_index] = transliterate(row[road_index], cache)
            if row[road_index] != original[road_index]:
                changed += 1
            if any(row[i] != original[i] for i in range(len(row)) if i != road_index):
                raise AssertionError(f"Non-road value changed at row {rows + 2}")
            writer.writerow(row)
            rows += 1

    # Full read-back validation before replacing the existing translated file.
    with path.open(encoding="utf-8-sig", newline="") as old, temp.open(
        encoding="utf-8-sig", newline=""
    ) as new:
        old_reader, new_reader = csv.reader(old), csv.reader(new)
        old_header, new_header = next(old_reader), next(new_reader)
        if old_header != new_header:
            raise AssertionError("Header changed")
        road_index = old_header.index("Road_Name")
        validated_rows = 0
        for validated_rows, (old_row, new_row) in enumerate(zip(old_reader, new_reader), 1):
            if len(old_row) != len(new_row):
                raise AssertionError(f"Column count changed at row {validated_rows + 1}")
            if any(old_row[i] != new_row[i] for i in range(len(old_row)) if i != road_index):
                raise AssertionError(f"Unexpected change at row {validated_rows + 1}")
            if THAI_ANY.search(new_row[road_index]):
                raise AssertionError(f"Thai remains at row {validated_rows + 1}")
        if validated_rows != rows:
            raise AssertionError("Row count changed")

    os.replace(temp, path)
    return {
        "file": path.name,
        "rows": rows,
        "road_name_rows_changed": changed,
        "before_sha256": before_hash,
        "after_sha256": sha256(path),
        "bytes": path.stat().st_size,
        "validated": True,
    }


def main():
    cache = {}
    reports = []
    for year in range(2019, 2026):
        reports.append(process(DATA / f"accident{year}_en.csv", cache))
    (DATA / "road_name_transliteration_map.json").write_text(
        json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (DATA / "road_name_transliteration_report.json").write_text(
        json.dumps(reports, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"unique_road_names": len(cache), "files": reports}, indent=2))


if __name__ == "__main__":
    main()
