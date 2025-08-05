import streamlit as st
import json
from utils.calculations import (
    compute_revenue,
    compute_shift_cost,
    compute_lost_revenue_gap,
    annualize
)

# Load benchmarks
with open("data/benchmarks.json", "r") as f:
    benchmarks = json.load(f)

st.set_page_config(page_title="Surgery ROI Calculator", layout="centered")
st.title("🧮 Surgery ROI Calculator – Annualized View")

# --- Inputs: specialty, cases, revenue ---
specialty = st.selectbox("Select Surgical Specialty", list(benchmarks.keys()))
default_direct = benchmarks[specialty]["direct_revenue_per_case"]

cases = st.number_input("Surgical Cases per Shift", min_value=0, step=1)
direct_per_case = st.number_input(
    "Average Direct Revenue per Case ($)", value=default_direct
)

# Anesthesia
include_anesthesia = st.checkbox("Include Anesthesia Revenue", value=False)
anesthesia_per_case = 0
if include_anesthesia:
    anesthesia_per_case = st.number_input("Anesthesia Revenue per Case ($)", min_value=0, value=200)
total_direct_per_case = direct_per_case + anesthesia_per_case

# Downstream breakdown
st.subheader("📦 Downstream Revenue Sources")
downstream_services = [
    {"label": "Imaging (X-ray, MRI)", "default_pct": 70, "default_rev": 500},
    {"label": "Physical Therapy", "default_pct": 50, "default_rev": 800},
    {"label": "Follow-up Visits", "default_pct": 90, "default_rev": 200},
    {"label": "ICU Readmissions", "default_pct": 10, "default_rev": 4000},
]
selected_downstreams = []
for ds in downstream_services:
    inc = st.checkbox(ds["label"], value=True)
    if inc:
        col1, col2 = st.columns(2)
        with col1:
            pct = st.number_input(f"{ds['label']} – % cases", min_value=0, max_value=100,
                                  value=ds["default_pct"], key=ds["label"]+"_pct")
        with col2:
            rev = st.number_input(f"{ds['label']} – Rev per case ($)", min_value=0,
                                  value=ds["default_rev"], key=ds["label"]+"_rev")
        selected_downstreams.append({"conversion_rate": pct, "revenue_per_case": rev})

# --- Staffing / locum cost inputs ---
st.subheader("💰 Locum / Staffing Cost Inputs")
cost_mode = st.radio("Base shift cost mode:", ["Hourly Rate", "Daily Rate"])
if cost_mode == "Hourly Rate":
    hourly_rate = st.number_input("Hourly Rate ($)", min_value=0, value=200)
    shift_hours = st.number_input("Hours per Shift", min_value=0, max_value=24, value=10)
    base_shift_cost = hourly_rate * shift_hours
else:
    base_shift_cost = st.number_input("Daily Rate ($)", min_value=0, value=2500)

travel_cost = st.number_input("Travel Cost per Day ($)", min_value=0, value=300)
housing_cost = st.number_input("Housing Cost per Day ($)", min_value=0, value=250)
total_shift_cost = compute_shift_cost(base_shift_cost, travel_cost, housing_cost)

# --- Lost-revenue if surgeon unavailable ---
st.subheader("⚠️ Lost Revenue If Surgeon Not On Staff")
include_gap = st.checkbox("Include lost‑case revenue gap", value=False)
lost_per_case = 0
if include_gap:
    lost_per_case = st.number_input("Estimated lost revenue per surgical case ($)", min_value=0, value=500)

# --- Annualization ---
st.subheader("📆 Annualization Settings")
shifts_per_year = st.number_input("Number of Locum Shifts per Year", min_value=0, value=50)

# --- Compute & Display Results ---
if st.button("Calculate Annual ROI"):
    direct, downstream, total_revenue_per_shift = compute_revenue(cases, total_direct_per_case, selected_downstreams)
    lost_gap_per_shift = compute_lost_revenue_gap(cases, lost_per_case)
    net_revenue_per_shift = total_revenue_per_shift + lost_gap_per_shift

    annual_revenue = annualize(net_revenue_per_shift, shifts_per_year)
    annual_cost = annualize(total_shift_cost, shifts_per_year)
    recovered_gap_annual = annualize(lost_gap_per_shift, shifts_per_year)
    net_gain = annual_revenue - annual_cost

    st.subheader("📊 Annual Results")

    st.markdown(f"**Annual Revenue (incl. gap)**: <span style='color:green;'>${annual_revenue:,.2f}</span>", unsafe_allow_html=True)
    st.markdown(f"**Annual Cost (Locum + Travel + Housing)**: <span style='color:#555;'>${annual_cost:,.2f}</span>", unsafe_allow_html=True)

    if include_gap and recovered_gap_annual > 0:
        st.markdown(f"**Recovered Lost Revenue**: <span style='color:green; font-weight:bold;'>+${recovered_gap_annual:,.2f}</span>", unsafe_allow_html=True)
    elif include_gap:
        st.markdown(f"**Lost Revenue Uncovered**: <span style='color:darkred; font-weight:bold;'>-${recovered_gap_annual:,.2f}</span>", unsafe_allow_html=True)

    # Net Gain instead of ROI
    if annual_cost > 0:
        net_style = "color:green;" if net_gain >= 0 else "color:darkred;"
        st.markdown(f"**Net Gain from Locum Program**: <span style='{net_style} font-size:24px; font-weight:bold;'>${net_gain:,.2f}</span>", unsafe_allow_html=True)
    else:
        st.warning("Please enter a shift cost greater than 0.")
