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

specialty = st.selectbox("Select Surgical Specialty", list(benchmarks.keys()))
default_direct = benchmarks[specialty]["direct_revenue_per_case"]

# Target vs Actual Cases per Shift for TMT analysis
st.subheader("📈 Case Volume Comparison")
target_cases = st.number_input("Target Surgical Cases per Shift", min_value=0, step=1, value=10)
actual_cases = st.number_input("Actual Surgical Cases Handled per Shift", min_value=0, step=1, value=actual_cases if "actual_cases" in locals() else 8)

# Inputs: revenue & anesthesia
direct_per_case = st.number_input("Average Direct Revenue per Case ($)", value=default_direct)
include_anesthesia = st.checkbox("Include Anesthesia Revenue", value=False)
anesthesia_per_case = 0
if include_anesthesia:
    anesthesia_per_case = st.number_input("Anesthesia Revenue per Case ($)", min_value=0, value=200)
total_direct_per_case = direct_per_case + anesthesia_per_case

# Downstream inputs
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
            pct = st.number_input(f"{ds['label']} – % of cases", min_value=0, max_value=100,
                                  value=ds["default_pct"], key=ds["label"]+"_pct")
        with col2:
            rev = st.number_input(f"{ds['label']} – Rev per case ($)", min_value=0,
                                  value=ds["default_rev"], key=ds["label"]+"_rev")
        selected_downstreams.append({"conversion_rate": pct, "revenue_per_case": rev})

# TMT staffing cost inputs
st.subheader("💰 Transition Management Team (TMT) Cost Inputs")
cost_mode = st.radio("Base shift cost mode:", ["Hourly Rate", "Daily Rate"])
if cost_mode == "Hourly Rate":
    hourly_rate = st.number_input("Hourly Rate ($)", min_value=0, value=200)
    shift_hours = st.number_input("Hours per Shift", min_value=0, max_value=24, value=10)
    base_shift_cost = hourly_rate * shift_hours
else:
    base_shift_cost = st.number_input("Daily Rate ($)", min_value=0, value=2500)

travel_cost = st.number_input("Travel Cost per Day ($)", min_value=0, value=300)
housing_cost = st.number_input("Housing Cost per Day ($)", min_value=0, value=250)
total_tmt_shift_cost = compute_shift_cost(base_shift_cost, travel_cost, housing_cost)

# Annualization
st.subheader("📆 Annualization Settings")
shifts_per_year = st.number_input("Number of TMT Shifts per Year", min_value=0, value=50)

# Toggle comparison
st.subheader("🔄 TMT Coverage Mode")
use_tmt = st.radio("Model Scenario:", ["Without TMT", "With TMT"])

if st.button("Calculate Annual Program Impact"):
    # Without TMT
    direct_no, downstream_no, rev_no = compute_revenue(actual_cases, total_direct_per_case, selected_downstreams)
    lost_cases = max(0, target_cases - actual_cases)
    lost_revenue_per_shift = lost_cases * (total_direct_per_case + sum([
        ds["conversion_rate"]/100 * ds["revenue_per_case"] for ds in selected_downstreams
    ]))
    net_revenue_no = rev_no

    # With TMT: assume extra capacity handles target_cases
    direct_tmt, downstream_tmt, rev_tmt = compute_revenue(target_cases, total_direct_per_case, selected_downstreams)
    net_revenue_tmt = rev_tmt

    # Costs
    annual_tmt_cost = annualize(total_tmt_shift_cost, shifts_per_year)

    # Annual revenue comparison
    annual_rev_no = annualize(net_revenue_no, shifts_per_year)
    annual_rev_tmt = annualize(net_revenue_tmt, shifts_per_year)
    recovered_revenue = annual_rev_tmt - annual_rev_no

    st.subheader("📊 Annual Results")

    st.write(f"**Without TMT**: ${annual_rev_no:,.2f} annual revenue (lost ${annualize(lost_revenue_per_shift, shifts_per_year):,.2f})")
    st.write(f"**With TMT**: ${annual_rev_tmt:,.2f} annual revenue")

    st.markdown(f"**Revenue Recovered by TMT**: <span style='color:green; font-weight:bold;'>+${recovered_revenue:,.2f}</span>", unsafe_allow_html=True)
    st.markdown(f"**Annual TMT Cost**: <span style='color:#555;'>${annual_tmt_cost:,.2f}</span>", unsafe_allow_html=True)

    net_gain = recovered_revenue - annual_tmt_cost
    style = "color:green;" if net_gain >= 0 else "color:darkred;"
    st.markdown(f"**Net Gain from Program**: <span style='{style} font-size:24px; font-weight:bold;'>${net_gain:,.2f}</span>", unsafe_allow_html=True)
