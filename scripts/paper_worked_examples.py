#!/usr/bin/env python3
"""Reproduce the figures of the Modan2 paper's worked example on the cranial dataset.

``benchmark_paper_tables.py`` produces the runtime and accuracy tables; this
script produces the numbers quoted in the worked example: the PCA variance
proportions, and for each grouping variable the canonical-axis proportions,
the cross-validated classification accuracy and its baselines, and the MANOVA.
It runs the same code paths as the application -- Procrustes superimposition,
``do_pca_analysis``, ``do_cva_analysis``, and MANOVA on the principal component
scores truncated by ``effective_component_count`` as ``ModanController`` does.

The data are those of Rovinsky et al. (2021), fetched from figshare by
``scripts/rovinsky2021_data.py``; the groupings are the published dietary
category (FeedCatgFine, ten categories) and prey category (PreyCatg, small or
large prey). The 16 thylacine specimens are removed before superimposition.
The dataset codes their diet and prey as NA, and an unknown category is not a
group to be discriminated; left in, it would act as one more "diet" that is in
fact one species.

``do_cva_analysis`` reports the cross-validated accuracy but not the
out-of-fold predictions, so the script refits the same PCA + LDA pipeline under
the same cross-validation to obtain them, checks that the accuracy agrees with
the application's, and derives the balanced accuracy and confusion matrix.

Usage:
    python scripts/paper_worked_examples.py
    python scripts/paper_worked_examples.py --repo /path/to/worktree/at/a/tag
"""

import argparse
import collections
import json
import sys
from pathlib import Path

import benchmark_paper_tables as bench
import numpy as np

DATASET_KEY = "cranial206"  # bench.DATASETS: the 222 specimens less the 16 thylacines
GROUP_VARIABLES = {"DietFine": "dietary category", "PreyCatg": "prey size"}


def out_of_fold_predictions(data_matrix, groups, n_components):
    """Refit the pipeline of ``do_cva_analysis`` under leave-one-out cross-validation."""
    from sklearn.decomposition import PCA
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.model_selection import LeaveOneOut, cross_val_predict
    from sklearn.pipeline import make_pipeline

    if n_components is None:
        estimator = LinearDiscriminantAnalysis()
    else:
        # The exact solver: the application's ARPACK path gives the same subspace.
        estimator = make_pipeline(PCA(n_components=n_components, svd_solver="full"), LinearDiscriminantAnalysis())
    return cross_val_predict(estimator, data_matrix, groups, cv=LeaveOneOut())


def analyse_grouping(md_statistics, aligned, data_matrix, pca, groups):
    from sklearn.metrics import balanced_accuracy_score, confusion_matrix

    groups = np.asarray(groups)
    counts = collections.Counter(groups.tolist())
    labels = sorted(counts, key=lambda g: (-counts[g], g))
    n_samples, n_groups = len(groups), len(counts)

    cva = md_statistics.do_cva_analysis(aligned, groups.tolist())
    if cva["accuracy_method"] != "leave-one-out":
        raise RuntimeError(f"expected leave-one-out cross-validation, got {cva['accuracy_method']}")
    predictions = out_of_fold_predictions(data_matrix, groups, cva["n_variables_used"] if cva["reduced"] else None)
    accuracy = float(np.mean(predictions == groups) * 100)
    if abs(accuracy - cva["cross_validated_accuracy"]) > 1e-9:
        raise RuntimeError(
            f"refitted accuracy {accuracy} differs from the application's {cva['cross_validated_accuracy']}"
        )

    k = md_statistics.effective_component_count(pca["eigenvalues"], n_samples=n_samples, n_groups=n_groups)
    manova = md_statistics.do_manova_analysis_on_pca([s[:k] for s in pca["scores"]], groups.tolist())
    tests = {t["name"]: t for t in manova["test_statistics"]}

    return {
        "n_groups": n_groups,
        "group_sizes": {g: counts[g] for g in labels},
        "cva_variables": cva["n_variables_used"],
        "canonical_axis_percent": [v * 100 for v in cva["eigenvalues"]],
        "cross_validation": cva["accuracy_method"],
        "cross_validated_accuracy": cva["cross_validated_accuracy"],
        "majority_class_accuracy": cva["chance_accuracy"],
        "balanced_accuracy": float(balanced_accuracy_score(groups, predictions) * 100),
        "majority_class_balanced_accuracy": 100.0 / n_groups,
        "per_group_recall": {g: float(np.mean(predictions[groups == g] == g) * 100) for g in labels},
        "confusion_matrix": {
            "labels": labels,
            "rows_true_columns_predicted": confusion_matrix(groups, predictions, labels=labels).tolist(),
        },
        "manova_variables": k,
        "manova": {
            name: {key: tests[name][key] for key in ("value", "df_num", "df_den", "f_statistic", "p_value")}
            for name in ("Wilks' lambda", "Pillai's trace", "Hotelling-Lawley trace", "Roy's greatest root")
            if name in tests
        },
    }


def main():
    ap = argparse.ArgumentParser(description="Reproduce the worked-example figures of the Modan2 paper.")
    ap.add_argument("--repo", default=None, help="run against another Modan2 checkout (e.g. a worktree at a tag)")
    ap.add_argument("--file", default=None, help="override the Morphologika file")
    ap.add_argument(
        "--out", default=None, help="write JSON here (default: benchmarks/paper_worked_examples_cranial206.json)"
    )
    args = ap.parse_args()

    repo = Path(args.repo).resolve() if args.repo else bench.DEFAULT_REPO
    env = bench.describe_environment(repo)
    print(f"# Modan2 {env['modan2_version']} ({env['git_describe']}{', dirty' if env['git_dirty'] else ''})")

    sys.path.insert(0, str(repo))
    import MdModel as mm
    import MdStatistics
    from components.formats.morphologika import Morphologika

    spec = bench.DATASETS[DATASET_KEY]
    path = Path(args.file) if args.file else bench.DEFAULT_REPO / spec["file"]
    dataset, morph = bench.load_dataset(mm, Morphologika, path, spec["name"])
    dataset, excluded = bench.apply_exclusion(mm, dataset, morph, spec)

    aligned = bench.superimpose(mm, dataset, "procrustes")
    data_matrix = np.asarray([np.asarray(config, dtype=float).ravel() for config in aligned])
    pca = MdStatistics.do_pca_analysis(aligned)
    ratio = np.asarray(pca["explained_variance_ratio"], dtype=float)
    cumulative = np.cumsum(ratio)

    results = {
        "environment": env,
        "dataset": spec["name"],
        "file": str(path),
        "excluded": excluded,
        "n_objects": len(data_matrix),
        "pca": {
            "pc1_percent": ratio[0] * 100,
            "pc2_percent": ratio[1] * 100,
            "pc1_pc2_percent": cumulative[1] * 100,
            "components_to_95_percent": int(np.searchsorted(cumulative, 0.95) + 1),
        },
        "groupings": {},
    }
    for variable, label in GROUP_VARIABLES.items():
        groups = bench.groups_for(dataset, morph, variable)
        results["groupings"][variable] = {
            "label": label,
            **analyse_grouping(MdStatistics, aligned, data_matrix, pca, groups),
        }

    p = results["pca"]
    print(
        f"# {results['n_objects']} specimens ({excluded['n']} excluded as {excluded['variable']} = {excluded['value']})"
    )
    print(f"PCA: PC1 {p['pc1_percent']:.1f}%, PC2 {p['pc2_percent']:.1f}%, {p['components_to_95_percent']} PCs to 95%")
    for variable, r in results["groupings"].items():
        wilks = r["manova"]["Wilks' lambda"]
        axes = ", ".join(f"CV{i + 1} {v:.1f}%" for i, v in enumerate(r["canonical_axis_percent"][:2]))
        print(
            f"{variable}: {r['n_groups']} groups, {axes},"
            f" LOOCV {r['cross_validated_accuracy']:.1f}% (majority {r['majority_class_accuracy']:.1f}%),"
            f" balanced {r['balanced_accuracy']:.1f}%, Wilks {wilks['value']:.3f},"
            f" F({wilks['df_num']}, {wilks['df_den']}) = {wilks['f_statistic']:.2f}"
        )

    out = Path(args.out) if args.out else bench.DEFAULT_REPO / "benchmarks" / "paper_worked_examples_cranial206.json"
    out.write_text(json.dumps(results, indent=2, default=float) + "\n")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
