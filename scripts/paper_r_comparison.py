#!/usr/bin/env python3
"""Compare the analyses of the Modan2 paper's worked example with an independent R implementation.

The worked example (``paper_worked_examples.py``) runs Procrustes superimposition,
PCA, CVA with leave-one-out classification, and MANOVA on the 206 cranial
specimens of known diet. This script runs the same analyses twice from the same
raw coordinates -- once through Modan2's code paths, once through
``paper_r_comparison.R`` (geomorph::gpagen, prcomp, MASS::lda, manova) -- and
reports how far the two agree:

  GPA     aligned coordinates, after the one global rotation that best maps R's
          frame onto Modan2's (the orientation of a GPA is arbitrary), and the
          pairwise Procrustes distances, which need no such rotation
  PCA     variance proportions, eigenvalues (Modan2 divides the covariance by
          n, prcomp by n - 1), the component count, and the scores up to sign
  CVA     component count, canonical-axis proportions, canonical scores
          (correlation, since the two scale the axes differently), and the
          resubstitution and leave-one-out predictions specimen by specimen
  MANOVA  the four test statistics with their F approximations

The Modan2 side also counts how often its rotation step had to correct a
reflection, since agreement says nothing about a case that never occurred.

The R environment is described in ``benchmarks/r-environment.yml``.

Usage:
    python scripts/paper_r_comparison.py --rscript ~/micromamba/envs/modan2-r/bin/Rscript
    python scripts/paper_r_comparison.py --repo /path/to/worktree/at/a/tag --rscript ...
"""

import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

import benchmark_paper_tables as bench
import numpy as np
import paper_worked_examples as worked

R_SCRIPT = Path(__file__).resolve().parent / "paper_r_comparison.R"
STATSMODELS_NAMES = {
    "Wilks": "Wilks' lambda",
    "Pillai": "Pillai's trace",
    "HotellingLawley": "Hotelling-Lawley trace",
    "Roy": "Roy's greatest root",
}
GPA_TOL = 1e-10  # gpagen's convergence tolerance; its default is 1e-4


def best_rotation(source, target):
    """The proper rotation Q minimising ||source @ Q - target||."""
    u, _, vt = np.linalg.svd(source.T @ target)
    correction = np.eye(source.shape[1])
    correction[-1, -1] = np.sign(np.linalg.det(u @ vt))
    return u @ correction @ vt


def pairwise_distances(configs):
    flat = configs.reshape(len(configs), -1)
    return np.linalg.norm(flat[:, None, :] - flat[None, :, :], axis=2)


def run_modan2(mm, MdStatistics, dataset, morph):
    ops = mm.MdDatasetOps(dataset)
    raw = [[list(lm) for lm in obj.landmark_list] for obj in ops.object_list]
    groupings = {
        variable: [obj.variable_list[morph.variablename_list.index(variable)] for obj in ops.object_list]
        for variable in worked.GROUP_VARIABLES
    }

    reflections = []
    rotation_matrix = mm.MdDatasetOps.rotation_matrix

    def counting(self, ref, target):
        v, _, w = np.linalg.svd(np.dot(np.transpose(ref), target))
        reflections.append(np.linalg.det(v) * np.linalg.det(w) < 0)
        return rotation_matrix(self, ref, target)

    mm.MdDatasetOps.rotation_matrix = counting
    try:
        ops.procrustes_superimposition()
    finally:
        mm.MdDatasetOps.rotation_matrix = rotation_matrix
    aligned = [obj.landmark_list for obj in ops.object_list]

    data_matrix = np.asarray([np.asarray(config, dtype=float).ravel() for config in aligned])
    pca = MdStatistics.do_pca_analysis(aligned)
    results = {"raw": raw, "aligned": np.asarray(aligned, dtype=float), "pca": pca, "groupings": {}}
    results["reflection_corrections"] = int(sum(reflections))
    results["rotations"] = len(reflections)

    for variable, groups in groupings.items():
        cva = MdStatistics.do_cva_analysis(aligned, groups)
        k = cva["n_variables_used"] if cva["reduced"] else None
        held_out = worked.out_of_fold_predictions(data_matrix, np.asarray(groups), k)
        accuracy = float(np.mean(held_out == np.asarray(groups)) * 100)
        if abs(accuracy - cva["cross_validated_accuracy"]) > 1e-9:
            raise RuntimeError(f"refitted accuracy {accuracy} differs from the application's")
        n_groups = len(set(groups))
        k_manova = MdStatistics.effective_component_count(pca["eigenvalues"], n_samples=len(groups), n_groups=n_groups)
        manova = MdStatistics.do_manova_analysis_on_pca([s[:k_manova] for s in pca["scores"]], groups)
        results["groupings"][variable] = {
            "groups": groups,
            "cva": cva,
            "loocv_predictions": held_out.tolist(),
            "manova_components": k_manova,
            "manova": {t["name"]: t for t in manova["test_statistics"]},
        }
    return results


def run_r(rscript, raw, groupings, variance_target, max_variables):
    with tempfile.TemporaryDirectory() as tmp:
        given = Path(tmp) / "input.json"
        produced = Path(tmp) / "output.json"
        given.write_text(
            json.dumps(
                {
                    "coords": raw,
                    "groupings": groupings,
                    "variance_target": variance_target,
                    "max_variables": max_variables,
                    "gpa_tol": GPA_TOL,
                }
            )
        )
        env = {**os.environ, "RGL_USE_NULL": "TRUE"}  # rgl, loaded by geomorph, needs no display
        subprocess.run([*shlex.split(rscript), str(R_SCRIPT), str(given), str(produced)], check=True, env=env)
        return json.loads(produced.read_text())


def compare(m, r):
    n = len(m["aligned"])
    out = {}

    # GPA ------------------------------------------------------------------
    m_cfg = m["aligned"]
    r_cfg = np.asarray(r["gpa"]["coords"], dtype=float)
    k = m_cfg.shape[2]
    q = best_rotation(r_cfg.reshape(-1, k), m_cfg.reshape(-1, k))
    diff = (r_cfg.reshape(-1, k) @ q).reshape(m_cfg.shape) - m_cfg
    sizes = lambda c: np.sqrt(((c - c.mean(axis=1, keepdims=True)) ** 2).sum(axis=(1, 2)))  # noqa: E731
    out["gpa"] = {
        "r_iterations": r["gpa"]["iterations"],
        "r_tolerance": GPA_TOL,
        "modan2_rotations": m["rotations"],
        "modan2_reflection_corrections": m["reflection_corrections"],
        "max_centroid_size_difference": float(np.abs(sizes(m_cfg) - sizes(r_cfg)).max()),
        "max_coordinate_difference": float(np.abs(diff).max()),
        "rms_coordinate_difference": float(np.sqrt((diff**2).mean())),
        "max_pairwise_distance_difference": float(np.abs(pairwise_distances(m_cfg) - pairwise_distances(r_cfg)).max()),
        "units": "centroid size (each aligned configuration has size 1)",
    }

    # PCA ------------------------------------------------------------------
    m_ratio = np.asarray(m["pca"]["explained_variance_ratio"], dtype=float)
    r_ratio = np.asarray(r["pca"]["ratio"], dtype=float)
    k95 = int(r["pca"]["components_to_target"])
    m_k95 = int(np.searchsorted(np.cumsum(m_ratio), 0.95) + 1)
    m_eig = np.asarray(m["pca"]["eigenvalues"], dtype=float)[:k95] * n / (n - 1)
    r_eig = np.asarray(r["pca"]["eigenvalues"], dtype=float)[:k95]
    m_scores = np.asarray(m["pca"]["scores"], dtype=float)[:, :k95]
    r_scores = np.asarray(r["pca"]["scores"], dtype=float)
    signs = np.sign((m_scores * r_scores).sum(axis=0))
    out["pca"] = {
        "components_to_95_percent": {"modan2": m_k95, "r": k95},
        "pc1_percent": {"modan2": m_ratio[0] * 100, "r": r_ratio[0] * 100},
        "pc2_percent": {"modan2": m_ratio[1] * 100, "r": r_ratio[1] * 100},
        "pc3_percent": {"modan2": m_ratio[2] * 100, "r": r_ratio[2] * 100},
        "max_variance_percent_difference_first_20": float(np.abs(m_ratio[:20] - r_ratio[:20]).max() * 100),
        "max_relative_eigenvalue_difference": float(np.abs(m_eig / r_eig - 1).max()),
        "max_score_difference": float(np.abs(m_scores - r_scores * signs).max()),
        "pc1_score_sd": float(r_scores[:, 0].std(ddof=1)),
    }

    # CVA and MANOVA, per grouping -----------------------------------------
    out["groupings"] = {}
    for variable, mg in m["groupings"].items():
        rg = r["groupings"][variable]
        cva = mg["cva"]
        groups = np.asarray(mg["groups"])
        m_cv = np.asarray(cva["canonical_variables"], dtype=float)
        # With two groups there is one canonical axis, and R writes its values unboxed.
        r_cv = np.asarray(rg["canonical_scores"], dtype=float).reshape(len(groups), -1)
        m_prop = np.asarray(cva["eigenvalues"], dtype=float)
        r_prop = np.atleast_1d(np.asarray(rg["canonical_proportions"], dtype=float))
        m_loo = np.asarray(mg["loocv_predictions"])
        r_loo = np.asarray(rg["loocv_predictions"])
        manova = {}
        for r_name, m_name in STATSMODELS_NAMES.items():
            mt, rt = mg["manova"][m_name], rg["manova"][r_name]
            manova[m_name] = {
                "modan2": {key: mt[key] for key in ("value", "f_statistic", "df_num", "df_den")},
                "r": {key: rt[key] for key in ("value", "f_statistic", "df_num", "df_den")},
                "relative_value_difference": abs(mt["value"] / rt["value"] - 1),
            }
        out["groupings"][variable] = {
            "n_groups": rg["n_groups"],
            "components": {
                "modan2_cva": cva["n_variables_used"],
                "modan2_manova": mg["manova_components"],
                "r": rg["components"],
            },
            "canonical_percent": {"modan2": (m_prop[:3] * 100).tolist(), "r": (r_prop[:3] * 100).tolist()},
            "max_canonical_percent_difference": float(np.abs(m_prop - r_prop[: len(m_prop)]).max() * 100),
            "canonical_score_correlation": [
                float(abs(np.corrcoef(m_cv[:, a], r_cv[:, a])[0, 1])) for a in range(r_cv.shape[1])
            ],
            "resubstitution_disagreements": int(
                (np.asarray(cva["classification"]) != np.asarray(rg["resubstitution_predictions"])).sum()
            ),
            "loocv_accuracy": {"modan2": cva["cross_validated_accuracy"], "r": rg["loocv_accuracy"]},
            "loocv_disagreements": int((m_loo != r_loo).sum()),
            "loocv_disagreeing_specimens": [int(i) for i in np.flatnonzero(m_loo != r_loo)],
            "true_groups_of_disagreements": groups[m_loo != r_loo].tolist(),
            "manova": manova,
        }
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Compare the worked-example analyses with an independent R implementation."
    )
    ap.add_argument("--repo", default=None, help="run against another Modan2 checkout (e.g. a worktree at a tag)")
    ap.add_argument(
        "--rscript", default="Rscript", help="command that runs Rscript in the environment of r-environment.yml"
    )
    ap.add_argument(
        "--out", default=None, help="write JSON here (default: benchmarks/paper_r_comparison_cranial206.json)"
    )
    args = ap.parse_args()

    repo = Path(args.repo).resolve() if args.repo else bench.DEFAULT_REPO
    env = bench.describe_environment(repo)
    print(f"# Modan2 {env['modan2_version']} ({env['git_describe']}{', dirty' if env['git_dirty'] else ''})")

    sys.path.insert(0, str(repo))
    import MdModel as mm
    import MdStatistics
    from components.formats.morphologika import Morphologika

    spec = bench.DATASETS["cranial206"]
    dataset, morph = bench.load_dataset(mm, Morphologika, bench.DEFAULT_REPO / spec["file"], spec["name"])
    dataset, excluded = bench.apply_exclusion(mm, dataset, morph, spec)

    m = run_modan2(mm, MdStatistics, dataset, morph)
    r = run_r(
        args.rscript,
        m["raw"],
        {variable: g["groups"] for variable, g in m["groupings"].items()},
        variance_target=0.95,
        max_variables=MdStatistics.MANOVA_MAX_VARIABLES,
    )
    results = {
        "environment": env,
        "r_versions": r["versions"],
        "dataset": spec["name"],
        "excluded": excluded,
        "n_objects": len(m["raw"]),
        **compare(m, r),
    }

    g, p = results["gpa"], results["pca"]
    print(f"# {results['n_objects']} specimens; R {r['versions']['R']}, geomorph {r['versions']['geomorph']}")
    print(
        f"GPA: max coordinate difference {g['max_coordinate_difference']:.1e}, max pairwise distance difference"
        f" {g['max_pairwise_distance_difference']:.1e} (centroid size); R iterations {g['r_iterations']};"
        f" Modan2 reflection corrections {g['modan2_reflection_corrections']} of {g['modan2_rotations']}"
    )
    print(
        f"PCA: PC1 {p['pc1_percent']['modan2']:.4f}% vs {p['pc1_percent']['r']:.4f}%, components to 95%"
        f" {p['components_to_95_percent']}, max eigenvalue difference {p['max_relative_eigenvalue_difference']:.1e}"
        f" (relative), max score difference {p['max_score_difference']:.1e} (PC1 sd {p['pc1_score_sd']:.3f})"
    )
    for variable, c in results["groupings"].items():
        print(
            f"{variable}: components {c['components']}, CV% {c['canonical_percent']},"
            f" score |r| {[round(x, 10) for x in c['canonical_score_correlation']]},"
            f" resubstitution disagreements {c['resubstitution_disagreements']},"
            f" LOOCV {c['loocv_accuracy']} ({c['loocv_disagreements']} disagreements)"
        )
        for name, t in c["manova"].items():
            print(f"    {name:<24} Modan2 {t['modan2']}  R {t['r']}")

    out = Path(args.out) if args.out else bench.DEFAULT_REPO / "benchmarks" / "paper_r_comparison_cranial206.json"
    out.write_text(json.dumps(results, indent=2, default=float) + "\n")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
