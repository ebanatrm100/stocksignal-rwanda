from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from stocksignal import REQUIRED_COLUMNS, audit_inventory

st.set_page_config(
    page_title="StockSignal | Inventory Intelligence",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_PATH = BASE_DIR / "sample_inventory.csv"

# A cohesive visual system: clinical, calm, and easy to scan under pressure.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
      --ink: #142538;
      --muted: #687b8e;
      --teal: #087f8c;
      --teal-dark: #086b75;
      --teal-pale: #e7f5f5;
      --blue-pale: #eef4fb;
      --line: #e3eaf0;
      --surface: #ffffff;
      --page: #f4f7fa;
      --amber: #b96a12;
      --amber-pale: #fff5e7;
      --red: #b83b45;
      --red-pale: #fff0f1;
      --green: #247a56;
      --green-pale: #eaf7f0;
    }

    html, body, [class*="css"] {
      font-family: 'DM Sans', sans-serif;
      color: var(--ink);
    }
    .stApp { background: var(--page); }
    [data-testid="stHeader"] { background: rgba(244,247,250,0.88); }
    [data-testid="stMainBlockContainer"] {
      max-width: 1500px;
      padding-top: 1.4rem;
      padding-bottom: 2.8rem;
    }
    h1, h2, h3, h4 { font-family: 'Manrope', sans-serif !important; color: var(--ink); }
    h2 { letter-spacing: -0.035em; }
    p, li, label { line-height: 1.55; }

    [data-testid="stSidebar"] {
      background: #ffffff;
      border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.15rem; }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: var(--ink); }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: var(--muted); }

    div[data-testid="stFileUploader"] section {
      background: #f8fbfd;
      border: 1px dashed #b8cbd8;
      border-radius: 14px;
      padding: 0.8rem;
    }
    div[data-testid="stFileUploader"] section:hover { border-color: var(--teal); }
    [data-testid="stMetric"] {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 17px 18px;
      box-shadow: 0 5px 18px rgba(19, 43, 64, 0.035);
    }
    [data-testid="stMetricLabel"] { color: var(--muted) !important; font-weight: 600; }
    [data-testid="stMetricValue"] { color: var(--ink) !important; font-family: 'Manrope', sans-serif; }

    [data-testid="stTabs"] [role="tablist"] {
      gap: 0.35rem;
      border-bottom: 1px solid var(--line);
    }
    [data-testid="stTabs"] button[role="tab"] {
      padding: 0.75rem 1rem;
      border-radius: 10px 10px 0 0;
      font-weight: 600;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
      color: var(--teal-dark);
      border-bottom-color: var(--teal) !important;
    }

    [data-testid="stDataFrame"] {
      border: 1px solid var(--line);
      border-radius: 12px;
      overflow: hidden;
      background: white;
    }
    [data-testid="stDownloadButton"] button,
    [data-testid="stButton"] button {
      border-radius: 10px;
      font-weight: 650;
      border: 1px solid #c7d8e0;
      transition: all 120ms ease-in-out;
    }
    [data-testid="stDownloadButton"] button:hover,
    [data-testid="stButton"] button:hover {
      border-color: var(--teal);
      color: var(--teal-dark);
    }
    [data-testid="stAlert"] { border-radius: 12px; }
    div[data-testid="stExpander"] {
      border: 1px solid var(--line);
      border-radius: 12px;
      background: white;
    }

    .brand-line { display:flex; align-items:center; gap:12px; margin-bottom: 1rem; }
    .brand-symbol {
      width: 45px; height: 45px; border-radius: 14px;
      display:flex; align-items:center; justify-content:center;
      background: linear-gradient(135deg, #0b7d88, #155a78);
      box-shadow: 0 7px 18px rgba(8,127,140,0.2);
      color: white; font-size: 23px; font-weight: 800;
    }
    .brand-name { font-family:'Manrope',sans-serif; font-weight:800; font-size: 1.18rem; letter-spacing:-0.04em; color:var(--ink); }
    .brand-sub { font-size:0.68rem; font-weight:700; letter-spacing:0.13em; color:var(--muted); text-transform:uppercase; margin-top:1px; }

    .hero {
      position: relative; overflow: hidden;
      border-radius: 24px;
      padding: 27px 30px 28px;
      color: white;
      background: linear-gradient(115deg, #102e43 0%, #135d6e 57%, #078a91 100%);
      box-shadow: 0 14px 32px rgba(16, 46, 67, 0.15);
      margin-bottom: 1.1rem;
    }
    .hero:after {
      content: ""; position:absolute; right:-75px; top:-135px;
      width:360px; height:360px; border-radius:50%;
      border:1px solid rgba(255,255,255,0.12);
      box-shadow: 0 0 0 30px rgba(255,255,255,0.035), 0 0 0 65px rgba(255,255,255,0.025);
      pointer-events:none;
    }
    .hero-top { display:flex; align-items:center; justify-content:space-between; gap:1rem; position:relative; z-index:1; }
    .hero-brand { display:flex; align-items:center; gap:10px; font-family:'Manrope',sans-serif; font-weight:800; letter-spacing:-0.03em; font-size:1.08rem; }
    .hero-brand-mark { background:rgba(255,255,255,0.15); border:1px solid rgba(255,255,255,0.2); border-radius:10px; padding:7px 9px; }
    .demo-badge { font-size:0.7rem; font-weight:800; letter-spacing:0.09em; text-transform:uppercase; padding:7px 10px; border-radius:99px; border:1px solid rgba(255,255,255,0.3); background:rgba(255,255,255,0.1); color:#e3ffff; white-space:nowrap; }
    .hero h1 { color:white !important; font-size:clamp(1.9rem, 3vw, 2.65rem); line-height:1.12; letter-spacing:-0.055em; margin:22px 0 10px; position:relative; z-index:1; }
    .hero h1 span { color:#88e1de; }
    .hero p { color:#d4e8ef; max-width:760px; margin:0; position:relative; z-index:1; font-size:1rem; }
    .hero-foot { display:flex; flex-wrap:wrap; gap:10px; margin-top:22px; position:relative; z-index:1; }
    .hero-chip { display:flex; align-items:center; gap:8px; border-radius:10px; background:rgba(255,255,255,0.1); padding:9px 12px; color:#f5ffff; font-size:0.81rem; border:1px solid rgba(255,255,255,0.1); }

    .section-kicker { color:var(--teal-dark); text-transform:uppercase; letter-spacing:0.14em; font-size:0.68rem; font-weight:800; margin-bottom:4px; }
    .section-title { font-family:'Manrope',sans-serif; color:var(--ink); font-size:1.34rem; font-weight:800; letter-spacing:-0.04em; margin:0; }
    .section-help { color:var(--muted); font-size:0.88rem; margin-top:4px; margin-bottom:0.8rem; }
    .panel {
      background: white; border:1px solid var(--line); border-radius:16px;
      padding:17px 18px; box-shadow:0 5px 18px rgba(19,43,64,0.025);
    }
    .panel-title { font-family:'Manrope',sans-serif; font-size:1rem; font-weight:800; color:var(--ink); margin-bottom:5px; }
    .panel-sub { color:var(--muted); font-size:0.83rem; margin-bottom:10px; }
    .callout {
      display:flex; gap:12px; align-items:flex-start;
      background:#fff9ed; border:1px solid #f3d7a9; border-left:4px solid #d58a22;
      border-radius:13px; padding:13px 15px; color:#704713; margin:0.4rem 0 1.25rem;
    }
    .callout-icon { font-size:1.1rem; line-height:1.4; }
    .callout strong { color:#6f410b; }
    .source-chip { display:inline-block; padding:6px 10px; background:#e9f6f6; border:1px solid #c9e9e8; border-radius:999px; color:#086b75; font-size:0.76rem; font-weight:700; }
    .summary-strip { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:10px; margin:0.5rem 0 1.25rem; }
    .summary-left { color:var(--muted); font-size:0.85rem; }
    .soft-note { border-radius:12px; background:#f0f6fa; border:1px solid #dfebf2; color:#50677b; padding:12px 14px; font-size:0.84rem; }
    .status-pill { display:inline-block; border-radius:99px; padding:4px 8px; font-size:0.72rem; font-weight:800; background:var(--amber-pale); color:var(--amber); }
    .sidebar-brand { padding:8px 0 18px; border-bottom:1px solid var(--line); margin-bottom:18px; }
    .sidebar-caption { color:var(--muted); font-size:0.79rem; line-height:1.5; }
    .footer { border-top:1px solid var(--line); padding-top:16px; color:#7b8b9a; font-size:0.76rem; text-align:center; margin-top:2rem; }
    @media (max-width: 700px) {
      .hero { padding:22px 20px; border-radius:18px; }
      .hero-top { align-items:flex-start; flex-direction:column; }
      .hero h1 { margin-top:18px; }
      .hero:after { opacity:0.35; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar: keep the controls available without letting them overwhelm the main workspace.
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
          <div class="brand-line">
            <div class="brand-symbol">＋</div>
            <div>
              <div class="brand-name">StockSignal</div>
              <div class="brand-sub">Inventory intelligence</div>
            </div>
          </div>
          <div class="sidebar-caption">A review workspace for inventory data quality, expiry dates, and estimated stock coverage.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### Review settings")
    analysis_date = st.date_input("Analysis date", value=date.today(), help="All date-based rules are evaluated against this date.")
    stale_days = st.number_input("Flag records older than (days)", min_value=0, max_value=365, value=30, help="Configurable demo threshold for record freshness.")
    expiry_days = st.number_input("Expiry warning window (days)", min_value=0, max_value=730, value=90, help="Flag batches expiring on or before this many days from the analysis date.")
    buffer_days = st.number_input("Lead-time review buffer (days)", min_value=0, max_value=180, value=7, help="Added to recorded lead time for screening. Not an official procurement standard.")
    st.markdown("---")
    st.markdown("**Review guide**")
    st.markdown(
        """
        <div class="sidebar-caption">
          <div style="margin:7px 0"><span style="color:#b96a12;font-weight:800">● Amber</span> &nbsp; Review recommended</div>
          <div style="margin:7px 0"><span style="color:#b83b45;font-weight:800">● Red</span> &nbsp; Potentially urgent issue</div>
          <div style="margin:7px 0"><span style="color:#247a56;font-weight:800">● Green</span> &nbsp; No configured rule triggered</div>
          <br>Thresholds are demonstration settings. Follow approved local procedures and verify every alert with an authorised person.
        </div>
        """,
        unsafe_allow_html=True,
    )

# Hero header.
st.markdown(
    """
    <section class="hero">
      <div class="hero-top">
        <div class="hero-brand"><span class="hero-brand-mark">✚</span><span>StockSignal</span></div>
        <div class="demo-badge">Prototype workspace · Synthetic data</div>
      </div>
      <h1>Inventory clarity.<br><span>Safer decisions.</span></h1>
      <p>Surface data-quality issues, expiry concerns, and estimated stock-cover risks so authorised teams know which records deserve a closer look.</p>
      <div class="hero-foot">
        <div class="hero-chip">◉ &nbsp; Human-reviewed findings</div>
        <div class="hero-chip">↗ &nbsp; Transparent rules</div>
        <div class="hero-chip">▤ &nbsp; CSV audit exports</div>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="callout">
      <div class="callout-icon">⚠</div>
      <div><strong>Demonstration and decision support only.</strong> Sample records are fabricated. StockSignal does not replace eLMIS, a pharmacist, or an authorised supply-chain decision-maker. A flag is a prompt to verify data and follow approved procedures—not an instruction to order, transfer, quarantine, dispense, or discard stock.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Data intake panel.
st.markdown('<div class="section-kicker">01 / Data intake</div><div class="section-title">Choose your inventory source</div><div class="section-help">Start with the synthetic sample or upload a CSV that follows the documented schema.</div>', unsafe_allow_html=True)
with st.container(border=True):
    intake_left, intake_right = st.columns([1.55, 1], gap="large")
    with intake_left:
        uploaded = st.file_uploader(
            "Upload inventory CSV",
            type=["csv"],
            help="Use the required column names listed below. Only upload data you are authorised to use.",
            label_visibility="visible",
        )
        st.markdown('<div class="soft-note">Tip: test with <strong>sample_inventory.csv</strong> first. Keep real facility data local and use only with written authorisation.</div>', unsafe_allow_html=True)
    with intake_right:
        st.markdown('<div class="panel-title">Required data fields</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-sub">Nine columns used by the current prototype.</div>', unsafe_allow_html=True)
        st.code("facility_code · product_code · product_name · batch_number\nquantity_on_hand · average_monthly_consumption · lead_time_days\nexpiry_date · last_stock_update", language="text")
        with st.expander("View data dictionary guidance"):
            st.markdown("Read `data_dictionary.md` in the project folder for field definitions, expected formats, and calculation assumptions.")

if uploaded is not None:
    try:
        source_df = pd.read_csv(uploaded)
        source_label = f"Uploaded file: {uploaded.name}"
    except Exception as exc:
        st.error(f"The CSV could not be read: {exc}")
        st.stop()
else:
    try:
        source_df = pd.read_csv(SAMPLE_PATH)
        source_label = "Synthetic demonstration data"
    except FileNotFoundError:
        st.error("sample_inventory.csv was not found. Keep it in the same folder as app.py.")
        st.stop()

source_label_safe = escape(source_label)
st.markdown(
    f'<div class="summary-strip"><div class="summary-left">Current source: <strong>{source_label_safe}</strong></div><div class="source-chip">● Data loaded for review</div></div>',
    unsafe_allow_html=True,
)

try:
    audited, product_risk = audit_inventory(
        source_df,
        as_of_date=analysis_date,
        stale_days=int(stale_days),
        expiry_warning_days=int(expiry_days),
        lead_buffer_days=int(buffer_days),
    )
except (ValueError, TypeError) as exc:
    st.error(str(exc))
    st.info("Correct the column names or file values, then upload the CSV again.")
    st.stop()

# Summary calculations use the existing reviewed logic.
quality_issue_rows = int(audited["data_quality_issue"].sum())
expiry_rows = int(audited["review_flags"].str.contains("Batch expires|Batch is expired", regex=True).sum())
stock_review_rows = int(product_risk["stock_review_status"].str.startswith("Review:").sum()) if not product_risk.empty else 0
clean_rows = max(0, len(audited) - quality_issue_rows)

st.markdown('<div class="section-kicker">02 / At a glance</div><div class="section-title">Review overview</div><div class="section-help">A quick summary of records that may require verification.</div>', unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4, gap="medium")
with m1:
    st.metric("Inventory records", f"{len(audited):,}", help="Number of inventory rows in the selected source.")
with m2:
    st.metric("Data-quality reviews", f"{quality_issue_rows:,}", delta=f"{quality_issue_rows / len(audited):.0%} of rows" if len(audited) else None, delta_color="inverse", help="Rows with one or more data-quality flags.")
with m3:
    st.metric("Expiry reviews", f"{expiry_rows:,}", help="Rows that are expired or inside the configured expiry-warning window.")
with m4:
    st.metric("Stock-cover reviews", f"{stock_review_rows:,}", help="Products at or below the configured lead-time plus buffer threshold.")

# Small orientation panel helps people understand the intended workflow.
left, right = st.columns([1.55, 1], gap="large")
with left:
    st.markdown('<div class="section-kicker">03 / Review queue</div><div class="section-title">Priority review list</div><div class="section-help">Products whose estimated days of stock meet the configured review rule.</div>', unsafe_allow_html=True)
    low_cover = product_risk[product_risk["stock_review_status"].str.startswith("Review:")].copy() if not product_risk.empty else product_risk
    if low_cover.empty:
        st.success("No product crossed the configured stock-cover review threshold in this dataset.")
    else:
        st.dataframe(low_cover, width="stretch", hide_index=True, height=min(360, 52 + 38 * len(low_cover)))
        st.download_button(
            "Download stock-cover review CSV",
            data=product_risk.to_csv(index=False).encode("utf-8"),
            file_name="stocksignal_product_review.csv",
            mime="text/csv",
            key="download_priority_review",
        )
with right:
    st.markdown('<div class="section-kicker">Quick context</div><div class="section-title">What needs attention?</div><div class="section-help">Counts are not mutually exclusive; a record can trigger more than one rule.</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="panel" style="margin-bottom:10px">
          <div style="display:flex;justify-content:space-between;gap:12px;align-items:center">
            <div><div class="panel-title">Data quality</div><div class="panel-sub" style="margin-bottom:0">Missing, stale, inconsistent, or invalid values</div></div>
            <div style="font-family:Manrope,sans-serif;font-size:1.55rem;font-weight:800;color:#b96a12">{quality_issue_rows}</div>
          </div>
        </div>
        <div class="panel" style="margin-bottom:10px">
          <div style="display:flex;justify-content:space-between;gap:12px;align-items:center">
            <div><div class="panel-title">Expiry review</div><div class="panel-sub" style="margin-bottom:0">Expired or approaching expiry dates</div></div>
            <div style="font-family:Manrope,sans-serif;font-size:1.55rem;font-weight:800;color:#b83b45">{expiry_rows}</div>
          </div>
        </div>
        <div class="panel">
          <div style="display:flex;justify-content:space-between;gap:12px;align-items:center">
            <div><div class="panel-title">No data-quality flag</div><div class="panel-sub" style="margin-bottom:0">Rows with no non-expiry quality rule triggered</div></div>
            <div style="font-family:Manrope,sans-serif;font-size:1.55rem;font-weight:800;color:#247a56">{clean_rows}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")
st.markdown('<div class="section-kicker">04 / Record-level evidence</div><div class="section-title">Detailed findings</div><div class="section-help">Review the exact records and rule messages behind each flag. Export the findings for further checking.</div>', unsafe_allow_html=True)
tab_quality, tab_expiry, tab_all = st.tabs(["Data quality", "Expiry review", "All inventory rows"])
with tab_quality:
    quality = audited[audited["data_quality_issue"]]
    if quality.empty:
        st.success("No data-quality rules were triggered for the selected source and settings.")
    else:
        st.caption(f"{len(quality)} row(s) require data-quality review.")
        st.dataframe(quality, width="stretch", hide_index=True, height=min(460, 76 + 38 * len(quality)))
    st.download_button(
        "Export row-level audit CSV",
        data=audited.to_csv(index=False).encode("utf-8"),
        file_name="stocksignal_row_audit.csv",
        mime="text/csv",
        key="download_row_audit",
    )
with tab_expiry:
    expiry_view = audited[audited["review_flags"].str.contains("Batch expires|Batch is expired", regex=True)].copy()
    if expiry_view.empty:
        st.info("No expired or near-expiry batches were flagged for the selected date and threshold.")
    else:
        st.caption(f"{len(expiry_view)} row(s) meet the configured expiry-review rule.")
        st.dataframe(expiry_view, width="stretch", hide_index=True, height=min(460, 76 + 38 * len(expiry_view)))
    st.markdown('<div class="soft-note">Expiry warnings are date-based. They do not determine whether stock is safe to dispense. Follow authorised procedures.</div>', unsafe_allow_html=True)
with tab_all:
    st.caption(f"Showing {len(audited)} row(s) from the current source.")
    st.dataframe(audited, width="stretch", hide_index=True, height=450)
    st.download_button(
        "Export all inventory review results",
        data=audited.to_csv(index=False).encode("utf-8"),
        file_name="stocksignal_all_inventory_review.csv",
        mime="text/csv",
        key="download_all_audit",
    )

with st.expander("How the calculations work and what they cannot tell you"):
    st.markdown(
        """
        **Estimated days of stock** = eligible stock quantity divided by estimated average daily consumption.

        Average daily consumption is estimated as average monthly consumption / 30.4375. The screening threshold is recorded lead time + the configurable review buffer. A product is flagged when estimated stock cover is at or below that threshold. Expired batches, batches with missing expiry dates, duplicate batch keys, missing identifiers, invalid quantities, and negative quantities are excluded from the cover quantity and remain visible for review.

        The audit checks required values, numeric/date parsing, negative quantities or consumption, negative lead time, duplicate facility/product/batch keys, inconsistent monthly consumption across batches, future update dates, stale records, and expiry status.

        **Important limitations:** this simple estimate does not model pending orders, seasonality, allocation, uncertainty in supplier delivery, clinical criticality, or programme-specific policies. The calculation assumes quantity and consumption are expressed in compatible units. These controls are configurable demonstration rules, not official clinical or procurement standards.

        A flagged item is a prompt to verify information and follow authorised procedures. It is not an instruction to reorder, transfer, quarantine, dispense, or discard stock. Real deployments require authorised users, privacy and security review, retention controls, appropriate local approvals, and evaluation against existing systems.
        """
    )

st.markdown(
    """
    <div class="footer">
      <strong>StockSignal</strong> &nbsp;·&nbsp; Prototype inventory review workspace<br>
      Synthetic demonstration data &nbsp;·&nbsp; Human review required &nbsp;·&nbsp; No clinical or procurement decisions
    </div>
    """,
    unsafe_allow_html=True,
)
