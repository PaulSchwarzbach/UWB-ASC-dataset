"""Compare a rebuild with the released canonical files.

Run from the repository root after the rebuild commands of the README:

    python -B tests/check_rebuild.py rebuild

Every file under the rebuild folder is compared with the file of the same
path under Data/. A Parquet file is compared byte for byte when the writer
versions it records (pyarrow and pandas) equal the installed ones, and by
content otherwise. A PNG figure is compared by its pixels, since the PNG
encoder may differ between environments. Every other file is compared byte
for byte, with the two fields that the README names under "What the scripts
rebuild" as the exception: a YAML file may differ in the numpy version that
drew it (numpy_version), and the column rolling_median_span_m of
truth_adjudication.csv may move by up to SPAN_TOL_M. Released files of a
rebuilt campaign that the rebuild lacks are listed, apart from the
hand-written READMEs and field labels. The exit code is 1 when a file differs
or is missing.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "Data"
NOT_BUILT = ("README.md", "los_nlos_field_labels.csv")
PER_RUN_KEY = "numpy_version:"
SPAN_COLUMN, SPAN_TOL_M = "rolling_median_span_m", 0.005


def parquet_match(a: Path, b: Path) -> str:
    import pandas as pd
    import pyarrow
    import pyarrow.parquet as pq
    if a.read_bytes() == b.read_bytes():
        return "bytes"
    meta = json.loads(pq.read_schema(b).metadata[b"pandas"])
    if (pq.read_metadata(b).created_by.endswith(pyarrow.__version__)
            and meta.get("pandas_version") == pd.__version__):
        return ""  # the same writer gave other bytes: a real difference
    try:
        pd.testing.assert_frame_equal(pd.read_parquet(a), pd.read_parquet(b),
                                      check_dtype=False, check_exact=True)
        return "content"
    except AssertionError:
        return ""


def png_match(a: Path, b: Path) -> str:
    if a.read_bytes() == b.read_bytes():
        return "bytes"
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        return "unchecked"
    x = np.asarray(Image.open(a).convert("RGBA"))
    y = np.asarray(Image.open(b).convert("RGBA"))
    return "pixels" if x.shape == y.shape and (x == y).all() else ""


def text_match(a: Path, b: Path) -> str:
    """Bytes, or equal apart from the per-environment fields of the README."""
    if a.read_bytes() == b.read_bytes():
        return "bytes"
    if a.suffix == ".yaml":
        def kept(p: Path) -> list:
            return [line for line in p.read_text(encoding="utf-8").splitlines()
                    if not line.lstrip().startswith(PER_RUN_KEY)]
        return "fields" if kept(a) == kept(b) else ""
    if a.name == "truth_adjudication.csv":
        import pandas as pd
        x, y = pd.read_csv(a), pd.read_csv(b)
        if list(x.columns) != list(y.columns) or len(x) != len(y) or SPAN_COLUMN not in x:
            return ""
        rest = [c for c in x.columns if c != SPAN_COLUMN]
        dev = (x[SPAN_COLUMN] - y[SPAN_COLUMN]).abs()
        both_nan = x[SPAN_COLUMN].isna() & y[SPAN_COLUMN].isna()
        if x[rest].equals(y[rest]) and ((dev <= SPAN_TOL_M) | both_nan).all():
            return "fields"
    return ""


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    rebuild = Path(sys.argv[1]).resolve()
    tally = {"bytes": 0, "content": 0, "pixels": 0, "fields": 0, "unchecked": 0}
    differ, new = [], []
    files = sorted(p for p in rebuild.rglob("*") if p.is_file())
    for p in files:
        rel = p.relative_to(rebuild)
        ref = DATA / rel
        if not ref.is_file():
            new.append(rel.as_posix())
            continue
        if p.suffix == ".parquet":
            how = parquet_match(p, ref)
        elif p.suffix == ".png":
            how = png_match(p, ref)
        else:
            how = text_match(p, ref)
        if how:
            tally[how] += 1
        else:
            differ.append(rel.as_posix())
    have = {p.relative_to(rebuild).as_posix() for p in files}
    has_qa = any("/qa/" in h for h in have)
    missing = []
    for campaign in sorted({Path(h).parts[0] for h in have}):
        for ref in sorted((DATA / campaign).rglob("*")):
            rel = ref.relative_to(DATA).as_posix()
            if (ref.is_file() and rel not in have and ref.name not in NOT_BUILT
                    and (has_qa or "/qa/" not in rel)):
                missing.append(rel)
    for label, items in (("DIFFER", differ), ("NEW", new), ("MISSING", missing)):
        for r in items:
            print(f"  {label:<8}{r}")
    print(f"check_rebuild: {len(files)} files: {tally['bytes']} identical bytes, "
          f"{tally['content']} equal content, {tally['pixels']} equal pixels, "
          f"{tally['fields']} equal but for the per-environment fields, "
          f"{tally['unchecked']} unchecked, {len(differ)} differ, {len(new)} not in Data/, "
          f"{len(missing)} released files not rebuilt")
    return 1 if differ or missing else 0


if __name__ == "__main__":
    sys.exit(main())
