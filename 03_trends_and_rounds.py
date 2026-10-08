import itertools, json, math, runpy
import numpy as np
import pandas as pd

DATA = "data/"
OUT = "output/"
reg = pd.read_csv(DATA + "IHME-GBD_2023_DATA-67c190e0-1.csv")
cty = pd.read_csv(DATA + "IHME-GBD_2023_DATA-c8589e17-1.csv")
imp23 = pd.read_csv(DATA + "IHME-GBD_2023_DATA-7c64da8e-1.csv")
imp21 = pd.read_csv(DATA + "IHME-GBD_2021_DATA-110219a5-1.csv")
for d in (reg, cty, imp23, imp21):
    d["m"] = d.measure_name.str[:4]
N = {}


def ser(loc, m="Prev", age="Age-standardized", met="Rate", sex="Both"):
    x = reg[
        (reg.location_name == loc)
        & (reg.m == m)
        & (reg.age_name == age)
        & (reg.metric_name == met)
        & (reg.sex_name == sex)
    ]
    return x.sort_values("year").set_index("year")


def fit(t, y, taus):
    X = [np.ones_like(t), t] + [np.clip(t - tau, 0, None) for tau in taus]
    X = np.vstack(X).T
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ beta
    return beta, X, float(res @ res)


def joinpoint(years, vals, kmax=3, minseg=4):
    t = np.asarray(years, float)
    y = np.log(np.asarray(vals, float))
    n = len(t)
    best = None
    for k in range(kmax + 1):
        cand = [c for c in t[1:-1] if c - t[0] >= minseg and t[-1] - c >= minseg]
        bestk = None
        for taus in itertools.combinations(cand, k):
            if any(b - a < minseg for a, b in zip(taus, taus[1:])):
                continue
            beta, X, rss = fit(t, y, taus)
            if bestk is None or rss < bestk[2]:
                bestk = (taus, beta, rss, X)
        taus, beta, rss, X = bestk
        p = 2 + 2 * k
        bic = n * math.log(rss / n) + p * math.log(n)
        if best is None or bic < best["bic"]:
            best = dict(k=k, taus=taus, beta=beta, rss=rss, X=X, bic=bic)
    taus, beta, X, rss = best["taus"], best["beta"], best["X"], best["rss"]
    p = X.shape[1]
    s2 = rss / (n - p - len(taus))
    cov = s2 * np.linalg.inv(X.T @ X)
    bounds = [t[0]] + list(taus) + [t[-1]]
    segs, slopes, lens, avecs = [], [], [], []
    for i in range(len(bounds) - 1):
        a = np.zeros(p)
        a[1] = 1
        a[2 : 2 + i] = 1
        sl = a @ beta
        se = math.sqrt(a @ cov @ a)
        f = lambda b: 100 * (math.exp(b) - 1)
        segs.append(
            dict(
                start=int(bounds[i]),
                end=int(bounds[i + 1]),
                apc=f(sl),
                lo=f(sl - 1.96 * se),
                hi=f(sl + 1.96 * se),
            )
        )
        slopes.append(sl)
        lens.append(bounds[i + 1] - bounds[i])
        avecs.append(a)
    w = np.array(lens) / sum(lens)
    aa = sum(wi * ai for wi, ai in zip(w, avecs))
    sl = aa @ beta
    se = math.sqrt(aa @ cov @ aa)
    f = lambda b: 100 * (math.exp(b) - 1)
    fitted = np.exp(X @ beta)
    return dict(
        k=best["k"],
        joinpoints=[int(x) for x in taus],
        segments=segs,
        aapc=f(sl),
        aapc_lo=f(sl - 1.96 * se),
        aapc_hi=f(sl + 1.96 * se),
        fitted=fitted.tolist(),
        years=[int(x) for x in t],
        observed=list(map(float, vals)),
    )


JP_LOCS = [
    "Global",
    "Central Europe, Eastern Europe, and Central Asia",
    "High-income",
    "Latin America and Caribbean",
    "North Africa and Middle East",
    "South Asia",
    "Southeast Asia, East Asia, and Oceania",
    "Sub-Saharan Africa",
]
jp = {}
rows = []
for loc in JP_LOCS:
    s = ser(loc)
    r = joinpoint(s.index.values, s.val.values)
    jp[loc] = r
    segtxt = "; ".join(
        f"{g['start']}–{g['end']}: {g['apc']:.2f} ({g['lo']:.2f} to {g['hi']:.2f})"
        for g in r["segments"]
    )
    rows.append(
        dict(
            location=loc,
            joinpoints=", ".join(map(str, r["joinpoints"])) or "none",
            segments=segtxt,
            aapc=f"{r['aapc']:.2f} ({r['aapc_lo']:.2f} to {r['aapc_hi']:.2f})",
        )
    )
pd.DataFrame(rows).to_csv(OUT + "joinpoint.csv", index=False)
N["joinpoint"] = {
    k: {
        kk: v[kk]
        for kk in ("k", "joinpoints", "segments", "aapc", "aapc_lo", "aapc_hi")
    }
    for k, v in jp.items()
}
json.dump(
    {
        k: {kk: v[kk] for kk in ("years", "observed", "fitted", "joinpoints")}
        for k, v in jp.items()
    },
    open(OUT + "joinpoint_fits.json", "w"),
)

sev = ["Moderate vision loss", "Severe vision loss", "Blindness"]


def imp_tab(d):
    p = d.pivot_table(
        index=["cause_name", "rei_name"], columns="m", values=["val", "lower", "upper"]
    )
    return p


t21, t23 = imp_tab(imp21), imp_tab(imp23)
sev_rows = []
for cause in ["Age-related macular degeneration", "All causes"]:
    for s in sev + ["Total"]:
        rec = dict(cause=cause, severity=s)
        for lab, t in (("GBD2021", t21), ("GBD2023", t23)):
            if s == "Total":
                rec[f"{lab}_prev"] = sum(
                    t.loc[(cause, x), ("val", "Prev")] for x in sev
                )
                rec[f"{lab}_yld"] = sum(t.loc[(cause, x), ("val", "YLDs")] for x in sev)
                rec[f"{lab}_prev_lo"] = rec[f"{lab}_prev_hi"] = np.nan
            else:
                rec[f"{lab}_prev"] = t.loc[(cause, s), ("val", "Prev")]
                rec[f"{lab}_prev_lo"] = t.loc[(cause, s), ("lower", "Prev")]
                rec[f"{lab}_prev_hi"] = t.loc[(cause, s), ("upper", "Prev")]
                rec[f"{lab}_yld"] = t.loc[(cause, s), ("val", "YLDs")]
        rec["prev_revision_pct"] = 100 * (rec["GBD2023_prev"] / rec["GBD2021_prev"] - 1)
        rec["yld_revision_pct"] = 100 * (rec["GBD2023_yld"] / rec["GBD2021_yld"] - 1)
        rec["yld_per_case_21"] = rec["GBD2021_yld"] / rec["GBD2021_prev"]
        rec["yld_per_case_23"] = rec["GBD2023_yld"] / rec["GBD2023_prev"]
        sev_rows.append(rec)
sevdf = pd.DataFrame(sev_rows)
sevdf.to_csv(OUT + "severity_2021.csv", index=False)
a = sevdf.set_index(["cause", "severity"])
amd = "Age-related macular degeneration"
N["severity"] = dict(
    mod21=a.loc[(amd, "Moderate vision loss"), "GBD2021_prev"],
    mod23=a.loc[(amd, "Moderate vision loss"), "GBD2023_prev"],
    sev21=a.loc[(amd, "Severe vision loss"), "GBD2021_prev"],
    sev23=a.loc[(amd, "Severe vision loss"), "GBD2023_prev"],
    bl21=a.loc[(amd, "Blindness"), "GBD2021_prev"],
    bl23=a.loc[(amd, "Blindness"), "GBD2023_prev"],
    mod_rev=a.loc[(amd, "Moderate vision loss"), "prev_revision_pct"],
    sev_rev=a.loc[(amd, "Severe vision loss"), "prev_revision_pct"],
    bl_rev=a.loc[(amd, "Blindness"), "prev_revision_pct"],
    mod_share_of_revision=100
    * (
        a.loc[(amd, "Moderate vision loss"), "GBD2023_prev"]
        - a.loc[(amd, "Moderate vision loss"), "GBD2021_prev"]
    )
    / (a.loc[(amd, "Total"), "GBD2023_prev"] - a.loc[(amd, "Total"), "GBD2021_prev"]),
    mod_pct21=100
    * a.loc[(amd, "Moderate vision loss"), "GBD2021_prev"]
    / a.loc[(amd, "Total"), "GBD2021_prev"],
    mod_pct23=100
    * a.loc[(amd, "Moderate vision loss"), "GBD2023_prev"]
    / a.loc[(amd, "Total"), "GBD2023_prev"],
    all_total21=a.loc[("All causes", "Total"), "GBD2021_prev"],
    all_total23=a.loc[("All causes", "Total"), "GBD2023_prev"],
    all_total_rev=a.loc[("All causes", "Total"), "prev_revision_pct"],
    all_yld_rev=a.loc[("All causes", "Total"), "yld_revision_pct"],
    all_bl_rev=a.loc[("All causes", "Blindness"), "prev_revision_pct"],
    all_mod_rev=a.loc[("All causes", "Moderate vision loss"), "prev_revision_pct"],
    amd_bl_share21=100
    * a.loc[(amd, "Blindness"), "GBD2021_prev"]
    / a.loc[("All causes", "Blindness"), "GBD2021_prev"],
    amd_bl_share23=100
    * a.loc[(amd, "Blindness"), "GBD2023_prev"]
    / a.loc[("All causes", "Blindness"), "GBD2023_prev"],
    dw21=[a.loc[(amd, s), "yld_per_case_21"] for s in sev],
    dw23=[a.loc[(amd, s), "yld_per_case_23"] for s in sev],
)

ns = runpy.run_path("02_projection.py", run_name="projection")
rate, rlo, rhi, P, slopes, pop_gbd, cases = (
    ns["rate"],
    ns["rlo"],
    ns["rhi"],
    ns["P"],
    ns["slopes"],
    ns["pop_gbd"],
    ns["cases"],
)
pub_proj, wpp_tot, out = ns["pub_proj"], ns["wpp_tot"], ns["out"]
b90, b13 = slopes(1990, 2023), slopes(2013, 2023)
pd.DataFrame(
    {
        "rate_2023": rate[2023],
        "rate_2023_lo": rlo[2023],
        "rate_2023_hi": rhi[2023],
        "annual_change_1990_2023": 100 * (np.exp(b90) - 1),
        "annual_change_2013_2023": 100 * (np.exp(b13) - 1),
    }
).rename_axis(["sex", "age_group_start"]).round(4).to_csv(
    OUT + "age_sex_rates_2023.csv"
)
anch19 = rate[2019]
anchmean = rate[[2019, 2020, 2021, 2022, 2023]].mean(axis=1)
proj = []
for y in [2030, 2040, 2050]:
    for sexsel in ["Female", "Male", "Both sexes"]:
        pick = (lambda s: s) if sexsel == "Both sexes" else (lambda s: s.loc[sexsel])

        def tot(r):
            v = r / 1e5 * P[y]
            return float(
                pick(v.groupby(level=0).sum()).sum()
                if sexsel == "Both sexes"
                else v.groupby(level=0).sum()[sexsel]
            )

        proj.append(
            dict(
                year=y,
                sex=sexsel,
                ref=tot(rate[2023]),
                lo=tot(rlo[2023]),
                hi=tot(rhi[2023]),
                trend90=tot(rate[2023] * np.exp(b90 * (y - 2023))),
                trend13=tot(rate[2023] * np.exp(b13 * (y - 2023))),
                anchor2019=tot(anch19),
                anchor1923=tot(anchmean),
            )
        )
projdf = pd.DataFrame(proj)
projdf.to_csv(OUT + "projections_by_scenario.csv", index=False)
pj = projdf[projdf.sex == "Both sexes"].set_index("year")
c23 = cases(rate[2023], pop_gbd[2023])
N["projection"] = pj.round(3).to_dict("index")
N["proj_2050_pct_increase"] = 100 * (pj.loc[2050, "ref"] / c23 - 1)

N1, N2 = wpp_tot.loc[2023].sum(), wpp_tot.loc[2050].sum()
c50 = pj.loc[2050, "ref"]
growth = 0.5 * ((N2 / N1 - 1) * c23 + (1 - N1 / N2) * c50)
N["decomp_2023_2050"] = dict(
    total=c50 - c23,
    growth=growth,
    aging=c50 - c23 - growth,
    growth_pct=100 * growth / (c50 - c23),
    aging_pct=100 * (1 - growth / (c50 - c23)),
)
N["bounds"] = dict(
    ui_ratio=(5.298 / 6.306, 7.471 / 6.306),
    bound_ratio_2050=(pj.loc[2050, "lo"] / c50, pj.loc[2050, "hi"] / c50),
)

imp = pub_proj.m_n * 1e6 / (pub_proj.m_rate / 1e5) + pub_proj.f_n * 1e6 / (
    pub_proj.f_rate / 1e5
)
pub = pd.DataFrame(
    {
        "published_M": pub_proj.total / 1e6,
        "implied_pop_B": imp / 1e9,
        "implied_allage_rate": pub_proj.total / imp * 1e5,
    }
)
pub["wpp_pop_B"] = (wpp_tot.sum(axis=1) / 1e9).reindex(pub.index)
pub["rate_consistent_M"] = (
    pub_proj.m_rate / 1e5 * wpp_tot.popM.reindex(pub.index)
    + pub_proj.f_rate / 1e5 * wpp_tot.popF.reindex(pub.index)
) / 1e6
refser = pd.Series(
    {y: out.loc[y, "New_constant_rates"] / 1e6 for y in range(2021, 2051)}
)
pub["updated_ref_M"] = refser.reindex(pub.index)
pub["rate_consistent_vs_ref_pct"] = 100 * (
    pub.rate_consistent_M / pub.updated_ref_M - 1
)
pub.round(4).to_csv(OUT + "published_projection_check.csv")
N["published"] = pub.loc[[2021, 2022, 2023, 2030, 2040, 2050]].round(3).to_dict("index")
N["published_rate_growth_2023_2050"] = 100 * (
    pub.loc[2050, "implied_allage_rate"] / pub.loc[2023, "implied_allage_rate"] - 1
)
gbd_allage = (
    reg[
        (reg.location_name == "Global")
        & (reg.m == "Prev")
        & (reg.age_name == "All ages")
        & (reg.metric_name == "Rate")
        & (reg.sex_name == "Both")
    ]
    .set_index("year")
    .val
)
N["ref_crude_2023"] = float(gbd_allage[2023])
N["ref_crude_2050"] = float(c50 / N2 * 1e5)
N["ref_crude_growth"] = 100 * (N["ref_crude_2050"] / N["ref_crude_2023"] - 1)

dpc = {}
for loc in JP_LOCS:
    d = [
        ser(loc, "DALY", "All ages", "Number").loc[y, "val"]
        / ser(loc, "Prev", "All ages", "Number").loc[y, "val"]
        for y in (1990, 2023)
    ]
    dpc[loc] = 100 * (d[1] / d[0] - 1)
N["daly_per_case_change"] = dpc
cs = cty[(cty.m == "Prev") & (cty.age_name == "Age-standardized")].pivot_table(
    index="location_name", columns="year", values="val"
)
cs["chg"] = 100 * (cs[2023] / cs[1990] - 1)
west = [
    "Benin",
    "Burkina Faso",
    "Côte d'Ivoire",
    "Gambia",
    "Ghana",
    "Guinea",
    "Guinea-Bissau",
    "Mali",
    "Niger",
    "Nigeria",
    "Togo",
    "Cabo Verde",
    "Liberia",
    "Mauritania",
    "Senegal",
    "Sierra Leone",
    "Sao Tome and Principe",
    "Chad",
    "Cameroon",
]
rising = cs.index[cs.chg > 0].tolist()
N["rising"] = rising
N["rising_west"] = [c for c in rising if c in west]
N["usa_can"] = (
    float(cs.loc["United States of America", 2023]),
    float(cs.loc["Canada", 2023]),
)
lac_cases = ser("Latin America and Caribbean", "Prev", "All ages", "Number").loc[
    2023, "val"
]
br = cty[
    (cty.location_name == "Brazil")
    & (cty.m == "Prev")
    & (cty.age_name == "All ages")
    & (cty.metric_name == "Number")
    & (cty.year == 2023)
].val.iloc[0]
N["brazil"] = dict(
    share=100 * br / lac_cases,
    aspr=float(cs.loc["Brazil", 2023]),
    chg=float(cs.loc["Brazil", "chg"]),
    lac_asdr_chg=100
    * (
        ser("Latin America and Caribbean", "DALY").loc[2023, "val"]
        / ser("Latin America and Caribbean", "DALY").loc[1990, "val"]
        - 1
    ),
)
N["highsdi_vs_hi"] = dict(
    high_sdi_chg=100
    * (ser("High SDI").loc[2023, "val"] / ser("High SDI").loc[1990, "val"] - 1),
    high_income_chg=100
    * (ser("High-income").loc[2023, "val"] / ser("High-income").loc[1990, "val"] - 1),
)
json.dump(N, open(OUT + "summary_statistics.json", "w"), indent=1, default=float)
