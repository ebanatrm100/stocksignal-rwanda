from datetime import date
from pathlib import Path

import pandas as pd

from stocksignal import REQUIRED_COLUMNS, audit_inventory

AS_OF = date(2026, 11, 6)


def row(facility="F1", product="P1", name="Product", batch="B1", qty=100, amc=100,
        lead=10, expiry="2027-06-30", updated="2026-11-01"):
    return {
        "facility_code": facility,
        "product_code": product,
        "product_name": name,
        "batch_number": batch,
        "quantity_on_hand": qty,
        "average_monthly_consumption": amc,
        "lead_time_days": lead,
        "expiry_date": expiry,
        "last_stock_update": updated,
    }


def review_for(df):
    _, products = audit_inventory(pd.DataFrame(df, columns=REQUIRED_COLUMNS), AS_OF)
    return products.iloc[0]


def test_stale_row_blocks_product_cover():
    result = review_for([row(updated="2026-09-10")])
    assert pd.isna(result["estimated_days_of_stock"])
    assert result["eligible_batch_rows"] == 0
    assert result["stock_review_status"].startswith("Review: data conflict")


def test_future_update_blocks_product_cover():
    result = review_for([row(updated="2026-11-08")])
    assert pd.isna(result["estimated_days_of_stock"])
    assert "future" in result["calculation_blockers"]


def test_duplicate_batch_blocks_whole_product_group():
    result = review_for([row(), row()])
    assert pd.isna(result["estimated_days_of_stock"])
    assert result["eligible_batch_rows"] == 0
    assert "Duplicate" in result["calculation_blockers"]


def test_expired_quantity_is_excluded_but_valid_batch_can_be_calculated():
    result = review_for([
        row(batch="EXPIRED", qty=900, expiry="2026-10-31"),
        row(batch="CURRENT", qty=100, expiry="2027-06-30"),
    ])
    assert result["eligible_quantity_on_hand"] == 100
    assert result["eligible_batch_rows"] == 1
    assert result["expired_batch_rows_excluded"] == 1
    assert "expired batch excluded" in result["stock_review_status"]


def test_missing_quantity_blocks_product_cover_even_if_other_rows_are_valid():
    result = review_for([row(batch="B1"), row(batch="B2", qty=None)])
    assert pd.isna(result["estimated_days_of_stock"])
    assert "Missing quantity_on_hand" in result["calculation_blockers"]


def test_infinite_quantity_is_invalid_and_blocks_cover():
    result = review_for([row(qty=float("inf"))])
    assert pd.isna(result["estimated_days_of_stock"])
    assert "Invalid number in quantity_on_hand" in result["calculation_blockers"]


def test_zero_consumption_is_not_calculable():
    result = review_for([row(amc=0)])
    assert pd.isna(result["estimated_days_of_stock"])
    assert result["stock_review_status"].startswith("Not calculable")


def test_inconsistent_consumption_blocks_cover():
    result = review_for([row(batch="B1", amc=100), row(batch="B2", amc=120)])
    assert pd.isna(result["estimated_days_of_stock"])
    assert "Inconsistent monthly consumption" in result["calculation_blockers"]


def test_negative_lead_time_blocks_cover():
    result = review_for([row(lead=-1)])
    assert pd.isna(result["estimated_days_of_stock"])
    assert "Negative lead time" in result["calculation_blockers"]


def test_missing_expiry_blocks_cover():
    result = review_for([row(expiry=None)])
    assert pd.isna(result["estimated_days_of_stock"])
    assert "Missing expiry_date" in result["calculation_blockers"]


def test_stale_and_future_rows_are_flagged_in_row_audit():
    audit, _ = audit_inventory(pd.DataFrame([
        row(batch="STALE", updated="2026-09-10"),
        row(batch="FUTURE", updated="2026-11-08"),
    ], columns=REQUIRED_COLUMNS), AS_OF)
    assert audit.loc[0, "data_quality_issue"]
    assert "stale" in audit.loc[0, "review_flags"]
    assert audit.loc[1, "data_quality_issue"]
    assert "future" in audit.loc[1, "review_flags"]


def test_clean_product_still_calculates_cover():
    result = review_for([row(qty=100, amc=100, lead=10)])
    assert result["estimated_days_of_stock"] == 30.4
    assert result["eligible_quantity_on_hand"] == 100
    assert result["eligible_batch_rows"] == 1


def test_all_expired_batches_are_not_calculable():
    result = review_for([row(expiry="2026-10-31")])
    assert pd.isna(result["estimated_days_of_stock"])
    assert result["eligible_batch_rows"] == 0
    assert result["stock_review_status"].startswith("Not calculable")


def test_competition_verification_sample_blocks_stale_future_duplicate_and_invalid_groups():
    sample_path = Path(__file__).resolve().parents[1] / "sample_verification_inventory.csv"
    data = pd.read_csv(sample_path)
    audit, products = audit_inventory(data, AS_OF)

    assert len(audit) == 12
    assert int(audit["data_quality_issue"].sum()) == 6
    assert int(audit["review_flags"].str.contains("Batch expires|Batch is expired", regex=True).sum()) == 3

    by_key = products.set_index(["facility_code", "product_code"])
    assert pd.isna(by_key.loc[("DEMO-HC-A", "AMX-250"), "estimated_days_of_stock"])
    assert pd.isna(by_key.loc[("DEMO-HC-A", "ORS-001"), "estimated_days_of_stock"])
    assert pd.isna(by_key.loc[("DEMO-HC-B", "PAR-500"), "estimated_days_of_stock"])
    assert pd.isna(by_key.loc[("DEMO-HC-B", "CEF-1G"), "estimated_days_of_stock"])

    # Clean Oxytocin and Paracetamol rows remain calculable and are correctly
    # flagged by the low-cover rule rather than being blocked as data conflicts.
    assert by_key.loc[("DEMO-HC-C", "OXY-10"), "estimated_days_of_stock"] == 5.1
    assert by_key.loc[("DEMO-HC-C", "PAR-500"), "estimated_days_of_stock"] == 33.8


def test_missing_or_invalid_last_update_blocks_product_cover():
    for update in (None, "not-a-date"):
        result = review_for([row(updated=update)])
        assert pd.isna(result["estimated_days_of_stock"])
        assert result["stock_review_status"].startswith("Review: data conflict")
