from datetime import date

import pandas as pd
import pytest

from stocksignal import REQUIRED_COLUMNS
from stocksignal_snapshots import compare_inventory_snapshots


def row(**overrides):
    record = {
        "facility_code": "F1",
        "product_code": "P1",
        "product_name": "Product",
        "batch_number": "B1",
        "quantity_on_hand": 100,
        "average_monthly_consumption": 100,
        "lead_time_days": 10,
        "expiry_date": "2027-06-30",
        "last_stock_update": "2026-11-01",
    }
    record.update(overrides)
    return record


def frame(*records):
    return pd.DataFrame(records, columns=REQUIRED_COLUMNS)


def test_identical_snapshots_are_reported_unchanged():
    summary, report = compare_inventory_snapshots(frame(row()), frame(row()))
    assert summary["unchanged_records"] == 1
    assert summary["changed_records"] == 0
    assert report.empty


def test_quantity_change_is_reported_with_before_and_after_values():
    summary, report = compare_inventory_snapshots(
        frame(row()), frame(row(quantity_on_hand=80))
    )
    assert summary["changed_records"] == 1
    assert report.iloc[0]["change_type"] == "Record changed"
    assert '"quantity_on_hand": "100"' in report.iloc[0]["previous_values"]
    assert '"quantity_on_hand": "80"' in report.iloc[0]["current_values"]


def test_added_and_removed_records_are_distinguished():
    previous = frame(row(batch_number="OLD"))
    current = frame(row(batch_number="NEW"))
    summary, report = compare_inventory_snapshots(previous, current)
    assert summary["added_records"] == 1
    assert summary["not_present_in_current"] == 1
    assert set(report["change_type"]) == {
        "Added in current snapshot", "Not present in current snapshot"
    }


def test_duplicate_key_in_either_snapshot_is_ambiguous_not_added_or_removed():
    previous = frame(row(), row())
    current = frame(row())
    summary, report = compare_inventory_snapshots(previous, current)
    assert summary["ambiguous_duplicate_keys"] == 1
    assert summary["added_records"] == 0
    assert summary["not_present_in_current"] == 0
    assert report.iloc[0]["change_type"] == "Ambiguous duplicate key"


def test_missing_key_rows_are_unmatchable():
    previous = frame(row(batch_number=None))
    current = frame(row())
    summary, report = compare_inventory_snapshots(previous, current)
    assert summary["unmatchable_rows"] == 1
    assert summary["added_records"] == 1
    assert "Unmatchable row (previous)" in set(report["change_type"])


def test_date_formats_compare_as_same_calendar_date():
    previous = frame(row(expiry_date="2027-06-30"))
    current = frame(row(expiry_date="2027-06-30 00:00:00"))
    summary, report = compare_inventory_snapshots(previous, current)
    assert summary["unchanged_records"] == 1
    assert report.empty


def test_required_columns_are_enforced():
    with pytest.raises(ValueError, match="missing required columns"):
        compare_inventory_snapshots(pd.DataFrame({"facility_code": ["F1"]}), frame(row()))


def test_multiple_changed_fields_are_reported_together():
    summary, report = compare_inventory_snapshots(
        frame(row()),
        frame(row(quantity_on_hand=85, last_stock_update="2026-11-05")),
    )
    assert summary["changed_records"] == 1
    assert "quantity_on_hand" in report.iloc[0]["changed_fields"]
    assert "last_stock_update" in report.iloc[0]["changed_fields"]
