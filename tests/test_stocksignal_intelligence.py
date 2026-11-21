import pandas as pd
import pytest

from stocksignal import REQUIRED_COLUMNS
from stocksignal_intelligence import (
    build_data_completeness_profile,
    parse_gs1_scan,
    simulate_stock_cover,
)


def make_row(**overrides):
    row = {
        "facility_code": "F1",
        "product_code": "P1",
        "product_name": "Demo product",
        "batch_number": "LOT-1",
        "quantity_on_hand": 100,
        "average_monthly_consumption": 100,
        "lead_time_days": 10,
        "expiry_date": "2027-06-30",
        "last_stock_update": "2026-11-01",
    }
    row.update(overrides)
    return row


def test_completeness_profile_counts_null_and_whitespace_values():
    data = pd.DataFrame(
        [make_row(), make_row(product_name=" "), make_row(expiry_date=None)],
        columns=REQUIRED_COLUMNS,
    )
    profile = build_data_completeness_profile(data).set_index("field")
    assert profile.loc["product_name", "missing_or_blank_values"] == 1
    assert profile.loc["expiry_date", "missing_or_blank_values"] == 1
    assert profile.loc["facility_code", "completeness_percent"] == 100.0


def test_completeness_profile_rejects_missing_required_columns():
    with pytest.raises(ValueError, match="Missing required columns"):
        build_data_completeness_profile(pd.DataFrame({"facility_code": ["F1"]}))


def test_scenario_simulator_compares_baseline_and_scenario_arithmetic():
    result = simulate_stock_cover(
        100, 100, 10,
        consumption_increase_percent=20,
        extra_lead_time_days=5,
        review_buffer_days=7,
    )
    assert result["baseline_days_of_stock"] == 30.4
    assert result["scenario_days_of_stock"] == 25.4
    assert result["baseline_threshold_days"] == 17.0
    assert result["scenario_threshold_days"] == 22.0
    assert result["scenario_status"] == "Above the user-defined scenario threshold"


def test_scenario_simulator_marks_result_at_or_below_user_threshold():
    result = simulate_stock_cover(
        50, 100, 10,
        consumption_increase_percent=20,
        extra_lead_time_days=5,
        review_buffer_days=7,
    )
    assert result["scenario_status"] == "At or below the user-defined scenario threshold"


def test_scenario_simulator_does_not_calculate_zero_consumption():
    result = simulate_stock_cover(100, 0, 10)
    assert result["scenario_days_of_stock"] is None
    assert result["scenario_status"].startswith("Not calculable")


@pytest.mark.parametrize("bad_value", [-1, float("inf"), float("nan"), "not-a-number"])
def test_scenario_simulator_rejects_invalid_or_negative_inputs(bad_value):
    with pytest.raises(ValueError):
        simulate_stock_cover(bad_value, 100, 10)


def test_gs1_hri_string_parses_supported_healthcare_fields():
    result = parse_gs1_scan("]d2(01)09506000134352(17)270630(10)LOT-A123(21)SER-09")
    assert result["valid"] is True
    assert result["fields"] == {
        "gtin": "09506000134352",
        "batch_number": "LOT-A123",
        "expiry_date": "2027-06-30",
        "serial_number": "SER-09",
    }


def test_gs1_element_string_uses_group_separator_after_variable_length_lot():
    scan = "01095060001343521727063010LOT-A123\x1d21SER-09"
    result = parse_gs1_scan(scan)
    assert result["valid"] is True
    assert result["fields"]["batch_number"] == "LOT-A123"
    assert result["fields"]["serial_number"] == "SER-09"


def test_gs1_parser_rejects_invalid_gtin_check_digit():
    result = parse_gs1_scan("(01)09506000134353(17)270630")
    assert result["valid"] is False
    assert any("check digit" in error for error in result["errors"])


def test_gs1_parser_requires_gtin_and_never_guesses_unknown_fields():
    result = parse_gs1_scan("(10)LOT-A123(17)270630")
    assert result["valid"] is False
    assert any("GTIN-14" in error for error in result["errors"])


def test_gs1_day_zero_is_interpreted_as_month_end_with_warning():
    result = parse_gs1_scan("(01)09506000134352(17)270200")
    assert result["valid"] is True
    assert result["fields"]["expiry_date"] == "2027-02-28"
    assert any("day 00" in warning for warning in result["warnings"])


def test_gs1_two_digit_year_uses_rolling_century_window():
    from datetime import date

    current_year = date.today().year
    future_year = current_year + 50
    past_year = current_year - 49
    future_yy = f"{future_year % 100:02d}"
    past_yy = f"{past_year % 100:02d}"

    future_result = parse_gs1_scan(f"(01)09506000134352(17){future_yy}0200")
    past_result = parse_gs1_scan(f"(01)09506000134352(17){past_yy}0200")

    assert future_result["valid"] is True
    assert past_result["valid"] is True
    assert future_result["fields"]["expiry_date"].startswith(str(future_year))
    assert past_result["fields"]["expiry_date"].startswith(str(past_year))
