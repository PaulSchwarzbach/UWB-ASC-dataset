# FAIR notes

How the UWB Anchor Self-Calibration Dataset (UWB-ASC) meets the FAIR
principles for data and code, and, in the last section, the best practices for
open data in indoor positioning. Each row names the mechanism and the file that
carries it.

## Findable

| mechanism | where |
|---|---|
| Persistent identifier, per version and for the concept | the Zenodo deposit (version DOI and concept DOI), cited in `README.md` and `CITATION.cff` |
| Machine-readable citation metadata | `CITATION.cff` (CFF 1.2.0, ORCID of the author), `.zenodo.json` (resource type dataset) |
| Keywords and description | `.zenodo.json`, `CITATION.cff` |
| One identifier scheme across all files | sessions `<set>/<session>`, node ids in hex, mask names (`Data/README.md`, *Identifier convention*); `tests/test_smoke.py` joins every range, truth pose and field label to a node |

## Accessible

| mechanism | where |
|---|---|
| Open access without registration | the public GitHub repository `PaulSchwarzbach/UWB-ASC-dataset` and the Zenodo record, over HTTPS |
| Long-term retention | Zenodo, which keeps the deposit independent of the GitHub repository |
| Raw sources retained | the raw archives of the deposit (Qorvo backup logs, MQTT SQLite databases, Total Station files), verified by `RAW_MANIFEST.md` and by the hashes in `Data/<set>/campaign.yaml` |
| Integrity | `SHA256SUMS` lists every file of the repository, and `.gitattributes` keeps the bytes on checkout |

## Interoperable

| mechanism | where |
|---|---|
| Open, columnar and text formats | Parquet for ranges and truth, YAML for metadata, CSV for the truth adjudication and the field labels, Markdown for the QA reports |
| Coordinate reference systems in full | set_b: ETRS89/UTM 33N (EPSG:25833) with DHHN2016 heights and the stored local origin; set_a: the campaign-local tachymeter frame; the Vicon frame with its wand-tie transform (`Data/README.md`, *Coordinate systems*) |
| Column and field dictionaries with units | `Data/README.md`, the READMEs of the deployments |
| Language-independent access | any Parquet and YAML reader; MATLAB `parquetread` (R2019a or newer) |

## Reusable

| mechanism | where |
|---|---|
| Explicit licences | `LICENSE-DATA` (CC BY 4.0) for the data and documentation, `LICENSE-CODE` (MIT) for the code |
| Provenance from raw to canonical | the SHA-256 of every raw file in `campaign.yaml` and `session.yaml -> sources` (both hashes of a stripped database), and the commits in `PROVENANCE.yaml`. A campaign of the draw tool records its options, the hashes of the generator modules and those of its geometry inputs in `campaign.yaml` |
| Reproducible pipeline | the builders of `Code/datasets/radiocal/scripts/` rebuild every canonical file from the raw deposit, the synthetic writer redraws the 81 seeded draws, the draw tool redraws them through its own scene code (`--reproduce`), and `tests/check_rebuild.py` compares (README, *What the scripts rebuild*) |
| Pinned environment | `requirements.txt`, the library versions that wrote the files |
| Quality documentation | the per-session QA reports (`<session>/qa/`), the truth adjudication of set_a, the field labels marked as a field judgement, and the limits stated in the deployment READMEs |
| Generated numbers | `Code/datasets/radiocal/scripts/06_data_facts.py` writes every number that the data descriptor and its supplementary material print about the data: the macros, each with its rule and source files in `data_facts.csv`, and the per-pair residuals, availability and residual distributions that the figures and supplementary tables show (`synthetic_quantiles.csv` for the synthetic draws, which the generator first checks against their model), each file with its rules in the docstring of the generator. `Code/descriptor/validation_figures.py` draws those figures from the released files. The descriptor's file table counts the files of this deposit, which `SHA256SUMS` lists, and its supplementary material transcribes the quality reports of `03_qa_all.py` |

## Best practices for open data in indoor positioning

How the release meets the recommendations of two studies by Anagnostopoulos et
al.:
- ORDIP, "ORDIP: Principle, practice and guidelines for open research data in
  indoor positioning", Internet of Things 30 (2025) 101485, its lessons and
  guidelines in §5 (pp. 26-31);
- "Comprehensive assessment of open science practices in indoor positioning:
  Open data, code, and material", IEEE Journal of Indoor and Seamless
  Positioning and Navigation 3 (2025) 175-194, its best practices in §V-B and
  Fig. 10 (pp. 184-187), cited as JISPIN below.

Each row names the practice, its source, its status for this release, and the
mechanism and file that carry it. The status is "met", "in part" (the last
column says which part is missing), "planned" (with the step that meets it), or
"not followed" (with the reason).

| practice | source | status | where |
|---|---|---|---|
| A long-term archive that issues persistent identifiers | ORDIP §5.1.1, p. 26, §5.1.8, p. 29; JISPIN p. 186 | met | the Zenodo record, with the version DOI 10.5281/zenodo.24055896 of version 1.0.0 and the concept DOI 10.5281/zenodo.24055895 of all versions |
| Compliance with the FAIR principles | ORDIP §5.2.3, p. 31 | met | the four sections above |
| Full metadata of the collection and of the environment | ORDIP §5.1.2, p. 27 | met | `README.md` (*Data dictionary*, the site: one building, one floor, no outdoor part), the README of each deployment (hardware, motion, ground truth, limits), `Data/*/campaign.yaml` |
| What was not recorded, stated as such | ORDIP §5.1.2, p. 27, and its count of undefined fields, pp. 17-20 | met | the *Not recorded* lists of the deployment READMEs (the physical-layer settings, the firmware version, the time of day of `set_a`), and `README.md` (the number of persons) |
| Open formats, and code that loads them | ORDIP §5.1.3, p. 27, §5.2.3, p. 31 | met | Parquet and YAML, readable by any Parquet and YAML reader, and the `radiocal` loader |
| One numbering protocol for versions, linked versions, and the changes of each in the metadata | ORDIP §5.1.4, pp. 27-28 | met | the version policy of `README.md` (*Versions*), `CHANGELOG.md`, the changes of each version in the notes of the Zenodo record, and all versions under its concept DOI |
| The scripts that derive data, and credit to the primary source | ORDIP §5.1.5, p. 28; JISPIN pp. 186-187 | met | the build scripts rebuild every canonical file from the raw archives, the synthetic writer and the draw tool record their seeds, parameters and the source of the parameters, and the readers credit TWR-CLOUD-Bern and selfloc and ask their users to cite both |
| Metadata and a sample readable before the bulk download | ORDIP §5.1.6, pp. 28-29, §5.2.3, p. 31 | in part | `README.md`, the data dictionary `Data/README.md`, and the QA report of each session. `README.md` gives the size of each part, and the raw archives come apart from the repository snapshot. Missing: a small sample of ranges and truth as a file of its own next to the snapshot |
| One licence per object, and a citation policy | ORDIP §5.1.7, p. 29 | met | `LICENSE-DATA` (CC BY 4.0) for the data and the documentation, `LICENSE-CODE` (MIT) for the code, scoped in `README.md` (*Licences*), `CITATION.cff` and *How to cite* |
| The dataset and its paper as two objects with two identifiers | ORDIP §5.1.8, p. 29; JISPIN p. 186 | in part | *How to cite* names the Zenodo record and the data descriptor apart. Missing: the identifier of the data descriptor, which its preprint and its article give |
| A short name | JISPIN p. 186 | met | UWB-ASC, in the record, the README, the paper and the citation |
| The code of the work shared, not only its data | JISPIN p. 185 | met | all code of the release, under MIT |
| The data available when the paper is reviewed | JISPIN p. 186 | met | the Zenodo record, public before the data descriptor was submitted |
| The use shown, next to the same use of an existing dataset | ORDIP §5.2.3, p. 31 | met | the loader with the topology views, and the readers that apply both to TWR-CLOUD-Bern and selfloc |
| Declared selections, so that results compare | ORDIP §5.2.1, p. 30, §6, p. 31; JISPIN p. 185 | met | the four topology views and the evaluation convention (`Data/README.md`, *Mask grammar*, and `Code/datasets/radiocal/README.md`) |
| Coordinates with their reference system | ORDIP §5.2.1, p. 30 | met | `Data/README.md`, *Coordinate systems* |
| The area of the collection | ORDIP §5.2.1, p. 30 | in part | every surveyed position in `Data/*/nodes.yaml`. Missing in these files: the extent of the surveyed nodes, which the data descriptor gives |
| A floor plan | ORDIP §5.2.1, p. 30 | not followed | no floor plan exists for release, and the surveyed nodes and control points are the only geometry of the site |
| Photos and videos of the setup | ORDIP §5.2.2, p. 30 | not followed | no photos in version 1.0.0, since their publication needs the permission of the site owner and of the photographers |
| Every configurable parameter of every device | ORDIP §5.2.2, p. 30 | not followed | the physical-layer settings and the firmware version were not recorded (the README of each deployment) |
| The path of a moving collector, and the checkpoints on a map | ORDIP §5.2.2, pp. 30-31 | met | the logged poses in `Data/set_b/s*/groundtruth.parquet`, and the surveyed markers `P01` to `P20` in `Data/set_a/nodes.yaml` |
| The instructions to the collectors, and the changes during a campaign | ORDIP §5.2.2, pp. 30-31 | not followed | no campaign file records them |
| Reuse tested by someone who took no part in the collection | ORDIP §5.2.3, p. 31 | in part | an internal code check of this release on 2026-11-06, whose report the author keeps: AI agents with no knowledge of the project read the release and the data descriptor alone, ran the documented steps in fresh environments on Python 3.10 and 3.14, and compared the outputs with the release and the paper. Missing: a test by a person who took no part in the collection |
