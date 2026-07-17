"""R02 latent-bug regression tests (issues surfaced during Batch C)."""

import MdModel
from ModanController import ModanController


def _dataset_with_objects(n=4, landmarks=5):
    ds = MdModel.MdDataset.create(dataset_name="D", dataset_desc="", dimension=2)
    for i in range(n):
        MdModel.MdObject.create(
            dataset=ds,
            object_name=f"O{i}",
            sequence=i + 1,
            landmark_str="\n".join([f"{i + j}.0\t{i + j + 1}.0" for j in range(landmarks)]),
        )
    return ds


def test_run_analysis_lowercase_pca_persists_results(mock_database):
    """The old-signature *lowercase* ``"pca"`` must persist PCA result JSON.

    Dispatch uses ``analysis_type.upper() == "PCA"`` but the persistence path used a
    case-sensitive ``analysis_type == "PCA"``, so a lowercase call ran PCA yet saved
    no scores (silent data loss). Fixed in R02 by harmonizing the persist check.
    """
    ds = _dataset_with_objects()
    controller = ModanController()
    controller.set_current_dataset(ds)

    analysis = controller.run_analysis("pca", {"name": "LowerCasePCA"})

    assert analysis is not None
    assert analysis.analysis_name == "LowerCasePCA"
    assert analysis.pca_analysis_result_json  # non-empty -> scores were persisted


def test_run_analysis_uppercase_pca_still_persists_results(mock_database):
    """Guard: the uppercase path (unchanged) keeps persisting results."""
    ds = _dataset_with_objects()
    controller = ModanController()
    controller.set_current_dataset(ds)

    analysis = controller.run_analysis("PCA", {"name": "UpperCasePCA"})

    assert analysis is not None
    assert analysis.pca_analysis_result_json
