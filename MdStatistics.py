import logging

import numpy
import pandas as pd
from statsmodels.multivariate.manova import MANOVA

logger = logging.getLogger(__name__)


class MdPrincipalComponent:
    """Legacy Principal Component Analysis class.

    Performs PCA on morphometric data.
    """

    def __init__(self):
        return

    def SetData(self, data):
        """Set the data for PCA analysis."""
        self.data = data
        self.nObservation = len(data)
        self.nVariable = len(data[0])

    def Analyze(self):
        """analyze"""
        self.raw_eigen_values = []
        self.eigen_value_percentages = []

        sums = [0.0 for x in range(self.nVariable)]
        avrs = [0.0 for x in range(self.nVariable)]
        """ calculate the empirical mean """
        for i in range(self.nObservation):
            for j in range(self.nVariable):
                sums[j] += float(self.data[i][j])

        for j in range(self.nVariable):
            avrs[j] = float(sums[j]) / float(self.nObservation)

        for i in range(self.nObservation):
            for j in range(self.nVariable):
                self.data[i][j] -= avrs[j]

        """ covariance matrix """
        np_data = numpy.array(self.data)
        self.covariance_matrix = numpy.dot(numpy.transpose(np_data), np_data) / self.nObservation

        v, s, w = numpy.linalg.svd(self.covariance_matrix)

        self.raw_eigen_values = s
        sum = 0
        for ss in s:
            sum += ss
        for ss in s:
            self.eigen_value_percentages.append(ss / sum)
        cumul = 0
        eigen_values = []
        i = 0
        nSignificantEigenValue = -1
        nEigenValues = -1
        for ss in s:
            cumul += ss
            eigen_values.append(ss)
            # print sum, cumul, ss
            if cumul / sum > 0.95 and nSignificantEigenValue == -1:
                nSignificantEigenValue = i + 1
            if (ss / sum) < 0.00001 and nEigenValues == -1:
                nEigenValues = i + 1
            i += 1

        self.rotated_matrix = numpy.dot(np_data, v)
        self.rotation_matrix = v
        self.loading = v
        return True


class MdCanonicalVariate:
    """Legacy Canonical Variate Analysis class.

    Performs CVA on morphometric data with group classification.
    """

    def __init__(self):
        self.dimension = -1
        self.nVariable = 0
        self.nObservation = 0
        # self.datamatrix = []
        return

    def SetData(self, data):
        """Set the data for CVA analysis."""
        self.data = data
        self.nObservation = len(data)
        self.nVariable = len(data[0])

    def SetCategory(self, category_list):
        """Set the category/group labels for CVA."""
        self.category_list = category_list

    def Analyze(self):
        """analyze"""
        actual_data = self.data
        category_data = self.category_list
        category_set = set(category_data)
        len(category_set)

        variances = [0.0 for x in range(self.nVariable)]
        total_avg = [0.0 for x in range(self.nVariable)]
        total_sum = [0.0 for x in range(self.nVariable)]
        total_count = self.nObservation

        avg_by_category = {}
        sum_by_category = {}
        count_by_category = {}
        # print "analyze"
        for k in list(category_set):
            count_by_category[k] = 0
            sum_by_category[k] = [0.0 for x in range(self.nVariable)]
            avg_by_category[k] = [0.0 for x in range(self.nVariable)]

        for i in range(total_count):
            k = category_data[i]
            count_by_category[k] += 1
            for j in range(self.nVariable):
                sum_by_category[k][j] += float(actual_data[i][j])
                total_sum[j] += float(actual_data[i][j])

        for k in list(category_set):
            for i in range(self.nVariable):
                avg_by_category[k][i] = sum_by_category[k][i] / count_by_category[k]
                # print k, sum_by_category[k], avg_by_category[k]

        for i in range(self.nVariable):
            total_avg[i] = total_sum[i] * 1.0 / total_count
        # print total_sum, total_avg

        """ check zero variance variables """
        for p in range(self.nVariable):
            for idx in range(self.nObservation):
                variances[p] += (float(actual_data[idx][p]) - total_avg[p]) ** 2

        covariance_matrix_size = 0
        for p in range(self.nVariable):
            if variances[p] == 0:
                pass
                # print "variance = 0 for ", p, "th variable"
            else:
                covariance_matrix_size += 1
        # print "covariance_matrix_size", covariance_matrix_size

        covariance_matrix = [[0.0 for x in range(covariance_matrix_size)] for y in range(covariance_matrix_size)]
        p_ = 0
        for p in range(self.nVariable):
            if variances[p] == 0:
                continue
            q_ = 0
            for q in range(self.nVariable):
                if variances[q] == 0:
                    continue
                for idx in range(self.nObservation):
                    diff_p = float(actual_data[idx][p]) - total_avg[p]
                    diff_q = float(actual_data[idx][q]) - total_avg[q]
                    # print p_, q_
                    covariance_matrix[p_][q_] += diff_p * diff_q / (total_count - 1)
                q_ += 1
            p_ += 1

        within_cov = [[0.0 for x in range(covariance_matrix_size)] for y in range(covariance_matrix_size)]
        between_cov = [[0.0 for x in range(covariance_matrix_size)] for y in range(covariance_matrix_size)]

        within_by_category = {}
        between_by_category = {}
        for key in list(category_set):
            within_by_category[key] = [0.0 for x in range(covariance_matrix_size)]
            between_by_category[key] = [0.0 for x in range(covariance_matrix_size)]

        p_ = 0
        for p in range(self.nVariable):
            if variances[p] == 0:
                continue
            q_ = 0
            for q in range(self.nVariable):
                if variances[q] == 0:
                    continue
                for idx in range(self.nObservation):
                    key = category_data[idx]
                    diff_p = float(actual_data[idx][p]) - avg_by_category[key][p]
                    diff_q = float(actual_data[idx][q]) - avg_by_category[key][q]
                    within_cov[p_][q_] += diff_p * diff_q / (total_count - len(category_set))
                q_ += 1
            p_ += 1

        p_ = 0
        for p in range(self.nVariable):
            if variances[p] == 0:
                continue
            q_ = 0
            for q in range(self.nVariable):
                if variances[q] == 0:
                    continue
                for key in list(category_set):
                    diff_p = avg_by_category[key][p] - total_avg[p]
                    diff_q = avg_by_category[key][q] - total_avg[q]
                    between_cov[p_][q_] += diff_p * diff_q * count_by_category[key] / len(category_set)
                q_ += 1
            p_ += 1

        w = numpy.array(within_cov)
        b = numpy.array(between_cov)

        try:
            wi = numpy.linalg.inv(w)
        except numpy.linalg.LinAlgError:
            # print "Singular matrix: ", e
            return False
        # print "wi", wi
        x = numpy.dot(wi, b)

        u, s, v = numpy.linalg.svd(x)

        self.raw_eigen_values = s[:]
        s /= sum(s)
        self.eigen_value_percentages = s[:]

        rotation_matrix = numpy.zeros((self.nVariable, self.nVariable))

        p_ = 0
        for p in range(self.nVariable):
            q_ = 0
            for q in range(self.nVariable):
                if variances[p] == 0 or variances[q] == 0:
                    rotation_matrix[p, q] = 0.0
                else:
                    rotation_matrix[p, q] = u[p_, q_]
                if variances[q] != 0:
                    q_ += 1
            if variances[p] != 0:
                p_ += 1

        np_data = numpy.zeros((self.nObservation, self.nVariable))
        for p in range(self.nObservation):
            for q in range(self.nVariable):
                np_data[p, q] = float(actual_data[p][q])

        self.rotation_matrix = rotation_matrix
        self.rotated_matrix = numpy.dot(np_data, rotation_matrix)
        self.loading = rotation_matrix
        return True


def PerformCVA(dataset_ops, classifier_index):
    cva = MdCanonicalVariate()

    # property_index = group_by
    logger.info("Perform CVA group by classifier index %s", classifier_index)
    if classifier_index < 0:
        # QMessageBox.information(self, "Information", "Please select a property.")
        return
    datamatrix = []
    category_list = []
    # obj = dataset_ops.object_list[0]
    # print(obj, obj.property_list, property_index)
    for obj in dataset_ops.object_list:
        datum = []
        for lm in obj.landmark_list:
            datum.extend(lm)
        datamatrix.append(datum)
        if classifier_index >= 0 and classifier_index < len(obj.variable_list):
            category_list.append(obj.variable_list[classifier_index])
        else:
            category_list.append("Unknown")

    cva.SetData(datamatrix)
    cva.SetCategory(category_list)
    analysis_return = cva.Analyze()
    if not analysis_return:
        return None

    min(cva.nObservation, cva.nVariable)

    return cva


def PerformPCA(dataset_ops):
    pca = MdPrincipalComponent()
    datamatrix = []
    for obj in dataset_ops.object_list:
        datum = []
        for lm in obj.landmark_list:
            datum.extend(lm)
        datamatrix.append(datum)

    pca.SetData(datamatrix)
    analysis_result = pca.Analyze()
    if not analysis_result:
        return None

    min(pca.nObservation, pca.nVariable)

    return pca


class MdManova:
    """Legacy MANOVA (Multivariate Analysis of Variance) class.

    Performs MANOVA on morphometric data to test group differences.
    """

    def __init__(self):
        return

    def SetData(self, data):
        self.data = data
        self.nObservation = len(data)
        self.nVariable = len(data[0])

    def SetCategory(self, category_list):
        self.category_list = category_list

    def SetColumnList(self, column_list):
        self.column_list = column_list
        # print("column_list", column_list)

    def SetGroupby(self, group_by):
        self.group_by = group_by

    def Analyze(self):
        """analyze"""
        formula = ""
        for i in range(self.nVariable):
            if i > 0:
                formula += "+"
            formula += self.column_list[i]
        formula += "~" + self.group_by
        # print(formula)
        df = pd.DataFrame(self.data, columns=self.column_list)
        df[self.group_by] = self.category_list
        # print(self.group_by)
        # print(df)
        # print(df.columns)
        # print(df[self.group_by])
        # print(df[self.column_list])
        # Define independent and dependent variables
        model = MANOVA.from_formula(formula, data=df)
        # print(model.mv_test())
        self.results = model.mv_test()
        return


def PerformManova(dataset_ops, new_coords, classifier_index):
    manova = MdManova()

    # property_index = group_by
    logger.info("Perform Manova group by property index %s", classifier_index)
    if classifier_index < 0:
        # QMessageBox.information(self, "Information", "Please select a property.")
        return
    datamatrix = new_coords
    column_list = []
    for pc_idx, _pc_val in enumerate(new_coords[0]):
        column_list.append("PC" + str(pc_idx + 1))

    category_list = []
    group_by_name = dataset_ops.variablename_list[classifier_index]
    # obj = dataset_ops.object_list[0]
    # print(obj, obj.property_list, property_index)
    # xyz = ["x", "y", "z"]
    for _idx, obj in enumerate(dataset_ops.object_list):
        if classifier_index >= 0 and classifier_index < len(obj.variable_list):
            category_list.append(obj.variable_list[classifier_index])
        else:
            category_list.append("Unknown")

    manova.SetData(datamatrix)
    manova.SetCategory(category_list)
    manova.SetColumnList(column_list)
    manova.SetGroupby(group_by_name)
    manova.Analyze()

    return manova


# ========== Modern Analysis Functions for Controller ==========


def do_pca_analysis(landmarks_data, n_components=None):
    """Perform PCA analysis on landmark data.

    Args:
        landmarks_data: List of landmark arrays
        n_components: Number of components (None for auto)

    Returns:
        Dictionary with PCA results
    """
    try:
        import logging

        import numpy as np

        logger = logging.getLogger(__name__)

        logger.info(f"PCA Analysis starting with {len(landmarks_data)} specimens")
        if landmarks_data:
            logger.info(f"First specimen has {len(landmarks_data[0])} landmarks")
            if landmarks_data[0]:
                logger.info(f"Each landmark has {len(landmarks_data[0][0])} dimensions")

        # Use MdPrincipalComponent class for consistency with Analysis Detail
        pca = MdPrincipalComponent()

        # Flatten landmark data
        datamatrix = []
        for landmarks in landmarks_data:
            datum = []
            for lm in landmarks:
                datum.extend(lm)  # Use all coordinates (X, Y, Z for 3D)
            datamatrix.append(datum)

        # Perform PCA using the same method as Analysis Detail
        pca.SetData(datamatrix)
        pca.Analyze()

        # Get number of components (use all variables for morphometrics - no truncation)
        if n_components is None:
            n_components = pca.nVariable  # Use all 90 variables/PCs

        # Get scores (rotated matrix) - keep full dimensions for morphometrics
        if hasattr(pca, "rotated_matrix"):
            scores = pca.rotated_matrix.tolist()  # Keep 62x90
        else:
            scores = []

        # Calculate mean shape from the centered data
        mean_shape = []
        dim = len(landmarks_data[0][0]) if landmarks_data and landmarks_data[0] else 2
        n_landmarks = len(landmarks_data[0]) if landmarks_data else 0

        # The mean is already calculated in pca.Analyze() during centering
        # We need to reconstruct it from the number of landmarks
        for _i in range(n_landmarks):
            if dim == 2:
                mean_shape.append([0.0, 0.0])  # Already centered
            elif dim == 3:
                mean_shape.append([0.0, 0.0, 0.0])  # Already centered

        # Get eigenvalues and calculate variance ratios
        eigenvalues = pca.raw_eigen_values.tolist() if hasattr(pca, "raw_eigen_values") else []
        explained_variance_ratio = pca.eigen_value_percentages if hasattr(pca, "eigen_value_percentages") else []

        # Calculate cumulative variance
        cumulative_variance = []
        cumul = 0
        for ratio in explained_variance_ratio:
            cumul += ratio
            cumulative_variance.append(cumul)

        # Get rotation matrix (eigenvectors) - should be 90x90 from SVD
        if hasattr(pca, "rotation_matrix") and pca.rotation_matrix is not None:
            full_rotation_matrix = np.array(pca.rotation_matrix)  # Should already be 90x90
        else:
            full_rotation_matrix = np.eye(pca.nVariable)  # Fallback to identity

        logger.info("PCA Analysis completed")
        logger.info(f"Number of components: {n_components}")
        logger.info(f"Scores shape: {len(scores)}x{len(scores[0]) if scores else 0}")
        logger.info(f"Full rotation matrix shape: {full_rotation_matrix.shape}")

        return {
            "n_components": n_components,
            "eigenvalues": eigenvalues,  # Keep all eigenvalues
            "eigenvectors": full_rotation_matrix.tolist(),  # Full 90x90 rotation matrix
            "rotation_matrix": full_rotation_matrix.tolist(),  # Full 90x90 rotation matrix
            "scores": scores,
            "explained_variance_ratio": explained_variance_ratio,  # Keep all variance ratios
            "cumulative_variance_ratio": cumulative_variance,  # Keep all cumulative variance
            "mean_shape": mean_shape,
            "raw_eigen_values": eigenvalues,
            "eigen_value_percentages": explained_variance_ratio,
        }

    except Exception as e:
        import traceback

        logger.error(f"PCA analysis error: {traceback.format_exc()}")
        raise ValueError(f"PCA analysis failed: {str(e)}") from e


def do_cva_analysis(landmarks_data, groups):
    """Perform CVA (Canonical Variate Analysis) on landmark data.

    Args:
        landmarks_data: List of landmark arrays
        groups: List of group labels for each specimen

    Returns:
        Dictionary with CVA results
    """
    try:
        import numpy as np
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
        from sklearn.metrics import accuracy_score

        # Flatten landmark data
        flattened_data = []
        for landmarks in landmarks_data:
            flat_coords = []
            for landmark in landmarks:
                flat_coords.extend(landmark[:2])
            flattened_data.append(flat_coords)

        data_matrix = np.array(flattened_data)
        group_array = np.array(groups)

        # Perform LDA (equivalent to CVA) without standardization
        lda = LinearDiscriminantAnalysis()
        cv_scores = lda.fit_transform(data_matrix, group_array)

        # Pad CVA scores to at least 3 dimensions for UI compatibility
        if cv_scores.shape[1] < 3:
            padding_width = 3 - cv_scores.shape[1]
            cv_scores = np.pad(cv_scores, ((0, 0), (0, padding_width)), mode="constant", constant_values=0)

        # Predict classifications
        predictions = lda.predict(data_matrix)
        accuracy = accuracy_score(group_array, predictions) * 100

        # Calculate group centroids
        unique_groups = np.unique(group_array)
        centroids = []
        for group in unique_groups:
            group_mask = group_array == group
            group_centroid = np.mean(cv_scores[group_mask], axis=0)
            centroids.append(group_centroid.tolist())

        return {
            "canonical_variables": cv_scores.tolist(),
            "eigenvalues": lda.explained_variance_ratio_.tolist(),
            "group_centroids": centroids,
            "classification": predictions.tolist(),
            "accuracy": accuracy,
            "groups": unique_groups.tolist(),
            "n_components": cv_scores.shape[1],
        }

    except Exception as e:
        raise ValueError(f"CVA analysis failed: {str(e)}") from e


def do_manova_analysis_on_procrustes(flattened_landmarks, groups):
    """Perform MANOVA analysis on Procrustes-aligned landmarks.

    Args:
        flattened_landmarks: List of flattened landmark coordinate arrays
        groups: List of group labels for each specimen

    Returns:
        Dictionary with MANOVA results
    """
    try:
        import logging

        import numpy as np
        import pandas as pd
        from statsmodels.multivariate.manova import MANOVA

        logger = logging.getLogger(__name__)

        logger.info(
            f"MANOVA on Procrustes: {len(flattened_landmarks)} specimens, {len(flattened_landmarks[0]) if flattened_landmarks else 0} coordinates"
        )

        # Create column names for coordinates
        n_coords = len(flattened_landmarks[0]) if flattened_landmarks else 0

        # Auto-detect dimension (2D or 3D)
        # If n_coords is divisible by 2 but not by 3, it's 2D
        # If n_coords is divisible by 3, it's 3D
        # Otherwise, use general coordinate naming
        if n_coords % 2 == 0 and n_coords % 3 != 0:
            # 2D data
            dimension = 2
            n_landmarks = n_coords // 2
            coord_labels = ["X", "Y"]
        elif n_coords % 3 == 0:
            # 3D data
            dimension = 3
            n_landmarks = n_coords // 3
            coord_labels = ["X", "Y", "Z"]
        else:
            # Fallback: general coordinate naming
            dimension = 1
            n_landmarks = n_coords
            coord_labels = [""]

        # Generate column names
        column_names = []
        for i in range(n_landmarks):
            for label in coord_labels:
                if label:
                    column_names.append(f"LM{i + 1}_{label}")
                else:
                    column_names.append(f"Coord{i + 1}")

        logger.debug(f"Detected {dimension}D data: {n_landmarks} landmarks, {n_coords} coordinates")

        # Limit to first 20 variables to avoid computational issues
        max_vars = 20
        if len(column_names) > max_vars:
            logger.warning(f"Too many variables ({len(column_names)}), limiting to first {max_vars}")
            flattened_landmarks = [row[:max_vars] for row in flattened_landmarks]
            column_names = column_names[:max_vars]

        # Create DataFrame for MANOVA
        df = pd.DataFrame(flattened_landmarks, columns=column_names)
        df["group"] = groups

        # Build formula for MANOVA
        formula = " + ".join(column_names) + " ~ group"
        logger.debug(f"MANOVA formula uses {len(column_names)} variables")

        # Perform MANOVA
        model = MANOVA.from_formula(formula, data=df)
        results = model.mv_test()

        # Extract test statistics
        test_statistics = []
        stats_summary = results.results["group"]["stat"]

        # Process each statistic type
        for stat_name in ["Wilks' lambda", "Pillai's trace", "Hotelling-Lawley trace", "Roy's greatest root"]:
            if stat_name in stats_summary.index:
                stat_row = stats_summary.loc[stat_name]
                test_statistics.append(
                    {
                        "name": stat_name,
                        "value": float(stat_row["Value"]),
                        "df_num": int(stat_row["Num DF"]),
                        "df_den": int(stat_row["Den DF"]),
                        "f_statistic": float(stat_row["F Value"]),
                        "p_value": float(stat_row["Pr > F"]),
                    }
                )

        logger.info(f"MANOVA completed: {len(test_statistics)} statistics computed")

        return {
            "analysis_type": "MANOVA",
            "test_statistics": test_statistics,
            "n_groups": len(np.unique(groups)),
            "n_observations": len(flattened_landmarks),
            "n_variables": len(column_names),
        }

    except Exception as e:
        import traceback

        logger = logging.getLogger(__name__)
        logger.error(f"MANOVA on Procrustes failed: {e}")
        logger.error(traceback.format_exc())
        raise


def do_manova_analysis_on_pca(pca_scores, groups):
    """Perform MANOVA analysis on PCA scores.

    Args:
        pca_scores: List of PCA score arrays (already truncated to effective components)
        groups: List of group labels for each specimen

    Returns:
        Dictionary with MANOVA results
    """
    try:
        import logging

        import numpy as np
        import pandas as pd
        from statsmodels.multivariate.manova import MANOVA

        logger = logging.getLogger(__name__)

        logger.info(f"MANOVA on PCA: {len(pca_scores)} specimens, {len(pca_scores[0]) if pca_scores else 0} components")

        # Create column names for PCA components
        n_components = len(pca_scores[0]) if pca_scores else 0
        column_names = [f"PC{i + 1}" for i in range(n_components)]

        # Create DataFrame for MANOVA
        df = pd.DataFrame(pca_scores, columns=column_names)
        df["group"] = groups

        # Build formula for MANOVA
        formula = " + ".join(column_names) + " ~ group"
        logger.debug(f"MANOVA formula: {formula}")

        # Perform MANOVA
        model = MANOVA.from_formula(formula, data=df)
        results = model.mv_test()

        # Extract test statistics
        test_statistics = []
        stats_summary = results.results["group"]["stat"]

        # Process each statistic type
        for stat_name in ["Wilks' lambda", "Pillai's trace", "Hotelling-Lawley trace", "Roy's greatest root"]:
            if stat_name in stats_summary.index:
                stat_row = stats_summary.loc[stat_name]
                test_statistics.append(
                    {
                        "name": stat_name,
                        "value": float(stat_row["Value"]),
                        "df_num": int(stat_row["Num DF"]),
                        "df_den": int(stat_row["Den DF"]),
                        "f_statistic": float(stat_row["F Value"]),
                        "p_value": float(stat_row["Pr > F"]),
                    }
                )

        logger.info(f"MANOVA completed: {len(test_statistics)} statistics computed")

        return {
            "analysis_type": "MANOVA",
            "test_statistics": test_statistics,
            "n_groups": len(np.unique(groups)),
            "n_observations": len(pca_scores),
            "n_variables": n_components,
        }

    except Exception as e:
        import traceback

        logger = logging.getLogger(__name__)
        logger.error(f"MANOVA on PCA failed: {e}")
        logger.error(traceback.format_exc())
        raise


def do_manova_analysis(landmarks_data, groups):
    """Perform MANOVA analysis on landmark data.

    Args:
        landmarks_data: List of landmark arrays
        groups: List of group labels for each specimen

    Returns:
        Dictionary with MANOVA results
    """
    try:
        import numpy as np
        from scipy import stats

        # Flatten landmark data
        flattened_data = []
        for landmarks in landmarks_data:
            flat_coords = []
            for landmark in landmarks:
                flat_coords.extend(landmark[:2])
            flattened_data.append(flat_coords)

        data_matrix = np.array(flattened_data)
        group_array = np.array(groups)

        unique_groups = np.unique(group_array)
        n_groups = len(unique_groups)
        n_vars = data_matrix.shape[1]
        n_obs = data_matrix.shape[0]

        # Calculate group means
        group_means = []
        group_sizes = []

        for group in unique_groups:
            group_data = data_matrix[group_array == group]
            group_means.append(np.mean(group_data, axis=0))
            group_sizes.append(len(group_data))

        group_means = np.array(group_means)

        # Overall mean
        overall_mean = np.mean(data_matrix, axis=0)

        # Between-group sum of squares (H)
        H = np.zeros((n_vars, n_vars))
        for i, (_group, size) in enumerate(zip(unique_groups, group_sizes)):
            diff = group_means[i] - overall_mean
            H += size * np.outer(diff, diff)

        # Within-group sum of squares (E)
        E = np.zeros((n_vars, n_vars))
        for group in unique_groups:
            group_data = data_matrix[group_array == group]
            group_mean = np.mean(group_data, axis=0)

            for row in group_data:
                diff = row - group_mean
                E += np.outer(diff, diff)

        # Calculate test statistics
        try:
            # Calculate eigenvalues for test statistics
            E_inv = np.linalg.pinv(E)  # Use pseudo-inverse for stability
            H_E_inv = np.dot(H, E_inv)
            eigenvalues = np.real(np.linalg.eigvals(H_E_inv))
            eigenvalues = eigenvalues[eigenvalues > 1e-10]  # Filter small eigenvalues

            # 1. Wilks' Lambda
            det_E = np.linalg.det(E)
            det_H_E = np.linalg.det(H + E)

            if det_H_E != 0:
                wilks_lambda = det_E / det_H_E
            else:
                wilks_lambda = np.prod(1.0 / (1.0 + eigenvalues)) if len(eigenvalues) > 0 else 0.0

            # 2. Pillai's Trace
            pillais_trace = np.sum(eigenvalues / (1.0 + eigenvalues)) if len(eigenvalues) > 0 else 0.0

            # 3. Hotelling-Lawley Trace
            hotellings_trace = np.sum(eigenvalues) if len(eigenvalues) > 0 else 0.0

            # 4. Roy's Greatest Root
            roys_greatest_root = np.max(eigenvalues) if len(eigenvalues) > 0 else 0.0

            # Calculate degrees of freedom
            df_hypothesis = n_groups - 1  # hypothesis degrees of freedom
            df_error = n_obs - n_groups  # error degrees of freedom

            # F-statistics and p-values for each test
            s = min(df_hypothesis, n_vars)
            abs(df_hypothesis - n_vars - 1) / 2
            (df_error - n_vars - 1) / 2

            # Approximate F-statistics for all tests
            df_num = df_hypothesis * n_vars
            df_den = n_obs - n_groups - n_vars + 1

            # 1. Wilks' Lambda F-test
            if df_den > 0 and wilks_lambda > 0:
                wilks_f = ((1 - wilks_lambda) / wilks_lambda) * (df_den / df_num)
                wilks_p = stats.f.sf(wilks_f, df_num, df_den)
            else:
                wilks_f = 0.0
                wilks_p = 1.0

            # 2. Pillai's Trace F-test
            if df_den > 0 and pillais_trace > 0:
                pillai_f = (pillais_trace / (s - pillais_trace)) * ((df_den - s + 1) / s)
                pillai_p = stats.f.sf(pillai_f, s, df_den - s + 1)
            else:
                pillai_f = 0.0
                pillai_p = 1.0

            # 3. Hotelling-Lawley Trace F-test
            if df_den > 0 and hotellings_trace > 0:
                hotelling_f = (hotellings_trace / s) * ((df_den - s + 1) / 1)
                hotelling_p = stats.f.sf(hotelling_f, s, df_den - s + 1)
            else:
                hotelling_f = 0.0
                hotelling_p = 1.0

            # 4. Roy's Greatest Root F-test
            if df_den > 0 and roys_greatest_root > 0:
                roy_f = roys_greatest_root * (df_den / s)
                roy_p = stats.f.sf(roy_f, s, df_den)
            else:
                roy_f = 0.0
                roy_p = 1.0

        except np.linalg.LinAlgError:
            wilks_lambda = pillais_trace = hotellings_trace = roys_greatest_root = 0.0
            wilks_f = pillai_f = hotelling_f = roy_f = 0.0
            wilks_p = pillai_p = hotelling_p = roy_p = 1.0
            df_num = df_den = 0

        return {
            "test_statistics": [
                {
                    "name": "Wilks' Lambda",
                    "value": wilks_lambda,
                    "f_statistic": wilks_f,
                    "p_value": wilks_p,
                    "df_num": df_num,
                    "df_den": df_den,
                },
                {
                    "name": "Pillai's Trace",
                    "value": pillais_trace,
                    "f_statistic": pillai_f,
                    "p_value": pillai_p,
                    "df_num": s,
                    "df_den": df_den - s + 1,
                },
                {
                    "name": "Hotelling-Lawley Trace",
                    "value": hotellings_trace,
                    "f_statistic": hotelling_f,
                    "p_value": hotelling_p,
                    "df_num": s,
                    "df_den": df_den - s + 1,
                },
                {
                    "name": "Roy's Greatest Root",
                    "value": roys_greatest_root,
                    "f_statistic": roy_f,
                    "p_value": roy_p,
                    "df_num": s,
                    "df_den": df_den,
                },
            ],
            "group_means": group_means.tolist(),
            "overall_mean": overall_mean.tolist(),
            "n_groups": n_groups,
            "group_sizes": group_sizes,
        }

    except Exception as e:
        raise ValueError(f"MANOVA analysis failed: {str(e)}") from e
