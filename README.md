# UWB Anchor Self-Calibration Dataset (UWB-ASC)

A testing ground for the self-calibration of UWB anchor positions. Two
deployments of Qorvo MDEK1001 modules (two-way ranging) in one industrial hall
in Torgau, Germany, come with surveyed node positions. The LOS deployment
(`Data/set_b`, recorded on 2025-10-22) adds motion-capture truth for the walks
of a mobile tag, and the NLOS deployment (`Data/set_a`, recorded on 2025-03-13) a
tag placed on 20 surveyed markers. A seeded range-error generator ships as
code, with 81 frozen synthetic draws on the surveyed anchors and a draw tool
that draws new scenes on the surveyed geometry, noise-free or with known
errors, with or without a mobile tag. Readers convert two public range
recordings into the same format. Every session is one superset measurement
graph, and four topology views select from it. The raw recordings, the
canonical sessions, the scripts that rebuild the one from the other and the
`radiocal` loader ship together. The data descriptor "Descriptor: UWB Anchor
Self-Calibration Dataset (UWB-ASC)" (P. Schwarzbach, submitted to IEEE Data
Descriptions) describes the release.

## Contents and layout

```
Data/                    the canonical data, with the data dictionary README.md
  set_a/                 the NLOS deployment: 22 sessions, truth adjudication, field labels
  set_b/                 the LOS deployment: 3 sessions, field labels
  synthetic/             SYNTHETIC: 81 seeded draws on the surveyed set_b/s03 anchors
Code/
  datasets/radiocal/     the radiocal package: loader, topology masks, builders, QA reports,
                         the synthetic writer (scripts/05), the data-facts generator
                         (scripts/06) and the draw tool (scripts/07)
  methods/               the seeded range-error generator that scripts 05 and 07 import
  external/              readers and converter for TWR-CLOUD-Bern and selfloc (no data)
  descriptor/            the script that draws Figs. 1, 2, 4, 5 and S1 of the data descriptor
docs/FAIR.md             how the release meets the FAIR principles and the best
                         practices for open data in indoor positioning
tests/                   the smoke test and the rebuild check
requirements.txt         the pinned environment that wrote the files
SHA256SUMS               the SHA-256 of every file
PROVENANCE.yaml          the commits this release was built from
```

Version 1.0.0 of this repository takes 42.8 MB in 412 files. Next to it, the
Zenodo deposit holds the raw archives `raw_set_a.zip` (9.7 MB) and
`raw_set_b.zip` (9.0 MB) with `RAW_MANIFEST.md`. The quality report and the
figures of each session (`Data/<set>/<session>/qa/`) show a session without
loading it.

## Where to look first

- `Data/README.md`, the data dictionary, then the README of a deployment.
- One session in a few lines, from the repository root:

```python
import radiocal

g = radiocal.load_session("Data/set_b/s01")   # superset graph of one session
view = g.apply_mask("fully_meshed")            # anchor-anchor ranges, no priors
view.edges.head()                              # t, t_raw, seq, from_id, to_id, range_m
g.nodes                                        # id, role, prior_type, x, y, z, sigma_m
```

- A noise-free scene of your own, here the tag DD98 walking among the set_b
  anchors, drawn into a folder outside `Data/` (see *Drawing new synthetic
  scenes*):

```
python -B Code/datasets/radiocal/scripts/07_draw_synthetic.py --scene walk --condition noise_free --out draws/walk_set_b
```

- The smoke test of *Quick check*.

## Install

Python 3.10 or newer, no GPU. The commands assume a POSIX shell (Git Bash or
WSL on Windows) and run from the repository root:

```
pip install -e "Code/datasets/radiocal[qa,methods]"
```

This install resolves current library versions within the bounds of
`pyproject.toml`, which keep pandas below 3. The `qa` extra adds matplotlib
for the QA reports, and `methods` adds scipy, which the set A builder needs.
`pip install Code/datasets/radiocal` without `-e` works as well, since the
topology masks ship as package data.

To rebuild the released files byte for byte, install the versions that wrote
them first (Python 3.12 or newer):

```
pip install -r requirements.txt
pip install -e "Code/datasets/radiocal[qa,methods]"
```

Tested on Windows 11: the pinned install with Python 3.12.13 and 3.14.6, the
unpinned one with Python 3.10.20, and a non-editable install of the package
wheel with Python 3.12.13.

A run needs less than 1 GB of memory. The smoke test, the largest step, peaks
at about 0.6 GB. On disk, an environment takes about 0.4 GB, this repository
43 MB, the raw archives 19 MB and 72 MB once unpacked, a rebuild 42 MB, and
the draw examples of this README 39 MB.

## Quick check

```
python -B tests/test_smoke.py
```

It writes only into a temporary folder, which it removes, and prints

```
ok  checksums: 411 files match SHA256SUMS
ok  sessions load (191423 + 351263 ranges)
ok  every range, pose and label joins a node of its campaign (106 sessions, 3829792 ranges)
ok  mask invariants hold on Data/set_b/s01
ok  mask invariants hold on Data/set_a/s07
ok  synthetic: 81 of 81 files match their ranges_sha256, and the redraw equals them
ok  data facts: 136 computed, 8 checked against the printed values
ok  pairs: 132 node pairs, consistent with the residual macros
ok  draw tool: its static scene reproduces the 81 frozen draws
ok  draw tool: noise-free walk and marker scenes equal their distances, a marker on set_b is refused
skip external: set UWBASC_EXTERNAL to the folder of the converted campaigns

smoke test passed
```

No warning is expected. With a numpy release whose random streams differ
from those of numpy 2.3.5, the synthetic line and the first draw-tool line
read `note ... generator drift` instead, while the files keep their hashes.
With `UWBASC_EXTERNAL` set to the folder that
`Code/external/convert_external.py --out` wrote, the last check reads
`ok  external: every converted campaign loads, joins its kept nodes and applies
its two views, multi_hop with the gauge triple`.

## What the scripts rebuild

The Zenodo deposit holds two raw archives next to the snapshot of this
repository: `raw_set_a.zip` and `raw_set_b.zip`, listed with the SHA-256 of
every raw file in `RAW_MANIFEST.md`. Place both at the repository root and
unpack them there, as the first two commands below do. They create
`raw/set_a/` and `raw/set_b/`, each with its own `README.txt` and
`LICENSE-DATA`. Then run the rest:

```
python -m zipfile -e raw_set_a.zip .
python -m zipfile -e raw_set_b.zip .
python -B Code/datasets/radiocal/scripts/01_inspect_raw.py --raw-root raw/set_b
python -B Code/datasets/radiocal/scripts/02_build_set_b.py --raw-root raw/set_b --out rebuild/set_b
python -B Code/datasets/radiocal/scripts/04_build_set_a.py --raw-root raw/set_a --out rebuild/set_a
python -B Code/datasets/radiocal/scripts/03_qa_all.py --data rebuild --out rebuild
python -B Code/datasets/radiocal/scripts/05_build_synthetic.py --out rebuild/synthetic
python -B tests/check_rebuild.py rebuild
python -B Code/datasets/radiocal/scripts/06_data_facts.py --out facts
python -B Code/descriptor/validation_figures.py --facts facts --out figures
```

- `01_inspect_raw.py` checks the set B raw files and writes nothing.
- `02_build_set_b.py` and `04_build_set_a.py` rebuild the two deployments,
  `03_qa_all.py` their QA reports, and `05_build_synthetic.py` the 81
  synthetic draws, which it checks against the hashes stored in
  `Data/synthetic/*/session.yaml` before it writes.
- `06_data_facts.py` writes the numbers that the data descriptor prints about
  the data, and `validation_figures.py` draws its figures from them and from
  `Data/` (see *Figures, tables and numbers*).
- Every command passes `--out`. Without it, scripts 02, 03, 04 and 05 write
  into `Data/`, which is **destructive**: they overwrite the released files.
  Script 06, the draw tool 07 and the figure script require `--out`, and the
  draw tool refuses any folder inside `Data/`.
- In the pinned environment, every canonical file rebuilds byte for byte:
  Parquet, YAML, CSV and the QA reports. The QA figures equal the released
  ones pixel for pixel, since the PNG encoder may differ. `check_rebuild.py`
  compares each file in that way and exits with 1 on a difference.
- The set B databases in the deposit are stripped of the streams of a vendor
  positioning system that ran alongside the campaign and is no part of this
  dataset. `campaign.yaml` and `session.yaml` store both hashes of each
  database, `sha256` of the original and `sha256_archived` of the stripped
  copy, and the builders accept either file. The YAML files therefore rebuild
  unchanged from the deposit. SQLite 3.50.4 wrote the stripped copies.
- With other library versions, a Parquet file records another writer, so
  `check_rebuild.py` compares it by content. Two fields then differ as well:
  the synthetic YAML files record the numpy version that drew them
  (`numpy_version`), and the column `rolling_median_span_m` of
  `Data/set_a/truth_adjudication.csv`, a stationarity figure that decides
  nothing, can move by a few millimetres, because the builder orders the tied
  epochs of a link by an unstable sort. `check_rebuild.py` accepts both: a
  YAML file that differs only in `numpy_version`, and that column within 5 mm.

## Drawing new synthetic scenes

The range-error generator ships as code: `Code/methods/range_errors.py` holds
the error model of P. Schwarzbach, R. Weber and O. Michler (IEEE Sensors J.
22(6):4836-4843, 2022) and five conditions built on it, among them the
per-pair `nlos`, which goes beyond the paper. `Code/methods/synthetic.py`
builds scenes on a surveyed geometry. The 81 frozen draws under
`Data/synthetic` come from them, and the draw tool
`Code/datasets/radiocal/scripts/07_draw_synthetic.py` draws further scenes
into a folder of your choice:

```
python -B Code/datasets/radiocal/scripts/07_draw_synthetic.py --scene static --geometry set_a/s21 --seeds 0-19 --out draws/static_set_a
python -B Code/datasets/radiocal/scripts/07_draw_synthetic.py --scene marker --geometry set_a/s07 --condition noise_free nlos --out draws/marker_p07_nlos
python -B Code/datasets/radiocal/scripts/07_draw_synthetic.py --scene walk --geometry set_b/s01 --condition noise_free gaussian --seeds 0-4 --out draws/walk_s01
python -B Code/datasets/radiocal/scripts/07_draw_synthetic.py --reproduce
```

- Scenes. `static` holds the anchors of a session alone, as the frozen
  draws, which are this scene on `set_b/s03`. `marker` adds the tag of a
  quasi-static session (`set_a/s01` to `s20`) at its verified truth point, and
  any other geometry is refused. `walk` moves the mobile node of the session
  (DD98 in set_b, 8B05 in `set_a/s01` to `s20`) on a Lissajous or line path
  within the bounding box of the anchors (`--path`, `--duration`).
- Options: `--condition` (`noise_free`, `gaussian`, `nlos`,
  `nlos_per_range`, `biased`), `--seeds` (draw k uses seed k), `--epochs`,
  `--bias`, `--ranges-3d` for slant instead of horizontal distances, `--tag-z`
  for the height of a walking tag, `--dropouts` for the dropouts of the model,
  and the model values (`--sigma-hw` and the others). `--out` is required, and
  the tool refuses a folder inside `Data/` or one that holds a campaign.
- Output: a campaign `synthetic_<scene>_<set>` in the layout of `Data/`, with
  sessions `syn_<scene>_<condition>_<NN>`, the four views, and for a tag its
  truth in the frame of `nodes.yaml` (`session.yaml -> truth_frame: local`).
  `campaign.yaml -> generator` records the options, the command, the model
  values, the hashes of both generator modules and the commit they come
  from, and `sources` the hashes of every geometry input. A changed generator
  module draws with a warning, and the campaign records its own hashes.
- Noise-free ranges equal their generating distances. On a view whose ranges
  fix the geometry, such as the full anchor mesh, a method whose range model
  matches them recovers the geometry up to the gauge of the evaluation
  convention, so the error it keeps is its own error floor. Without
  `--dropouts`, a noise-free draw uses no random numbers and is written once.
- Under `nlos`, a walk keeps one multipath excess per tag-anchor pair for the
  whole walk, drawn at the distance of the first epoch.
- `--reproduce` draws the frozen setup in memory through the static scene of
  the tool and compares the 81 hashes with those stored in
  `Data/synthetic/*/session.yaml`. It writes nothing.

## Data dictionary

- `Data/README.md`: identifiers (`<set>/<session>`), the columns of
  `ranges.parquet` and `groundtruth.parquet`, the fields of `nodes.yaml`,
  `session.yaml` and `campaign.yaml`, the mask grammar, the coordinate
  systems and the field labels. `Data/set_a/README.md` and
  `Data/set_b/README.md` hold the properties and limits of each deployment.
- Frames: set_b lies in a local grid frame of ETRS89/UTM 33N (EPSG:25833) with
  DHHN2016 heights, its origin stored in `nodes.yaml -> crs`. set_a lies in a
  campaign-local tachymeter frame. The Vicon frame of the set_b walks is tied
  to the set_b grid by the surveyed calibration wand
  (`session.yaml -> transform_vicon_to_local`).
- Views: `fully_meshed`, `slam_bipartite`, `mobile_assisted` and `multi_hop`,
  in `Data/<set>/masks/` and as package data of `radiocal`. The datum of an
  estimate, through the priors that a view keeps or through a gauge triple,
  and both ways to compare an estimate with the survey, with and without the
  alignment, are in `Code/datasets/radiocal/README.md` ("Coordinate frames and
  gauge freedom").
- Limits, stated in the deployment READMEs: the Vicon truth covers about a
  fifth of the walk epochs because the logger dropped poses, and no native
  captures exist. The ranges carry a clock offset of about 7 s to the Vicon
  clock with a stated uncertainty. set_a has no timestamps. The set_b node
  D5B4 never ranges, and the set_b pair 5BB6-D38F is obstructed.
- The field labels (`los_nlos_field_labels.csv`) are a field judgement, not
  truth.
- Site: one industrial hall, so one building and one floor, with no outdoor
  part. No floor plan ships, and the surveyed nodes and control points of
  `nodes.yaml` are the only geometry of the site. How many persons took part
  in the campaigns is not recorded.
- Synthetic model values: the noise, the multipath and the maximum range are
  those of P. Schwarzbach, R. Weber and O. Michler, IEEE Sensors J.
  22(6):4836-4843, 2022. The outlier probability is a parameter that the paper
  defines without a value ("modeled variably", Sec. IV). The release sets it
  to 0.05, the value in the code of the author's earlier simulation framework
  that the simulator ports, and the draw tool takes another with `--p-out`.
  The bias of the `biased` condition equals the median anchor-pair residual of
  set_b. The values stand in `Data/synthetic/campaign.yaml -> generator`.
- Some texts name files of the companion tutorial's release that this release
  does not contain. None of these files is needed to load, rebuild or check
  the data.
  - `Code/methods/estimate_vicon_transform.py`, a UWB-based cross-check of the
    wand tie, appears in the set B builders and in the notes they write into
    `Data/set_b/campaign.yaml` and `session.yaml -> transform_provenance`.
  - `run_synthetic.py`, the tutorial's synthetic baseline, appears in the
    docstrings of `Code/methods/range_errors.py` and of scripts 05 and 07.
    Its `frozen.csv` is the default of their `--frozen` option and the
    `ranges_sha256_reference` of the synthetic YAML files.
  - The tutorial's evaluation module, whose exact-recovery checks drew their
    scenes there, appears in the docstring of `Code/methods/synthetic.py`.
    `data_facts.csv` names its `evaluation_slam.py` and `gt_error_budget.py`
    as the sources of four rule constants.
  - `Code/external/README.md` marks its benchmark parts, and
    `Code/datasets/radiocal/README.md` and `Data/README.md` mention the
    tutorial's estimators, benchmark tables and benchmark driver.

## Figures, tables and numbers of the descriptor

Every number that the data descriptor and its supplementary material print
about the data comes from
`Code/datasets/radiocal/scripts/06_data_facts.py --out DIR`, apart from the
numbers of Table 4, which a script of the descriptor's manuscript reads from
the files of this Zenodo record, and the quality reports
(`qa/report.md`, written by `03_qa_all.py`) that the supplementary material
transcribes. The data-facts script writes:

- `data_macros.tex`, one LaTeX macro per fact;
- `tab_sessions.tex`, the session table that the companion tutorial prints
  (the descriptor formats its Table 2 from `sessions.csv`);
- `sessions.csv`, one row per measured session (counts, ranges per pair,
  durations, window, rates, the directed pairs without ranges);
- `data_facts.csv`, each macro with its value, rule and source files;
- `pairs.csv`, one row per node pair of the residual sessions (residual,
  spread, availability, field label);
- `labels.csv`, the field labels against the residuals;
- `residual_quantiles.csv`, the distribution of the per-epoch range residuals;
- `synthetic_quantiles.csv`, the distribution of the residuals of the frozen
  synthetic draws per condition.

It reads only the released files and runs no estimator. Before it writes, it
checks the frozen synthetic draws against their model: the noise-free draw
equals its distances, the gaussian and biased draws match the noise and the
bias, every pair of an nlos draw matches its stored excess (zero where the
draw stores none), and the tail of
the nlos_per_range draws matches the share that the published model predicts.
Its rule constants are macros as well. Four restate the companion tutorial's
evaluation, two are read from the source of `04_build_set_a.py`, and five are
the data-facts script's own (the bias flag and the four tolerances of the synthetic
check), and the row of each in `data_facts.csv` names its source.

Where each float of the descriptor comes from:

| float | source |
|---|---|
| Fig. 1, topology views | `Code/descriptor/validation_figures.py`, from `Data/set_b/s01` loaded by `radiocal` with the four masks of `Data/set_b/masks/`, and the epochs of the tag matched to its poses by the coverage rule of `06_data_facts.py` |
| Fig. 2, layout | `Code/descriptor/validation_figures.py`, from `Data/*/nodes.yaml`, `Data/*/masks/mobile_assisted.yaml`, `Data/set_*/los_nlos_field_labels.csv` (the pairs labeled NLOS), and the `groundtruth.parquet` and `session.yaml` of `set_b/s01` and `s02` |
| Fig. 3, processing pipeline | drawn by hand (TikZ), no data |
| Fig. 4, range residuals | `Code/descriptor/validation_figures.py`, from `residual_quantiles.csv` |
| Fig. 5, pair availability | `Code/descriptor/validation_figures.py`, from `pairs.csv` |
| Table 1, data of the testing ground | set by hand, no number |
| Table 2, measured sessions | `sessions.csv`, formatted by a script of the descriptor's manuscript, which spans the quasi-static sessions `set_a/s01` to `s20` by their smallest and largest values and computes no other value |
| Table 3, settings of the range simulator | `data_macros.tex`, set by hand, with the options of `07_draw_synthetic.py` |
| Table 4, files | the files of this Zenodo record, which `SHA256SUMS` and `RAW_MANIFEST.md` list, counted by a script of the descriptor's manuscript: every file once, an archive by its members, sizes in decimal units (whole kB below 1 MB, else MB to one decimal), rows and columns from the Parquet metadata and the CSV files |
| Supplementary Table S1, measured sessions | `sessions.csv`, formatted by a script of the descriptor's manuscript that computes no value |
| Supplementary Table S2, quality report of each session | the `qa/report.md` of each session, transcribed by the same script |
| Supplementary Table S3, directed pairs without ranges | `sessions.csv` (`missing_directed_pairs`), formatted by the same script |
| Supplementary Table S4, residual and availability of every node pair | `pairs.csv`, formatted by the same script |
| Supplementary Table S5, field labels against the residuals | `labels.csv`, formatted by the same script |
| Supplementary Table S6, quantiles of the measured and the synthetic residuals | `residual_quantiles.csv` and `synthetic_quantiles.csv`, selected and rounded to the centimeter by a script of the descriptor's manuscript that computes no statistic |
| Supplementary Table S7, ground truth step by step | `data_macros.tex`, set by hand |
| Supplementary Fig. S1, synthetic residuals | `Code/descriptor/validation_figures.py`, from `synthetic_quantiles.csv` |

The formatting scripts stay with the manuscript, since they hold its layout
only, and every value they print is in the files above. The script that counts
Table 4 stays with it as well. It reads the record as uploaded, the raw
archives included, and every count and size it prints can be checked against
`SHA256SUMS`, `RAW_MANIFEST.md` and the files.

## Runtimes and determinism

Measured on an idle Intel Core Ultra 7 355 with 32 GB of memory, Windows 11
and Python 3.14.6 in the pinned environment, each command with interpreter
start. Other load lengthens the times: with three runs at once on the same
machine, a step took up to five times as long.

| step | time |
|---|---|
| `tests/test_smoke.py` | 20 to 30 s |
| `01_inspect_raw.py` | 5 s |
| `02_build_set_b.py` | 4 s |
| `04_build_set_a.py` | 8 s |
| `03_qa_all.py`, all 25 sessions | 15 s |
| `05_build_synthetic.py` | 5 s |
| `06_data_facts.py` | 12 s |
| `07_draw_synthetic.py --reproduce` | 3 s |
| `07_draw_synthetic.py --scene walk`, five conditions, one seed | 4 s |
| `Code/descriptor/validation_figures.py` | 7 s |
| `tests/check_rebuild.py` | 3 s |

A fresh environment installs in about four minutes, pinned or not, measured
with three installs at once.

The synthetic draws are seeded: draw k uses seed k, with one numpy generator
stream per error component. The draw tool records its options and the hashes
of the generator and of the geometry in each campaign it writes, so a draw
repeats exactly under the same numpy. The builders draw no random numbers. The figure
script writes its PDFs without a creation date, so a second run on the same
platform writes the same bytes. Without the font Times New Roman, matplotlib
takes another serif font, and the bytes differ. The set A
tag height comes from a robust least-squares fit (scipy), rounded to 1 cm.
Per-run fields are the commits in `PROVENANCE.yaml` and, in another
environment, the two fields named under *What the scripts rebuild*.

## Licences

- **Data and documentation** (everything under `Data/` and `docs/`, the files
  at the repository root apart from the two licences, and the raw archives of
  the deposit): Creative Commons Attribution 4.0 International, see
  `LICENSE-DATA`.
- **Code** (everything under `Code/` and `tests/`, their READMEs included):
  MIT, see `LICENSE-CODE`.
- No code of a third party ships. `Code/methods/range_errors.py` ports the
  author's own simulation framework. The parser
  `radiocal/io/qorvo_log.py` reads the log lines that the decoder of the
  UWB kit writes and contains none of its code. The firmware of the modules
  and any vendor licence key are not published.
- The public recordings TWR-CLOUD-Bern (MIT, by its Zenodo record) and
  selfloc (no licence stated) are not redistributed. Users fetch them, and
  `Code/external/` checks each file by its SHA-256 before it converts it.

## Versions

A major version changes canonical values or columns, a minor version adds
sessions or files, and a patch changes documentation and metadata only. All
versions hang under the concept DOI 10.5281/zenodo.24055895, which resolves to
the latest version, and `CHANGELOG.md` lists the changes of each.

## How to cite

Cite the deposit, preferably by its version DOI:

```bibtex
@misc{schwarzbach_uwbasc_2026,
  author    = {Schwarzbach, Paul},
  title     = {{UWB} Anchor Self-Calibration Dataset ({UWB-ASC})},
  year      = {2026},
  publisher = {Zenodo},
  version   = {1.0.0},
  doi       = {10.5281/zenodo.24055896}
}
```

and the data descriptor named at the top of this file. `CITATION.cff` holds
the same metadata.

Users of the readers in `Code/external/` cite the recordings they convert,
each by its record and its paper:

- TWR-CLOUD-Bern: D. Xenakis, A. Di Maio and T. Braun, Zenodo, version 5,
  doi 10.5281/zenodo.20277908, and "Descriptor: Two-Way-Ranging-Based
  Cooperative Localization With an Open UWB Dataset From Bern-University
  (TWR-CLOUD-Bern)", IEEE Data Descriptions 3:441-452, 2026,
  doi 10.1109/IEEEDATA.2026.3701019;
- selfloc: the repository <https://github.com/d3s-trento/selfloc> at commit
  `39c1271`, and P. Corbalán, G. P. Picco, M. Coors and V. Jain,
  "Self-Localization of Ultra-Wideband Anchors: From Theory to Practice",
  IEEE Access 11:29711-29725, 2023, doi 10.1109/ACCESS.2023.3261567.

## Questions and issues

Open an issue at <https://github.com/PaulSchwarzbach/UWB-ASC-dataset/issues>.

## Acknowledgments

The author thanks Fynn Hansen, Albrecht Michler, and Andrea Jung for their
support with the measurement campaigns, Deveritec GmbH for the firmware that
enabled the fully meshed measurements, and MRK Management Consultants GmbH for
access to the hall.

## Declaration on generative AI

The author used Anthropic's Claude models (Claude Fable 5, Opus 5 and Opus 5.5,
as the commit trailers of the sources name them) through the Claude Code
command-line interface to develop the dataset tooling, the synthetic writer,
the draw tool, the data-facts generator, the release scripts and the script
that draws the descriptor's figures, and to draft the documentation. Two instances of Claude Opus 5.5 transcribed the set_b field
labels from the scan independently of each other, and one transcribed the
set_a labels next to a script that extracted them. The author reviewed and edited
the code, the transcriptions and the documentation and takes full
responsibility for the content of this repository.
