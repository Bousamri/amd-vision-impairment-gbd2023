import numpy as np
import pandas as pd
import pyreadr

DATA = "data/"
OUT = "output/"

g = pd.read_csv(DATA + "IHME-GBD_2023_DATA-35224841-1.csv")
g = g[g.age_name != "All ages"].copy()
g["a0"] = g.age_name.str.extract(r"^(\d+)").astype(int)
g = g[g.a0 >= 45]
num = g[g.metric_name == "Number"].pivot_table(
    index=["sex_name", "a0"], columns="year", values="val"
)
rate = g[g.metric_name == "Rate"].pivot_table(
    index=["sex_name", "a0"], columns="year", values="val"
)
rlo = g[g.metric_name == "Rate"].pivot_table(
    index=["sex_name", "a0"], columns="year", values="lower"
)
rhi = g[g.metric_name == "Rate"].pivot_table(
    index=["sex_name", "a0"], columns="year", values="upper"
)
pop_gbd = num / rate * 1e5

est = pyreadr.read_r(DATA + "popAge1dt.rda")["popAge1dt"]
prj = pyreadr.read_r(DATA + "popprojAge1dt.rda")["popprojAge1dt"]
prj["year"] = prj.year.astype(int)
est = est[est.country_code == 900][["year", "age", "popM", "popF"]]
prj = prj[prj.country_code == 900][["year", "age", "popM", "popF"]]
w = pd.concat([est, prj])
w = w[(w.year >= 1990) & (w.year <= 2050)]
wpp_tot = w.groupby("year")[["popM", "popF"]].sum() * 1000
w["a0"] = np.minimum((w.age // 5) * 5, 95)
w = w[w.a0 >= 45]
wl = w.melt(
    id_vars=["year", "a0"], value_vars=["popM", "popF"], var_name="s", value_name="pop"
)
wl["sex_name"] = wl.s.map({"popM": "Male", "popF": "Female"})
wpp = wl.groupby(["sex_name", "a0", "year"])["pop"].sum().unstack("year") * 1000
wpp_tot = (wpp_tot + wpp_tot.shift(1)) / 2
wpp = (wpp + wpp.shift(1, axis=1)) / 2
wpp = wpp.reindex(rate.index)

YEARS = list(range(2024, 2051))

P = pd.DataFrame({y: pop_gbd[2023] * wpp[y] / wpp[2023] for y in YEARS})


def cases(rates, pop):
    return (rates / 1e5 * pop).sum()


A = pd.Series({y: cases(rate[2023], P[y]) for y in YEARS})
A_lo = pd.Series({y: cases(rlo[2023], P[y]) for y in YEARS})
A_hi = pd.Series({y: cases(rhi[2023], P[y]) for y in YEARS})


def slopes(start, end):
    yrs = np.arange(start, end + 1)
    out = {}
    for idx in rate.index:
        y = np.log(rate.loc[idx, yrs].values)
        out[idx] = np.polyfit(yrs, y, 1)[0]
    return pd.Series(out)


def trend_proj(start, end, base_year=2023, years=YEARS, pop=P):
    b = slopes(start, end)
    return pd.Series(
        {y: cases(rate[base_year] * np.exp(b * (y - base_year)), pop[y]) for y in years}
    )


B_long = trend_proj(1990, 2023)
B_recent = trend_proj(2013, 2023)

b13 = slopes(1990, 2013)
pred2023_trend = cases(rate[2013] * np.exp(b13 * 10), pop_gbd[2023])
pred2023_const = cases(rate[2013], pop_gbd[2023])
actual2023 = num[2023].sum()

pub_proj = pd.read_csv(DATA + "published_projection_gbd2021.csv", index_col="year")
pub_proj["total"] = (pub_proj.m_n + pub_proj.f_n) * 1e6
pub_proj["rates_wpp"] = pub_proj.m_rate / 1e5 * wpp_tot.popM.reindex(
    pub_proj.index
) + pub_proj.f_rate / 1e5 * wpp_tot.popF.reindex(pub_proj.index)

d21 = pd.read_csv(DATA + "IHME-GBD_2021_DATA-48f5d8d4-1.csv")
d23 = pd.read_csv(DATA + "IHME-GBD_2023_DATA-8a125c94-1.csv")
sel = (
    lambda d: d[
        (d.cause_name == "Age-related macular degeneration")
        & (d.measure_name == "Prevalence")
        & (d.age_name == "All ages")
        & (d.metric_name == "Number")
    ]
    .set_index("year")
    .val
)
gbd21, gbd23 = sel(d21), sel(d23)

out = pd.DataFrame(index=range(2021, 2051))
out["published_projection"] = pub_proj.total
out["published_rates_wpp"] = pub_proj.rates_wpp
out["GBD2023_estimate"] = gbd23.reindex(out.index)
for name, s in [
    ("New_constant_rates", A),
    ("New_constant_lo", A_lo),
    ("New_constant_hi", A_hi),
    ("New_trend_1990_2023", B_long),
    ("New_trend_2013_2023", B_recent),
]:
    out[name] = s
    out.loc[[2021, 2022, 2023], name] = gbd23.loc[[2021, 2022, 2023]].values
out.to_csv(OUT + "projections.csv")
