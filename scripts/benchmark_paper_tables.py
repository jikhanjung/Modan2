#!/usr/bin/env python3
"""Reproduce the runtime table of the Modan2 paper on a real published dataset.

Unlike ``benchmark_analysis.py``, which times the analysis primitives on random
data, this script reads one of the Morphologika datasets shipped with the
repository and times the code paths the application itself runs, so that the
figures can be quoted directly in the manuscript.

It reports the three parts of the runtime table:

  (a) superimposition                 - Procrustes and Bookstein
  (b) downstream analysis             - PCA, CVA, MANOVA, and their sum
  (c) cost of missing-landmark imputation at several missing fractions

Two details matter for comparability with the published numbers:

  * MANOVA is timed on PCA scores (``do_manova_analysis_on_pca``), because that
    is what ``ModanController._run_manova`` calls when a PCA result is present.
    Timing ``do_manova_analysis_on_procrustes`` instead understates it by an
    order of magnitude.
  * Every figure is the median of ``--runs`` repetitions.

Usage:
    python scripts/benchmark_paper_tables.py                     # 222 x 72 cranial dataset
    python scripts/benchmark_paper_tables.py --dataset dense14   # 14 x 381 dataset
    python scripts/benchmark_paper_tables.py --runs 9 --markdown
    python scripts/benchmark_paper_tables.py --manova-paths      # which MANOVA path costs what
    python scripts/benchmark_paper_tables.py --repo /path/to/other/checkout

``--repo`` runs the benchmark against a different checkout of Modan2 (e.g. a
``git worktree`` at an earlier tag) while reading the datasets from this one,
which is how a runtime change between two versions can be attributed to the
code rather than to the machine.
"""

import argparse
import json
import platform
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_REPO = HERE.parent

DATASETS = {
    "cranial222": {
        "file": "Morphometrics dataset/Thylacine2020_NeuroGM.txt",
        "name": "Cranial 222x72",
        "group_var": "FeedCat1",  # dietary category
    },
    "dense14": {
        "file": "Morphometrics dataset/Rovinsky_etal Morphologika.txt",
        "name": "Dense 14x381",
        "group_var": "Sex",
    },
}

MISSING_FRACTIONS = (0.05, 0.10, 0.20)


# --------------------------------------------------------------------------
# environment
# --------------------------------------------------------------------------
def describe_environment(repo):
    """Record what the numbers were produced on; they are meaningless without it."""
    cpu = platform.processor() or platform.machine()
    try:  # /proc/cpuinfo carries the marketing name on Linux, platform does not
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass

    mem_gb = None
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal"):
                mem_gb = round(int(line.split()[1]) / 1024 / 1024)
                break
    except OSError:
        pass

    def git(*args):
        try:
            return subprocess.run(
                ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
            ).stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    sys.path.insert(0, str(repo))
    try:
        import version as modan_version

        ver = modan_version.__version__
    except Exception:
        ver = None

    return {
        "modan2_version": ver,
        "git_describe": git("describe", "--tags", "--always"),
        "git_dirty": bool(git("status", "--porcelain")),
        "repo": str(repo),
        "cpu": cpu,
        "memory_gb": mem_gb,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


# --------------------------------------------------------------------------
# dataset loading
# --------------------------------------------------------------------------
def load_dataset(mm, Morphologika, path, name):
    """Read a Morphologika file into a fresh in-memory database."""
    mm.gDatabase.init(":memory:")
    mm.gDatabase.create_tables([mm.MdDataset, mm.MdObject, mm.MdAnalysis, mm.MdImage, mm.MdThreeDModel])

    morph = Morphologika(str(path), name)
    dataset = mm.MdDataset.create(
        dataset_name=name,
        dimension=morph.dimension,
        landmark_count=morph.nlandmarks,
        propertyname_str=",".join(morph.variablename_list),
    )
    for i, obj_name in enumerate(morph.object_name_list):
        rows = morph.landmark_data[obj_name]
        mm.MdObject.create(
            dataset=dataset,
            object_name=obj_name,
            sequence=i + 1,
            landmark_str="\n".join("\t".join(r) for r in rows),
            property_str=",".join(morph.property_list_list[i]) if morph.property_list_list else "",
        )
    return dataset, morph


def groups_for(dataset, morph, var_name):
    idx = morph.variablename_list.index(var_name)
    return [obj.get_variable_list()[idx] for obj in dataset.object_list]


# --------------------------------------------------------------------------
# timing helpers
# --------------------------------------------------------------------------
def time_median(fn, runs):
    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return statistics.median(times), times


def superimpose(mm, dataset, method):
    ds_ops = mm.MdDatasetOps(dataset)
    if method == "bookstein":
        ds_ops.bookstein_superimposition()
    else:
        ds_ops.procrustes_superimposition()
    return [obj.landmark_list for obj in ds_ops.object_list]


def punch_holes(dataset, fraction, seed):
    """Blank `fraction` of all landmark positions at random.

    Returns (originals, n_removed). A landmark is never removed from every
    specimen, since nothing could then estimate it. Restore with `restore()`.
    """
    rng = random.Random(seed)
    objects = list(dataset.object_list)
    for obj in objects:
        obj.unpack_landmark()
    n_obj = len(objects)
    n_lm = len(objects[0].landmark_list)
    dim = len(objects[0].landmark_list[0])

    cells = [(i, j) for i in range(n_obj) for j in range(n_lm)]
    rng.shuffle(cells)
    target = int(round(fraction * len(cells)))

    per_lm = [0] * n_lm
    holes = {}
    n_chosen = 0
    for i, j in cells:
        if n_chosen >= target:
            break
        if per_lm[j] >= n_obj - 1:
            continue
        per_lm[j] += 1
        holes.setdefault(i, []).append(j)
        n_chosen += 1

    originals = {}
    for i, lm_idx in holes.items():
        obj = objects[i]
        originals[obj.id] = obj.landmark_str
        rows = [list(map(str, lm)) for lm in obj.landmark_list]
        for j in lm_idx:
            rows[j] = ["Missing"] * dim
        obj.landmark_str = "\n".join("\t".join(r) for r in rows)
        obj.save()
    return originals, n_chosen


def restore(mm, originals):
    for obj_id, lm_str in originals.items():
        obj = mm.MdObject.get_by_id(obj_id)
        obj.landmark_str = lm_str
        obj.save()


# --------------------------------------------------------------------------
# benchmark
# --------------------------------------------------------------------------
def run(args, mm, MdStatistics, Morphologika):
    spec = DATASETS.get(args.dataset)
    path = Path(args.file) if args.file else DEFAULT_REPO / spec["file"]
    name = spec["name"] if spec else path.stem
    group_var = args.group_var or (spec["group_var"] if spec else None)

    dataset, morph = load_dataset(mm, Morphologika, path, name)
    n_obj = len(list(dataset.object_list))
    results = {
        "dataset": name,
        "file": str(path),
        "n_objects": n_obj,
        "n_landmarks": dataset.landmark_count,
        "dimension": morph.dimension,
        "group_variable": group_var,
        "runs": args.runs,
    }
    print(f"# {name}: {n_obj} specimens x {dataset.landmark_count} landmarks, {morph.dimension}D")
    print(f"# grouping variable: {group_var}   (available: {morph.variablename_list})")
    print(f"# median of {args.runs} runs\n")

    # (a) superimposition ---------------------------------------------------
    t_proc, _ = time_median(lambda: superimpose(mm, dataset, "procrustes"), args.runs)
    dataset.baseline_point_list = [1, 2, 3] if morph.dimension == 3 else [1, 2]
    dataset.pack_baseline()
    dataset.save()
    t_book, _ = time_median(lambda: superimpose(mm, dataset, "bookstein"), args.runs)
    results["superimposition"] = {"procrustes": t_proc, "bookstein": t_book}
    print(f"(a) Procrustes (GPA)          {t_proc:7.3f} s")
    print(f"    Bookstein                 {t_book:7.3f} s\n")

    # (b) downstream analysis ----------------------------------------------
    lm_data = superimpose(mm, dataset, "procrustes")
    groups = groups_for(dataset, morph, group_var)

    t_pca, _ = time_median(lambda: MdStatistics.do_pca_analysis(lm_data), args.runs)
    t_cva, _ = time_median(lambda: MdStatistics.do_cva_analysis(lm_data, groups), args.runs)
    pca_result = MdStatistics.do_pca_analysis(lm_data)
    t_man, _ = time_median(lambda: MdStatistics.do_manova_analysis_on_pca(pca_result["scores"], groups), args.runs)
    full = t_proc + t_pca + t_cva + t_man
    results["downstream"] = {"pca": t_pca, "cva": t_cva, "manova": t_man, "full_workflow": full}
    print(f"(b) PCA                       {t_pca:7.3f} s")
    print(f"    CVA                       {t_cva:7.3f} s")
    print(f"    MANOVA (on PCA scores)    {t_man:7.3f} s")
    print(f"    Full workflow             {full:7.3f} s\n")

    # (c) imputation cost ---------------------------------------------------
    results["imputation"] = {"0%": {"time": t_proc, "relative": 1.0, "n_removed": 0}}
    print(f"(c) complete                  {t_proc:7.3f} s   1.0x")
    for frac in MISSING_FRACTIONS:
        originals, n_removed = punch_holes(dataset, frac, seed=args.seed + int(frac * 100))
        try:
            t, _ = time_median(lambda: superimpose(mm, dataset, "procrustes"), args.runs)
        finally:
            restore(mm, originals)
        key = f"{int(frac * 100)}%"
        results["imputation"][key] = {"time": t, "relative": t / t_proc, "n_removed": n_removed}
        print(f"    {key:>3} missing               {t:7.3f} s   {t / t_proc:.1f}x   ({n_removed} positions)")

    return results


def compare_manova_paths(args, mm, MdStatistics, Morphologika):
    """Time the three MANOVA entry points on the same aligned data.

    ``ModanController`` uses the PCA-score path; the other two exist for callers
    that have no PCA result. They differ by an order of magnitude, so quoting the
    wrong one silently misreports the workflow cost.
    """
    import numpy as np

    spec = DATASETS[args.dataset]
    path = Path(args.file) if args.file else DEFAULT_REPO / spec["file"]
    dataset, morph = load_dataset(mm, Morphologika, path, spec["name"])
    lm_data = superimpose(mm, dataset, "procrustes")
    groups = groups_for(dataset, morph, args.group_var or spec["group_var"])
    flat = [np.array(lm).flatten().tolist() for lm in lm_data]
    pca_result = MdStatistics.do_pca_analysis(lm_data)

    paths = {
        "do_manova_analysis_on_pca (used by ModanController)": lambda: MdStatistics.do_manova_analysis_on_pca(
            pca_result["scores"], groups
        ),
        "do_manova_analysis_on_procrustes": lambda: MdStatistics.do_manova_analysis_on_procrustes(flat, groups),
        "do_manova_analysis (generic)": lambda: MdStatistics.do_manova_analysis(lm_data, groups),
    }
    out = {}
    for label, fn in paths.items():
        t, _ = time_median(fn, args.runs)
        out[label] = t
        print(f"{label:<52} {t:7.4f} s")
    return out


def _similarity_fit(source, target):
    """Least-squares similarity transform (rotation, scale, translation) taking
    `source` onto `target`. Both are (n, k) arrays of matched points."""
    import numpy as np

    src_c = source - source.mean(axis=0)
    tgt_c = target - target.mean(axis=0)
    u, s, vt = np.linalg.svd(src_c.T @ tgt_c)
    d = np.sign(np.linalg.det(u @ vt))
    correction = np.eye(source.shape[1])
    correction[-1, -1] = d
    rotation = u @ correction @ vt
    scale = s[:-1].sum() + d * s[-1]
    denom = (src_c**2).sum()
    scale = scale / denom if denom else 1.0
    return rotation, scale, source.mean(axis=0), target.mean(axis=0)


def _apply_similarity(points, fit):
    rotation, scale, src_mean, tgt_mean = fit
    return scale * ((points - src_mean) @ rotation) + tgt_mean


def measure_accuracy(args, mm, MdStatistics, Morphologika):
    """Reconstruct removed landmarks and compare them with the positions the same
    specimens occupy when the complete dataset is analyzed.

    Each estimate is compared in a frame established from that specimen's
    never-removed landmarks only, so the residual reflects the estimate rather
    than a difference in global alignment. Errors are a percentage of centroid
    size, pooled over `--patterns` independent removal patterns per condition.
    """
    import numpy as np

    spec = DATASETS.get(args.dataset)
    path = Path(args.file) if args.file else DEFAULT_REPO / spec["file"]
    name = spec["name"] if spec else path.stem

    dataset, morph = load_dataset(mm, Morphologika, path, name)
    n_obj = len(list(dataset.object_list))
    print(f"# {name}: {n_obj} specimens x {dataset.landmark_count} landmarks, {morph.dimension}D")
    print(f"# {args.patterns} removal patterns per condition\n")

    reference = [np.asarray(lm, dtype=float) for lm in superimpose(mm, dataset, "procrustes")]
    ref_cs = [np.sqrt(((c - c.mean(axis=0)) ** 2).sum()) for c in reference]
    mean_shape = np.mean(np.stack(reference), axis=0)

    # The floor no mean-shape estimator can beat: how far a specimen's own
    # landmark sits from the corresponding landmark of the mean shape.
    floor = np.concatenate([np.linalg.norm(cfg - mean_shape, axis=1) / cs * 100 for cfg, cs in zip(reference, ref_cs)])
    print(f"Shape-variation floor: mean {floor.mean():.2f}%, median {np.median(floor):.2f}%\n")

    results = {
        "dataset": name,
        "n_objects": n_obj,
        "n_landmarks": dataset.landmark_count,
        "dimension": morph.dimension,
        "patterns": args.patterns,
        "floor": {"mean": float(floor.mean()), "median": float(np.median(floor))},
        "conditions": {},
    }

    print(f"{'removed':>8} {'n':>8} {'mean':>8} {'median':>8} {'95th':>8} {'max':>8}")
    for frac in args.fractions:
        errors = []
        for pattern in range(args.patterns):
            originals, _ = punch_holes(dataset, frac, seed=args.seed + pattern * 101 + int(frac * 1000))
            removed = {}
            for obj_id in originals:
                obj = mm.MdObject.get_by_id(obj_id)
                obj.unpack_landmark()
                removed[obj_id] = [j for j, lm in enumerate(obj.landmark_list) if any(v is None for v in lm)]
            try:
                imputed_ops = mm.MdDatasetOps(dataset)
                imputed_ops.procrustes_superimposition()
                imputed = {o.id: np.asarray(o.landmark_list, dtype=float) for o in imputed_ops.object_list}
            finally:
                restore(mm, originals)

            for idx, obj in enumerate(dataset.object_list):
                gaps = removed.get(obj.id)
                if not gaps:
                    continue
                cfg = imputed.get(obj.id)
                if cfg is None:
                    continue
                kept = [j for j in range(len(cfg)) if j not in set(gaps)]
                fit = _similarity_fit(cfg[kept], reference[idx][kept])
                aligned = _apply_similarity(cfg, fit)
                d = np.linalg.norm(aligned[gaps] - reference[idx][gaps], axis=1) / ref_cs[idx] * 100
                errors.append(d)

        e = np.concatenate(errors)
        cond = {
            "n_imputed": int(e.size),
            "mean": float(e.mean()),
            "median": float(np.median(e)),
            "p95": float(np.percentile(e, 95)),
            "max": float(e.max()),
        }
        results["conditions"][f"{frac * 100:g}%"] = cond
        print(
            f"{frac * 100:>7g}% {e.size:>8} {e.mean():>7.2f}% {np.median(e):>7.2f}%"
            f" {np.percentile(e, 95):>7.2f}% {e.max():>7.2f}%"
        )

    return results


def accuracy_as_markdown(r):
    lines = [
        f"*{r['dataset']}, {r['n_objects']} specimens × {r['n_landmarks']} landmarks, {r['dimension']}D."
        f" Shape-variation floor: mean {r['floor']['mean']:.2f}%, median {r['floor']['median']:.2f}%.*",
        "",
        "| Positions removed | *n* imputed | Mean | Median | 95th pct. | Max |",
        "|---|---|---|---|---|---|",
    ]
    for key, c in r["conditions"].items():
        lines.append(
            f"| {key} | {c['n_imputed']:,} | {c['mean']:.2f}% | {c['median']:.2f}%"
            f" | {c['p95']:.2f}% | {c['max']:.2f}% |"
        )
    return "\n".join(lines)


def as_markdown(results):
    r = results
    lines = [
        f"*(a) Superimposition* — {r['dataset']}, median of {r['runs']} runs",
        "",
        "| Method | Time |",
        "|---|---|",
        f"| Procrustes (GPA) | {r['superimposition']['procrustes']:.2f} s |",
        f"| Bookstein | {r['superimposition']['bookstein']:.2f} s |",
        "",
        "*(b) Downstream analysis, on Procrustes-aligned coordinates*",
        "",
        "| Analysis | Time |",
        "|---|---|",
        f"| PCA | {r['downstream']['pca']:.2f} s |",
        f"| CVA | {r['downstream']['cva']:.2f} s |",
        f"| MANOVA | {r['downstream']['manova']:.2f} s |",
        f"| **Full workflow** (Procrustes + PCA + CVA + MANOVA) | **{r['downstream']['full_workflow']:.2f} s** |",
        "",
        "*(c) Cost of missing-landmark imputation, relative to complete data*",
        "",
        "| Positions missing | Time | Relative to complete |",
        "|---|---|---|",
    ]
    for key, v in r["imputation"].items():
        label = "0% (complete)" if key == "0%" else key
        lines.append(f"| {label} | {v['time']:.2f} s | {v['relative']:.1f}× |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(
        description="Reproduce the paper's runtime table on a real dataset.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--dataset",
        default="cranial222",
        choices=sorted(DATASETS),
        help="which shipped dataset to use (default: cranial222)",
    )
    ap.add_argument("--file", default=None, help="override with an arbitrary Morphologika file")
    ap.add_argument("--group-var", default=None, help="grouping variable for CVA/MANOVA")
    ap.add_argument("--runs", type=int, default=5, help="repetitions per measurement (default: 5)")
    ap.add_argument("--seed", type=int, default=20260813, help="seed for the removal patterns")
    ap.add_argument(
        "--repo", default=None, help="run against another Modan2 checkout (e.g. a worktree at an earlier tag)"
    )
    ap.add_argument("--markdown", action="store_true", help="also print the table in manuscript form")
    ap.add_argument("--manova-paths", action="store_true", help="instead, time the three MANOVA entry points and exit")
    ap.add_argument(
        "--accuracy", action="store_true", help="instead, measure imputation accuracy against the complete data"
    )
    ap.add_argument(
        "--patterns", type=int, default=10, help="removal patterns per condition, accuracy mode (default: 10)"
    )
    ap.add_argument(
        "--fractions",
        type=float,
        nargs="+",
        default=[0.01, 0.05, 0.10, 0.20],
        help="missing fractions for accuracy mode (default: 0.01 0.05 0.10 0.20)",
    )
    ap.add_argument("--out", default=None, help="write JSON here (default: benchmarks/paper_tables_<dataset>.json)")
    args = ap.parse_args()

    repo = Path(args.repo).resolve() if args.repo else DEFAULT_REPO
    env = describe_environment(repo)
    print(f"# Modan2 {env['modan2_version']} ({env['git_describe']}{', dirty' if env['git_dirty'] else ''})")
    print(f"# {env['cpu']}, {env['memory_gb']} GB, Python {env['python']}")
    print(f"# {env['timestamp']}\n")

    sys.path.insert(0, str(repo))
    import MdModel as mm
    import MdStatistics
    from components.formats.morphologika import Morphologika

    if args.manova_paths:
        payload = {"environment": env, "manova_paths": compare_manova_paths(args, mm, MdStatistics, Morphologika)}
    elif args.accuracy:
        results = measure_accuracy(args, mm, MdStatistics, Morphologika)
        payload = {"environment": env, **results}
        if args.markdown:
            print()
            print(accuracy_as_markdown(results))
    else:
        results = run(args, mm, MdStatistics, Morphologika)
        payload = {"environment": env, **results}
        if args.markdown:
            print()
            print(as_markdown(results))

    suffix = "accuracy" if args.accuracy else "manova_paths" if args.manova_paths else "runtime"
    out = Path(args.out) if args.out else DEFAULT_REPO / "benchmarks" / f"paper_{suffix}_{args.dataset}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
