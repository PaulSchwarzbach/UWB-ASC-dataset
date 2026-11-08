"""Smoke test of the UWB-ASC testing ground.

Run from the repository root after the install of the README:

    python -B tests/test_smoke.py

It checks every file against SHA256SUMS, loads one session per deployment,
joins every range, truth pose and field label to a node of its campaign,
applies the four topology masks, checks the 81 synthetic draws against their
stored hashes and draws them again in memory, and recomputes a few data facts
and the per-pair table with Code/datasets/radiocal/scripts/06_data_facts.py.
The draw tool 07_draw_synthetic.py then redraws the frozen draws through its
static scene, draws a short noise-free walk and a marker scene into a temporary
folder, which the test removes, and must refuse a marker scene on set_b.
With the environment variable UWBASC_EXTERNAL set to the folder of the
campaigns that Code/external/convert_external.py wrote, the test also loads
those campaigns, joins their ranges to their nodes and applies their two views.
It writes nothing else.
Run as plain python or through pytest.
"""
import hashlib
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "Data"
SCRIPTS = REPO / "Code" / "datasets" / "radiocal" / "scripts"
sys.path.insert(0, str(REPO / "Code" / "methods"))  # range_errors, synthetic

import radiocal  # noqa: E402

RANGE_COLUMNS = ["t", "t_raw", "seq", "from_id", "to_id", "range_m"]
MASKS = ["fully_meshed", "slam_bipartite", "mobile_assisted", "multi_hop"]
PRIOR_SUBSET = {"5BB6", "4A23", "8B05"}
CAMPAIGNS = ["set_a", "set_b", "synthetic"]
# values that the data descriptor prints, from 06_data_facts.py
FACTS = {"WEnodeAnchorsSetB": "10", "WEnodeAnchorsStaticSetA": "12",
         "WEresAaMedSetB": "0.27", "WEgtCoverShareSpan": "19--20",
         "DFinvalidPctSetB": "0.066", "DFsynSessions": "81",
         "DFsynResMedBiased": "0.270", "DFsynTailSharePct": "20.1"}
EXTERNAL_MASKS = ["fully_meshed", "multi_hop"]  # the views of a converted campaign


def script(name):
    """A numbered script of Code/datasets/radiocal/scripts as a module."""
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), SCRIPTS / name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_checksums():
    sums = REPO / "SHA256SUMS"
    if not sums.is_file():
        print("skip checksums: no SHA256SUMS here (not a built release)")
        return
    bad, n = [], 0
    for line in sums.read_text(encoding="utf-8").splitlines():
        digest, path = line.split("  ", 1)
        n += 1
        p = REPO / path
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            bad.append(path)
    assert not bad, f"{len(bad)} of {n} files differ from SHA256SUMS, for example {bad[:3]}"
    print(f"ok  checksums: {n} files match SHA256SUMS")


def test_sessions_load():
    g25 = radiocal.load_session(DATA / "set_b" / "s03")
    g24 = radiocal.load_session(DATA / "set_a" / "s21")
    for g in (g25, g24):
        assert list(g.edges.columns[:6]) == RANGE_COLUMNS, g.edges.columns
        assert len(g.edges) > 0
    assert len(g25.nodes) == 11, f"set_b nodes: {len(g25.nodes)}"
    assert len(g24.nodes) == 12, f"set_a nodes: {len(g24.nodes)}"
    print(f"ok  sessions load ({len(g25.edges)} + {len(g24.edges)} ranges)")


def test_identifiers():
    n_sessions = n_ranges = 0
    for c in CAMPAIGNS:
        reg = yaml.safe_load((DATA / c / "nodes.yaml").read_text(encoding="utf-8"))
        ids = {n["id"] for n in reg["nodes"]}
        for sy in sorted((DATA / c).glob("*/session.yaml")):
            e = pd.read_parquet(sy.parent / "ranges.parquet", columns=["from_id", "to_id"])
            unknown = (set(e["from_id"]) | set(e["to_id"])) - ids
            assert not unknown, f"{c}/{sy.parent.name}: ranges name unknown nodes {unknown}"
            gt = sy.parent / "groundtruth.parquet"
            if gt.exists():
                truth = set(pd.read_parquet(gt, columns=["node_id"])["node_id"])
                assert truth <= ids, f"{c}/{sy.parent.name}: truth names {truth - ids}"
            n_sessions += 1
            n_ranges += len(e)
        labels = DATA / c / "los_nlos_field_labels.csv"
        if labels.exists():
            lab = pd.read_csv(labels, dtype=str)
            unknown = (set(lab["node_a"]) | set(lab["node_b"])) - ids
            assert not unknown, f"{c}: field labels name unknown nodes {unknown}"
    print(f"ok  every range, pose and label joins a node of its campaign "
          f"({n_sessions} sessions, {n_ranges} ranges)")


def test_mask_invariants():
    for sdir in ["set_b/s01", "set_a/s07"]:
        g = radiocal.load_session(DATA / sdir)
        roles = dict(zip(g.nodes["id"], g.nodes["role"]))
        for name in MASKS:
            v = g.apply_mask(name)
            assert len(v.edges) > 0, f"{sdir}/{name}: empty view"
            aa = ((v.edges["from_id"].map(roles) == "anchor")
                  & (v.edges["to_id"].map(roles) == "anchor")).sum()
            if name == "slam_bipartite":
                assert aa == 0, f"{sdir}: anchor-anchor edges in the bipartite view"
            if name == "fully_meshed":
                assert len(v.priors()) == 0, f"{sdir}: fully_meshed exposes priors"
                assert aa == len(v.edges), f"{sdir}: other edges in fully_meshed"
            if name in ("mobile_assisted", "multi_hop"):
                anchors = set(g.nodes.loc[g.nodes["role"] == "anchor", "id"])
                assert set(v.priors()["id"]) == PRIOR_SUBSET & anchors, \
                    f"{sdir}/{name}: prior subset {set(v.priors()['id'])}"
        print(f"ok  mask invariants hold on Data/{sdir}")


def test_synthetic():
    syn = script("05_build_synthetic.py")
    stored, from_files = {}, 0
    for sy in sorted((DATA / "synthetic").glob("syn_*/session.yaml")):
        d = yaml.safe_load(sy.read_text(encoding="utf-8"))["draw"]
        r = pd.read_parquet(sy.parent / "ranges.parquet", columns=["range_m"])["range_m"]
        stored[(d["condition"], int(d["index"]))] = d["ranges_sha256"]
        from_files += syn.ranges_sha256(r.to_numpy(float)) == d["ranges_sha256"]
    assert len(stored) == 81 and from_files == 81, \
        f"synthetic: {from_files} of {len(stored)} files match their ranges_sha256"
    draws = syn.draw_all(syn.reference(DATA))
    redrawn = sum(syn.ranges_sha256(e["range_m"].to_numpy(float)) == stored.get(k)
                  for k, (e, _) in draws.items())
    camp = yaml.safe_load((DATA / "synthetic" / "campaign.yaml").read_text(encoding="utf-8"))
    drawn_with = camp["generator"]["numpy_version"]
    if redrawn == len(stored):
        print(f"ok  synthetic: {from_files} of 81 files match their ranges_sha256, "
              f"and the redraw equals them")
        return
    msg = (f"synthetic redraw: {redrawn} of {len(stored)} draws equal the files "
           f"(numpy {np.__version__}, the files were drawn with numpy {drawn_with})")
    assert np.__version__ != drawn_with, msg
    print(f"note {msg}: generator drift of another numpy, the files stay valid")


def test_data_facts():
    facts = script("06_data_facts.py")
    F, _ = facts.compute(DATA)
    got = {r["macro"]: r["value"] for r in F.rows}
    bad = {k: (got.get(k), v) for k, v in FACTS.items() if got.get(k) != v}
    assert not bad, f"data facts differ (computed, printed): {bad}"
    print(f"ok  data facts: {len(got)} computed, {len(FACTS)} checked against the printed values")
    # the per-pair table behind the descriptor's figures and supplementary tables;
    # pair_table stops when a pair residual disagrees with its macro
    pairs = facts.pair_table(DATA, facts=got)
    print(f"ok  pairs: {len(pairs)} node pairs, consistent with the residual macros")


def draw(*args) -> subprocess.CompletedProcess:
    """07_draw_synthetic.py with the given options, in this interpreter."""
    return subprocess.run([sys.executable, "-B", str(SCRIPTS / "07_draw_synthetic.py"), *args],
                          capture_output=True, text=True)


def noise_free_exact(sdir: Path) -> None:
    """The ranges of a noise-free scene equal the 2-D distances between the
    positions of nodes.yaml and the truth of the tag, by the formula of the
    generator, and the four views apply."""
    g = radiocal.load_session(sdir)
    pos = {r.id: (r.x, r.y) for r in g.nodes.itertuples() if r.prior_type != "none"}
    e = g.edges
    unknown = (set(e["from_id"]) | set(e["to_id"])) - set(g.nodes["id"])
    assert not unknown, f"{sdir.name}: ranges name unknown nodes {unknown}"
    if len(g.truth):
        assert g.truth["frame"].dtype == np.float64, f"{sdir.name}: frame is not numeric"
        tag = str(g.truth["node_id"].iloc[0])
        at = g.truth.set_index("t")[["x", "y"]]
        t_epoch = e.groupby("seq")["t"].min()
        tag_xy = {s: (tuple(at.iloc[0]) if len(at) == 1 else tuple(at.loc[t]))
                  for s, t in t_epoch.items()}
    def xy(node, seq):
        return tag_xy[seq] if node not in pos else pos[node]
    a = np.array([xy(n, s) for n, s in zip(e["from_id"], e["seq"])], dtype=float)
    b = np.array([xy(n, s) for n, s in zip(e["to_id"], e["seq"])], dtype=float)
    d = np.linalg.norm(a - b, axis=-1)
    assert np.array_equal(e["range_m"].to_numpy(float), d), \
        f"{sdir.name}: noise-free ranges differ from the generating distances"
    for name in MASKS:
        assert len(g.apply_mask(name).edges) > 0, f"{sdir.name}/{name}: empty view"


def test_draw_tool():
    camp = yaml.safe_load((DATA / "synthetic" / "campaign.yaml").read_text(encoding="utf-8"))
    drawn_with = camp["generator"]["numpy_version"]
    r = draw("--reproduce")
    if r.returncode == 0:
        print("ok  draw tool: its static scene reproduces the 81 frozen draws")
    else:
        msg = f"draw tool --reproduce: {r.stdout.strip() or r.stderr.strip()}"
        assert "DRIFT" in r.stdout, msg  # a changed module or another fault, no drift
        assert np.__version__ != drawn_with, msg
        print(f"note {msg}: generator drift of another numpy, the files stay valid")
    with tempfile.TemporaryDirectory() as tmp:
        walk, marker, refused = Path(tmp) / "walk", Path(tmp) / "marker", Path(tmp) / "refused"
        for out, opts in ((walk, ["--scene", "walk", "--duration", "8"]),
                          (marker, ["--scene", "marker", "--geometry", "set_a/s07",
                                    "--epochs", "20"])):
            r = draw(*opts, "--condition", "noise_free", "--out", str(out))
            assert r.returncode == 0, f"draw tool {' '.join(opts)}: {r.stderr.strip()}"
            sessions = sorted(out.glob("syn_*/session.yaml"))
            assert len(sessions) == 1, f"draw tool {' '.join(opts)}: {len(sessions)} sessions"
            noise_free_exact(sessions[0].parent)
        r = draw("--scene", "marker", "--out", str(refused))
        assert r.returncode != 0 and not refused.exists(), "draw tool: a marker on set_b was not refused"
    print("ok  draw tool: noise-free walk and marker scenes equal their distances, "
          "a marker on set_b is refused")


def test_external():
    root = os.environ.get("UWBASC_EXTERNAL")
    if not root:
        print("skip external: set UWBASC_EXTERNAL to the folder of the converted campaigns")
        return
    camps = sorted(p for p in Path(root).glob("ext_*") if (p / "campaign.yaml").is_file())
    assert camps, f"external: no converted campaign ext_* under {root}"
    for c in camps:
        meta = yaml.safe_load((c / "campaign.yaml").read_text(encoding="utf-8"))
        triple = set(meta["benchmark"]["gauge_triple"])
        reg = yaml.safe_load((c / "nodes.yaml").read_text(encoding="utf-8"))
        kept = {n["id"] for n in reg["nodes"] if "status" not in n}
        masks = sorted(p.stem for p in (c / "masks").glob("*.yaml"))
        assert masks == EXTERNAL_MASKS, f"{c.name}: masks {masks}"
        for sy in sorted(c.glob("*/session.yaml")):
            g = radiocal.load_session(sy.parent)
            unknown = (set(g.edges["from_id"]) | set(g.edges["to_id"])) - kept
            assert not unknown, f"{c.name}/{sy.parent.name}: ranges name nodes that are not kept"
            for name in EXTERNAL_MASKS:
                v = g.apply_mask(name)
                assert len(v.edges) > 0, f"{c.name}/{sy.parent.name}/{name}: empty view"
                want = set() if name == "fully_meshed" else triple
                assert set(v.priors()["id"]) == want, f"{c.name}/{name}: priors"
    print("ok  external: every converted campaign loads, joins its kept nodes and applies "
          "its two views, multi_hop with the gauge triple")


if __name__ == "__main__":
    test_checksums()
    test_sessions_load()
    test_identifiers()
    test_mask_invariants()
    test_synthetic()
    test_data_facts()
    test_draw_tool()
    test_external()
    print("\nsmoke test passed")
