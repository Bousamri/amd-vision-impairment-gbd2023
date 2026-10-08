import itertools
import json
import math
import os
import numpy as np
import pandas as pd

DATA = "data/"
OUT = "output/"
os.makedirs(OUT + "figures", exist_ok=True)
reg = pd.read_csv(DATA + "IHME-GBD_2023_DATA-67c190e0-1.csv")
cty = pd.read_csv(DATA + "IHME-GBD_2023_DATA-c8589e17-1.csv")
age = pd.read_csv(DATA + "IHME-GBD_2023_DATA-35224841-1.csv")
for d in (reg, cty, age):
    d["measure"] = d.measure_name.map(
        {"Prevalence": "prev", "DALYs (Disability-Adjusted Life Years)": "daly"}
    )

ROWS = [
    ("Global", "Both", "Global"),
    ("Female", "Female", "Global"),
    ("Male", "Male", "Global"),
    ("High SDI", "Both", "High SDI"),
    ("High-middle SDI", "Both", "High-middle SDI"),
    ("Middle SDI", "Both", "Middle SDI"),
    ("Low-middle SDI", "Both", "Low-middle SDI"),
    ("Low SDI", "Both", "Low SDI"),
    (
        "Central Europe, Eastern Europe, and Central Asia",
        "Both",
        "Central Europe, Eastern Europe, and Central Asia",
    ),
    ("High-income", "Both", "High-income"),
    ("Latin America and Caribbean", "Both", "Latin America and Caribbean"),
    ("North Africa and Middle East", "Both", "North Africa and Middle East"),
    ("South Asia", "Both", "South Asia"),
    (
        "Southeast Asia, East Asia, and Oceania",
        "Both",
        "Southeast Asia, East Asia, and Oceania",
    ),
    ("Sub-Saharan Africa", "Both", "Sub-Saharan Africa"),
]


def pick(d, loc, sex, measure, agename, metric, year=None):
    x = d[
        (d.location_name == loc)
        & (d.sex_name == sex)
        & (d.measure == measure)
        & (d.age_name == agename)
        & (d.metric_name == metric)
    ]
    if year is not None:
        x = x[x.year == year]
    return x.sort_values("year")


PC = pd.concat(
    [
        pd.read_csv(DATA + "IHME-GBD_2023_DATA-334dcb5b-1.csv"),
        pd.read_csv(DATA + "IHME-GBD_2023_DATA-8c88aea3-1.csv"),
    ]
)
PC["measure"] = PC.measure_name.map(
    {"Prevalence": "prev", "DALYs (Disability-Adjusted Life Years)": "daly"}
)


def pct(loc, measure, agename, metric):
    x = PC[
        (PC.location_name == loc)
        & (PC.measure == measure)
        & (PC.age_name == agename)
        & (PC.metric_name == metric)
    ]
    if len(x) == 0:
        return (np.nan, np.nan)
    r = x.iloc[0]
    return (100 * r.lower, 100 * r.upper)


def build_table(measure):
    recs = []
    for label, sex, loc in ROWS:
        n90 = pick(reg, loc, sex, measure, "All ages", "Number", 1990).iloc[0]
        n23 = pick(reg, loc, sex, measure, "All ages", "Number", 2023).iloc[0]
        a90 = pick(reg, loc, sex, measure, "Age-standardized", "Rate", 1990).iloc[0]
        a23 = pick(reg, loc, sex, measure, "Age-standardized", "Rate", 2023).iloc[0]
        clo, chi = (
            pct(loc, measure, "All ages", "Number")
            if sex == "Both"
            else (np.nan, np.nan)
        )
        alo, ahi = (
            pct(loc, measure, "Age-standardized", "Rate")
            if sex == "Both"
            else (np.nan, np.nan)
        )
        chg = 100 * (n23.val / n90.val - 1)
        achg = 100 * (a23.val / a90.val - 1)
        recs.append(
            dict(
                location=label,
                n1990=n90.val,
                n1990_lo=n90.lower,
                n1990_hi=n90.upper,
                n2023=n23.val,
                n2023_lo=n23.lower,
                n2023_hi=n23.upper,
                count_change_pct=chg,
                count_change_lo=clo,
                count_change_hi=chi,
                asr1990=a90.val,
                asr1990_lo=a90.lower,
                asr1990_hi=a90.upper,
                asr2023=a23.val,
                asr2023_lo=a23.lower,
                asr2023_hi=a23.upper,
                asr_change_pct=achg,
                asr_change_lo=alo,
                asr_change_hi=ahi,
            )
        )
    return pd.DataFrame(recs)


t1 = build_table("prev")
s1 = build_table("daly")
t1.to_csv(OUT + "prevalence_by_location.csv", index=False)
s1.to_csv(OUT + "dalys_by_location.csv", index=False)


def cty_val(measure, agename, metric, year, col="val"):
    x = cty[
        (cty.measure == measure)
        & (cty.age_name == agename)
        & (cty.metric_name == metric)
        & (cty.year == year)
    ]
    return x.set_index("location_name")[col]


C = pd.DataFrame(
    {
        "cases_1990": cty_val("prev", "All ages", "Number", 1990),
        "cases_2023": cty_val("prev", "All ages", "Number", 2023),
        "cases_2023_lo": cty_val("prev", "All ages", "Number", 2023, "lower"),
        "cases_2023_hi": cty_val("prev", "All ages", "Number", 2023, "upper"),
        "aspr_1990": cty_val("prev", "Age-standardized", "Rate", 1990),
        "aspr_2023": cty_val("prev", "Age-standardized", "Rate", 2023),
        "aspr_2023_lo": cty_val("prev", "Age-standardized", "Rate", 2023, "lower"),
        "aspr_2023_hi": cty_val("prev", "Age-standardized", "Rate", 2023, "upper"),
        "dalys_2023": cty_val("daly", "All ages", "Number", 2023),
        "asdr_1990": cty_val("daly", "Age-standardized", "Rate", 1990),
        "asdr_2023": cty_val("daly", "Age-standardized", "Rate", 2023),
    }
)
C["aspr_change_pct"] = 100 * (C.aspr_2023 / C.aspr_1990 - 1)
C["asdr_change_pct"] = 100 * (C.asdr_2023 / C.asdr_1990 - 1)
C["cases_change_pct"] = 100 * (C.cases_2023 / C.cases_1990 - 1)
C.round(3).to_csv(OUT + "country_estimates.csv")

a = age[age.age_name != "All ages"].copy()
a["a0"] = a.age_name.str.extract(r"^(\d+)").astype(int)
num = a[a.metric_name == "Number"].pivot_table(
    index=["sex_name", "a0"], columns="year", values="val"
)
rate = a[a.metric_name == "Rate"].pivot_table(
    index=["sex_name", "a0"], columns="year", values="val"
)
allage = age[age.age_name == "All ages"]
N_sex = {
    s: (
        allage[(allage.sex_name == s) & (allage.metric_name == "Number")]
        .set_index("year")
        .val
        / allage[(allage.sex_name == s) & (allage.metric_name == "Rate")]
        .set_index("year")
        .val
        * 1e5
    )
    for s in ["Male", "Female"]
}
Ntot = N_sex["Male"] + N_sex["Female"]
pop = num / rate * 1e5
pop = pop.fillna(0)


def decompose(y1, y2):
    idx = rate.index[rate.index.get_level_values("a0") >= 45]
    fac = {
        1: dict(N=Ntot[y1], s=(pop.loc[idx, y1] / Ntot[y1]), r=rate.loc[idx, y1] / 1e5),
        2: dict(N=Ntot[y2], s=(pop.loc[idx, y2] / Ntot[y2]), r=rate.loc[idx, y2] / 1e5),
    }

    def f(sel):
        return fac[sel["N"]]["N"] * (fac[sel["s"]]["s"] * fac[sel["r"]]["r"]).sum()

    names = ["N", "s", "r"]
    contrib = {k: 0.0 for k in names}
    for k in names:
        others = [x for x in names if x != k]
        for m in range(len(others) + 1):
            for S in itertools.combinations(others, m):
                w = (
                    math.factorial(len(S))
                    * math.factorial(len(names) - len(S) - 1)
                    / math.factorial(len(names))
                )
                base = {x: (2 if x in S else 1) for x in names}
                with_k = dict(base)
                with_k[k] = 2
                contrib[k] += w * (f(with_k) - f(base))
    total = f({"N": 2, "s": 2, "r": 2}) - f({"N": 1, "s": 1, "r": 1})
    return total, contrib


tot, con = decompose(1990, 2023)

R = {}
g = t1.set_index("location")
R["global"] = g.loc["Global"].to_dict()
R["female"] = g.loc["Female"].to_dict()
R["male"] = g.loc["Male"].to_dict()
R["dalys_global"] = s1.set_index("location").loc["Global"].to_dict()
R["dalys_female"] = s1.set_index("location").loc["Female"].to_dict()
R["dalys_male"] = s1.set_index("location").loc["Male"].to_dict()
R["sdi"] = (
    g.loc[
        ["High SDI", "High-middle SDI", "Middle SDI", "Low-middle SDI", "Low SDI"],
        [
            "asr2023",
            "asr2023_lo",
            "asr2023_hi",
            "asr_change_pct",
            "asr_change_lo",
            "asr_change_hi",
            "n2023",
            "count_change_pct",
        ],
    ]
    .round(3)
    .to_dict("index")
)
R["super"] = (
    g.iloc[8:][
        [
            "asr2023",
            "asr2023_lo",
            "asr2023_hi",
            "asr_change_pct",
            "asr_change_lo",
            "asr_change_hi",
            "n2023",
            "count_change_pct",
        ]
    ]
    .round(3)
    .to_dict("index")
)
R["sdi_dalys"] = (
    s1.set_index("location")
    .loc[["High SDI", "Low SDI", "Low-middle SDI"], ["asr2023", "asr_change_pct"]]
    .round(3)
    .to_dict("index")
)
R["decomp_1990_2023"] = dict(total=tot, **con)
R["countries"] = dict(
    top_aspr=C.aspr_2023.sort_values(ascending=False).head(6).round(1).to_dict(),
    bottom_aspr=C.aspr_2023.sort_values().head(6).round(1).to_dict(),
    top_cases=(C.cases_2023.sort_values(ascending=False).head(5) / 1e6)
    .round(3)
    .to_dict(),
    top3_share=float(
        C.cases_2023.sort_values(ascending=False).head(3).sum() / C.cases_2023.sum()
    ),
    n_increase=int((C.aspr_change_pct > 0).sum()),
    n_decrease=int((C.aspr_change_pct < 0).sum()),
    largest_increase=C.aspr_change_pct.sort_values(ascending=False)
    .head(5)
    .round(1)
    .to_dict(),
    largest_decrease=C.aspr_change_pct.sort_values().head(5).round(1).to_dict(),
    aspr_ratio_max_min=float(C.aspr_2023.max() / C.aspr_2023.min()),
)
cases23 = num[2023]
R["age"] = dict(
    peak_group_both=int(cases23.groupby(level="a0").sum().idxmax()),
    peak_group_cases=float(cases23.groupby(level="a0").sum().max()),
    share_70plus=float(
        cases23[cases23.index.get_level_values("a0") >= 70].sum() / cases23.sum()
    ),
    share_female=float(cases23["Female"].sum() / cases23.sum()),
    rate_female_95=float(rate.loc[("Female", 95), 2023]),
    rate_male_95=float(rate.loc[("Male", 95), 2023]),
    rate_female_50=float(rate.loc[("Female", 50), 2023]),
    rate_male_50=float(rate.loc[("Male", 50), 2023]),
    female_male_rate_ratio_by_age=(rate.loc["Female", 2023] / rate.loc["Male", 2023])
    .round(3)
    .to_dict(),
    cases_by_age_sex=(cases23.unstack(0) / 1e3).round(1).to_dict(),
)
open(OUT + "descriptive_statistics.json", "w").write(
    json.dumps(R, indent=1, default=float)
)

g21 = pd.read_csv(DATA + "IHME-GBD_2021_DATA-48f5d8d4-1.csv").assign(round="GBD2021")
g23 = pd.read_csv(DATA + "IHME-GBD_2023_DATA-8a125c94-1.csv").assign(round="GBD2023")
comb = pd.concat([g21, g23], ignore_index=True)
comb["m"] = comb.measure_name.str[:4]
comb["key"] = (
    comb.m + np.where(comb.age_name == "All ages", "_n_", "_as_") + comb.metric_name
)
comb.to_pickle(OUT + "gbd2021_gbd2023_global.pkl")
c21 = comb[
    (comb.year == 2021) & (comb.age_name == "All ages") & (comb.metric_name == "Number")
]
c21 = c21[["round", "cause_name", "measure_name", "val", "lower", "upper"]]
c21.sort_values(["cause_name", "measure_name", "round"]).to_csv(
    OUT + "causes_2021.csv", index=False
)
