from stocksignal_workflows import parse_inventory_note


def test_example_voice_note_is_parsed_as_a_draft():
    parsed = parse_inventory_note(
        "I just found 3 boxes of Amoxicillin expiring next month on shelf B3"
    )
    assert parsed["quantity"] == 3.0
    assert parsed["unit"] == "boxes"
    assert parsed["product_name"] == "Amoxicillin"
    assert parsed["expiry_statement"] == "expiring next month"
    assert parsed["shelf_code"] == "B3"


def test_iso_expiry_date_is_kept_as_text_for_human_confirmation():
    parsed = parse_inventory_note(
        "Adding 50 vials of Oxytocin expiring on 2027-01-15 at shelf A2"
    )
    assert parsed["quantity"] == 50.0
    assert parsed["product_name"] == "Oxytocin"
    assert parsed["expiry_statement"] == "expiring on 2027-01-15"
    assert parsed["shelf_code"] == "A2"


def test_empty_or_unrecognised_note_does_not_guess_values():
    assert parse_inventory_note("")["quantity"] is None
    parsed = parse_inventory_note("Some medicine was seen in the room")
    assert parsed["quantity"] is None
    assert parsed["product_name"] == ""
    assert parsed["shelf_code"] == ""
