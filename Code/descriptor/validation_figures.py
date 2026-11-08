"""Figures of the data descriptor UWB-ASC: Figs. 1, 2, 4, 5 and S1.

The figures are drawn from the released files under Data/ and from the output
folder of the data-facts generator
(Code/datasets/radiocal/scripts/06_data_facts.py --out DIR), which holds every
plotted value that is not itself a released file:

  Fig. 1  fig_views_a_fully_meshed.pdf, fig_views_b_mobile_assisted.pdf,
          fig_views_c_slam_bipartite.pdf, fig_views_d_multi_hop.pdf,
          fig_views_legend.pdf
          The four topology views of the walk set_b/s01, each the mask of the
          campaign (Data/set_b/masks/) that radiocal applies to the session:
          - the anchors at their surveyed positions;
          - the anchor pairs that the view keeps, straight, and as arcs bent
            by LABEL_RAD to one side where the straight line passes within
            ARC_CLEAR_M of a third anchor;
          - in the views that keep the ranges of the tag, its logged poses and
            the ranges of N_FAN epochs, each a fan from the pose matched to the
            epoch to the anchors that ranged with the tag in it;
          - the anchors of the datum (the subset of masks/mobile_assisted.yaml):
            filled where the view keeps their surveyed priors (the prior
            subset), and outlined where it keeps no prior and the same anchors
            form the default gauge triple.
          The fan epochs follow the coverage rule of 06_data_facts.py
          (tag_epochs: the earliest range of the tag in an epoch, matched to
          the nearest Vicon pose within MATCH_TOL_S, under the wand tie of
          session.yaml). Steps above MAX_GAP_S split the poses into bursts,
          farthest-point sampling of the burst medians picks N_FAN bursts,
          starting at the first, and each burst gives its middle matched epoch.
          The script stops when the priors of a view differ from the subset of
          its mask or are neither none nor that triple, when slam_bipartite
          keeps an anchor pair, when fully_meshed
          or multi_hop keeps a range of the tag, when multi_hop keeps a pair
          that fully_meshed lacks, or when the ranges of mobile_assisted differ
          from those of fully_meshed and slam_bipartite together. Fig. 1 has no
          axes, since Fig. 2 gives the frame.
  Fig. 2  fig_layout_a_set_b.pdf, fig_layout_b_set_a.pdf, fig_layout_legend.pdf
          The surveyed layout of each deployment, from nodes.yaml:
          - the anchors, and the prior subset of the views
            (masks/mobile_assisted.yaml);
          - the node that never ranges;
          - the control and reference points (a point whose shots conflict,
            conflict: true in nodes.yaml, is left out), and the markers of the
            roving tag, drawn above the anchors;
          - the origin of the Vicon frame (control point WAND-0-0);
          - the pairs that the field labels (los_nlos_field_labels.csv) mark
            NLOS alone, without the pairs with two values, as straight lines
            between the surveyed positions of their nodes. A line that passes
            within LABEL_CLEAR_PT of another mark of the panel, one that does
            not sit at an end of the pair, gives way to the first arc of
            LABEL_BENDS that clears every mark, or else to the one with the
            largest clearance. The script stops when no arc clears more than
            the line;
          - the logged tag poses of the set_b walks s01 and s02, registered by
            the wand tie of their session.yaml.
  Fig. 4  fig_residuals.pdf
          The empirical distribution of the per-epoch range residuals of both
          deployments (residual_quantiles.csv). The grid lines of the ordinate
          mark the median, P75 and P95 (ECDF_LEVELS), and an unlabeled one
          the end at one.
  Fig. S1 fig_synthetic_residuals.pdf (supplementary material)
          The empirical distribution of the residuals of the frozen synthetic
          draws per condition (synthetic_quantiles.csv), on the abscissa and
          the grid lines of Fig. 4.
  Fig. 5  fig_availability_a_set_b.pdf, fig_availability_b_set_a.pdf,
          fig_availability_legend.pdf
          The share of the epochs in which each directed pair ranges
          (pairs.csv).

Fig. 3 of the article, the processing pipeline, is drawn by hand in TikZ.
Each PDF holds one axes or one legend, and the article arranges the panels as
subfloats. A figure carries tick labels, axis labels and legends, and no other
text. The PDFs are written without a creation date, so a second run on the
same platform writes the same bytes. The fonts are Times New Roman, or the
serif fallback of matplotlib where it is missing.

From the repository root, after `06_data_facts.py --out facts`:

    python -B Code/descriptor/validation_figures.py --facts facts --out figures

It writes only into --out and runs no estimator.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ next to the released code

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.cm import ScalarMappable  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, Normalize  # noqa: E402
from matplotlib.legend_handler import HandlerTuple  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Patch  # noqa: E402
from matplotlib.ticker import FixedLocator, FuncFormatter, MultipleLocator, NullLocator  # noqa: E402

HERE = Path(__file__).resolve()
SETS = ("set_b", "set_a")
WALKS = ("s01", "s02")  # the set_b sessions whose poses the wand tie registers

# ---------------------------------------------------------------- the style
# The figure system of the companion tutorial, at the sizes of the IEEEoj-data
# class: \columnwidth 246 pt, \textwidth 504 pt.
COLUMN_W, TEXT_W = 3.40, 6.97          # inches
FS_LABEL, FS_TICK, FS_LEGEND = 8, 7, 7
LW_DATA = 1.1
BLUE, ORANGE, TEAL = "#2166AC", "#E08214", "#1A8A6A"   # palBlue, palOrange, palTeal
PURPLE = "#984EA3"                     # palPurple
GREY_LIGHT, GREY_MID, GREY_DARK = "#C8C8C8", "#8C8C8C", "#4D4D4D"
GREY_POSE = "#A8A8A8"                  # the logged tag poses, behind every node
COLOR = {"set_b": BLUE, "set_a": ORANGE}
STYLE = {
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": FS_LABEL,
    "axes.labelsize": FS_LABEL,
    "xtick.labelsize": FS_TICK,
    "ytick.labelsize": FS_TICK,
    "legend.fontsize": FS_LEGEND,
    "axes.linewidth": 0.5,
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "xtick.minor.size": 1.5,
    "ytick.minor.size": 1.5,
    "xtick.major.pad": 2.0,
    "ytick.major.pad": 2.0,
    "axes.labelpad": 2.5,
    "axes.grid": False,
    "lines.linewidth": LW_DATA,
    "legend.frameon": True,
    "legend.fancybox": False,
    "legend.framealpha": 0.92,
    "legend.edgecolor": "#CCCCCC",
    "legend.borderpad": 0.35,
    "legend.handlelength": 1.6,
    "legend.handletextpad": 0.5,
    "legend.labelspacing": 0.3,
    "legend.borderaxespad": 0.4,
    "pdf.fonttype": 42,
    "savefig.dpi": 600,
    "text.usetex": False,
}
GRID = dict(color=GREY_LIGHT, lw=0.35)

# Fig. 1: the four views of one walk, in the order of the list of views in the
# article, each panel a quarter of the text width less the gaps of \hfil, with
# shared limits and no axes
VIEWS_SESSION = ("set_b", "s01")
VIEWS = (("fully_meshed", "fig_views_a_fully_meshed"),
         ("mobile_assisted", "fig_views_b_mobile_assisted"),
         ("slam_bipartite", "fig_views_c_slam_bipartite"),
         ("multi_hop", "fig_views_d_multi_hop"))
N_FAN = 4                      # the fans of the tag, as in the tutorial's views figure
VIEWS_AXES_W = 1.62            # inches
VIEWS_MARGIN = dict(left=0.02, right=0.02, bottom=0.02, top=0.02)
VIEWS_PAD_M = 0.6              # around every mark, arcs included
# A pair whose straight line passes this close to a third anchor would hide
# behind it, so it bends by LABEL_RAD to one side (Fig. 2 has its own rule in
# print points, LABEL_CLEAR_PT). In set_b these
# are four long pairs along the row 5BB6, 4AA4, 5388, 4503 and 4A23, and three
# pairs that pass 8AA5, 8B05 and 5388. Every other pair is straight.
ARC_CLEAR_M = 0.4
VIEW_LW, VIEW_ALPHA = 0.45, 0.85
VIEW_MS, VIEW_MS_D, VIEW_MS_TAG = 3.4, 3.2, 2.0
# Fig. 2: one panel height for both deployments, each panel at the aspect of its layout
LAYOUT_AXES_H = 2.05
LAYOUT_MARGIN = dict(left=0.40, right=0.05, bottom=0.32, top=0.04)
LAYOUT_PAD_M = 1.0
# Figs. 4 and S1: one flat axes box in one column each, on one abscissa
ECDF_W, ECDF_H = 2.88, 1.40
ECDF_MARGIN = dict(left=0.42, right=0.10, bottom=0.34, top=0.05)
ECDF_XLIM = (-1.0, 3.0)
# the grid lines of the ordinate: the median, P75 and P95, which read off the
# curves where these end within the abscissa, and an unlabeled grid line at
# one, against which a curve that ends below one
# shows
ECDF_LEVELS = (0.0, 0.5, 0.75, 0.95)
# Fig. 2: the pairs labeled NLOS, thin lines behind the nodes. A straight line
# that passes a third mark, in set_b along the row 5BB6, 4AA4, 5388, 4503 and
# 4A23, would make that mark look like an end of the pair. Such a pair becomes
# the first arc of LABEL_BENDS (a share of its length, to either side) that
# clears every mark, or else the one with the largest clearance, never one that
# clears less than the line. The clearance
# is set in print points, since the two panels have different scales (0.4 m is
# 2 pt in panel (b), less than the radius of a node), and a mark within
# LABEL_CLEAR_PT of an end of the pair, such as the marker P01 under the static
# 8B05 of set_a, does not count.
LABEL_LW, LABEL_ALPHA, LABEL_RAD = 0.6, 0.6, 0.15
LABEL_BENDS = (LABEL_RAD, -LABEL_RAD, 2 * LABEL_RAD, -2 * LABEL_RAD)
LABEL_CLEAR_PT = 3.0   # the radius of a node, half the line width, and a margin
# the conditions of the synthetic draws in Fig. S1: the gaussian family in
# teal, the NLOS family in purple, and the noise-free draw in grey
SYN_CURVES = (("noise_free", GREY_DARK, "-"), ("gaussian", TEAL, "-"),
              ("biased", TEAL, "--"), ("nlos", PURPLE, "-"),
              ("nlos_per_range", PURPLE, "--"))
# Fig. 5: square matrices, two in one row. The bottom margin holds the rotated
# node ids and the axis label with the white of Fig. 2 below it.
MATRIX_SIDE = 2.40
MATRIX_MARGIN = dict(left=0.50, right=0.04, bottom=0.43, top=0.04)
AVAIL_CMAP = LinearSegmentedColormap.from_list("availability", ["#E7F2ED", TEAL])


def panel(axes_w: float, axes_h: float, left: float, right: float, bottom: float,
          top: float):
    """One figure with one axes of the given size at fixed margins (inches)."""
    fig = plt.figure(figsize=(left + axes_w + right, bottom + axes_h + top))
    w, h = fig.get_size_inches()
    ax = fig.add_axes([left / w, bottom / h, axes_w / w, axes_h / h])
    return fig, ax


def save(fig, out: Path, name: str, tight: bool = False) -> str:
    """The PDF without a creation date, so that a rerun writes the same bytes."""
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight" if tight else None,
                pad_inches=0.02, metadata={"CreationDate": None})
    plt.close(fig)
    return f"{name}.pdf"


def read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------- the inputs

def default_data() -> Path | None:
    """Data/ of the release that holds this script, or, in the descriptor's
    working repository, that of its built release Published_repo/."""
    for p in HERE.parents:
        if (p / "Data").is_dir() and (p / "Code" / "datasets" / "radiocal").is_dir():
            return p / "Data"
        if (p / "Published_repo" / "Data").is_dir():
            return p / "Published_repo" / "Data"
    return None


def release_radiocal(data: Path):
    """radiocal, imported from the release that holds data."""
    src = str(data.parent / "Code" / "datasets" / "radiocal" / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    import radiocal
    return radiocal


def transform_class(data: Path):
    """radiocal's Transform, imported from the release that holds data."""
    return release_radiocal(data).frames.Transform


def release_script(data: Path, name: str):
    """A numbered script of the release's Code/datasets/radiocal/scripts as a
    module, loaded as the smoke test loads it."""
    path = data.parent / "Code" / "datasets" / "radiocal" / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_quantiles(q: pd.DataFrame, name: str, columns) -> None:
    """A quantile table runs from the level 0 to 1, and no column decreases."""
    missing = [c for c in columns if c not in q.columns]
    if missing:
        sys.exit(f"validation_figures: {name} lacks the columns {missing}")
    for col in columns:
        if np.any(np.diff(q[col].to_numpy(float)) < 0):
            sys.exit(f"validation_figures: {name} column {col} decreases")
    if q["p"].iloc[0] != 0.0 or q["p"].iloc[-1] != 1.0:
        sys.exit(f"validation_figures: {name} does not run from 0 to 1")


def check_inputs(data: Path, facts: Path) -> tuple[dict, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """The node files, pairs.csv and the two quantile tables, checked against
    each other and against the synthetic campaign."""
    regs = {c: read_yaml(data / c / "nodes.yaml") for c in SETS}
    pairs = pd.read_csv(facts / "pairs.csv", dtype={"node_a": str, "node_b": str},
                        keep_default_na=False, na_values=[""])
    for c in SETS:
        ids = {str(n["id"]) for n in regs[c]["nodes"]}
        p = pairs[pairs["set"] == c]
        if set(p["node_a"]) | set(p["node_b"]) != ids or len(p) != len(ids) * (len(ids) - 1) // 2:
            sys.exit(f"validation_figures: pairs.csv does not hold every pair of {c}/nodes.yaml")
        silent = {str(n["id"]) for n in regs[c]["nodes"] if "status" in n}
        never = p[p["status"] == "node never ranges"]
        if not all((a in silent) or (b in silent) for a, b in zip(never["node_a"], never["node_b"])):
            sys.exit(f"validation_figures: {c}: a pair without a ranging node names no node "
                     "with a status in nodes.yaml")
    q = pd.read_csv(facts / "residual_quantiles.csv")
    check_quantiles(q, "residual_quantiles.csv", ("set_b_anchor", "set_b_tag", "set_a_anchor"))
    qs = pd.read_csv(facts / "synthetic_quantiles.csv")
    conditions = read_yaml(data / "synthetic" / "campaign.yaml")["generator"]["conditions"]
    if sorted(c for c, _, _ in SYN_CURVES) != sorted(conditions):
        sys.exit("validation_figures: the curves of Fig. S1 do not match the conditions of "
                 "synthetic/campaign.yaml")
    check_quantiles(qs, "synthetic_quantiles.csv", conditions)
    return regs, pairs, q, qs


# ------------------------------------------------------------ Fig. 1, views

def fan_epochs(g, facts06, Transform) -> tuple[pd.DataFrame, np.ndarray]:
    """The N_FAN fan epochs of the walk g by the rule of the docstring (Fig. 1),
    each with its seq and the registered position of the tag, and the
    registered horizontal poses of the whole walk."""
    t_ep, truth, j, ok = facts06.tag_epochs(g)
    mobile, anc = facts06.mobile_of(g), set(facts06.surveyed(g).index)
    e = g.edges
    tag = e[((e["from_id"] == mobile) & e["to_id"].isin(anc))
            | ((e["to_id"] == mobile) & e["from_id"].isin(anc))]
    first = tag.groupby("seq")["t"].min().sort_index()
    if not np.array_equal(first.to_numpy(float), t_ep):
        sys.exit("validation_figures: the epochs of the tag differ from tag_epochs of 06")
    xy = Transform.from_dict(g.meta["transform_vicon_to_local"]).apply(
        truth[["x", "y", "z"]].to_numpy(float))[:, :2]
    burst = np.r_[0, np.cumsum(np.diff(truth["t"].to_numpy(float)) > facts06.MAX_GAP_S)]
    m = pd.DataFrame({"seq": first.index.to_numpy()[ok], "t": t_ep[ok], "pose": j[ok]})
    m["burst"] = burst[m["pose"].to_numpy()]
    groups = [grp.sort_values("t") for _, grp in m.groupby("burst", sort=True)]
    if len(groups) < N_FAN:
        sys.exit(f"validation_figures: {len(groups)} bursts with matched epochs, "
                 f"fewer than the {N_FAN} fans")
    med = np.array([np.median(xy[grp["pose"].to_numpy()], axis=0) for grp in groups])
    pick = [0]
    while len(pick) < N_FAN:
        d = np.linalg.norm(med[:, None, :] - med[None, pick, :], axis=-1).min(axis=1)
        d[pick] = -np.inf
        pick.append(int(np.argmax(d)))
    rows = [groups[k].iloc[len(groups[k]) // 2] for k in sorted(pick)]
    fans = pd.DataFrame({"seq": [int(r["seq"]) for r in rows],
                         "x": [float(xy[int(r["pose"]), 0]) for r in rows],
                         "y": [float(xy[int(r["pose"]), 1]) for r in rows]})
    return fans, xy


def arc_middle(a, b) -> tuple[float, float]:
    """The middle of the arc that FancyArrowPatch draws from a to b with
    arc3,rad=LABEL_RAD on equal axes: its control point lies LABEL_RAD times
    the chord from the middle of the chord, and the curve halfway to it."""
    (x1, y1), (x2, y2) = a, b
    return ((x1 + x2) / 2 + LABEL_RAD / 2 * (y2 - y1),
            (y1 + y2) / 2 - LABEL_RAD / 2 * (x2 - x1))


def passes_anchor(a, b, others) -> bool:
    """Whether the straight line from a to b passes within ARC_CLEAR_M of one
    of the other anchors."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ab = b - a
    for p in others:
        t = np.clip(np.dot(np.asarray(p, float) - a, ab) / np.dot(ab, ab), 0.0, 1.0)
        if np.linalg.norm(np.asarray(p, float) - (a + t * ab)) < ARC_CLEAR_M:
            return True
    return False


def views(data: Path, out: Path, radiocal, Transform) -> list[str]:
    c, s = VIEWS_SESSION
    g0 = radiocal.load_session(data / c / s)
    facts06 = release_script(data, "06_data_facts.py")
    mobile = facts06.mobile_of(g0)
    anc = facts06.surveyed(g0)
    ids = set(anc.index)
    xy = {str(i): (float(r.x), float(r.y)) for i, r in anc.iterrows()}
    triple = [str(a) for a in read_yaml(data / c / "masks" / "mobile_assisted.yaml")
              ["priors"]["subset"]]
    fans, walk = fan_epochs(g0, facts06, Transform)
    roles = g0.roles()

    kept = {}
    for name, _ in VIEWS:
        v = g0.apply_mask(name)
        e = v.edges
        fr, to = e["from_id"].map(roles), e["to_id"].map(roles)
        is_aa = fr.eq("anchor") & to.eq("anchor")
        aa = {(min(a, b), max(a, b)) for a, b in zip(e.loc[is_aa, "from_id"], e.loc[is_aa, "to_id"])}
        am = e[(e["from_id"] == mobile) | (e["to_id"] == mobile)]
        spec = radiocal.load_mask(name, search_dirs=[data / c / "masks"])
        rule = spec.get("priors", "surveyed")
        want = (set() if rule == "none" else ids if rule == "surveyed"
                else {str(a) for a in rule["subset"]} & ids)
        got = {str(i) for i in v.priors()["id"]}
        if got != want:
            sys.exit(f"validation_figures: {c}/{s}/{name} keeps the priors {sorted(got)}, "
                     f"its mask {sorted(want)}")
        if got not in (set(), set(triple) & ids):  # the diamonds stand for the triple alone
            sys.exit(f"validation_figures: {c}/{s}/{name} keeps the priors {sorted(got)}, "
                     f"neither none nor the subset of mobile_assisted.yaml")
        kept[name] = {"aa": aa, "am": am, "priors": got,
                      "edges": set(zip(e["seq"], e["from_id"], e["to_id"]))}
    if kept["slam_bipartite"]["aa"]:
        sys.exit("validation_figures: slam_bipartite keeps an anchor pair")
    for name in ("fully_meshed", "multi_hop"):
        if len(kept[name]["am"]):
            sys.exit(f"validation_figures: {name} keeps a range of the tag")
    if not kept["multi_hop"]["aa"] <= kept["fully_meshed"]["aa"]:
        sys.exit("validation_figures: multi_hop keeps a pair that fully_meshed lacks")
    if kept["mobile_assisted"]["edges"] != (kept["fully_meshed"]["edges"]
                                            | kept["slam_bipartite"]["edges"]):
        sys.exit("validation_figures: the ranges of mobile_assisted differ from those of "
                 "fully_meshed and slam_bipartite together")

    def fan_segments(am: pd.DataFrame) -> list:
        segs = []
        for f in fans.itertuples():
            ep = am[am["seq"] == f.seq]
            others = sorted((set(ep["from_id"]) | set(ep["to_id"])) - {mobile})
            segs += [((f.x, f.y), xy[str(a)]) for a in others]
        return segs

    bent = {(a, b) for a, b in kept["fully_meshed"]["aa"]
            if passes_anchor(xy[a], xy[b], [xy[i] for i in sorted(ids) if i not in (a, b)])}
    # one set of limits for all panels: the anchors, the walk, the fans and the
    # middles of every arc that a panel draws
    middles = [arc_middle(xy[a], xy[b]) for a, b in sorted(bent)]
    pts = np.vstack([np.array(list(xy.values())), walk, fans[["x", "y"]].to_numpy(float),
                     np.array(middles, float).reshape(-1, 2)])
    lo, hi = pts.min(axis=0) - VIEWS_PAD_M, pts.max(axis=0) + VIEWS_PAD_M
    axes_h = VIEWS_AXES_W * (hi[1] - lo[1]) / (hi[0] - lo[0])

    written = []
    for name, fname in VIEWS:
        k = kept[name]
        fig, ax = panel(VIEWS_AXES_W, axes_h, **VIEWS_MARGIN)
        if len(k["am"]):
            ax.scatter(walk[:, 0], walk[:, 1], s=0.2, c=GREY_POSE, lw=0, rasterized=True,
                       zorder=1)
        for a, b in sorted(k["aa"]):  # from the lower to the higher id, as in Fig. 2
            rad = LABEL_RAD if (a, b) in bent else 0.0
            ax.add_patch(FancyArrowPatch(xy[a], xy[b], arrowstyle="-", shrinkA=0, shrinkB=0,
                                         connectionstyle=f"arc3,rad={rad}",
                                         color=GREY_MID, lw=VIEW_LW, alpha=VIEW_ALPHA,
                                         capstyle="butt", zorder=2))
        if len(k["am"]):
            ax.add_collection(LineCollection(fan_segments(k["am"]), colors=TEAL,
                                             linewidths=VIEW_LW, alpha=VIEW_ALPHA,
                                             capstyle="butt", zorder=3))
            ax.plot(fans["x"], fans["y"], ls="none", marker="o", ms=VIEW_MS_TAG,
                    mfc=GREY_DARK, mec="none", zorder=4)
        plain = np.array([xy[i] for i in sorted(ids) if i not in triple], float)
        datum = np.array([xy[i] for i in triple], float)
        ax.plot(plain[:, 0], plain[:, 1], ls="none", marker="o", ms=VIEW_MS, mfc=BLUE,
                mec="white", mew=0.4, zorder=5)
        if k["priors"]:   # the absolute datum: the view keeps the surveyed priors
            ax.plot(datum[:, 0], datum[:, 1], ls="none", marker="D", ms=VIEW_MS_D, mfc=BLUE,
                    mec=GREY_DARK, mew=0.7, zorder=6)
        else:             # the relative datum: the same anchors as the gauge triple
            ax.plot(datum[:, 0], datum[:, 1], ls="none", marker="D", ms=VIEW_MS_D,
                    mfc="white", mec=BLUE, mew=0.8, zorder=6)
        ax.set_xlim(lo[0], hi[0])
        ax.set_ylim(lo[1], hi[1])
        ax.set_aspect("equal", adjustable="box")
        ax.set_axis_off()
        written.append(save(fig, out, fname))

    def dot(color, marker="o", ms=VIEW_MS, mfc=None, mec="white", mew=0.4):
        return Line2D([], [], ls="none", marker=marker, ms=ms, mfc=mfc or color, mec=mec,
                      mew=mew)

    def line(color):  # a little wider than in the panels, so the short handle reads
        return Line2D([], [], color=color, lw=1.5 * VIEW_LW, alpha=VIEW_ALPHA,
                      solid_capstyle="butt")
    handles = [dot(BLUE),
               dot(BLUE, "D", VIEW_MS_D, mec=GREY_DARK, mew=0.7),
               dot(BLUE, "D", VIEW_MS_D, mfc="white", mec=BLUE, mew=0.8),
               line(GREY_MID),
               (line(TEAL), dot(GREY_DARK, ms=VIEW_MS_TAG, mec="none")),
               dot(GREY_POSE, ms=2.2, mec="none")]
    labels = ["anchor", "anchor of the prior subset", "anchor of the default triple",
              "anchor pair", "tag ranges of one epoch", "logged tag pose"]
    for ncol in (6, 3):  # one row where it fits the text width, else two
        fig = plt.figure(figsize=(TEXT_W, 0.24 if ncol == 6 else 0.42))
        leg = fig.legend(handles, labels, loc="center", ncol=ncol, frameon=False,
                         handlelength=1.6, columnspacing=1.2, labelspacing=0.35,
                         handler_map={tuple: HandlerTuple(ndivide=None, pad=0.4)})
        fig.canvas.draw()
        if leg.get_window_extent().width / fig.dpi <= TEXT_W - 0.1 or ncol == 3:
            break
        plt.close(fig)
    written.append(save(fig, out, "fig_views_legend", tight=True))
    print(f"validation_figures: {c}/{s}: anchor pairs "
          + ", ".join(f"{n} {len(kept[n]['aa'])}" for n, _ in VIEWS)
          + f"; arcs {sorted('-'.join(p) for p in bent)}; fan epochs {list(fans['seq'])}; "
          + f"legend in {ncol} columns")
    return written


# ----------------------------------------------------------- Fig. 2, layout

def nlos_segments(data: Path, c: str, nodes: list) -> list:
    """The pairs that the field labels of campaign c mark NLOS (label NLOS,
    without the pairs that carry two values), each as the ids of its two nodes
    and their horizontal surveyed positions. Stops when a labeled node has no
    surveyed position in nodes.yaml."""
    xy = {str(n["id"]): tuple(n["prior"]["xyz_local"][:2]) for n in nodes}
    labels = pd.read_csv(data / c / "los_nlos_field_labels.csv",
                         dtype={"node_a": str, "node_b": str}, keep_default_na=False)
    pairs = labels[labels["label"] == "NLOS"]
    missing = sorted({v for v in pd.concat([pairs["node_a"], pairs["node_b"]]) if v not in xy})
    if missing:
        sys.exit(f"validation_figures: {c}: the field labels name nodes without a surveyed "
                 f"position: {missing}")
    # from the lower to the higher id, so that every arc bends the same way on a rerun
    return [(min(a, b), max(a, b), xy[min(a, b)], xy[max(a, b)])
            for a, b in zip(pairs["node_a"], pairs["node_b"])]


def label_path(a, b, rad: float, n: int = 1000) -> np.ndarray:
    """n points of the path that FancyArrowPatch draws from a to b with
    arc3,rad=rad on equal axes: the quadratic Bezier curve whose control point
    lies rad times the chord, turned to the right, from the middle of the chord
    (as in arc_middle). rad 0 gives the straight line."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ctrl = (a + b) / 2 + rad * np.array([b[1] - a[1], a[0] - b[0]])
    t = np.linspace(0.0, 1.0, n)[:, None]
    return (1 - t) ** 2 * a + 2 * (1 - t) * t * ctrl + t ** 2 * b


def label_rad(a, b, marks: np.ndarray, pt_per_m: float) -> float:
    """The bend of a pair labeled NLOS in Fig. 2. A mark counts when it lies at
    least LABEL_CLEAR_PT from both ends of the pair. The straight line (0) is
    kept when it clears every such mark by LABEL_CLEAR_PT. Otherwise the pair
    takes the first arc of LABEL_BENDS that does, the gentle bends first, or,
    where none does, the one that keeps the largest clearance. The script stops
    if that arc clears no more than the line, since the caption says that such
    a pair is drawn as an arc."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    clear_m = LABEL_CLEAR_PT / pt_per_m
    far = marks[(np.linalg.norm(marks - a, axis=1) >= clear_m)
                & (np.linalg.norm(marks - b, axis=1) >= clear_m)]
    if not len(far):
        return 0.0

    def clearance(rad: float) -> float:
        path = label_path(a, b, rad)
        return float(np.min(np.linalg.norm(path[:, None, :] - far[None, :, :], axis=-1)))
    line_c = clearance(0.0)
    if line_c >= clear_m:
        return 0.0
    bends = [(clearance(rad), rad) for rad in LABEL_BENDS]
    for c, rad in bends:
        if c >= clear_m:
            return rad
    best_c, best_rad = max(bends, key=lambda cb: cb[0])   # the first on a tie
    if best_c <= line_c:
        sys.exit("validation_figures: no arc of LABEL_BENDS clears the marks better than the "
                 "straight line of a pair labeled NLOS")
    return best_rad


def layout(data: Path, regs: dict, out: Path, Transform) -> list[str]:
    poses = []
    for s in WALKS:
        meta = read_yaml(data / "set_b" / s / "session.yaml")
        xyz = pd.read_parquet(data / "set_b" / s / "groundtruth.parquet",
                              columns=["x", "y", "z"]).to_numpy(float)
        poses.append(Transform.from_dict(meta["transform_vicon_to_local"]).apply(xyz))
    poses = np.vstack(poses)

    written = []
    for c, name in (("set_b", "fig_layout_a_set_b"), ("set_a", "fig_layout_b_set_a")):
        reg = regs[c]
        subset = set(read_yaml(data / c / "masks" / "mobile_assisted.yaml")["priors"]["subset"])
        nodes = [n for n in reg["nodes"] if n["prior"]["type"] == "surveyed"]
        anchors = np.array([n["prior"]["xyz_local"][:2] for n in nodes
                            if "status" not in n and str(n["id"]) not in subset], float)
        prior = np.array([n["prior"]["xyz_local"][:2] for n in nodes
                          if "status" not in n and str(n["id"]) in subset], float)
        silent = np.array([n["prior"]["xyz_local"][:2] for n in nodes if "status" in n],
                          float).reshape(-1, 2)
        cps = reg.get("control_points", [])
        # the origin of the Vicon frame only. WAND-001 on its +y axis lies
        # within half a metre and stays out, like every other WAND point
        wand = np.array([p["xyz_local"][:2] for p in cps if p["name"] == "WAND-0-0"],
                        float).reshape(-1, 2)
        nlos = nlos_segments(data, c, nodes)
        markers = np.array([p["xyz_local"][:2] for p in cps
                            if p["name"][0] == "P" and p["name"][1:].isdigit()], float).reshape(-1, 2)
        # control and reference points, without a point whose shots conflict
        # (conflict: true in nodes.yaml)
        refs = np.array([p["xyz_local"][:2] for p in cps
                         if not p["name"].startswith("WAND")
                         and not (p["name"][0] == "P" and p["name"][1:].isdigit())
                         and not p.get("conflict", False)],
                        float).reshape(-1, 2)
        walk = poses[:, :2] if c == "set_b" else np.empty((0, 2))
        pts = np.vstack([a for a in (anchors, prior, silent, wand, markers, refs, walk) if len(a)])
        lo, hi = pts.min(axis=0) - LAYOUT_PAD_M, pts.max(axis=0) + LAYOUT_PAD_M
        axes_w = LAYOUT_AXES_H * (hi[0] - lo[0]) / (hi[1] - lo[1])
        pt_per_m = 72.0 * LAYOUT_AXES_H / (hi[1] - lo[1])
        marks = np.vstack([a for a in (anchors, prior, silent, wand, markers, refs) if len(a)])
        fig, ax = panel(axes_w, LAYOUT_AXES_H, **LAYOUT_MARGIN)
        if len(walk):
            ax.scatter(walk[:, 0], walk[:, 1], s=0.35, c=GREY_POSE, lw=0, rasterized=True,
                       zorder=1)
        bent = []
        for ida, idb, a, b in nlos:
            rad = label_rad(a, b, marks, pt_per_m)
            path = label_path(a, b, rad)
            if (path < lo).any() or (path > hi).any():
                sys.exit(f"validation_figures: {c}: the line of {ida}-{idb} leaves the panel")
            if rad:
                bent.append(f"{ida}-{idb}{'+' if rad > 0 else '-'}")
            ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-", shrinkA=0, shrinkB=0,
                                         connectionstyle=f"arc3,rad={rad}",
                                         color=COLOR[c], lw=LABEL_LW, alpha=LABEL_ALPHA,
                                         capstyle="butt", zorder=1.5))
        print(f"validation_figures: {c}: {len(nlos)} pairs labeled NLOS, arcs {bent}")
        if len(refs):
            ax.plot(refs[:, 0], refs[:, 1], ls="none", marker="^", ms=3.4, mfc=GREY_MID,
                    mec="none", zorder=2)
        if len(markers):  # above the anchors, since P01 lies next to the static 8B05
            ax.plot(markers[:, 0], markers[:, 1], ls="none", marker="s", ms=3.2, mfc="white",
                    mec=COLOR[c], mew=0.8, zorder=6)
        if len(wand):
            ax.plot(wand[:, 0], wand[:, 1], ls="none", marker="x", ms=3.6, color=GREY_DARK,
                    mew=0.9, zorder=4)
        ax.plot(anchors[:, 0], anchors[:, 1], ls="none", marker="o", ms=4.6, mfc=COLOR[c],
                mec="white", mew=0.5, zorder=5)
        ax.plot(prior[:, 0], prior[:, 1], ls="none", marker="D", ms=4.4, mfc=COLOR[c],
                mec=GREY_DARK, mew=0.8, zorder=5)
        if len(silent):
            ax.plot(silent[:, 0], silent[:, 1], ls="none", marker="o", ms=4.6, mfc="white",
                    mec=COLOR[c], mew=1.0, zorder=5)
        ax.set_xlim(lo[0], hi[0])
        ax.set_ylim(lo[1], hi[1])
        ax.set_aspect("equal", adjustable="box")
        for axis in (ax.xaxis, ax.yaxis):
            axis.set_major_locator(MultipleLocator(5))
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        written.append(save(fig, out, name))

    def dot(color, marker="o", ms=4.6, mfc=None, mec="white", mew=0.5):
        return Line2D([], [], ls="none", marker=marker, ms=ms, mfc=mfc or color, mec=mec,
                      mew=mew)

    def line(color):  # a little wider than in the panels, so the short handle reads
        return Line2D([], [], color=color, lw=1.5 * LABEL_LW, alpha=LABEL_ALPHA,
                      solid_capstyle="butt")
    handles = [
        (dot(BLUE), dot(ORANGE)),
        (dot(BLUE, "D", 4.4, mec=GREY_DARK, mew=0.8), dot(ORANGE, "D", 4.4, mec=GREY_DARK, mew=0.8)),
        dot(BLUE, mfc="white", mec=BLUE, mew=1.0),
        dot(GREY_MID, "^", 3.4, mec="none"),
        dot(ORANGE, "s", 3.2, mfc="white", mec=ORANGE, mew=0.8),
        dot(GREY_DARK, "x", 3.6, mec=GREY_DARK, mew=0.9),
        dot(GREY_POSE, "o", 2.2, mec="none"),
        (line(BLUE), line(ORANGE)),
    ]
    labels = ["anchor", "anchor of the prior subset", "surveyed node that never ranges",
              "control or reference point", "marker of the roving tag",
              "origin of the Vicon frame", "logged tag pose", "pair labeled NLOS"]
    fig = plt.figure(figsize=(TEXT_W, 0.42))
    fig.legend(handles, labels, loc="center", ncol=4, frameon=False, handlelength=1.6,
               columnspacing=1.4, labelspacing=0.35,
               handler_map={tuple: HandlerTuple(ndivide=None, pad=0.4)})
    written.append(save(fig, out, "fig_layout_legend", tight=True))
    return written


# -------------------------------------------------------- Fig. 4, residuals

def ecdf_panel(q: pd.DataFrame, curves, name: str, out: Path,
               legend_title: str | None = None) -> str:
    """One ECDF panel (Fig. 4 or S1) from a quantile table: curves holds the
    column, the colour, the line style and the legend label of each curve."""
    fig, ax = panel(ECDF_W, ECDF_H, **ECDF_MARGIN)
    p = q["p"].to_numpy(float)
    for col, color, ls, label in curves:
        x = q[col].to_numpy(float)
        # the quantile curve closed as a distribution function: 0 left of the
        # smallest residual, 1 right of the largest
        ax.plot(np.r_[-1e3, x, 1e3], np.r_[0.0, p, 1.0], color=color, ls=ls, lw=LW_DATA,
                label=label, zorder=3 if ls == "--" else 2)
    ax.set_xlim(*ECDF_XLIM)
    ax.xaxis.set_major_locator(FixedLocator([-1, 0, 1, 2, 3]))
    ax.xaxis.set_minor_locator(MultipleLocator(0.5))
    ax.set_ylim(-0.02, 1.02)
    ax.yaxis.set_major_locator(FixedLocator(ECDF_LEVELS))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.2f}"))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.grid(True, which="major", **GRID)
    ax.axhline(1.0, zorder=0.5, **GRID)  # the end at one, without a tick label
    ax.set_axisbelow(True)
    ax.set_xlabel("Range residual (m)")
    ax.set_ylabel("ECDF")
    ax.legend(loc="lower right", handlelength=2.2, title=legend_title,
              title_fontsize=FS_LEGEND)
    return save(fig, out, name)


def residuals(q: pd.DataFrame, qs: pd.DataFrame, out: Path) -> list[str]:
    measured = [("set_b_anchor", BLUE, "-", "LOS deployment, anchor pairs"),
                ("set_b_tag", BLUE, "--", "LOS deployment, walking tag"),
                ("set_a_anchor", ORANGE, "-", "NLOS deployment, anchor pairs")]
    synthetic = [(c, color, ls, c) for c, color, ls in SYN_CURVES]
    return [ecdf_panel(q, measured, "fig_residuals", out),
            ecdf_panel(qs, synthetic, "fig_synthetic_residuals", out,
                       legend_title="Synthetic condition")]


# ----------------------------------------------------- Fig. 5, availability

def availability(pairs: pd.DataFrame, out: Path) -> list[str]:
    written = []
    norm = Normalize(0.0, 100.0)
    for c, name in (("set_b", "fig_availability_a_set_b"), ("set_a", "fig_availability_b_set_a")):
        p = pairs[pairs["set"] == c]
        ids = sorted(set(p["node_a"]) | set(p["node_b"]))
        idx = {v: i for i, v in enumerate(ids)}
        n = len(ids)
        share = np.full((n, n), np.nan)  # row: the measuring node, column: the measured node
        count = np.full((n, n), -1)      # directed ranges, -1 on the diagonal
        for r in p.itertuples():
            share[idx[r.node_a], idx[r.node_b]] = r.availability_ab_pct
            share[idx[r.node_b], idx[r.node_a]] = r.availability_ba_pct
            count[idx[r.node_a], idx[r.node_b]] = r.ranges_ab
            count[idx[r.node_b], idx[r.node_a]] = r.ranges_ba
        empty = count == 0
        fig, ax = panel(MATRIX_SIDE, MATRIX_SIDE, **MATRIX_MARGIN)
        ax.imshow(np.where(empty, np.nan, share), cmap=AVAIL_CMAP, norm=norm,
                  interpolation="nearest")
        ax.imshow(np.where(np.eye(n, dtype=bool), 1.0, np.nan),
                  cmap=LinearSegmentedColormap.from_list("diag", ["#DDDDDD", "#DDDDDD"]),
                  interpolation="nearest")
        rows, cols = np.nonzero(empty)
        ax.plot(cols, rows, ls="none", marker="x", ms=4.0, mew=0.9, color=GREY_DARK)
        ax.set_xticks(range(n))
        ax.set_xticklabels(ids, rotation=90)
        ax.set_yticks(range(n))
        ax.set_yticklabels(ids)
        ax.tick_params(length=0, pad=1.5)
        ax.set_xticks(np.arange(-0.5, n), minor=True)
        ax.set_yticks(np.arange(-0.5, n), minor=True)
        ax.grid(which="minor", color="white", lw=0.6)
        ax.tick_params(which="minor", length=0)
        for s in ax.spines.values():
            s.set_color("#AAAAAA")
            s.set_linewidth(0.5)
        ax.set_xlabel("Measured node")
        ax.set_ylabel("Measuring node")
        written.append(save(fig, out, name))

    fig = plt.figure(figsize=(TEXT_W, 0.48))
    cax = fig.add_axes([0.16, 0.62, 0.40, 0.18])
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=AVAIL_CMAP), cax=cax,
                      orientation="horizontal")
    cb.set_ticks([0, 25, 50, 75, 100])
    cb.ax.tick_params(labelsize=FS_TICK, width=0.5, length=2)
    cb.outline.set_linewidth(0.5)
    cb.set_label("Share of epochs (%)", fontsize=FS_LABEL, labelpad=2)
    fig.legend([Line2D([], [], ls="none", marker="x", ms=4.0, mew=0.9, color=GREY_DARK),
                Patch(facecolor="#DDDDDD", edgecolor="none")],
               ["pair without ranges", "a node with itself"], loc="center left",
               bbox_to_anchor=(0.62, 0.62), frameon=False, handlelength=1.2,
               labelspacing=0.35)
    written.append(save(fig, out, "fig_availability_legend", tight=True))
    return written


# --------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", type=Path, default=None, metavar="DIR",
                    help="the Data/ folder of the release (default: the release that holds "
                         "this script)")
    ap.add_argument("--facts", type=Path, required=True, metavar="DIR",
                    help="the output folder of 06_data_facts.py (pairs.csv, residual_quantiles.csv, "
                         "synthetic_quantiles.csv)")
    ap.add_argument("--out", type=Path, required=True, metavar="DIR",
                    help="folder for the PDFs")
    args = ap.parse_args()
    data = args.data or default_data()
    if data is None or not (data / "set_b" / "nodes.yaml").is_file():
        sys.exit("validation_figures: no release Data/ found, pass --data")
    regs, pairs, q, qs = check_inputs(data, args.facts)
    Transform = transform_class(data)
    args.out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(STYLE)
    written = views(data, args.out, release_radiocal(data), Transform) \
        + layout(data, regs, args.out, Transform) + residuals(q, qs, args.out) \
        + availability(pairs, args.out)
    print(f"validation_figures: {len(written)} PDFs -> {args.out}")
    for w in written:
        print(f"   {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
