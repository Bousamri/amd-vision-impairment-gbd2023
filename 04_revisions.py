import json
import math
import numpy as np
import pandas as pd

DATA = "data/"
OUT = "output/"
reg = pd.read_csv(DATA + "IHME-GBD_2023_DATA-67c190e0-1.csv")
reg["m"] = reg.measure_name.str[:4]
comb = pd.read_pickle(OUT + "gbd2021_gbd2023_global.pkl")
S = {}


def outside(v21, lo21, hi21, v23, lo23, hi23):
    return bool((v23 < lo21 or v23 > hi21) and (v21 < lo23 or v21 > hi23))


rows = []
amd = comb[comb.cause_name == "Age-related macular degeneration"]
for key, label in [
    ("Prev_n_Number", "Prevalent cases"),
    ("Prev_as_Rate", "Age-standardized prevalence"),
    ("DALY_n_Number", "DALYs"),
    ("DALY_as_Rate", "Age-standardized DALY rate"),
]:
    for yr in (1990, 2021):
        a = amd[(amd["round"] == "GBD2021") & (amd.key == key) & (amd.year == yr)].iloc[
            0
        ]
        b = amd[(amd["round"] == "GBD2023") & (amd.key == key) & (amd.year == yr)].iloc[
            0
        ]
        rows.append(
            dict(
                measure=label,
                year=yr,
                gbd21=a.val,
                gbd21_lo=a.lower,
                gbd21_hi=a.upper,
                gbd23=b.val,
                gbd23_lo=b.lower,
                gbd23_hi=b.upper,
                revision_pct=100 * (b.val / a.val - 1),
                outside_both=outside(a.val, a.lower, a.upper, b.val, b.lower, b.upper),
            )
        )
glob = pd.DataFrame(rows)
glob.to_csv(OUT + "global_revision_flags.csv", index=False)
x = (
    amd[amd.key == "Prev_n_Number"]
    .pivot_table(index="year", columns="round", values="val")
    .dropna()
)
rev = 100 * (x.GBD2023 / x.GBD2021 - 1)
S["count_revision_range"] = dict(
    smallest=float(rev.max()),
    smallest_year=int(rev.idxmax()),
    largest=float(rev.min()),
    largest_year=int(rev.idxmin()),
)

sev = pd.read_csv(OUT + "severity_2021.csv")
sev["outside_both"] = [
    (
        outside(
            r.GBD2021_prev,
            r.GBD2021_prev_lo,
            r.GBD2021_prev_hi,
            r.GBD2023_prev,
            r.GBD2023_prev_lo,
            r.GBD2023_prev_hi,
        )
        if r.severity != "Total"
        else np.nan
    )
    for r in sev.itertuples()
]
sev.to_csv(OUT + "severity_2021.csv", index=False)

g21 = pd.read_csv(DATA + "IHME-GBD_2021_DATA-322d9f23-1.csv")
g23n = pd.read_csv(DATA + "IHME-GBD_2023_DATA-c9a2b09d-1.csv")
g23a = pd.read_csv(DATA + "IHME-GBD_2023_DATA-3f2f59b1-1.csv")
regions = sorted(g23a.location_name.unique())


def pick(d, age, metric):
    x = d[
        (d.age_name == age) & (d.metric_name == metric) & d.location_name.isin(regions)
    ]
    return x.set_index("location_name")[["val", "lower", "upper"]]


n21, n23 = pick(g21, "All ages", "Number"), pick(g23n, "All ages", "Number")
a21, a23 = pick(g21, "Age-standardized", "Rate"), pick(g23a, "Age-standardized", "Rate")
reg_rev = pd.DataFrame(
    {
        "gbd21": n21.val,
        "gbd21_lo": n21.lower,
        "gbd21_hi": n21.upper,
        "gbd23": n23.val,
        "gbd23_lo": n23.lower,
        "gbd23_hi": n23.upper,
        "asr21": a21.val,
        "asr21_lo": a21.lower,
        "asr21_hi": a21.upper,
        "asr23": a23.val,
        "asr23_lo": a23.lower,
        "asr23_hi": a23.upper,
    }
)
reg_rev["change"] = reg_rev.gbd23 - reg_rev.gbd21
reg_rev["count_revision_pct"] = 100 * (reg_rev.gbd23 / reg_rev.gbd21 - 1)
reg_rev["share_of_net_change"] = 100 * reg_rev.change / reg_rev.change.sum()
reg_rev["asr_revision_pct"] = 100 * (reg_rev.asr23 / reg_rev.asr21 - 1)
reg_rev["outside_both"] = [
    outside(r.asr21, r.asr21_lo, r.asr21_hi, r.asr23, r.asr23_lo, r.asr23_hi)
    for r in reg_rev.itertuples()
]
reg_rev = reg_rev.sort_values("change")
reg_rev.to_csv(OUT + "regional_revision_2021.csv")
S["regional"] = dict(
    net_change=float(reg_rev.change.sum()),
    gbd21_total=float(reg_rev.gbd21.sum()),
    gbd23_total=float(reg_rev.gbd23.sum()),
    n_outside=int(reg_rev.outside_both.sum()),
    rows=reg_rev.round(4)
    .reset_index()
    .rename(columns={"index": "location"})
    .to_dict("records"),
)

a21 = pd.read_csv(DATA + "IHME-GBD_2021_DATA-31a816dc-1.csv")
a23 = pd.read_csv(DATA + "IHME-GBD_2023_DATA-35224841-1.csv")
a23 = a23[(a23.year == 2021) & a23.age_name.isin(a21.age_name.unique())]
k = ["sex_name", "age_name", "metric_name"]
age = a21[k + ["val", "lower", "upper"]].merge(
    a23[k + ["val", "lower", "upper"]], on=k, suffixes=("_21", "_23")
)
rate = age[age.metric_name == "Rate"].copy()
rate["revision_pct"] = 100 * (rate.val_23 / rate.val_21 - 1)
rate["outside_both"] = [
    outside(r.val_21, r.lower_21, r.upper_21, r.val_23, r.lower_23, r.upper_23)
    for r in rate.itertuples()
]
num = age[age.metric_name == "Number"].groupby("age_name")[["val_21", "val_23"]].sum()
num["change"] = num.val_23 - num.val_21
num["share_of_net_change"] = 100 * num.change / num.change.sum()
rate["a0"] = rate.age_name.str.extract(r"^(\d+)").astype(int)
rate = rate.sort_values(["sex_name", "a0"])
rate.to_csv(OUT + "age_revision_2021.csv", index=False)
num.to_csv(OUT + "age_revision_counts_2021.csv")
S["age"] = dict(
    rate_revision=rate.pivot_table(
        index="a0", columns="sex_name", values="revision_pct"
    )
    .round(2)
    .to_dict(),
    outside=int(rate.outside_both.sum()),
    n=int(len(rate)),
    share=num.share_of_net_change.round(2).to_dict(),
)


def series(loc, m="Prev", agename="Age-standardized", metric="Rate"):
    x = reg[
        (reg.location_name == loc)
        & (reg.m == m)
        & (reg.age_name == agename)
        & (reg.metric_name == metric)
        & (reg.sex_name == "Both")
    ]
    return x.sort_values("year").set_index("year").val


brk = []
for loc in ["Global", "High-income"]:
    s = series(loc)
    t = s.index.values.astype(float)
    y = np.log(s.values)
    X = np.vstack([np.ones_like(t), t, np.clip(t - 2006, 0, None)]).T
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ beta
    cov = (res @ res) / (len(y) - 3) * np.linalg.inv(X.T @ X)
    f = lambda b: 100 * (math.exp(b) - 1)
    se = math.sqrt(cov[2, 2])
    brk.append(
        dict(
            location=loc,
            apc_before=f(beta[1]),
            apc_after=f(beta[1] + beta[2]),
            slope_change_pp=100 * beta[2],
            change_lo=100 * (beta[2] - 1.96 * se),
            change_hi=100 * (beta[2] + 1.96 * se),
        )
    )
brk = pd.DataFrame(brk)
brk.to_csv(OUT + "break_2006.csv", index=False)
S["break_2006"] = brk.round(3).to_dict("records")

locs = [
    "Global",
    "Central Europe, Eastern Europe, and Central Asia",
    "High-income",
    "Latin America and Caribbean",
    "North Africa and Middle East",
    "South Asia",
    "Southeast Asia, East Asia, and Oceania",
    "Sub-Saharan Africa",
]
mix = []
for loc in locs:
    d = {
        y: series(loc, "DALY", "All ages", "Number")[y]
        / series(loc, "Prev", "All ages", "Number")[y]
        for y in (1990, 2023)
    }
    mix.append(
        dict(
            location=loc,
            dalys_per_case_1990=d[1990],
            dalys_per_case_2023=d[2023],
            change_pct=100 * (d[2023] / d[1990] - 1),
        )
    )
mix = pd.DataFrame(mix)
mix.to_csv(OUT + "severity_mix_index.csv", index=False)
S["severity_mix"] = mix.round(4).to_dict("records")
S["global_flags"] = glob.round(4).to_dict("records")
json.dump(S, open(OUT + "revision_statistics.json", "w"), indent=1, default=float)
