"""Streaming TSV parser. Memory-bounded, schema-aware."""
from __future__ import annotations
import csv
import zipfile
from pathlib import Path
from typing import Iterator, Dict, Any
import io

csv.field_size_limit(10_000_000)


def stream_tsv_from_zip(zip_path: Path) -> Iterator[Dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as z:
        names = [n for n in z.namelist() if n.endswith(".tsv")]
        if not names:
            return
        with z.open(names[0]) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace")
            reader = csv.DictReader(text, delimiter="\t", quoting=csv.QUOTE_NONE)
            for row in reader:
                yield {k.strip('"'): v.strip('"') if v else v for k, v in row.items()}
