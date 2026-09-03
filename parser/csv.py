import csv
from typing import TypedDict
from ._meta import FileMeta, file_meta


class CsvResult(FileMeta):
    """Parsed CSV file metadata."""
    type: str
    content: str
    rows: int
    columns: int
    headers: list[str]
    delimiter: str


def parse_csv(path: str) -> CsvResult:
    """Parse a CSV file.

    Detects delimiter, extracts headers and counts rows.

    Args:
        path: str — path to the CSV file.

    Returns:
        dict: {
            "type": str — always "csv",
            "content": str — formatted table preview,
            "rows": int — number of data rows,
            "columns": int — number of columns,
            "headers": list[str] — first row as headers,
            "delimiter": str — detected delimiter,
            "path": str — full file path,
            "name": str — file name only,
            "size": int — file size in bytes,
        }
    """
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        sample = f.read(8192)

    try:
        dialect = csv.Sniffer().sniff(sample)
    except csv.Error:
        dialect = csv.excel

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, dialect)
        all_rows = list(reader)

    if not all_rows:
        return {
            "type": "csv", "content": "", "rows": 0, "columns": 0,
            "headers": [], "delimiter": dialect.delimiter, **file_meta(path),
        }

    headers = all_rows[0]
    data_rows = all_rows[1:]
    columns = max(len(row) for row in all_rows) if all_rows else 0

    lines = [f"Headers: {dialect.delimiter.join(headers)}"]
    lines.append(f"Rows: {len(data_rows)}, Columns: {columns}")
    lines.append("")
    for i, row in enumerate(data_rows[:50]):
        lines.append(dialect.delimiter.join(row))
    if len(data_rows) > 50:
        lines.append(f"\n... ({len(data_rows) - 50} more rows)")

    return {
        "type": "csv",
        "content": "\n".join(lines),
        "rows": len(data_rows),
        "columns": columns,
        "headers": headers,
        "delimiter": dialect.delimiter,
        **file_meta(path),
    }
