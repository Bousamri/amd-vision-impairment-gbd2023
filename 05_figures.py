import json, runpy, textwrap
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.colors import to_hex
import numpy as np
import pandas as pd
import geopandas as gpd
from pyproj import Transformer

OUT = "output/figures/"
DATA = "data/"
RES = "output/"
plt.rcParams.update(
    {
        "font.family": "Liberation Sans",
        "font.size": 8.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "legend.frameon": False,
    }
)
RED, BLUE, DARK, GREY = "#B2182B", "#2166AC", "#333333", "#8C8C8C"
FEM, MAL, C21, C23 = "#C44E52", "#4C72B0", "#4C72B0", "#C44E52"
SAVE = dict(dpi=300, bbox_inches="tight", pad_inches=0.12)


def panel(ax, letter, x=-0.12, y=1.04):
    ax.text(
        x,
        y,
        letter,
        transform=ax.transAxes,
        fontsize=11,
        fontweight="bold",
        va="bottom",
    )


reg = pd.read_csv(DATA + "IHME-GBD_2023_DATA-67c190e0-1.csv")
age = pd.read_csv(DATA + "IHME-GBD_2023_DATA-35224841-1.csv")
R2 = json.load(open(RES + "descriptive_statistics.json"))
t1 = pd.read_csv(RES + "prevalence_by_location.csv").set_index("location")
ns = runpy.run_path("02_projection.py", run_name="projection")
out, pub_proj, wpp_tot = ns["out"], ns["pub_proj"], ns["wpp_tot"]


def series(loc, sex, measure, agename, metric):
    x = reg[
        (reg.location_name == loc)
        & (reg.sex_name == sex)
        & (reg.measure_name == measure)
        & (reg.age_name == agename)
        & (reg.metric_name == metric)
    ]
    return x.sort_values("year")


fig, ax = plt.subplots(
    1, 3, figsize=(7.6, 3.0), gridspec_kw={"width_ratios": [1, 1, 1.2]}
)
for sex, col, lab in [
    ("Both", DARK, "Both sexes"),
    ("Female", FEM, "Female"),
    ("Male", MAL, "Male"),
]:
    s = series("Global", sex, "Prevalence", "All ages", "Number")
    ax[0].fill_between(
        s.year, s.lower / 1e6, s.upper / 1e6, color=col, alpha=0.13, lw=0
    )
    ax[0].plot(s.year, s.val / 1e6, color=col, lw=1.6, label=lab)
    s = series("Global", sex, "Prevalence", "Age-standardized", "Rate")
    ax[1].fill_between(s.year, s.lower, s.upper, color=col, alpha=0.13, lw=0)
    ax[1].plot(s.year, s.val, color=col, lw=1.6)
ax[0].set_ylabel("Prevalent cases (millions)")
ax[1].set_ylabel("Age-standardized prevalence\n(per 100 000)")
ax[0].set_ylim(0, 8)
ax[1].set_ylim(0, 110)
for a_ in ax[:2]:
    a_.set_xlim(1990, 2023)
    a_.set_xticks([1990, 2000, 2010, 2020])
ax[0].legend(loc="upper left", fontsize=7.5)
d = R2["decomp_1990_2023"]
items = [
    ("Population growth", d["N"] / 1e6, "#6BAED6"),
    ("Population aging", d["s"] / 1e6, "#2171B5"),
    ("Age- and sex-specific\nprevalence", d["r"] / 1e6, "#FB6A4A"),
    ("Net change", d["total"] / 1e6, DARK),
]
yy = np.arange(len(items))[::-1]
ax[2].barh(yy, [v for _, v, _ in items], color=[c for _, _, c in items], height=0.6)
ax[2].axvline(0, color="black", lw=0.8)
for y_, (lab, v, _) in zip(yy, items):
    ax[2].text(
        max(v, 0) + 0.1,
        y_,
        f"{v:+.2f}".replace("-", "–"),
        va="center",
        ha="left",
        fontsize=7.5,
    )
ax[2].set_yticks(yy, [l for l, _, _ in items], fontsize=7.5)
ax[2].set_xlim(-0.8, 4.6)
ax[2].set_xlabel("Change in cases, 1990–2023\n(millions)")
panel(ax[0], "A", x=-0.3)
panel(ax[1], "B", x=-0.33)
panel(ax[2], "C", x=-0.55)
fig.tight_layout(w_pad=1.2)
fig.savefig(OUT + "Figure1.png", **SAVE)
plt.close(fig)

iso = pd.read_csv(DATA + "gbd_iso3.csv", index_col=0).iso3
C = pd.read_csv(RES + "country_estimates.csv", index_col=0)
C["iso"] = iso.reindex(C.index).values
w = gpd.read_file(DATA + "ne_50m_admin_0_countries.geojson")
w = w[w.ADMIN != "Antarctica"].copy()
w["iso"] = (
    w["ISO_A3_EH"]
    .where(w["ISO_A3_EH"] != "-99", w["ADM0_A3"])
    .replace({"SOL": "SOM", "CYN": "CYP"})
)
w = w.merge(C[["iso", "aspr_2023", "aspr_change_pct"]], on="iso", how="left").to_crs(
    "ESRI:54030"
)
tr = Transformer.from_crs("EPSG:4326", "ESRI:54030", always_xy=True)
bins_a = [-1e9, 25, 50, 75, 100, 125, 150, 1e9]
lab_a = [
    "<25",
    "25 to <50",
    "50 to <75",
    "75 to <100",
    "100 to <125",
    "125 to <150",
    "≥150",
]
cols_a = [to_hex(c) for c in plt.get_cmap("YlOrRd")(np.linspace(0.08, 0.95, 7))]
bins_b = [-1e9, -30, -20, -10, 0, 10, 25, 1e9]
lab_b = [
    "<–30",
    "–30 to <–20",
    "–20 to <–10",
    "–10 to <0",
    "0 to <10",
    "10 to <25",
    "≥25",
]
cols_b = [
    to_hex(c)
    for c in plt.get_cmap("RdBu_r")([0.02, 0.15, 0.28, 0.42, 0.62, 0.78, 0.95])
]
INSETS = [
    ("Caribbean", (-90, 9, -59, 27)),
    ("Gulf", (45, 22, 60, 31)),
    ("Singapore and Malay Peninsula", (99, -1, 106, 7)),
    ("Melanesia", (158, -23, 180, -8)),
]
fig = plt.figure(figsize=(7.4, 10.2))
gs = fig.add_gridspec(
    4, 4, height_ratios=[3.2, 1.05, 3.2, 1.05], hspace=0.25, wspace=0.08
)
for r0, col, bins, labs, cols, title, letter in [
    (
        0,
        "aspr_2023",
        bins_a,
        lab_a,
        cols_a,
        "Age-standardized prevalence per 100 000, 2023",
        "A",
    ),
    (
        2,
        "aspr_change_pct",
        bins_b,
        lab_b,
        cols_b,
        "Change in age-standardized prevalence, 1990–2023 (%)",
        "B",
    ),
]:
    k = pd.cut(w[col], bins=bins, labels=False, right=False)
    colors = [cols[int(i)] if pd.notna(i) else "#D9D9D9" for i in k]
    ax = fig.add_subplot(gs[r0, :])
    w.plot(ax=ax, color=colors, edgecolor="white", linewidth=0.15)
    ax.set_axis_off()
    ax.text(
        0.0,
        1.0,
        letter,
        transform=ax.transAxes,
        fontsize=11,
        fontweight="bold",
        va="top",
    )
    handles = [
        Patch(facecolor=c, edgecolor="none", label=l) for c, l in zip(cols, labs)
    ] + [Patch(facecolor="#D9D9D9", label="No data")]
    ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.02),
        ncol=8,
        fontsize=6.6,
        handlelength=1.0,
        columnspacing=0.7,
        title=title,
        title_fontsize=7.3,
    )
    for j, (name, (x0, y0, x1, y1)) in enumerate(INSETS):
        ia = fig.add_subplot(gs[r0 + 1, j])
        w.plot(ax=ia, color=colors, edgecolor="#666666", linewidth=0.15)
        (X0, Y0), (X1, Y1) = tr.transform(x0, y0), tr.transform(x1, y1)
        ia.set_xlim(X0, X1)
        ia.set_ylim(Y0, Y1)
        ia.set_xticks([])
        ia.set_yticks([])
        for sp in ia.spines.values():
            sp.set_visible(True)
            sp.set_linewidth(0.6)
            sp.set_color("#999999")
        ia.set_title(name, fontsize=6.8, pad=2)
fig.savefig(OUT + "Figure2.png", **SAVE)
plt.close(fig)

dd = pd.read_pickle(RES + "gbd2021_gbd2023_global.pkl")
sev = pd.read_csv(RES + "severity_2021.csv")
rr = pd.read_csv(RES + "regional_revision_2021.csv", index_col=0)
ag = pd.read_csv(RES + "age_revision_2021.csv")
fig = plt.figure(figsize=(7.4, 9.6))
gs = fig.add_gridspec(3, 2, height_ratios=[1, 1.1, 1.45], hspace=0.55, wspace=0.42)
axA = fig.add_subplot(gs[0, :])
for rnd, col, lab in [("GBD2021", C21, "GBD 2021"), ("GBD2023", C23, "GBD 2023")]:
    x = dd[
        (dd["round"] == rnd)
        & (dd.cause_name == "Age-related macular degeneration")
        & (dd.key == "Prev_n_Number")
    ].sort_values("year")
    axA.fill_between(x.year, x.lower / 1e6, x.upper / 1e6, color=col, alpha=0.15, lw=0)
    axA.plot(x.year, x.val / 1e6, color=col, lw=1.8, label=lab)
axA.set_xlim(1990, 2023)
axA.set_ylim(0, 10.5)
axA.set_ylabel("People with vision impairment\ndue to AMD (millions)")
axA.legend(loc="upper left", fontsize=7.5)
panel(axA, "A", x=-0.09)
axB = fig.add_subplot(gs[1, 0])
s_ = sev[(sev.cause == "Age-related macular degeneration") & (sev.severity != "Total")]
xx = np.arange(3)
wd = 0.38
for j, (rnd, col, lab) in enumerate(
    [("GBD2021", C21, "GBD 2021"), ("GBD2023", C23, "GBD 2023")]
):
    v = s_[f"{rnd}_prev"].values / 1e6
    lo = s_[f"{rnd}_prev_lo"].values / 1e6
    hi = s_[f"{rnd}_prev_hi"].values / 1e6
    axB.bar(xx + (j - 0.5) * wd, v, width=wd, color=col, label=lab)
    axB.errorbar(
        xx + (j - 0.5) * wd,
        v,
        yerr=[v - lo, hi - v],
        fmt="none",
        ecolor="#444444",
        elinewidth=0.7,
        capsize=2,
    )
axB.set_xticks(xx, ["Moderate", "Severe", "Blindness"])
axB.set_ylabel("Prevalent cases in 2021 (millions)")
axB.legend(loc="upper right", fontsize=7.5)
panel(axB, "B", x=-0.25)
axC = fig.add_subplot(gs[1, 1])
ages = sorted(ag.a0.unique())
xa = np.arange(len(ages))
for sex, col, mk in [("Female", FEM, "o"), ("Male", MAL, "s")]:
    g_ = ag[ag.sex_name == sex].set_index("a0").loc[ages]
    axC.plot(xa, g_.revision_pct, color=col, lw=1.3, label=sex)
    filled = g_.outside_both.values.astype(bool)
    axC.scatter(
        xa[filled], g_.revision_pct.values[filled], color=col, marker=mk, s=18, zorder=3
    )
    axC.scatter(
        xa[~filled],
        g_.revision_pct.values[~filled],
        facecolors="white",
        edgecolors=col,
        marker=mk,
        s=18,
        zorder=3,
    )
axC.axhline(0, color="black", lw=0.8)
axC.set_xticks(
    xa,
    [f"{a}–{a + 4}" if a < 95 else "≥95" for a in ages],
    rotation=45,
    ha="right",
    fontsize=6.8,
)
axC.set_ylabel("Revision of 2021 prevalence rate,\nGBD 2023 vs GBD 2021 (%)")
axC.set_xlabel("Age group (years)")
axC.legend(loc="lower right", fontsize=7.2)
panel(axC, "C", x=-0.28)
axD = fig.add_subplot(gs[2, :])
yy = np.arange(len(rr))
cols = ["#8C2D04" if o in (True, "True") else "#FDAE6B" for o in rr.outside_both]
axD.barh(yy, rr.change / 1e3, color=cols, height=0.7)
axD.axvline(0, color="black", lw=0.8)
axD.set_yticks(yy, rr.index, fontsize=6.8)
axD.invert_yaxis()
axD.set_xlabel("Change in prevalent cases in 2021, GBD 2023 minus GBD 2021 (thousands)")
handles = [
    Patch(
        facecolor="#8C2D04",
        label="Age-standardized prevalence outside both rounds\u2019 95% UIs",
    ),
    Patch(
        facecolor="#FDAE6B",
        label="Age-standardized prevalence within at least one 95% UI",
    ),
]
axD.legend(handles=handles, loc="lower left", fontsize=6.8)
panel(axD, "D", x=-0.2)
fig.savefig(OUT + "Figure3.png", **SAVE)
plt.close(fig)

h = series("Global", "Both", "Prevalence", "All ages", "Number")
fig, ax = plt.subplots(figsize=(7.2, 3.8))
ax.fill_between(h.year, h.lower / 1e6, h.upper / 1e6, color=RED, alpha=0.12, lw=0)
ax.plot(h.year, h.val / 1e6, color=RED, lw=1.8, label="GBD 2023 estimates (95% UI)")
lo_b, hi_b = out.New_constant_lo.copy(), out.New_constant_hi.copy()
lo_b.loc[2023] = ns["cases"](ns["rlo"][2023], ns["pop_gbd"][2023])
hi_b.loc[2023] = ns["cases"](ns["rhi"][2023], ns["pop_gbd"][2023])
yrs = np.arange(2023, 2051)
ax.fill_between(
    yrs,
    lo_b.loc[yrs] / 1e6,
    hi_b.loc[yrs] / 1e6,
    color=RED,
    alpha=0.07,
    lw=0,
    label="Projection bounds (see legend)",
)
y2 = np.arange(2023, 2051)
ax.plot(
    y2,
    out.New_constant_rates.loc[y2] / 1e6,
    color=RED,
    lw=1.8,
    ls="--",
    label="Demographic projection (2023 rates held constant)",
)
ax.plot(
    y2,
    out.New_trend_1990_2023.loc[y2] / 1e6,
    color=RED,
    lw=1.2,
    ls=":",
    label="Trend projection (1990–2023 trends continued)",
)
py = np.arange(2021, 2051)
ax.plot(
    py,
    out.published_projection.loc[py] / 1e6,
    color=GREY,
    lw=1.4,
    ls="-.",
    label="Previously published projection (GBD 2021)",
)
ax.annotate(
    "+31% in one year\n(2021 to 2022)",
    xy=(2021.6, 9.4),
    xytext=(2008.5, 13.2),
    fontsize=7.2,
    color="#555555",
    arrowprops=dict(arrowstyle="->", color="#777777", lw=0.8),
)
for sname, dy in [
    ("New_constant_rates", 0.35),
    ("New_trend_1990_2023", -0.35),
    ("published_projection", 0),
]:
    ax.text(
        2050.7,
        out.loc[2050, sname] / 1e6 + dy,
        f"{out.loc[2050, sname] / 1e6:.1f}",
        va="center",
        fontsize=7.5,
    )
ax.axvline(2023.5, color="#BDBDBD", lw=0.8)
ax.set_xlim(1990, 2053)
ax.set_ylim(0, 23)
ax.set_xticks([1990, 2000, 2010, 2020, 2030, 2040, 2050])
ax.set_ylabel("People with vision impairment\ndue to AMD (millions)")
h_, l_ = ax.get_legend_handles_labels()
l_[1] = "Demographic projection bounds"
ax.legend(h_, l_, loc="upper left", fontsize=7.2)
fig.tight_layout()
fig.savefig(OUT + "Figure4.png", **SAVE)
plt.close(fig)

jf = json.load(open(RES + "joinpoint_fits.json"))
fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9))
for a_, loc, letter in [(ax[0], "Global", "A"), (ax[1], "High-income", "B")]:
    r = jf[loc]
    a_.axvspan(2006, 2010, color="#EEEEEE", lw=0, label="Anti-VEGF uptake (2006–2010)")
    a_.plot(
        r["years"],
        r["observed"],
        "o",
        color=DARK,
        ms=2.8,
        label="GBD 2023 estimate",
        clip_on=False,
        zorder=5,
    )
    a_.plot(r["years"], r["fitted"], "-", color=RED, lw=1.5, label="Joinpoint fit")
    for jp in r["joinpoints"]:
        a_.axvline(jp, color=RED, lw=0.7, ls=":")
    a_.set_title(loc, fontsize=8.5)
    a_.set_xlim(1989, 2024)
    a_.set_ylabel("Age-standardized prevalence\n(per 100 000)")
    lo_, hi_ = min(r["observed"] + r["fitted"]), max(r["observed"] + r["fitted"])
    pad = 0.06 * (hi_ - lo_)
    a_.set_ylim(lo_ - pad, hi_ + pad)
    panel(a_, letter, x=-0.22)
ax[0].legend(loc="lower left", fontsize=6.8)
fig.tight_layout(w_pad=1.5)
fig.savefig(OUT + "FigureS1.png", **SAVE)
plt.close(fig)

rows = [
    "Global",
    "High SDI",
    "High-middle SDI",
    "Middle SDI",
    "Low-middle SDI",
    "Low SDI",
    "Central Europe, Eastern Europe, and Central Asia",
    "High-income",
    "Latin America and Caribbean",
    "North Africa and Middle East",
    "South Asia",
    "Southeast Asia, East Asia, and Oceania",
    "Sub-Saharan Africa",
]
T = t1.loc[rows]
ypos = []
yv = 0
for i in range(len(rows)):
    if i in (1, 6):
        yv += 0.7
    ypos.append(-yv)
    yv += 1
fig, ax = plt.subplots(
    1, 2, figsize=(7.2, 4.3), sharey=True, gridspec_kw={"width_ratios": [1.25, 1]}
)
for yv_, r in zip(ypos, rows):
    a90, a23 = T.loc[r, "asr1990"], T.loc[r, "asr2023"]
    ax[0].plot([a90, a23], [yv_, yv_], color="#BDBDBD", lw=1.4, zorder=1)
    ax[0].errorbar(
        a90,
        yv_ + 0.15,
        xerr=[[a90 - T.loc[r, "asr1990_lo"]], [T.loc[r, "asr1990_hi"] - a90]],
        fmt="o",
        mfc="#9ECAE1",
        mec=BLUE,
        ecolor=BLUE,
        ms=4,
        elinewidth=0.7,
        capsize=1.5,
        label="1990" if r == "Global" else None,
    )
    ax[0].errorbar(
        a23,
        yv_ - 0.15,
        xerr=[[a23 - T.loc[r, "asr2023_lo"]], [T.loc[r, "asr2023_hi"] - a23]],
        fmt="o",
        color=RED,
        ms=4,
        elinewidth=0.7,
        capsize=1.5,
        label="2023" if r == "Global" else None,
    )
    e, lo, hi = (
        T.loc[r, "asr_change_pct"],
        T.loc[r, "asr_change_lo"],
        T.loc[r, "asr_change_hi"],
    )
    ax[1].errorbar(
        [e],
        [yv_],
        xerr=[[e - lo], [hi - e]],
        fmt="o",
        color=DARK,
        ms=4,
        elinewidth=1,
        capsize=2,
    )
ax[1].axvline(0, color="black", lw=0.8)
ax[0].set_yticks(ypos, ["\n".join(textwrap.wrap(r, 30)) for r in rows], fontsize=7.5)
ax[0].set_xlabel("Age-standardized prevalence per 100 000 (95% UI)")
ax[1].set_xlabel("Change in age-standardized prevalence,\n1990–2023 (%, 95% UI)")
ax[0].set_xlim(0, 180)
ax[1].set_xlim(-40, 15)
ax[0].legend(loc="upper right", fontsize=7.5)
panel(ax[0], "A", x=-0.62, y=1.01)
panel(ax[1], "B", x=-0.06, y=1.01)
fig.tight_layout(w_pad=1.0)
fig.savefig(OUT + "FigureS4.png", **SAVE)
plt.close(fig)

a = age[(age.age_name != "All ages") & (age.year == 2023)].copy()
a["a0"] = a.age_name.str.extract(r"^(\d+)").astype(int)
a = a[a.a0 >= 45]
labels = [f"{x}–{x+4}" if x < 95 else "≥95" for x in sorted(a.a0.unique())]
x = np.arange(len(labels))
fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9))
for j, (sex, col) in enumerate([("Female", FEM), ("Male", MAL)]):
    n = a[(a.sex_name == sex) & (a.metric_name == "Number")].sort_values("a0")
    r = a[(a.sex_name == sex) & (a.metric_name == "Rate")].sort_values("a0")
    ax[0].bar(x + (j - 0.5) * 0.4, n.val / 1e3, width=0.4, color=col, label=sex)
    ax[0].errorbar(
        x + (j - 0.5) * 0.4,
        n.val / 1e3,
        yerr=[(n.val - n.lower) / 1e3, (n.upper - n.val) / 1e3],
        fmt="none",
        ecolor="#444444",
        elinewidth=0.6,
        capsize=1,
    )
    ax[1].errorbar(
        x,
        r.val,
        yerr=[r.val - r.lower, r.upper - r.val],
        color=col,
        marker="o",
        ms=3,
        lw=1.4,
        elinewidth=0.8,
        capsize=1.5,
        label=sex,
    )
ax[0].set_ylabel("Prevalent cases (thousands)")
ax[1].set_ylabel("Prevalence per 100 000")
for a_ in ax:
    a_.set_xticks(x, labels, rotation=45, ha="right", fontsize=7)
    a_.set_xlabel("Age group (years)")
ax[0].legend(loc="upper left", fontsize=7.5)
ax[1].legend(loc="upper left", fontsize=7.5)
panel(ax[0], "A", x=-0.2)
panel(ax[1], "B", x=-0.2)
fig.tight_layout(w_pad=1.5)
fig.savefig(OUT + "FigureS5.png", **SAVE)
plt.close(fig)

causes = [
    "Near vision loss",
    "Refraction disorders",
    "Cataract",
    "Other vision loss",
    "Glaucoma",
    "Age-related macular degeneration",
]
labs = [
    "Near vision loss",
    "Refraction disorders",
    "Cataract",
    "Other vision loss",
    "Glaucoma",
    "AMD",
]
cols = ["#BBBBBB", "#56B4E9", "#E69F00", "#009E73", "#0072B2", "#CC79A7"]
wv = (
    dd[(dd.year == 2021) & (dd.key == "DALY_n_Number")].pivot_table(
        index="cause_name", columns="round", values="val"
    )
    / 1e6
)
fig, ax = plt.subplots(1, 2, figsize=(7.4, 4.0), gridspec_kw={"width_ratios": [1, 1.3]})
for j, rnd in enumerate(["GBD2021", "GBD2023"]):
    bottom = 0
    for c, lab, col in zip(causes, labs, cols):
        ax[0].bar(
            j,
            wv.loc[c, rnd],
            bottom=bottom,
            color=col,
            width=0.6,
            edgecolor="white",
            lw=0.5,
            label=lab if j == 0 else None,
        )
        bottom += wv.loc[c, rnd]
    ax[0].text(j, bottom + 0.4, f"{bottom:.1f}", ha="center", va="bottom", fontsize=8.5)
ax[0].set_xticks([0, 1], ["GBD 2021", "GBD 2023"])
ax[0].set_ylabel("DALYs from vision loss in 2021 (millions)")
ax[0].set_ylim(0, 33)
hh, ll = ax[0].get_legend_handles_labels()
ax[0].legend(
    hh,
    ll,
    fontsize=7.3,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.12),
    ncol=2,
    handlelength=1.2,
    columnspacing=1.0,
)
rev = (100 * (wv["GBD2023"] / wv["GBD2021"] - 1)).reindex(causes)
dist21 = (
    wv.loc["Blindness and vision loss", "GBD2021"]
    - wv.loc["Near vision loss", "GBD2021"]
)
dist23 = (
    wv.loc["Blindness and vision loss", "GBD2023"]
    - wv.loc["Near vision loss", "GBD2023"]
)
items = [
    (
        "All causes",
        100
        * (
            wv.loc["Blindness and vision loss", "GBD2023"]
            / wv.loc["Blindness and vision loss", "GBD2021"]
            - 1
        ),
        "#555555",
    ),
    ("Distance vision loss", 100 * (dist23 / dist21 - 1), "#555555"),
] + [(lab, rev[c], col) for c, lab, col in zip(causes, labs, cols)]
items = items[::-1]
yy = np.arange(len(items))
ax[1].barh(yy, [v for _, v, _ in items], color=[c for _, _, c in items], height=0.62)
ax[1].axvline(0, color="black", lw=0.8)
for i, (lab, v, _) in enumerate(items):
    ax[1].text(
        v + (1.5 if v >= 0 else -1.5),
        i,
        f"{v:+.1f}%".replace("-", "–"),
        va="center",
        ha="left" if v >= 0 else "right",
        fontsize=8,
    )
ax[1].set_yticks(yy, [lab for lab, _, _ in items])
ax[1].set_xlim(-90, 65)
ax[1].set_xlabel("Revision of 2021 DALYs,\nGBD 2023 vs GBD 2021 (%)")
panel(ax[0], "A", x=-0.28, y=1.03)
panel(ax[1], "B", x=-0.45, y=1.03)
fig.tight_layout()
fig.savefig(OUT + "FigureS2.png", **SAVE)
plt.close(fig)

imp = (
    pub_proj.m_n * 1e6 / (pub_proj.m_rate / 1e5)
    + pub_proj.f_n * 1e6 / (pub_proj.f_rate / 1e5)
) / 1e9
fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.0))
ax[0].plot(
    imp.index,
    imp.values,
    color=DARK,
    lw=1.6,
    ls="--",
    label="Implied by published\ncounts and rates",
)
ax[0].plot(
    wpp_tot.loc[2021:2050].index,
    wpp_tot.loc[2021:2050].sum(axis=1) / 1e9,
    color="#009E73",
    lw=1.6,
    label="WPP 2024",
)
ax[0].set_ylabel("World population (billions)")
ax[0].set_ylim(0, 17)
ax[0].set_xlim(2021, 2050)
ax[0].legend(loc="lower right", fontsize=7.5)
yA = np.arange(2021, 2051)
ax[1].plot(
    yA,
    out.published_projection.loc[yA] / 1e6,
    color=DARK,
    lw=1.6,
    ls="--",
    label="Published projection",
)
ax[1].plot(
    yA,
    out.published_rates_wpp.loc[yA] / 1e6,
    color=DARK,
    lw=1.2,
    ls=":",
    label="Published rates × WPP 2024 population",
)
e = np.arange(2021, 2024)
p = np.arange(2023, 2051)
ax[1].plot(
    e,
    out.GBD2023_estimate.loc[e] / 1e6,
    color=C23,
    lw=2.2,
    label="GBD 2023 estimates (2021–2023)",
)
ax[1].plot(
    p,
    out.New_constant_rates.loc[p] / 1e6,
    color=C23,
    lw=1.4,
    ls="--",
    label="Updated reference projection (2024–2050)",
)
ax[1].set_ylabel("People with vision impairment\ndue to AMD (millions)")
ax[1].set_ylim(0, 23)
ax[1].set_xlim(2021, 2050)
ax[1].legend(loc="upper left", fontsize=6.8)
for a_, t in zip(ax, ["A", "B"]):
    a_.text(-0.2, 1.03, t, transform=a_.transAxes, fontsize=11, fontweight="bold")
fig.tight_layout(w_pad=1.5)
fig.savefig(OUT + "FigureS3.png", **SAVE)
plt.close(fig)
