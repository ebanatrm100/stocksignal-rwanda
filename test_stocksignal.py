from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from stocksignal import REQUIRED_COLUMNS, audit_inventory

SAMPLE = Path(__file__).resolve().parents[1] / "sample_inventory.csv"
AS_OF = date(2026, 10, 11)


def make_row(**overrides):
    row = {
        "facility_code": "DEMO-HC-99",
        "product_code": "DEMO-TEST-01",
        "product_name": "Synthetic test item",
        "batch_number": "BATCH-001",
        "quantity_on_hand": 100,
        "average_monthly_consumption": 100,
        "lead_time_days": 10,
        "expiry_date": "2027-10-01",
        "last_stock_update": "2026-10-10",
    }
    row.update(overrides)
    return row


def test_sample_flags_expected_data_issues():
    data = pd.read_csv(SAMPLE)
    audit, products = audit_inventory(data, AS_OF)

    assert audit["review_flags"].str.contains("Negative quantity on hand").any()
    assert audit["review_flags"].str.contains("Duplicate facility/product/batch key").sum() == 2
    assert audit["review_flags"].str.contains("Batch is expired").any()
    assert audit["review_flags"].str.contains("Stock record is stale").any()
    assert products["stock_review_status"].str.startswith("Review:").any()


def test_missing_required_column_raises_error():
    data = pd.read_csv(SAMPLE).drop(columns=["expiry_date"])
    with pytest.raises(ValueError, match="expiry_date"):
        audit_inventory(data, AS_OF)


def test_negative_threshold_raises_error():
    with pytest.raises(ValueError, match="cannot be negative"):
        audit_inventory(pd.read_csv(SAMPLE), AS_OF, stale_days=-1)


def test_expired_stock_is_excluded_from_cover():
    data = pd.DataFrame(
        [
            make_row(batch_number="GOOD", quantity_on_hand=30, expiry_date="2027-01-01"),
            make_row(batch_number="EXPIRED", quantity_on_hand=300, expiry_date="2026-10-01"),
        ]
    )
    _, products = audit_inventory(data, AS_OF, lead_buffer_days=0)
    product = products.iloc[0]

    assert product["eligible_quantity_on_hand"] == 30
    assert product["eligible_batch_rows"] == 1
    assert product["excluded_batch_rows"] == 1
    assert product["estimated_days_of_stock"] == 9.1


def test_missing_expiry_and_duplicate_batch_rows_are_excluded_from_cover():
    row = make_row(batch_number="DUP", expiry_date="2027-10-01")
    data = pd.DataFrame(
        [row, row, make_row(batch_number="NO-EXPIRY", expiry_date=None, quantity_on_hand=500)]
    )
    _, products = audit_inventory(data, AS_OF)
    product = products.iloc[0]

    assert product["eligible_batch_rows"] == 0
    assert product["excluded_batch_rows"] == 3
    assert pd.isna(product["estimated_days_of_stock"])
    assert "no eligible" in product["stock_review_status"].lower()


def test_infinite_numeric_values_are_flagged_and_not_used():
    data = pd.DataFrame([make_row(quantity_on_hand="inf")])
    audit, products = audit_inventory(data, AS_OF)

    assert "Invalid number in quantity_on_hand" in audit.iloc[0]["review_flags"]
    assert products.iloc[0]["eligible_batch_rows"] == 0
    assert pd.isna(products.iloc[0]["estimated_days_of_stock"])


def test_zero_consumption_does_not_divide_by_zero():
    data = pd.DataFrame([make_row(average_monthly_consumption=0)])
    _, products = audit_inventory(data, AS_OF)

    assert pd.isna(products.iloc[0]["estimated_days_of_stock"])
    assert "consumption is zero" in products.iloc[0]["stock_review_status"].lower()


def test_missing_columns_are_defined_and_required():
    assert "facility_code" in REQUIRED_COLUMNS
    assert "expiry_date" in REQUIRED_COLUMNS


def test_negative_quantity_is_flagged_and_excluded():
    data = pd.DataFrame([make_row(quantity_on_hand=-6)])
    audit, products = audit_inventory(data, AS_OF)

    assert "Negative quantity on hand" in audit.iloc[0]["review_flags"]
    assert products.iloc[0]["eligible_batch_rows"] == 0
    assert pd.isna(products.iloc[0]["estimated_days_of_stock"])


def test_conflicting_consumption_is_flagged():
    data = pd.DataFrame(
        [
            make_row(batch_number="A", average_monthly_consumption=100),
            make_row(batch_number="B", average_monthly_consumption=120),
        ]
    )
    audit, _ = audit_inventory(data, AS_OF)

    assert audit["review_flags"].str.contains("Inconsistent monthly consumption across batches").all()
