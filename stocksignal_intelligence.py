"""Explainable, human-reviewed intelligence helpers for StockSignal.

These functions are deterministic utilities for a demonstration prototype.
They do not predict demand, recommend procurement, or make clinical decisions.
"""
from __future__ import annotations

import calendar
from datetime import date
import math
import re
from typing import Any

import pandas as pd

from stocksignal import REQUIRED_COLUMNS

DAYS_PER_MONTH = 30.4375
GS1_SUPPORTED_AIS = {"01", "10", "17", "21"}
_GROUP_SEPARATOR = "\x1d"
_HRI_MARKER = re.compile(r"\((\d{2,4})\)")


def build_data_completeness_profile(data: pd.DataFrame) -> pd.DataFrame:
    """Return per-required-field completeness counts and percentages.

    Blank strings and whitespace-only strings count as missing. This is a
    descriptive profile, not a single quality score or validation decision.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("Inventory data must be a pandas DataFrame.")
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing_columns:
        raise ValueError("Missing required columns: " + ", ".join(missing_columns))

    total_rows = len(data)
    rows: list[dict[str, Any]] = []
    for column in REQUIRED_COLUMNS:
        series = data[column]
        missing = series.isna()
        if pd.api.types.is_object_dtype(series.dtype) or pd.api.types.is_string_dtype(series.dtype):
            blank = series.astype("string").str.strip().eq("").fillna(False)
            missing = missing | blank
        missing_count = int(missing.sum())
        present_count = total_rows - missing_count
        completeness = round((present_count / total_rows) * 100, 1) if total_rows else 0.0
        rows.append(
            {
                "field": column,
                "present_values": present_count,
                "missing_or_blank_values": missing_count,
                "completeness_percent": completeness,
            }
        )
    return pd.DataFrame(rows)


def _nonnegative_number(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite number.") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{label} must be a finite, non-negative number.")
    return number


def simulate_stock_cover(
    eligible_quantity: Any,
    average_monthly_consumption: Any,
    lead_time_days: Any,
    *,
    consumption_increase_percent: Any = 0,
    extra_lead_time_days: Any = 0,
    review_buffer_days: Any = 7,
) -> dict[str, float | str | None]:
    """Compare baseline arithmetic with a user-defined what-if scenario.

    A scenario changes only the assumed consumption rate and lead-time delay.
    It is a sensitivity calculation, not a forecast or procurement instruction.
    """
    quantity = _nonnegative_number(eligible_quantity, "Eligible quantity")
    consumption = _nonnegative_number(average_monthly_consumption, "Monthly consumption")
    lead = _nonnegative_number(lead_time_days, "Lead time")
    increase = _nonnegative_number(consumption_increase_percent, "Consumption increase")
    delay = _nonnegative_number(extra_lead_time_days, "Extra lead time")
    buffer_days = _nonnegative_number(review_buffer_days, "Review buffer")

    if consumption == 0:
        return {
            "baseline_days_of_stock": None,
            "scenario_days_of_stock": None,
            "baseline_threshold_days": lead + buffer_days,
            "scenario_threshold_days": lead + delay + buffer_days,
            "scenario_margin_days": None,
            "scenario_status": "Not calculable — monthly consumption is zero",
        }

    baseline_daily = consumption / DAYS_PER_MONTH
    scenario_daily = baseline_daily * (1 + increase / 100)
    baseline_cover = quantity / baseline_daily
    scenario_cover = quantity / scenario_daily
    baseline_threshold = lead + buffer_days
    scenario_threshold = lead + delay + buffer_days
    margin = scenario_cover - scenario_threshold
    status = (
        "At or below the user-defined scenario threshold"
        if margin <= 0
        else "Above the user-defined scenario threshold"
    )
    return {
        "baseline_days_of_stock": round(baseline_cover, 1),
        "scenario_days_of_stock": round(scenario_cover, 1),
        "baseline_threshold_days": round(baseline_threshold, 1),
        "scenario_threshold_days": round(scenario_threshold, 1),
        "scenario_margin_days": round(margin, 1),
        "scenario_status": status,
    }


def _valid_gtin14(value: str) -> bool:
    if len(value) != 14 or not value.isdigit():
        return False
    weighted_sum = sum(
        int(digit) * (3 if index % 2 == 0 else 1)
        for index, digit in enumerate(reversed(value[:-1]))
    )
    expected_check_digit = (10 - weighted_sum % 10) % 10
    return int(value[-1]) == expected_check_digit


def _parse_gs1_date(value: str) -> tuple[str | None, str | None]:
    if len(value) != 6 or not value.isdigit():
        return None, "AI (17) expiry date must contain six digits in YYMMDD format."
    year_short, month, day = int(value[:2]), int(value[2:4]), int(value[4:6])
    # GS1 uses a rolling century window: 49 years in the past and 50 in the future.
    current_year = date.today().year
    window_start = current_year - 49
    window_end = current_year + 50
    year_candidates = [
        candidate for candidate in range(window_start, window_end + 1)
        if candidate % 100 == year_short
    ]
    if not year_candidates:
        return None, "AI (17) year cannot be resolved inside the GS1 century window."
    year = year_candidates[0]
    if not 1 <= month <= 12:
        return None, "AI (17) contains an invalid month."
    last_day = calendar.monthrange(year, month)[1]
    if day == 0:
        # GS1 permits DD=00 to mean the final calendar day of the month.
        day = last_day
    if not 1 <= day <= last_day:
        return None, "AI (17) contains an invalid calendar day."
    return f"{year:04d}-{month:02d}-{day:02d}", None


def _extract_hri_elements(scan: str) -> tuple[dict[str, str], list[str], list[str]] | None:
    markers = list(_HRI_MARKER.finditer(scan))
    if not markers:
        return None
    if scan[: markers[0].start()].strip():
        return {}, ["Unexpected text before the first GS1 Application Identifier."], []

    elements: dict[str, str] = {}
    warnings: list[str] = []
    errors: list[str] = []
    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(scan)
        value = scan[marker.end() : end].strip().strip(_GROUP_SEPARATOR)
        ai = marker.group(1)
        if ai not in GS1_SUPPORTED_AIS:
            warnings.append(f"AI ({ai}) is not interpreted by this prototype.")
            continue
        if ai in elements:
            errors.append(f"AI ({ai}) appears more than once; verify the scan.")
            continue
        elements[ai] = value
    return elements, warnings, errors


def _extract_element_string(scan: str) -> tuple[dict[str, str], list[str], list[str]]:
    elements: dict[str, str] = {}
    warnings: list[str] = []
    errors: list[str] = []
    position = 0
    while position < len(scan):
        if scan[position] == _GROUP_SEPARATOR:
            position += 1
            continue
        ai = scan[position : position + 2]
        if ai == "01":
            value_start, value_end = position + 2, position + 16
            if value_end > len(scan):
                errors.append("AI (01) is incomplete; GTIN-14 requires 14 digits.")
                break
            value = scan[value_start:value_end]
            position = value_end
        elif ai == "17":
            value_start, value_end = position + 2, position + 8
            if value_end > len(scan):
                errors.append("AI (17) is incomplete; expiry date requires six digits.")
                break
            value = scan[value_start:value_end]
            position = value_end
        elif ai in {"10", "21"}:
            separator = scan.find(_GROUP_SEPARATOR, position + 2)
            if separator == -1:
                value = scan[position + 2 :]
                position = len(scan)
                warnings.append(
                    f"AI ({ai}) is variable-length and was treated as the final field. "
                    "A GS1 group separator is required before any following element."
                )
            else:
                value = scan[position + 2 : separator]
                position = separator + 1
        else:
            errors.append(
                f"Unsupported or unrecognised element at character {position + 1}; "
                "this prototype supports AIs 01, 10, 17 and 21 only."
            )
            break
        if ai in elements:
            errors.append(f"AI ({ai}) appears more than once; verify the scan.")
        else:
            elements[ai] = value
    return elements, warnings, errors


def parse_gs1_scan(raw_scan: str) -> dict[str, Any]:
    """Parse a limited GS1 scan/HRI string into a human-verification draft.

    Supported AIs: 01 (GTIN-14), 10 (batch/lot), 17 (expiry YYMMDD), and
    21 (serial). This does not decode barcode images or replace GS1 validation.
    """
    scan = str(raw_scan or "").strip()
    for prefix in ("]d2", "]C1", "]Q3", "]e0"):
        if scan.startswith(prefix):
            scan = scan[len(prefix) :]
            break

    fields = {"gtin": "", "batch_number": "", "expiry_date": "", "serial_number": ""}
    if not scan:
        return {"valid": False, "fields": fields, "errors": ["Enter or scan GS1 data first."], "warnings": []}

    extracted = _extract_hri_elements(scan)
    if extracted is None:
        elements, warnings, errors = _extract_element_string(scan)
    else:
        elements, warnings, errors = extracted

    gtin = elements.get("01", "").strip()
    batch = elements.get("10", "").strip()
    expiry_raw = elements.get("17", "").strip()
    serial = elements.get("21", "").strip()

    if not gtin:
        errors.append("A valid trade-item identifier (AI 01 / GTIN-14) is required for this draft.")
    elif not _valid_gtin14(gtin):
        errors.append("AI (01) must be a valid 14-digit GTIN with a correct check digit.")
    if batch and len(batch) > 20:
        errors.append("AI (10) batch/lot value exceeds the 20-character GS1 limit.")
    if serial and len(serial) > 20:
        errors.append("AI (21) serial value exceeds the 20-character GS1 limit.")

    expiry = ""
    if expiry_raw:
        expiry, expiry_error = _parse_gs1_date(expiry_raw)
        if expiry_error:
            errors.append(expiry_error)
        elif expiry_raw.endswith("00"):
            warnings.append("AI (17) day 00 was interpreted as the final day of its stated month; verify the source label.")
    else:
        warnings.append("No AI (17) expiry date was present in the scanned data.")
    if not batch:
        warnings.append("No AI (10) batch/lot value was present in the scanned data.")

    fields.update(
        {
            "gtin": gtin,
            "batch_number": batch,
            "expiry_date": expiry or "",
            "serial_number": serial,
        }
    )
    return {"valid": bool(gtin) and not errors, "fields": fields, "errors": errors, "warnings": warnings}
