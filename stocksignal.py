"""Core rule-based checks for the STOCKSIGNAL demonstration prototype.

This module intentionally provides transparent screening rules rather than a
predictive model or an ordering recommendation. Every result needs human review.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "facility_code",
    "product_code",
    "product_name",
    "batch_number",
    "quantity_on_hand",
    "average_monthly_consumption",
    "lead_time_days",
    "expiry_date",
    "last_stock_update",
]

TEXT_COLUMNS = ["facility_code", "product_code", "product_name", "batch_number"]
NUMERIC_COLUMNS = ["quantity_on_hand", "average_monthly_consumption", "lead_time_days"]
DATE_COLUMNS = ["expiry_date", "last_stock_update"]
BATCH_KEY_COLUMNS = ["facility_code", "product_code", "batch_number"]
PRODUCT_KEY_COLUMNS = ["facility_code", "product_code"]


def _is_blank(value: Any) -> bool:
    """Return whether a scalar input is missing or a blank string."""
    if pd.isna(value):
        return True
    return isinstance(value, str) and not value.strip()


def _finite_numeric_series(series: pd.Series) -> pd.Series:
    """Parse numeric values, treating positive/negative infinity as invalid."""
    parsed = pd.to_numeric(series, errors="coerce")
    finite = pd.Series(np.isfinite(parsed.fillna(0)), index=series.index)
    return parsed.where(parsed.isna() | finite)


def audit_inventory(
    data: pd.DataFrame,
    as_of_date: date,
    stale_days: int = 30,
    expiry_warning_days: int = 90,
    lead_buffer_days: int = 7,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return ``(row_audit, product_review)`` for a stock CSV/DataFrame.

    Estimated cover is calculated as:

        eligible stock quantity / (average monthly consumption / 30.4375)

    Only non-negative quantities belonging to identifiable, unique batch rows
    with a known expiry date on or after ``as_of_date`` are counted. Expired,
    duplicate-key, missing-expiry, missing-key, invalid, and negative-quantity
    rows are excluded from the cover quantity and remain visible for review.

    This is a simple screening estimate. It does not model pending orders,
    seasonality, allocation, demand uncertainty, or clinical criticality.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("Input data must be a pandas DataFrame.")

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing_columns:
        raise ValueError("Missing required columns: " + ", ".join(missing_columns))

    if any(value < 0 for value in (stale_days, expiry_warning_days, lead_buffer_days)):
        raise ValueError("Day thresholds cannot be negative.")
    if not isinstance(as_of_date, date):
        raise TypeError("as_of_date must be a datetime.date value.")

    original = data[REQUIRED_COLUMNS].copy().reset_index(drop=True)
    df = original.copy()

    for column in TEXT_COLUMNS:
        df[column] = df[column].astype("string").str.strip()
        df[column] = df[column].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})

    for column in NUMERIC_COLUMNS:
        df[column] = _finite_numeric_series(df[column])

    for column in DATE_COLUMNS:
        df[column] = pd.to_datetime(df[column], errors="coerce").dt.date

    expiry_cutoff = as_of_date + timedelta(days=int(expiry_warning_days))
    flags: list[list[str]] = [[] for _ in range(len(df))]

    # Required values and type/number/date parsing checks.
    for position, (_, row) in enumerate(df.iterrows()):
        for column in TEXT_COLUMNS:
            if pd.isna(row[column]):
                flags[position].append(f"Missing {column}")

        for column in NUMERIC_COLUMNS:
            raw = original.iloc[position][column]
            if _is_blank(raw):
                flags[position].append(f"Missing {column}")
            elif pd.isna(row[column]):
                flags[position].append(f"Invalid number in {column}")

        for column in DATE_COLUMNS:
            raw = original.iloc[position][column]
            if _is_blank(raw):
                flags[position].append(f"Missing {column}")
            elif pd.isna(row[column]):
                flags[position].append(f"Invalid date in {column}")

        quantity = row["quantity_on_hand"]
        consumption = row["average_monthly_consumption"]
        lead_time = row["lead_time_days"]
        if pd.notna(quantity) and quantity < 0:
            flags[position].append("Negative quantity on hand")
        if pd.notna(consumption) and consumption < 0:
            flags[position].append("Negative average monthly consumption")
        if pd.notna(lead_time) and lead_time < 0:
            flags[position].append("Negative lead time")

        updated = row["last_stock_update"]
        if updated is not None and not pd.isna(updated):
            if updated > as_of_date:
                flags[position].append("Stock update date is in the future")
            elif (as_of_date - updated).days > stale_days:
                flags[position].append(f"Stock record is stale (> {stale_days} days)")

        expiry = row["expiry_date"]
        if expiry is not None and not pd.isna(expiry):
            if expiry < as_of_date:
                flags[position].append("Batch is expired - verify and follow authorised procedure")
            elif expiry <= expiry_cutoff:
                flags[position].append(f"Batch expires within {expiry_warning_days} days")

    # Only assess duplicates when all parts of the batch key are present.
    duplicate_mask = pd.Series(False, index=df.index, dtype=bool)
    complete_batch_key = df[BATCH_KEY_COLUMNS].notna().all(axis=1)
    complete_indexes = df.index[complete_batch_key]
    if len(complete_indexes):
        duplicate_mask.loc[complete_indexes] = df.loc[complete_indexes].duplicated(
            subset=BATCH_KEY_COLUMNS, keep=False
        )
    for position, is_duplicate in enumerate(duplicate_mask.tolist()):
        if is_duplicate:
            flags[position].append("Duplicate facility/product/batch key")

    # Conflicting monthly-consumption values make the estimate less reliable.
    complete_product_key = df[PRODUCT_KEY_COLUMNS].notna().all(axis=1)
    valid_amc = df["average_monthly_consumption"].notna() & df["average_monthly_consumption"].ge(0)
    consistency_rows = df.loc[complete_product_key & valid_amc]
    for _, group in consistency_rows.groupby(PRODUCT_KEY_COLUMNS, sort=False):
        if group["average_monthly_consumption"].nunique() > 1:
            for position in group.index:
                flags[position].append("Inconsistent monthly consumption across batches")

    audit = df.copy()
    audit["review_flags"] = ["; ".join(row_flags) if row_flags else "No rule triggered" for row_flags in flags]
    audit["flag_count"] = [len(row_flags) for row_flags in flags]
    audit["data_quality_issue"] = [
        any(
            not (flag.startswith("Batch expires") or flag.startswith("Batch is expired"))
            for flag in row_flags
        )
        for row_flags in flags
    ]

    # A row is eligible to contribute to estimated cover only when its stock
    # quantity and identity are usable and its expiry status can be verified.
    eligible_for_cover = (
        complete_product_key
        & complete_batch_key
        & ~duplicate_mask
        & df["quantity_on_hand"].notna()
        & df["quantity_on_hand"].ge(0)
        & df["expiry_date"].notna()
        & df["expiry_date"].ge(as_of_date)
    )

    product_rows: list[dict[str, Any]] = []
    for (facility, product), group in df.groupby(PRODUCT_KEY_COLUMNS, dropna=False, sort=True):
        eligible_group = group.loc[eligible_for_cover.loc[group.index]]
        eligible_count = len(eligible_group)
        source_count = len(group)
        stock = (
            float(eligible_group["quantity_on_hand"].sum())
            if eligible_count
            else None
        )

        amc_values = group["average_monthly_consumption"].dropna()
        amc_values = amc_values[amc_values >= 0]
        amc = float(amc_values.median()) if len(amc_values) else None

        lead_values = group["lead_time_days"].dropna()
        lead_values = lead_values[lead_values >= 0]
        lead_time = float(lead_values.max()) if len(lead_values) else None

        name = next((value for value in group["product_name"].tolist() if pd.notna(value)), "Unknown")
        threshold = lead_time + int(lead_buffer_days) if lead_time is not None else None
        days_cover = None

        if eligible_count == 0:
            review = "Not calculable - no eligible unique, non-expired batch rows"
        elif amc is None:
            review = "Not calculable - check stock/consumption data"
        elif amc <= 0:
            review = "Not calculable - average monthly consumption is zero"
        elif threshold is None:
            review = "Not calculable - lead time is missing or invalid"
        else:
            days_cover = round(stock / (amc / 30.4375), 1)
            if days_cover <= threshold:
                review = "Review: estimated cover is at/below lead time + buffer"
            else:
                review = "No low-cover flag from this simple rule"

        product_rows.append(
            {
                "facility_code": facility,
                "product_code": product,
                "product_name": name,
                "eligible_quantity_on_hand": round(stock, 2) if stock is not None else None,
                "average_monthly_consumption_used": round(amc, 2) if amc is not None else None,
                "lead_time_days_used": lead_time,
                "estimated_days_of_stock": days_cover,
                "review_threshold_days": threshold,
                "stock_review_status": review,
                "source_rows": source_count,
                "eligible_batch_rows": eligible_count,
                "excluded_batch_rows": source_count - eligible_count,
            }
        )

    product_review = pd.DataFrame(product_rows)
    if not product_review.empty:
        product_review = product_review.sort_values(
            by="estimated_days_of_stock", na_position="last", kind="stable"
        ).reset_index(drop=True)

    return audit, product_review
