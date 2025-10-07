"""Multi-Analysis Workflow Integration Tests.

Tests complete multi-analysis workflows:
- Create dataset → Run PCA → CVA → MANOVA
- Analysis result persistence
- Multiple analysis methods on same dataset
- Large dataset analysis
- Analysis comparison workflows
"""

import pytest

import MdModel
from MdStatistics import do_cva_analysis, do_manova_analysis, do_pca_analysis


class TestSequentialAnalysisWorkflow:
    """Test running multiple analysis methods sequentially on same dataset."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    @pytest.fixture
    def dataset_with_grouped_objects(self):
        """Create dataset with objects that have grouping variables."""
        dataset = MdModel.MdDataset.create(
            dataset_name="Multi-Analysis Dataset", dimension=2, landmark_count=5, propertyname_str="Group,Sex"
        )

        # Create 20 objects with 2 groups and 2 sexes
        for i in range(20):
            group = "GroupA" if i < 10 else "GroupB"
            sex = "M" if i % 2 == 0 else "F"

            landmarks = "\n".join([f"{10 + i + j * 5}.0\t{20 + i + j * 3}.0" for j in range(5)])

            MdModel.MdObject.create(
                object_name=f"Obj_{i:02d}",
                dataset=dataset,
                sequence=i + 1,
                landmark_str=landmarks,
                property_str=f"{group},{sex}",
            )

        return dataset

    def test_sequential_pca_cva_manova_workflow(self, qtbot, dataset_with_grouped_objects):
        """Test running PCA → CVA → MANOVA on same dataset."""
        dataset = dataset_with_grouped_objects

        # Step 1: Run PCA analysis
        pca_analysis = MdModel.MdAnalysis.create(
            dataset=dataset, analysis_name="PCA Analysis", superimposition_method="Procrustes"
        )

        # Prepare data for PCA
        objects = list(dataset.object_list)
        for obj in objects:
            obj.unpack_landmark()

        landmarks = [obj.landmark_list for obj in objects]

        # Run PCA
        pca_result = do_pca_analysis(landmarks)

        # Store PCA results
        if pca_result and "scores" in pca_result:
            import json

            pca_analysis.pca_analysis_result_json = json.dumps(pca_result["scores"])
            pca_analysis.pca_eigenvalues_json = json.dumps(pca_result.get("eigenvalues", []))
            pca_analysis.save()

        # Step 2: Run CVA analysis
        cva_analysis = MdModel.MdAnalysis.create(
            dataset=dataset, analysis_name="CVA Analysis", superimposition_method="Procrustes", cva_group_by="Group"
        )

        # Prepare groups for CVA
        groups = [obj.property_str.split(",")[0] for obj in objects]

        # Run CVA
        cva_result = do_cva_analysis(landmarks, groups)

        # Store CVA results
        if cva_result and "canonical_variables" in cva_result:
            import json

            cva_analysis.cva_analysis_result_json = json.dumps(cva_result["canonical_variables"])
            cva_analysis.cva_eigenvalues_json = json.dumps(cva_result.get("eigenvalues", []))
            cva_analysis.save()

        # Step 3: Run MANOVA
        manova_analysis = MdModel.MdAnalysis.create(
            dataset=dataset, analysis_name="MANOVA Analysis", superimposition_method="Procrustes", cva_group_by="Group"
        )

        # Run MANOVA
        manova_result = do_manova_analysis(landmarks, groups)

        # Store MANOVA results
        if manova_result:
            import json

            manova_analysis.pca_analysis_result_json = json.dumps(manova_result)
            manova_analysis.save()

        # Step 4: Verify all analyses exist
        assert dataset.analyses.count() == 3

        analyses = list(dataset.analyses)
        analysis_names = [a.analysis_name for a in analyses]
        assert "PCA Analysis" in analysis_names
        assert "CVA Analysis" in analysis_names
        assert "MANOVA Analysis" in analysis_names

        # Verify each analysis has results
        pca = dataset.analyses.where(MdModel.MdAnalysis.analysis_name == "PCA Analysis").first()
        assert pca.pca_analysis_result_json is not None

        cva = dataset.analyses.where(MdModel.MdAnalysis.analysis_name == "CVA Analysis").first()
        assert cva.cva_analysis_result_json is not None

        manova = dataset.analyses.where(MdModel.MdAnalysis.analysis_name == "MANOVA Analysis").first()
        assert manova.pca_analysis_result_json is not None

    def test_multiple_pca_analyses_different_superimposition(self, qtbot, dataset_with_grouped_objects):
        """Test running PCA with different superimposition methods."""
        dataset = dataset_with_grouped_objects

        objects = list(dataset.object_list)
        for obj in objects:
            obj.unpack_landmark()
        landmarks = [obj.landmark_list for obj in objects]

        # Run PCA with Procrustes
        pca_procrustes = MdModel.MdAnalysis.create(
            dataset=dataset, analysis_name="PCA - Procrustes", superimposition_method="Procrustes"
        )
        result_procrustes = do_pca_analysis(landmarks)
        if result_procrustes and "scores" in result_procrustes:
            import json

            pca_procrustes.pca_analysis_result_json = json.dumps(result_procrustes["scores"])
            pca_procrustes.save()

        # Run PCA with Bookstein
        pca_bookstein = MdModel.MdAnalysis.create(
            dataset=dataset, analysis_name="PCA - Bookstein", superimposition_method="Bookstein"
        )
        result_bookstein = do_pca_analysis(landmarks)
        if result_bookstein and "scores" in result_bookstein:
            import json

            pca_bookstein.pca_analysis_result_json = json.dumps(result_bookstein["scores"])
            pca_bookstein.save()

        # Verify both analyses exist
        assert dataset.analyses.count() == 2

        analyses = list(dataset.analyses)
        assert analyses[0].superimposition_method != analyses[1].superimposition_method

    def test_cva_with_different_grouping_variables(self, qtbot, dataset_with_grouped_objects):
        """Test running CVA with different grouping variables."""
        dataset = dataset_with_grouped_objects

        objects = list(dataset.object_list)
        for obj in objects:
            obj.unpack_landmark()
        landmarks = [obj.landmark_list for obj in objects]

        # CVA grouped by Group
        groups_by_group = [obj.property_str.split(",")[0] for obj in objects]
        cva_by_group = MdModel.MdAnalysis.create(
            dataset=dataset, analysis_name="CVA by Group", superimposition_method="Procrustes", cva_group_by="Group"
        )
        result_group = do_cva_analysis(landmarks, groups_by_group)
        if result_group and "canonical_variables" in result_group:
            import json

            cva_by_group.cva_analysis_result_json = json.dumps(result_group["canonical_variables"])
            cva_by_group.save()

        # CVA grouped by Sex
        groups_by_sex = [obj.property_str.split(",")[1] for obj in objects]
        cva_by_sex = MdModel.MdAnalysis.create(
            dataset=dataset, analysis_name="CVA by Sex", superimposition_method="Procrustes", cva_group_by="Sex"
        )
        result_sex = do_cva_analysis(landmarks, groups_by_sex)
        if result_sex and "canonical_variables" in result_sex:
            import json

            cva_by_sex.cva_analysis_result_json = json.dumps(result_sex["canonical_variables"])
            cva_by_sex.save()

        # Verify both analyses exist with different groupings
        assert dataset.analyses.count() == 2

        cva_analyses = list(dataset.analyses)
        assert cva_analyses[0].cva_group_by != cva_analyses[1].cva_group_by


class TestAnalysisPersistence:
    """Test analysis result persistence and retrieval."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    def test_analysis_results_persist_after_reload(self, qtbot):
        """Test that analysis results persist and can be retrieved."""
        # Create dataset with objects
        dataset = MdModel.MdDataset.create(
            dataset_name="Persistence Test", dimension=2, landmark_count=4, propertyname_str="Group"
        )

        for i in range(10):
            landmarks = "\n".join([f"{10 + i + j}.0\t{20 + i + j}.0" for j in range(4)])
            MdModel.MdObject.create(
                object_name=f"Obj_{i}", dataset=dataset, landmark_str=landmarks, property_str=f"Group{i % 2}"
            )

        # Run analysis and store results
        analysis = MdModel.MdAnalysis.create(
            dataset=dataset, analysis_name="Persistence PCA", superimposition_method="Procrustes"
        )

        import json

        test_data = {"scores": [[1.0, 2.0], [3.0, 4.0]], "eigenvalues": [5.0, 6.0]}
        analysis.pca_analysis_result_json = json.dumps(test_data)
        analysis.pca_eigenvalues_json = json.dumps([5.0, 6.0])
        analysis.save()

        analysis_id = analysis.id

        # Retrieve analysis in fresh query
        retrieved_analysis = MdModel.MdAnalysis.get_by_id(analysis_id)

        # Verify results persisted
        assert retrieved_analysis.pca_analysis_result_json is not None
        retrieved_data = json.loads(retrieved_analysis.pca_analysis_result_json)
        assert retrieved_data == test_data

    def test_delete_dataset_cascades_to_analyses(self, qtbot):
        """Test that deleting dataset also deletes all analyses."""
        # Create dataset with objects
        dataset = MdModel.MdDataset.create(dataset_name="Cascade Test", dimension=2, landmark_count=3)

        for i in range(5):
            MdModel.MdObject.create(object_name=f"Obj_{i}", dataset=dataset, landmark_str="1,2\n3,4\n5,6")

        # Create multiple analyses
        analysis_ids = []
        for i in range(3):
            analysis = MdModel.MdAnalysis.create(
                dataset=dataset, analysis_name=f"Analysis_{i}", superimposition_method="Procrustes"
            )
            analysis_ids.append(analysis.id)

        # Verify analyses exist
        assert dataset.analyses.count() == 3

        # Delete dataset
        dataset_id = dataset.id
        dataset.delete_instance()

        # Verify dataset deleted
        assert not MdModel.MdDataset.select().where(MdModel.MdDataset.id == dataset_id).exists()

        # Verify all analyses deleted (cascade)
        for analysis_id in analysis_ids:
            assert not MdModel.MdAnalysis.select().where(MdModel.MdAnalysis.id == analysis_id).exists()


class TestLargeDatasetAnalysis:
    """Test analysis workflows with large datasets."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    def test_analysis_with_100_objects(self, qtbot):
        """Test running analysis on dataset with 100 objects."""
        # Create dataset with 100 objects
        dataset = MdModel.MdDataset.create(
            dataset_name="Large Dataset", dimension=2, landmark_count=10, propertyname_str="Group"
        )

        for i in range(100):
            landmarks = "\n".join([f"{100 + i + j * 10}.0\t{200 + i + j * 15}.0" for j in range(10)])
            MdModel.MdObject.create(
                object_name=f"Obj_{i:03d}",
                dataset=dataset,
                sequence=i + 1,
                landmark_str=landmarks,
                property_str=f"Group{i % 5}",
            )

        # Verify dataset created
        assert dataset.object_list.count() == 100

        # Run PCA analysis
        objects = list(dataset.object_list)
        for obj in objects:
            obj.unpack_landmark()
        landmarks = [obj.landmark_list for obj in objects]

        MdModel.MdAnalysis.create(dataset=dataset, analysis_name="Large PCA", superimposition_method="Procrustes")

        result = do_pca_analysis(landmarks)

        # Verify analysis completed
        assert result is not None
        assert "scores" in result
        assert len(result["scores"]) == 100

    def test_analysis_with_many_landmarks(self, qtbot):
        """Test analysis with 50 landmarks per object."""
        # Create dataset with 50 landmarks
        dataset = MdModel.MdDataset.create(dataset_name="Many Landmarks", dimension=2, landmark_count=50)

        # Create 20 objects with 50 landmarks each
        for i in range(20):
            landmarks = "\n".join([f"{i + j}.0\t{i + j + 1}.0" for j in range(50)])
            MdModel.MdObject.create(object_name=f"Obj_{i}", dataset=dataset, landmark_str=landmarks)

        # Run analysis
        objects = list(dataset.object_list)
        for obj in objects:
            obj.unpack_landmark()
        landmarks = [obj.landmark_list for obj in objects]

        MdModel.MdAnalysis.create(
            dataset=dataset, analysis_name="Many Landmarks PCA", superimposition_method="Procrustes"
        )

        result = do_pca_analysis(landmarks)

        # Verify analysis handled many landmarks
        assert result is not None
        assert "scores" in result


class TestAnalysisComparison:
    """Test analysis comparison workflows."""

    @pytest.fixture(autouse=True)
    def setup_database(self, mock_database):
        """Setup database for all tests."""
        pass

    def test_compare_pca_results_different_methods(self, qtbot):
        """Test comparing PCA results from different superimposition methods."""
        # Create dataset
        dataset = MdModel.MdDataset.create(dataset_name="Comparison Test", dimension=2, landmark_count=5)

        for i in range(15):
            landmarks = "\n".join([f"{10 + i + j}.0\t{20 + i + j}.0" for j in range(5)])
            MdModel.MdObject.create(object_name=f"Obj_{i}", dataset=dataset, landmark_str=landmarks)

        objects = list(dataset.object_list)
        for obj in objects:
            obj.unpack_landmark()
        landmarks = [obj.landmark_list for obj in objects]

        # Run PCA with different methods
        methods = ["Procrustes", "Bookstein", "Resistant Fit"]
        analyses = []

        for method in methods:
            analysis = MdModel.MdAnalysis.create(
                dataset=dataset, analysis_name=f"PCA - {method}", superimposition_method=method
            )

            result = do_pca_analysis(landmarks)
            if result and "scores" in result:
                import json

                analysis.pca_analysis_result_json = json.dumps(result["scores"])
                analysis.save()

            analyses.append(analysis)

        # Verify all analyses created
        assert dataset.analyses.count() == 3

        # Verify each has different superimposition method
        methods_used = [a.superimposition_method for a in analyses]
        assert len(set(methods_used)) == 3

    def test_reanalyze_after_adding_objects(self, qtbot):
        """Test re-running analysis after adding more objects to dataset."""
        # Create initial dataset
        dataset = MdModel.MdDataset.create(dataset_name="Reanalysis Test", dimension=2, landmark_count=4)

        # Add initial 10 objects
        for i in range(10):
            landmarks = "\n".join([f"{10 + i + j}.0\t{20 + i + j}.0" for j in range(4)])
            MdModel.MdObject.create(object_name=f"Initial_{i}", dataset=dataset, landmark_str=landmarks)

        # Run first analysis
        objects = list(dataset.object_list)
        for obj in objects:
            obj.unpack_landmark()
        landmarks = [obj.landmark_list for obj in objects]

        analysis1 = MdModel.MdAnalysis.create(
            dataset=dataset, analysis_name="Initial PCA", superimposition_method="Procrustes"
        )

        result1 = do_pca_analysis(landmarks)
        if result1 and "scores" in result1:
            import json

            analysis1.pca_analysis_result_json = json.dumps(result1["scores"])
            analysis1.save()

        initial_count = len(result1["scores"]) if result1 else 0

        # Add 10 more objects
        for i in range(10, 20):
            landmarks = "\n".join([f"{10 + i + j}.0\t{20 + i + j}.0" for j in range(4)])
            MdModel.MdObject.create(object_name=f"Added_{i}", dataset=dataset, landmark_str=landmarks)

        # Run second analysis with all objects
        objects = list(dataset.object_list)
        for obj in objects:
            obj.unpack_landmark()
        landmarks = [obj.landmark_list for obj in objects]

        analysis2 = MdModel.MdAnalysis.create(
            dataset=dataset, analysis_name="Updated PCA", superimposition_method="Procrustes"
        )

        result2 = do_pca_analysis(landmarks)
        if result2 and "scores" in result2:
            import json

            analysis2.pca_analysis_result_json = json.dumps(result2["scores"])
            analysis2.save()

        updated_count = len(result2["scores"]) if result2 else 0

        # Verify both analyses exist
        assert dataset.analyses.count() == 2

        # Verify second analysis has more objects
        assert updated_count == 20
        assert initial_count == 10
