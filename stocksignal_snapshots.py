"""Safe comparison of two inventory CSV exports.

This module reports observable differences only. It does not infer why a
quantity changed, approve stock movements, or write to either source file.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
import json
import math
from typing import Any

import pandas as pd

from stocksignal import REQUIRED_COLUMNS

KEY_COLUMNS = ("facility_code", "product_code", "batch_number")
COMPARE_COLUMNS = (
    "product_name",
    "quantity_on_hand",
    "average_monthly_consumption",
    "lead_time_days",
    "expiry_date",
    "last_stock_update",
)
NUMERIC_COLUMNS = {"quantity_on_hand", "average_monthly_consumption", "lead_time_days"}
DATE_COLUMNS = {"expiry_date", "last_stock_update"}
REPORT_COLUMNS = [
    "change_type",
    "facility_code",
    "product_code",
    "batch_number",
    "previous_row",
    "current_row",
    "changed_fields",
    "previous_values",
    "current_values",
    "review_note",
]


def _is_missing(value: Any) -> bool:
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _canonical(value: Any, column: str) -> str:
    """Normalise values for comparison without guessing business meaning."""
    if _is_missing(value):
        return ""
    if column in NUMERIC_COLUMNS:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value).strip()
        if not math.isfinite(number):
            return f"INVALID:{number}"
        return format(number, ".15g")
    if column in DATE_COLUMNS:
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return str(value).strip()
        return parsed.date().isoformat()
    return str(value).strip()


def _key(row: pd.Series) -> tuple[str, str, str]:
    return tuple(_canonical(row[column], column) for column in KEY_COLUMNS)  # type: ignore[return-value]


def _json_values(values: dict[str, str]) -> str:
    return json.dumps(values, ensure_ascii=False, sort_keys=True)


def compare_inventory_snapshots(
    previous: pd.DataFrame,
    current: pd.DataFrame,
) -> tuple[dict[str, int], pd.DataFrame]:
    """Compare previous/current exports by facility + product + batch.

    Duplicate keys in either file are marked ambiguous and are never treated
    as added, removed, changed, or unchanged. Rows missing key fields are
    reported as unmatchable. A removed record means only that its key was not
    present in the newer export; it does not establish why it disappeared.
    """
    for label, frame in (("previous", previous), ("current", current)):
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"{label.title()} snapshot must be a pandas DataFrame.")
        missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
        if missing:
            raise ValueError(f"{label.title()} snapshot is missing required columns: " + ", ".join(missing))

    old = previous.loc[:, REQUIRED_COLUMNS].copy().reset_index(drop=True)
    new = current.loc[:, REQUIRED_COLUMNS].copy().reset_index(drop=True)
    old_keys = [_key(row) for _, row in old.iterrows()]
    new_keys = [_key(row) for _, row in new.iterrows()]
    old_counts = Counter(key for key in old_keys if all(key))
    new_counts = Counter(key for key in new_keys if all(key))

    ambiguous = {
        key for key in set(old_counts) | set(new_counts)
        if old_counts.get(key, 0) > 1 or new_counts.get(key, 0) > 1
    }
    old_positions: dict[tuple[str, str, str], int] = {
        key: index for index, key in enumerate(old_keys) if all(key) and key not in ambiguous
    }
    new_positions: dict[tuple[str, str, str], int] = {
        key: index for index, key in enumerate(new_keys) if all(key) and key not in ambiguous
    }

    events: list[dict[str, Any]] = []

    def add_event(
        change_type: str,
        key: tuple[str, str, str] | None,
        previous_row: int | None,
        current_row: int | None,
        changed: dict[str, str] | None = None,
        old_values: dict[str, str] | None = None,
        new_values: dict[str, str] | None = None,
        note: str = "",
    ) -> None:
        key = key or ("", "", "")
        events.append({
            "change_type": change_type,
            "facility_code": key[0],
            "product_code": key[1],
            "batch_number": key[2],
            "previous_row": previous_row,
            "current_row": current_row,
            "changed_fields": "; ".join((changed or {}).keys()),
            "previous_values": _json_values(old_values or {}),
            "current_values": _json_values(new_values or {}),
            "review_note": note,
        })

    # Duplicate keys are deliberately excluded from normal matching.
    for key in sorted(ambiguous):
        add_event(
            "Ambiguous duplicate key", key, None, None,
            old_values={"row_count": str(old_counts.get(key, 0))},
            new_values={"row_count": str(new_counts.get(key, 0))},
            note="Duplicate identity in at least one snapshot; verify source rows before comparing.",
        )

    # Rows without a complete identity cannot be matched safely.
    unmatchable_rows = 0
    for index, key in enumerate(old_keys):
        if not all(key):
            unmatchable_rows += 1
            add_event(
                "Unmatchable row (previous)", None, index + 2, None,
                old_values={column: _canonical(old.iloc[index][column], column) for column in REQUIRED_COLUMNS},
                note="One or more identity fields are missing; this row was not matched.",
            )
    for index, key in enumerate(new_keys):
        if not all(key):
            unmatchable_rows += 1
            add_event(
                "Unmatchable row (current)", None, None, index + 2,
                new_values={column: _canonical(new.iloc[index][column], column) for column in REQUIRED_COLUMNS},
                note="One or more identity fields are missing; this row was not matched.",
            )

    old_set = set(old_positions)
    new_set = set(new_positions)
    added_keys = sorted(new_set - old_set)
    removed_keys = sorted(old_set - new_set)
    matched_keys = sorted(old_set & new_set)
    changed_count = 0
    unchanged_count = 0

    for key in added_keys:
        index = new_positions[key]
        row = new.iloc[index]
        add_event(
            "Added in current snapshot", key, None, index + 2,
            new_values={column: _canonical(row[column], column) for column in COMPARE_COLUMNS},
            note="Identity is present in the newer export only; verify against the source system.",
        )

    for key in removed_keys:
        index = old_positions[key]
        row = old.iloc[index]
        add_event(
            "Not present in current snapshot", key, index + 2, None,
            old_values={column: _canonical(row[column], column) for column in COMPARE_COLUMNS},
            note="Identity is absent from the newer export; this does not establish why it disappeared.",
        )

    for key in matched_keys:
        old_index, new_index = old_positions[key], new_positions[key]
        old_row, new_row = old.iloc[old_index], new.iloc[new_index]
        old_values: dict[str, str] = {}
        new_values: dict[str, str] = {}
        for column in COMPARE_COLUMNS:
            before = _canonical(old_row[column], column)
            after = _canonical(new_row[column], column)
            if before != after:
                old_values[column] = before
                new_values[column] = after
        if old_values:
            changed_count += 1
            add_event(
                "Record changed", key, old_index + 2, new_index + 2,
                changed=old_values, old_values=old_values, new_values=new_values,
                note="One or more source fields changed; the comparison does not infer the cause.",
            )
        else:
            unchanged_count += 1

    summary = {
        "previous_rows": len(old),
        "current_rows": len(new),
        "added_records": len(added_keys),
        "not_present_in_current": len(removed_keys),
        "changed_records": changed_count,
        "unchanged_records": unchanged_count,
        "ambiguous_duplicate_keys": len(ambiguous),
        "unmatchable_rows": unmatchable_rows,
    }
    report = pd.DataFrame(events, columns=REPORT_COLUMNS)
    return summary, report


def build_snapshot_audit_metadata(
    previous_filename: str,
    current_filename: str,
    summary: dict[str, int],
) -> pd.DataFrame:
    """Return a small, downloadable comparison receipt for the current run."""
    receipt = {
        "comparison_generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "previous_filename": str(previous_filename),
        "current_filename": str(current_filename),
        **summary,
        "purpose": "Read-only inventory snapshot comparison; human verification required.",
    }
    return pd.DataFrame([receipt])
