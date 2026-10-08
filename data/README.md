# Input data

Place all files in this folder under the names below.

## 1. GBD Results Tool exports (13 files, not included)

Download them from https://vizhub.healthdata.org/gbd-results/ (free account). The authors downloaded them in September 2026.

Each download is a zip file containing one CSV with a random name. Rename the CSV to the name in the first column and save it here. Select exactly the options listed and leave every other setting at its default. "Both" in the Sex column means both sexes combined. The last column gives the number of rows in the authors' files, so you can check a download.

| Save as | Round | GBD estimate | Measure | Metric | Cause | Location | Age | Sex | Year | Rows |
|---|---|---|---|---|---|---|---|---|---|---|
| `IHME-GBD_2023_DATA-8a125c94-1.csv` | GBD 2023 | Cause of death or injury | Prevalence; DALYs (Disability-Adjusted Life Years) | Number; Rate | Blindness and vision loss; Age-related macular degeneration; Cataract; Glaucoma; Refraction disorders; Near vision loss; Other vision loss | Global | All ages; Age-standardized | Both | Every year, 1990–2023 | 1428 |
| `IHME-GBD_2023_DATA-67c190e0-1.csv` | GBD 2023 | Cause of death or injury | Prevalence; DALYs | Number; Rate | Age-related macular degeneration | Global; the five SDI quintiles; the seven GBD super-regions | All ages; Age-standardized | Male; Female; Both | Every year, 1990–2023 | 7956 |
| `IHME-GBD_2023_DATA-c8589e17-1.csv` | GBD 2023 | Cause of death or injury | Prevalence; DALYs | Number; Rate | Age-related macular degeneration | All 204 countries and territories | All ages; Age-standardized | Both | 1990; 2023 | 2448 |
| `IHME-GBD_2023_DATA-35224841-1.csv` | GBD 2023 | Cause of death or injury | Prevalence | Number; Rate | Age-related macular degeneration | Global | Each 5-year group from 40–44 to 95+; All ages | Male; Female | Every year, 1990–2023 | 1768 |
| `IHME-GBD_2023_DATA-334dcb5b-1.csv` | GBD 2023 | Cause of death or injury | Prevalence; DALYs | Number; Rate | Age-related macular degeneration | The five SDI quintiles; the seven GBD super-regions | All ages; Age-standardized | Both | Percent change, 1990–2023 | 174* |
| `IHME-GBD_2023_DATA-8c88aea3-1.csv` | GBD 2023 | Cause of death or injury | Prevalence; DALYs | Number; Rate | Age-related macular degeneration | Global | All ages; Age-standardized | Both | Percent change, 1990–2023 | 6 |
| `IHME-GBD_2023_DATA-7c64da8e-1.csv` | GBD 2023 | Impairment (Moderate vision loss; Severe vision loss; Blindness) | Prevalence; YLDs (Years Lived with Disability) | Number | All causes; Age-related macular degeneration | Global | All ages | Both | 2021 | 12 |
| `IHME-GBD_2023_DATA-c9a2b09d-1.csv` | GBD 2023 | Cause of death or injury | Prevalence | Number; Rate | Age-related macular degeneration | The 21 GBD regions | All ages | Both | 2021 | 92* |
| `IHME-GBD_2023_DATA-3f2f59b1-1.csv` | GBD 2023 | Cause of death or injury | Prevalence | Rate | Age-related macular degeneration | The 21 GBD regions | Age-standardized | Both | 2021 | 21 |
| `IHME-GBD_2021_DATA-48f5d8d4-1.csv` | GBD 2021 | Cause of death or injury | Prevalence; DALYs | Number; Rate | The same seven causes as the first file | Global | All ages; Age-standardized | Both | Every year, 1990–2021 | 1344 |
| `IHME-GBD_2021_DATA-110219a5-1.csv` | GBD 2021 | Impairment (Moderate vision loss; Severe vision loss; Blindness) | Prevalence; YLDs | Number | All causes; Age-related macular degeneration | Global | All ages | Both | 2021 | 12 |
| `IHME-GBD_2021_DATA-31a816dc-1.csv` | GBD 2021 | Cause of death or injury | Prevalence | Number; Rate | Age-related macular degeneration | Global | Each 5-year group from 45–49 to 95+ | Male; Female | 2021 | 44 |
| `IHME-GBD_2021_DATA-322d9f23-1.csv` | GBD 2021 | Cause of death or injury | Prevalence | Number; Rate | Age-related macular degeneration | The 21 GBD regions | All ages; Age-standardized | Both | 2021 | 63 |

\* The authors' files also contained other location groupings, which the scripts ignore. If you select only the locations listed, these files have 72 and 42 rows.

The GBD Results Tool does not provide counts for age-standardized estimates. Selecting Number and Rate with All ages and Age-standardized therefore gives three combinations (all-age count, all-age rate and age-standardized rate), not four.

These data are subject to the IHME Free-of-Charge Non-Commercial User Agreement and are not redistributed here.

Citations:

- Global Burden of Disease Collaborative Network. Global Burden of Disease Study 2023 (GBD 2023) Results. Seattle, United States: Institute for Health Metrics and Evaluation (IHME), 2024.
- Global Burden of Disease Collaborative Network. Global Burden of Disease Study 2021 (GBD 2021) Results. Seattle, United States: Institute for Health Metrics and Evaluation (IHME), 2022.

Source: Institute for Health Metrics and Evaluation. Used with permission. All rights reserved.

## 2. World Population Prospects 2024 (2 files, not included)

`popAge1dt.rda` and `popprojAge1dt.rda` come from the `data` folder of the `wpp2024` R package, version 1.1-3 (https://github.com/PPgp/wpp2024).

- Source: United Nations, Department of Economic and Social Affairs, Population Division. World Population Prospects 2024.
- License: Creative Commons Attribution 3.0 IGO.

The scripts convert the package's end-of-year (31 December) populations to mid-year (1 July) values by averaging consecutive years.

## 3. Natural Earth country boundaries (1 file, not included)

`ne_50m_admin_0_countries.geojson`, from the `geojson` folder of https://github.com/nvkelso/natural-earth-vector (version 5.2.0-pre, downloaded October 2026).

Natural Earth data are in the public domain.

## 4. Authors' files (included)

- **`gbd_iso3.csv`**: the ISO 3166-1 alpha-3 code for each of the 204 GBD countries and territories. It is used to join GBD estimates to the map boundaries. Tokelau does not appear on the 1:50 million map.
- **`published_projection_gbd2021.csv`**: the published GBD 2021-based forecast of vision impairment due to AMD.
  - Contents: counts (`m_n`, `f_n`, millions) and all-age rates (`m_rate`, `f_rate`, per 100 000) by sex, 2021–2050; point estimates only.
  - Source: transcribed from appendix Table S16 of GBD 2021 Global AMD Collaborators. Global burden of vision impairment due to age-related macular degeneration, 1990–2021, with forecasts to 2050: a systematic analysis for the Global Burden of Disease Study 2021. Lancet Glob Health 2025;13:e1175–90. doi:10.1016/S2214-109X(25)00143-3.
