import streamlit as st
import pandas as pd

# -----------------------------
# Default Benchmark Data
# -----------------------------
SPECIALTIES = {
    "General Surgery": {"direct": 675, "downstream": 1500},
    "Orthopedic Surgery": {"direct": 850, "downstream": 2200},
    "Neurosurgery": {"direct": 1000, "downstream": 2500},
    "Cardiovascular": {"direct": 1200, "downstream": 2800},
    "Urology": {"direct": 600, "downstream": 1200},
    "ENT": {"direct": 500, "downstream": 1000},
    "Trauma Surgery": {"direct": 700, "downstream": 1600},
}

# -----------------------------
# Helper Functions
# -----------------------------
def compute_revenue(cases, direct_per_case, downstreams):
    direct = cases * direct_per_case
    downstream = sum([cases * ds["conversion_rate"] / 100 * ds["revenue_per_case"] for ds in downstreams])
    return direct, downstream, direct + downstream

def annualize(amount_per_shift, shifts_per_year):
    return amount_per_shift * shifts_per_year

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Surgery ROI Calculator", layout="centered")
st.title("🔍 Surgery ROI & Program Impact Calculator")

# Input Fields
st.header("1. Shift & Specialty Inputs")
specialty = st.selectbox("Select Surgical Specialty", list(SPECIALTIES.keys()))
defaults = SPECIALTIES[specialty]

cases_per_shift = st.number_input("# of Surgical Cases per Shift", min_value=0, value=4)
direct_per_case = st.number_input("Avg Direct Revenue per Case ($)", min_value=0, value=defaults["direct"])

# Downstream Revenue Breakdown
st.subheader("Downstream Revenue")
downstream_types = ["Imaging", "Lab", "PT", "Follow-up", "Other"]
selected_downstreams = []

for dtype in downstream_types:
    col1, col2 = st.columns(2)
    with col1:
        conv = st.slider(f"{dtype} Retention %", 0, 100, 70)
    with col2:
        rev = st.number_input(f"{dtype} Revenue per Case ($)", min_value=0, value=defaults["downstream"] // len(downstream_types))
    selected_downstreams.append({"type": dtype, "conversion_rate": conv, "revenue_per_case": rev})

# Cost Inputs
st.header("2. Cost Inputs")
col1, col2, col3 = st.columns(3)

with col1:
    cost_mode = st.radio("TMT Cost Type", ["Hourly", "Daily"])
    hourly_rate = st.number_input("Hourly Rate ($)", value=250)

with col2:
    hours_per_shift = st.number_input("Hours per Shift", value=12)

with col3:
    travel_cost = st.number_input("Travel + Housing Cost per Day ($)", value=300)

operating_costs = st.number_input("Other Operating Costs per Shift ($)", value=500)

# Toggle for Transition Management Team
st.header("3. TMT Coverage Mode")
tmt_toggle = st.radio("Model Scenario:", ["Without TMT", "With TMT"])
shifts_per_year = st.number_input("Estimated Annual Shifts", value=250)

target_cases = st.number_input("Target Cases per Shift with TMT", value=cases_per_shift + 2)
actual_cases = target_cases if tmt_toggle == "With TMT" else cases_per_shift

total_direct_per_case = direct_per_case
total_tmt_shift_cost = (
    (hourly_rate * hours_per_shift if cost_mode == "Hourly" else hourly_rate) + travel_cost + operating_costs
)

# -----------------------------
# Calculations & Output
# -----------------------------
if st.button("Calculate Annual Program Impact"):
    # Revenue & costs
    direct_no, downstream_no, rev_no = compute_revenue(actual_cases if tmt_toggle == "Without TMT" else cases_per_shift, total_direct_per_case, selected_downstreams)
    lost_cases = max(0, target_cases - cases_per_shift)
    lost_revenue_per_shift = lost_cases * (total_direct_per_case + sum([
        ds["conversion_rate"]/100 * ds["revenue_per_case"] for ds in selected_downstreams
    ]))

    direct_tmt, downstream_tmt, rev_tmt = compute_revenue(target_cases, total_direct_per_case, selected_downstreams)
    annual_rev_no = annualize(rev_no, shifts_per_year)
    annual_rev_tmt = annualize(rev_tmt, shifts_per_year)
    annual_tmt_cost = annualize(total_tmt_shift_cost, shifts_per_year)

    recovered_revenue = annual_rev_tmt - annual_rev_no
    net_gain = recovered_revenue - annual_tmt_cost

    st.subheader("📊 Annual Results")

    lost_rev_style = "background-color:darkred; color:white; padding:2px 6px; border-radius:6px; font-weight:bold;"
    gain_style = "background-color:green; color:white; padding:2px 6px; border-radius:6px; font-weight:bold;"

    st.markdown(
        f"**Without TMT**: ${annual_rev_no:,.2f} annual revenue "
        f"(<span style='{lost_rev_style}'>Lost ${annualize(lost_revenue_per_shift, shifts_per_year):,.2f}</span>)",
        unsafe_allow_html=True
    )

    st.markdown(
        f"**With TMT**: <span style='{gain_style}'>${annual_rev_tmt:,.2f} annual revenue</span>",
        unsafe_allow_html=True
    )

    st.markdown(
        f"**Revenue Recovered by TMT**: <span style='{gain_style}'>+${recovered_revenue:,.2f}</span>",
        unsafe_allow_html=True
    )

    st.write(f"**Annual TMT Cost**: ${annual_tmt_cost:,.2f}")

    style = gain_style if net_gain >= 0 else lost_rev_style
    st.markdown(
        f"**Net Gain from Program**: <span style='{style}'>${net_gain:,.2f}</span>",
        unsafe_allow_html=True
    )
