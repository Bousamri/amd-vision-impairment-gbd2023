# Vision impairment due to age-related macular degeneration in the Global Burden of Disease Study 2023: analysis code

Analysis code for a study of vision impairment due to age-related macular degeneration (AMD) based on the Global Burden of Disease Study (GBD) 2023. The study quantifies how GBD 2023 revised the GBD 2021 estimates, checks the internal consistency of a published GBD 2021-based projection, projects the number of people affected to 2050, and describes trends for 1990–2023. The article is under review; its citation will be added here on publication.

The scripts reproduce every table and figure in the article and its supplement.

## Scripts

Run them in numerical order from this folder.

| Script | What it does | Article items |
|---|---|---|
| `01_descriptive.py` | Counts, rates and percent changes globally, by sex, Socio-demographic Index (SDI) quintile, super-region and country; decomposition of the 1990–2023 change; cause-level values from both rounds | Table 1; Figure 1C; Supplementary Tables S1, S8 and S11 |
| `02_projection.py` | Reference demographic projection, trend scenarios and back-test; inputs for the check of the published projection (also called by scripts 03 and 05) | Figure 4 |
| `03_trends_and_rounds.py` | Joinpoint regression; revision by severity; projection scenarios and decomposition of the 2023–2050 change; check of the published projection; age- and sex-specific annual change | Supplementary Tables S2, S5, S9, S10 and S12 |
| `04_revisions.py` | Global, regional and age-specific revisions with uncertainty flags; segmented model with a break at 2006; disability-adjusted life-years (DALYs) per prevalent case | Supplementary Tables S2 to S7 |
| `05_figures.py` | All figures | Figures 1 to 4; Supplementary Figures S1 to S5 |

Results are written to `output/` and figures to `output/figures/`. A full run takes about one minute.

## Requirements

- Python 3.13 (tested with 3.13.16).
- Packages: `pip install -r requirements.txt`. The versions are pinned; with them, the figures match the published figures pixel for pixel.
- The Liberation Sans font (free, preinstalled on most Linux systems). Without it, Matplotlib substitutes another font; figure layout then changes slightly, but no number changes.

## Data

All inputs go in `data/`. Two files are the authors' own and are included. The others are third-party data that must be downloaded; `data/README.md` gives the exact settings for each file.

- **GBD estimates (13 files).** These are not included. The Institute for Health Metrics and Evaluation (IHME) Free-of-Charge Non-Commercial User Agreement does not allow redistribution of downloaded data sets. They can be downloaded free of charge from the GBD Results Tool (https://vizhub.healthdata.org/gbd-results/).
- **Population (2 files).** United Nations World Population Prospects 2024, from the `wpp2024` R package.
- **Country boundaries (1 file).** Natural Earth.

Source: Institute for Health Metrics and Evaluation. Used with permission. All rights reserved.

## Run

```
pip install -r requirements.txt
python 01_descriptive.py
python 02_projection.py
python 03_trends_and_rounds.py
python 04_revisions.py
python 05_figures.py
```

## License

The code and the authors' data files are released under the MIT License (see `LICENSE`). The values in `data/published_projection_gbd2021.csv` were transcribed from a published article (see `data/README.md`); cite that article when using them. Third-party data remain under their providers' terms.

## Citation

See `CITATION.cff`. Please also cite the article once it is published.
