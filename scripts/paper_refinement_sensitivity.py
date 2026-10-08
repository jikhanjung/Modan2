#!/usr/bin/env python3
"""How much the missing-landmark estimates depend on the cap on refinement rounds.

The imputation loop stops at a convergence tolerance or after
``MAX_IMPUTATION_REFINEMENTS`` rounds (5), and on the datasets of the paper's
accuracy table it almost always reaches the cap first (``benchmark_paper_tables.py
--accuracy`` records this). This script repeats that assessment -- same datasets,
same removal patterns, same error measure -- with the cap raised to 10 and 20, and
reports for each cap

  * the error statistics of the accuracy table, and how the loop ended;
  * against the shipped cap of 5, how far each estimate moved, and how much its
    error changed.

Estimates are compared in the frame of the complete-data alignment, after each
specimen's reconstructed configuration has been fitted onto its complete one on
the landmarks it kept -- the frame in which the accuracy table measures error --
so the comparison does not depend on the arbitrary orientation of each run.

Usage:
    python scripts/paper_refinement_sensitivity.py
    python scripts/paper_refinement_sensitivity.py --repo /path/to/worktree/at/a/tag
"""

import argparse
import json
import sys
from pathlib import Path

import benchmark_paper_tables as bench
import numpy as np

CAPS = (5, 10, 20)
FRACTIONS = (0.01, 0.05, 0.10, 0.20)
DATASET_KEYS = ("cranial222", "dense16")


def reconstruct(mm, dataset, reference, ref_cs, frac, pattern, seed):
    """Positions and errors of every estimate of one removal pattern, in the reference frame."""
    originals, _ = bench.punch_holes(dataset, frac, seed=seed + pattern * 101 + int(frac * 1000))
    removed = {}
    for obj_id in originals:
        obj = mm.MdObject.get_by_id(obj_id)
        obj.unpack_landmark()
        removed[obj_id] = [j for j, lm in enumerate(obj.landmark_list) if any(v is None for v in lm)]
    try:
        ops = mm.MdDatasetOps(dataset)
        with bench.RefinementTrace(mm) as trace:
            ops.procrustes_superimposition()
        imputed = {o.id: np.asarray(o.landmark_list, dtype=float) for o in ops.object_list}
    finally:
        bench.restore(mm, originals)

    positions, errors = [], []
    for idx, obj in enumerate(dataset.object_list):
        gaps = removed.get(obj.id)
        if not gaps:
            continue
        cfg = imputed[obj.id]
        kept = [j for j in range(len(cfg)) if j not in set(gaps)]
        aligned = bench._apply_similarity(cfg, bench._similarity_fit(cfg[kept], reference[idx][kept]))
        positions.append(aligned[gaps] / ref_cs[idx] * 100)
        errors.append(np.linalg.norm(aligned[gaps] - reference[idx][gaps], axis=1) / ref_cs[idx] * 100)
    return np.concatenate(positions), np.concatenate(errors), trace.outcome()


def main():
    ap = argparse.ArgumentParser(description="Sensitivity of the imputation to its cap on refinement rounds.")
    ap.add_argument("--repo", default=None, help="run against another Modan2 checkout (e.g. a worktree at a tag)")
    ap.add_argument("--patterns", type=int, default=10, help="removal patterns per condition (default: 10)")
    ap.add_argument("--seed", type=int, default=20260813, help="seed for the removal patterns")
    ap.add_argument(
        "--out", default=None, help="write JSON here (default: benchmarks/paper_refinement_sensitivity.json)"
    )
    args = ap.parse_args()

    repo = Path(args.repo).resolve() if args.repo else bench.DEFAULT_REPO
    env = bench.describe_environment(repo)
    print(f"# Modan2 {env['modan2_version']} ({env['git_describe']}{', dirty' if env['git_dirty'] else ''})")

    sys.path.insert(0, str(repo))
    import MdModel as mm
    from components.formats.morphologika import Morphologika

    shipped_cap = mm.MAX_IMPUTATION_REFINEMENTS
    results = {"environment": env, "shipped_cap": shipped_cap, "caps": list(CAPS), "patterns": args.patterns}
    results["units"] = "percent of centroid size, in the frame of the complete-data alignment"
    results["datasets"] = {}
    try:
        for key in DATASET_KEYS:
            spec = bench.DATASETS[key]
            dataset, _ = bench.load_dataset(mm, Morphologika, bench.DEFAULT_REPO / spec["file"], spec["name"])
            reference = [np.asarray(lm, dtype=float) for lm in bench.superimpose(mm, dataset, "procrustes")]
            ref_cs = [np.sqrt(((c - c.mean(axis=0)) ** 2).sum()) for c in reference]
            per_fraction = {}
            for frac in FRACTIONS:
                by_cap = {}
                for cap in CAPS:
                    mm.MAX_IMPUTATION_REFINEMENTS = cap
                    runs = [
                        reconstruct(mm, dataset, reference, ref_cs, frac, p, args.seed) for p in range(args.patterns)
                    ]
                    by_cap[cap] = (
                        np.concatenate([r[0] for r in runs]),
                        np.concatenate([r[1] for r in runs]),
                        [r[2] for r in runs],
                    )
                base_pos, base_err, _ = by_cap[shipped_cap]
                rows = {}
                for cap, (pos, err, outcomes) in by_cap.items():
                    moved = np.linalg.norm(pos - base_pos, axis=1)
                    rows[str(cap)] = {
                        "mean": float(err.mean()),
                        "median": float(np.median(err)),
                        "p95": float(np.percentile(err, 95)),
                        "max": float(err.max()),
                        "refinement": bench.summarize_refinement(outcomes, cap),
                        "vs_shipped_cap": {
                            "max_estimate_shift": float(moved.max()),
                            "mean_estimate_shift": float(moved.mean()),
                            "max_error_change": float(np.abs(err - base_err).max()),
                            "mean_error_change": float(err.mean() - base_err.mean()),
                        },
                    }
                    r = rows[str(cap)]
                    stops = r["refinement"]
                    print(
                        f"{key} {frac:4.0%} cap {cap:2d}: mean {r['mean']:.4f}%  max {r['max']:.2f}%"
                        f"  shift max {r['vs_shipped_cap']['max_estimate_shift']:.1e}%"
                        f"  error change max {r['vs_shipped_cap']['max_error_change']:.1e}%"
                        f"  stopped at tolerance {stops['stopped_at_tolerance']}/{stops['runs']},"
                        f" rounds {stops['rounds']}"
                    )
                per_fraction[f"{frac * 100:g}%"] = rows
            results["datasets"][key] = {"name": spec["name"], "conditions": per_fraction}
    finally:
        mm.MAX_IMPUTATION_REFINEMENTS = shipped_cap

    out = Path(args.out) if args.out else bench.DEFAULT_REPO / "benchmarks" / "paper_refinement_sensitivity.json"
    out.write_text(json.dumps(results, indent=2) + "\n")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
