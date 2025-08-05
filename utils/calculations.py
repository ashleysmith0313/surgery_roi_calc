def compute_revenue(cases, direct_per_case, downstreams):
    direct_revenue = cases * direct_per_case
    downstream_revenue = 0
    for ds in downstreams:
        pct = ds.get("conversion_rate", 0)
        rev = ds.get("revenue_per_case", 0)
        downstream_revenue += cases * (pct / 100.0) * rev
    total_revenue = direct_revenue + downstream_revenue
    return direct_revenue, downstream_revenue, total_revenue

def compute_shift_cost(base_shift_cost, travel_cost, housing_cost):
    return base_shift_cost + travel_cost + housing_cost

def compute_lost_revenue_gap(cases, lost_per_case):
    return cases * lost_per_case

def annualize(value_per_shift, shifts_per_year):
    return value_per_shift * shifts_per_year

def compute_roi(total_revenue, total_cost):
    if total_cost <= 0:
        return None
    return total_revenue / total_cost
