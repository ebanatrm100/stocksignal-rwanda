"""Frontline workflow screens for the StockSignal demonstration prototype.

The workflows create review records; they do not autonomously change stock or
approve transfers. Streamlit session state is temporary. Production persistence,
identity controls, speech recognition and full offline PWA behaviour require
additional infrastructure.
"""
from __future__ import annotations

import html
import io
import re
import uuid
import zipfile
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pandas as pd
import streamlit as st

SHELVES = [f"{row}{col}" for row in "ABCD" for col in range(1, 5)]


def parse_inventory_note(note: str) -> dict[str, Any]:
    """Extract a cautious draft from supplied text; this is not speech-to-text."""
    text = " ".join(str(note or "").strip().split())
    result: dict[str, Any] = {
        "quantity": None,
        "unit": "",
        "product_name": "",
        "expiry_statement": "",
        "shelf_code": "",
    }
    if not text:
        return result

    quantity = re.search(
        r"\b(\d+(?:[.,]\d+)?)\s+(boxes?|packs?|bottles?|vials?|units?|"
        r"tablets?|capsules?|cartons?|strips?|sachets?)\s+of\s+(.+?)"
        r"(?=\s+(?:expir(?:ing|es|y)|on\s+shelf|at\s+shelf|from\s+facility)\b|$)",
        text,
        flags=re.IGNORECASE,
    )
    if quantity:
        try:
            result["quantity"] = float(quantity.group(1).replace(",", "."))
        except ValueError:
            pass
        result["unit"] = quantity.group(2).lower()
        result["product_name"] = quantity.group(3).strip(" .,:;")

    expiry = re.search(
        r"\b(expir(?:ing|es|y)\s+(?:on\s+)?(?:next\s+month|this\s+month|"
        r"in\s+\d+\s+days?|\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}))",
        text,
        flags=re.IGNORECASE,
    )
    if expiry:
        result["expiry_statement"] = expiry.group(1).strip()

    shelf = re.search(
        r"\b(?:on\s+shelf|at\s+shelf)\s+([A-D]\s?\d{1,2})\b",
        text,
        flags=re.IGNORECASE,
    )
    if shelf:
        result["shelf_code"] = shelf.group(1).replace(" ", "").upper()
    return result


def _batch_key(row: pd.Series, row_number: int | None = None) -> str:
    base = "|".join(str(row.get(column, "")).strip() for column in (
        "facility_code", "product_code", "batch_number"
    ))
    # Add the row number so duplicate rows remain separately visible in this map.
    return f"{base}|row-{row_number}" if row_number is not None else base


def _csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8")


def render_workflows(
    source_df: pd.DataFrame,
    audited: pd.DataFrame,
    product_risk: pd.DataFrame,
    analysis_date: date,
    expiry_days: int,
) -> None:
    """Render voice-review, shelf-map, swap-board and offline-kit workflows."""
    st.markdown("---")
    st.markdown(
        '<div class="section-kicker">05 / Frontline workflows</div>'
        '<div class="section-title">StockSignal Supply Companion</div>'
        '<div class="section-help">Frontline observations, physical shelf locations and proposed inter-facility coordination.</div>',
        unsafe_allow_html=True,
    )
    voice_tab, shelf_tab, swap_tab, offline_tab = st.tabs([
        "🎙️ Voice inventory auditor",
        "🗂️ Smart-shelf map",
        "⇄ District swap board",
        "↧ Offline work kit",
    ])

    # Voice: microphone recording plus a verified transcript and a review queue.
    with voice_tab:
        st.markdown("#### Capture an inventory observation")
        st.caption(
            "Record a short memo, enter or correct its transcript, then queue a structured draft for verification."
        )
        st.info(
            "Microphone recording is available in supported browsers with permission. "
            "This version does not automatically transcribe audio. The text parser is "
            "rule-based, and no inventory quantity changes until an authorised person "
            "checks the observation against the source records."
        )
        audio = st.audio_input("Record a stock observation", key="ss_audio_memo")
        if audio is not None:
            audio_bytes = audio.getvalue()
            st.audio(audio_bytes)
            st.download_button(
                "Download recorded memo",
                audio_bytes,
                file_name="stocksignal_voice_observation.wav",
                mime="audio/wav",
                key="ss_download_voice_memo",
            )

        transcript = st.text_area(
            "Verified transcript / observation text",
            placeholder='Example: "I found 3 boxes of Amoxicillin expiring next month on shelf B3."',
            height=90,
            key="ss_voice_transcript",
        )
        parsed = parse_inventory_note(transcript)
        if transcript.strip():
            st.markdown("**Draft extraction — verify each field**")
            st.dataframe(
                pd.DataFrame([{
                    "Quantity": parsed["quantity"] if parsed["quantity"] is not None else "Not detected",
                    "Unit": parsed["unit"] or "Not detected",
                    "Product": parsed["product_name"] or "Not detected",
                    "Expiry wording": parsed["expiry_statement"] or "Not detected",
                    "Shelf": parsed["shelf_code"] or "Not detected",
                }]),
                hide_index=True,
                use_container_width=True,
            )

        facilities = sorted(
            str(value)
            for value in audited.get("facility_code", pd.Series(dtype=str)).dropna().unique()
        ) or ["DEMO-FACILITY"]
        with st.form("ss_voice_review_form"):
            left, right = st.columns(2)
            with left:
                facility = st.selectbox("Facility", facilities, key="ss_voice_facility")
                product = st.text_input("Product name", value=parsed["product_name"], key="ss_voice_product")
                quantity = st.number_input(
                    "Observed quantity",
                    min_value=0.0,
                    value=float(parsed["quantity"] or 0.0),
                    step=1.0,
                    key="ss_voice_quantity",
                )
            with right:
                unit = st.text_input("Unit", value=parsed["unit"], key="ss_voice_unit")
                expiry_text = st.text_input(
                    "Expiry wording (not a confirmed date)",
                    value=parsed["expiry_statement"],
                    key="ss_voice_expiry",
                )
                shelf_options = ["Not recorded"] + SHELVES
                shelf_default = (
                    SHELVES.index(parsed["shelf_code"]) + 1
                    if parsed["shelf_code"] in SHELVES
                    else 0
                )
                shelf = st.selectbox(
                    "Shelf location", shelf_options, index=shelf_default, key="ss_voice_shelf"
                )
            batch = st.text_input("Batch number (verify from the pack)", key="ss_voice_batch")
            submit_note = st.form_submit_button("Add to human verification queue", type="primary")

        if submit_note:
            if not product.strip() or quantity <= 0 or not unit.strip():
                st.error("Enter a product name, positive quantity and unit.")
            else:
                st.session_state.setdefault("ss_voice_notes", []).append({
                    "observation_id": uuid.uuid4().hex[:10],
                    "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "facility_code": facility,
                    "product_name": product.strip(),
                    "observed_quantity": float(quantity),
                    "unit": unit.strip(),
                    "batch_number": batch.strip(),
                    "expiry_statement": expiry_text.strip(),
                    "shelf_code": "" if shelf == "Not recorded" else shelf,
                    "transcript": transcript.strip(),
                    "status": "Pending human verification",
                })
                st.success("Observation queued. The inventory source has not been changed.")

        observations = st.session_state.get("ss_voice_notes", [])
        if observations:
            st.markdown("#### Pending observations")
            observation_frame = pd.DataFrame(observations)
            st.dataframe(observation_frame, hide_index=True, use_container_width=True)
            st.download_button(
                "Export observation queue",
                _csv_bytes(observation_frame),
                file_name="stocksignal_observation_queue.csv",
                mime="text/csv",
                key="ss_export_voice_queue",
            )
        else:
            st.caption("No observations are queued in this browser session.")

    # Shelf map: manual batch-to-cell assignment on a 4x4 grid.
    with shelf_tab:
        st.markdown("#### Physical shelf locator")
        st.caption(
            "Assign each batch to a shelf cell. Colours are review signals, not handling or dispensing instructions."
        )
        if audited.empty:
            st.info("Load inventory records to use the shelf map.")
        else:
            facilities = sorted(str(value) for value in audited["facility_code"].dropna().unique())
            if facilities:
                selected_facility = st.selectbox("Choose facility", facilities, key="ss_shelf_facility")
                facility_rows = audited[
                    audited["facility_code"].astype(str) == selected_facility
                ].reset_index(drop=True)
                choices: dict[str, str] = {}
                rows_by_key: dict[str, pd.Series] = {}
                for row_number, row in facility_rows.iterrows():
                    item_key = _batch_key(row, row_number)
                    choices[item_key] = (
                        f"{row.get('product_name', 'Unknown')} · {row.get('product_code', '')} "
                        f"· Batch {row.get('batch_number', '')} · row {row_number + 1}"
                    )
                    rows_by_key[item_key] = row

                if choices:
                    with st.form("ss_shelf_assign_form"):
                        selected_key = st.selectbox(
                            "Inventory batch",
                            list(choices),
                            format_func=lambda key: choices.get(key, key),
                            key="ss_shelf_batch_choice",
                        )
                        selected_cell = st.selectbox("Shelf cell", SHELVES, key="ss_shelf_cell_choice")
                        save_cell = st.form_submit_button("Save shelf location")
                    if save_cell:
                        st.session_state.setdefault("ss_shelf_assignments", {})[selected_key] = selected_cell
                        st.success(f"Shelf location saved: {selected_cell}.")

                assignments = st.session_state.get("ss_shelf_assignments", {})
                risk_lookup: dict[tuple[str, str], str] = {}
                for _, risk_row in product_risk.iterrows():
                    risk_lookup[(
                        str(risk_row.get("facility_code", "")),
                        str(risk_row.get("product_code", "")),
                    )] = str(risk_row.get("stock_review_status", ""))

                shelf_contents: dict[str, list[pd.Series]] = {cell: [] for cell in SHELVES}
                for item_key, cell in assignments.items():
                    if item_key in rows_by_key and cell in shelf_contents:
                        shelf_contents[cell].append(rows_by_key[item_key])

                st.markdown("**Shelf grid**")
                for row_letter in "ABCD":
                    columns = st.columns(4, gap="small")
                    for column_number, column in enumerate(columns, start=1):
                        cell = f"{row_letter}{column_number}"
                        entries = shelf_contents[cell]
                        colour, status = "#eef2f5", "Unassigned"
                        if entries:
                            item = entries[0]
                            product_key = (
                                str(item.get("facility_code", "")),
                                str(item.get("product_code", "")),
                            )
                            expiry = item.get("expiry_date")
                            if risk_lookup.get(product_key, "").startswith("Review:") or (
                                pd.notna(expiry) and expiry < analysis_date
                            ):
                                colour, status = "#fde8e8", "Priority review"
                            elif pd.isna(expiry):
                                colour, status = "#edf0f3", "Expiry unknown"
                            elif (expiry - analysis_date).days <= int(expiry_days):
                                colour, status = "#fff2d8", "Expiry review"
                            else:
                                colour, status = "#e5f5ec", "No configured alert"
                        names = [html.escape(str(item.get("product_name", "Unknown"))) for item in entries[:2]]
                        detail = "<br>".join(names) if names else "No batch assigned"
                        if len(entries) > 2:
                            detail += f"<br>+{len(entries) - 2} more"
                        with column:
                            st.markdown(
                                f'<div style="background:{colour};border:1px solid #d8e1e8;'
                                f'border-radius:12px;padding:12px 9px;min-height:112px;margin-bottom:8px;">'
                                f'<div style="font-weight:800;font-size:1.05rem;color:#163247">{cell}</div>'
                                f'<div style="font-size:0.76rem;color:#42596b;margin:5px 0">{detail}</div>'
                                f'<div style="font-size:0.69rem;font-weight:800;color:#344d60">{status}</div></div>',
                                unsafe_allow_html=True,
                            )
                st.caption(
                    "Red = priority review/expired-record verification · Yellow = expiry window · "
                    "Grey = unassigned/unknown expiry · Green = no configured alert."
                )
                assignment_rows = []
                for item_key, cell in assignments.items():
                    parts = item_key.split("|", 3)
                    if len(parts) == 4:
                        assignment_rows.append({
                            "facility_code": parts[0],
                            "product_code": parts[1],
                            "batch_number": parts[2],
                            "row_reference": parts[3],
                            "shelf_code": cell,
                        })
                if assignment_rows:
                    st.download_button(
                        "Export shelf assignments",
                        _csv_bytes(pd.DataFrame(assignment_rows)),
                        file_name="stocksignal_shelf_assignments.csv",
                        mime="text/csv",
                        key="ss_export_shelves",
                    )

    # Marketplace: session-only offers and non-binding expressions of interest.
    with swap_tab:
        st.markdown("#### Inter-facility coordination board")
        st.info(
            "Demonstration board only: offers are not shared across users or saved centrally. "
            "Any proposed movement requires authorised review, local policy checks and a "
            "separately arranged transport process."
        )
        offers = st.session_state.setdefault("ss_swap_offers", [])
        requests = st.session_state.setdefault("ss_swap_requests", [])

        imported_board = st.file_uploader(
            "Import a previously exported offer board", type=["csv"], key="ss_import_swap_board"
        )
        if imported_board is not None:
            try:
                incoming = pd.read_csv(imported_board)
                required = {
                    "offer_id", "source_facility", "product_code", "product_name",
                    "batch_number", "quantity_offered", "expiry_date", "status",
                }
                if not required.issubset(incoming.columns):
                    st.error("The file is missing required StockSignal offer-board columns.")
                else:
                    known_ids = {str(item.get("offer_id")) for item in offers}
                    new_rows = [
                        item for item in incoming.to_dict(orient="records")
                        if str(item.get("offer_id")) not in known_ids
                    ]
                    offers.extend(new_rows)
                    st.success(f"Imported {len(new_rows)} offer(s) into this session.")
            except Exception as exc:
                st.error(f"Could not read the offer board: {exc}")

        expiry_cutoff = analysis_date + timedelta(days=int(expiry_days))
        candidates = audited.copy()
        if not candidates.empty:
            expiry_series = pd.to_datetime(candidates["expiry_date"], errors="coerce").dt.date
            candidates = candidates[
                candidates["quantity_on_hand"].notna()
                & (candidates["quantity_on_hand"] > 0)
                & expiry_series.notna()
                & (expiry_series >= analysis_date)
                & (expiry_series <= expiry_cutoff)
                & ~candidates["review_flags"].str.contains(
                    "Duplicate facility/product/batch key", na=False
                )
            ].copy()
            candidates["_offer_label"] = candidates.apply(
                lambda row: (
                    f"{row['facility_code']} · {row['product_name']} · "
                    f"{row['batch_number']} · Qty {row['quantity_on_hand']}"
                ),
                axis=1,
            )

        st.markdown("**Near-expiry batches for human assessment**")
        st.caption(
            "The app identifies records inside the expiry window; it cannot determine surplus. "
            "Check local needs and approvals before drafting an offer."
        )
        if candidates.empty:
            st.caption("No non-expired, positive-quantity batch is inside the configured expiry window.")
        else:
            with st.form("ss_create_offer_form"):
                chosen_label = st.selectbox(
                    "Candidate batch", candidates["_offer_label"].tolist(), key="ss_offer_candidate"
                )
                chosen_row = candidates[candidates["_offer_label"] == chosen_label].iloc[0]
                max_quantity = float(chosen_row["quantity_on_hand"])
                offer_quantity = st.number_input(
                    "Quantity to discuss (same unit as inventory)",
                    min_value=0.0,
                    max_value=max_quantity,
                    value=max_quantity,
                    step=1.0,
                    key="ss_offer_quantity",
                )
                offer_note = st.text_input("Optional non-confidential note", key="ss_offer_note")
                create_offer = st.form_submit_button("Create draft offer")
            if create_offer:
                if offer_quantity <= 0:
                    st.error("Offer quantity must be greater than zero.")
                else:
                    offers.append({
                        "offer_id": uuid.uuid4().hex[:10],
                        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "source_facility": str(chosen_row["facility_code"]),
                        "product_code": str(chosen_row["product_code"]),
                        "product_name": str(chosen_row["product_name"]),
                        "batch_number": str(chosen_row["batch_number"]),
                        "quantity_offered": float(offer_quantity),
                        "expiry_date": str(chosen_row["expiry_date"]),
                        "note": offer_note.strip(),
                        "status": "Open — pending authorised review",
                    })
                    st.success("Draft offer added. No stock has been reserved or transferred.")

        if offers:
            offers_frame = pd.DataFrame(offers)
            st.markdown("**Offers in this session**")
            st.dataframe(offers_frame, hide_index=True, use_container_width=True)
            st.download_button(
                "Export offer board CSV",
                _csv_bytes(offers_frame),
                file_name="stocksignal_swap_offers.csv",
                mime="text/csv",
                key="ss_export_swap_offers",
            )
            open_offers = [item for item in offers if str(item.get("status", "")).startswith("Open")]
            facilities = sorted(
                str(value)
                for value in audited.get("facility_code", pd.Series(dtype=str)).dropna().unique()
            )
            if open_offers and facilities:
                offer_labels = {
                    str(item["offer_id"]): (
                        f"{item['product_name']} · {item['source_facility']} · {item['batch_number']}"
                    )
                    for item in open_offers
                }
                with st.form("ss_swap_interest_form"):
                    selected_offer_id = st.selectbox(
                        "Offer", list(offer_labels),
                        format_func=lambda key: offer_labels[key],
                        key="ss_swap_offer_select",
                    )
                    selected_offer = next(
                        item for item in open_offers if str(item["offer_id"]) == selected_offer_id
                    )
                    receiving_facilities = [
                        value for value in facilities
                        if value != str(selected_offer["source_facility"])
                    ]
                    if receiving_facilities:
                        receiving_facility = st.selectbox(
                            "Receiving facility", receiving_facilities, key="ss_swap_destination"
                        )
                    else:
                        receiving_facility = None
                        st.warning("The uploaded data needs at least two distinct facilities to test a request.")
                    request_quantity = st.number_input(
                        "Quantity requested", min_value=0.0,
                        max_value=float(selected_offer["quantity_offered"]),
                        step=1.0, key="ss_swap_request_qty",
                    )
                    record_interest = st.form_submit_button(
                        "Record non-binding interest", disabled=not receiving_facilities
                    )
                if record_interest:
                    if request_quantity <= 0:
                        st.error("Enter a positive quantity.")
                    else:
                        requests.append({
                            "request_id": uuid.uuid4().hex[:10],
                            "offer_id": selected_offer_id,
                            "source_facility": str(selected_offer["source_facility"]),
                            "receiving_facility": receiving_facility,
                            "product_code": str(selected_offer["product_code"]),
                            "batch_number": str(selected_offer["batch_number"]),
                            "quantity_requested": float(request_quantity),
                            "status": "Interest recorded — authorised review required",
                            "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        })
                        st.success("Interest recorded. This does not approve or initiate a transfer.")
            if requests:
                request_frame = pd.DataFrame(requests)
                st.markdown("**Expressions of interest**")
                st.dataframe(request_frame, hide_index=True, use_container_width=True)
                st.download_button(
                    "Export request log CSV",
                    _csv_bytes(request_frame),
                    file_name="stocksignal_swap_requests.csv",
                    mime="text/csv",
                    key="ss_export_swap_requests",
                )
            if not open_offers:
                st.caption("There are no open offers to request.")
        st.caption(
            "No clinical-equivalence matching, stock reservation, transport booking "
            "or inventory deduction is performed."
        )

    # Portable work pack for offline spreadsheet review, not an offline PWA.
    with offline_tab:
        st.markdown("#### Prepare a field work kit")
        st.info(
            "The hosted Streamlit app still needs internet to open and sync. This ZIP "
            "is a portable work pack for approved offline spreadsheet review; it is "
            "not a standalone offline app, background sync service or conflict-safe database."
        )
        shelf_rows = []
        for item_key, cell in st.session_state.get("ss_shelf_assignments", {}).items():
            parts = item_key.split("|", 3)
            if len(parts) == 4:
                shelf_rows.append({
                    "facility_code": parts[0],
                    "product_code": parts[1],
                    "batch_number": parts[2],
                    "row_reference": parts[3],
                    "shelf_code": cell,
                })
        frames = {
            "inventory_source.csv": source_df,
            "shelf_assignments.csv": pd.DataFrame(shelf_rows),
            "observation_queue.csv": pd.DataFrame(st.session_state.get("ss_voice_notes", [])),
            "swap_offers.csv": pd.DataFrame(st.session_state.get("ss_swap_offers", [])),
            "swap_requests.csv": pd.DataFrame(st.session_state.get("ss_swap_requests", [])),
        }
        bundle = io.BytesIO()
        with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for filename, frame in frames.items():
                archive.writestr(filename, _csv_bytes(frame).decode("utf-8"))
            archive.writestr(
                "READ_ME_FIRST.txt",
                "STOCKSIGNAL FIELD WORK KIT\n\n"
                "This export is not a standalone offline app. Protect it and use only synthetic or specifically authorised data.\n"
                "When offline, review/edit inventory_source.csv with an approved spreadsheet tool and preserve its column names.\n"
                "When connectivity returns, upload the revised CSV to StockSignal and compare changes before accepting them.\n"
                "There is no conflict detection or automatic multi-user sync. Do not overwrite records blindly.\n"
                "Flags are not instructions to order, move, quarantine, dispense or discard stock. An authorised person must verify every change.\n",
            )
        st.download_button(
            "Download StockSignal field work kit (.zip)",
            bundle.getvalue(),
            file_name="stocksignal_field_work_kit.zip",
            mime="application/zip",
            type="primary",
            key="ss_download_offline_kit",
        )
        st.caption(
            "Draft queues and shelf assignments live in temporary Streamlit session state. "
            "Export important work before closing or refreshing the session."
        )
