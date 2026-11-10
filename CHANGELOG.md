# Changelog

Changes of the UWB-ASC testing ground, one section per published version. The
version numbers are those of the Zenodo versions. Changes on GitHub `main` that
no version holds yet stand under *Unreleased*.

## [Unreleased]

Documentation and metadata on GitHub `main`, not yet in a Zenodo version:
- the preprint of the data descriptor, arXiv:2611.11579
  (doi 10.48550/arXiv.2611.11579), in the README (its opening and *How to
  cite*), as the preferred citation of `CITATION.cff`, as `isDescribedBy` in
  `.zenodo.json`, and in `docs/FAIR.md`, whose row on the dataset and its paper
  is now met;
- `PROVENANCE.yaml` names the commits of this build, whose release sources
  equal those of 1.0.0.

## [1.0.0] - 2026-11-08

First release:
- the LOS deployment (`set_b`, 2025-10-22) and the NLOS deployment (`set_a`,
  2025-03-13) of one industrial hall in Torgau, as canonical Parquet and YAML
  sessions with their QA reports;
- the field LOS/NLOS labels of both deployments, a field judgement;
- the 81 seeded synthetic draws on the surveyed `set_b/s03` anchors;
- the range-error generator as code, with the draw tool
  `07_draw_synthetic.py`, which draws new seeded scenes outside the deposit;
- the `radiocal` package with the builders, the synthetic writer and the
  data-facts generator;
- the script that draws Figs. 1, 2, 4, 5 and S1 of the data descriptor from the
  released files (`Code/descriptor/validation_figures.py`);
- the readers of TWR-CLOUD-Bern and selfloc, with no recording redistributed;
- the raw archives of both deployments in the Zenodo deposit.
