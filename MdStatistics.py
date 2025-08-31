import pandas as pd
import MdUtils as mu
import numpy
from statsmodels.multivariate.manova import MANOVA

from MdLogger import setup_logger
logger = setup_logger(__name__)

class MdPrincipalComponent:
    def __init__(self):
        return

    def SetData(self, data):
        self.data = data
        self.nObservation = len(data)
        self.nVariable = len(data[0])

    def Analyze(self):
        '''analyze'''
        self.raw_eigen_values = []
        self.eigen_value_percentages = []

        sums = [0.0 for x in range(self.nVariable)]
        avrs = [0.0 for x in range(self.nVariable)]
        ''' calculate the empirical mean '''
        for i in range(self.nObservation):
            for j in range(self.nVariable):
                sums[j] += float(self.data[i][j])

        for j in range(self.nVariable):
            avrs[j] = float(sums[j]) / float(self.nObservation)

        for i in range(self.nObservation):
            for j in range(self.nVariable):
                self.data[i][j] -= avrs[j]

        ''' covariance matrix '''
        np_data = numpy.matrix(self.data)
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
            #print sum, cumul, ss
            if cumul / sum > 0.95 and nSignificantEigenValue == -1:
                nSignificantEigenValue = i + 1
            if (ss / sum ) < 0.00001 and nEigenValues == -1:
                nEigenValues = i + 1
            i += 1

        self.rotated_matrix = numpy.dot(np_data, v)
        self.rotation_matrix = v
        self.loading = v
        return True


class MdCanonicalVariate:
    def __init__(self):
        self.dimension = -1
        self.nVariable = 0
        self.nObservation = 0
        # self.datamatrix = []
        return

    def SetData(self, data):
        self.data = data
        self.nObservation = len(data)
        self.nVariable = len(data[0])

    def SetCategory(self, category_list):
        self.category_list = category_list

    def Analyze(self):
        '''analyze'''
        actual_data = self.data
        category_data = self.category_list
        category_set = set(category_data)
        num_category = len(category_set)

        variances = [0.0 for x in range(self.nVariable)]
        total_avg = [0.0 for x in range(self.nVariable)]
        total_sum = [0.0 for x in range(self.nVariable)]
        total_count = self.nObservation

        avg_by_category = {}
        sum_by_category = {}
        count_by_category = {}
        #print "analyze"
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
                #print k, sum_by_category[k], avg_by_category[k]

        for i in range(self.nVariable):
            total_avg[i] = total_sum[i] * 1.0 / total_count
        #print total_sum, total_avg

        ''' check zero variance variables '''
        for p in range(self.nVariable):
            for idx in range(self.nObservation):
                variances[p] += ( float(actual_data[idx][p]) - total_avg[p] ) ** 2

        covariance_matrix_size = 0
        for p in range(self.nVariable):
            if variances[p] == 0:
                pass
                #print "variance = 0 for ", p, "th variable" 
            else:
                covariance_matrix_size += 1
        #print "covariance_matrix_size", covariance_matrix_size

        covariance_matrix = [[0.0 for x in range(covariance_matrix_size)] for y in range(covariance_matrix_size)]
        p_ = 0
        for p in range(self.nVariable):
            if variances[p] == 0: continue
            q_ = 0
            for q in range(self.nVariable):
                if variances[q] == 0: continue
                for idx in range(self.nObservation):
                    diff_p = float(actual_data[idx][p]) - total_avg[p]
                    diff_q = float(actual_data[idx][q]) - total_avg[q]
                    #print p_, q_
                    covariance_matrix[p_][q_] += diff_p * diff_q / ( total_count - 1 )
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
            if variances[p] == 0: continue
            q_ = 0
            for q in range(self.nVariable):
                if variances[q] == 0: continue
                for idx in range(self.nObservation):
                    key = category_data[idx]
                    diff_p = float(actual_data[idx][p]) - avg_by_category[key][p]
                    diff_q = float(actual_data[idx][q]) - avg_by_category[key][q]
                    within_cov[p_][q_] += diff_p * diff_q / ( total_count - len(category_set) )
                q_ += 1
            p_ += 1

        p_ = 0
        for p in range(self.nVariable):
            if variances[p] == 0: continue
            q_ = 0
            for q in range(self.nVariable):
                if variances[q] == 0: continue
                for key in list(category_set):
                    diff_p = avg_by_category[key][p] - total_avg[p]
                    diff_q = avg_by_category[key][q] - total_avg[q]
                    between_cov[p_][q_] += diff_p * diff_q * count_by_category[key] / len(category_set)
                q_ += 1
            p_ += 1

        w = numpy.matrix(within_cov)
        b = numpy.matrix(between_cov)

        try:
            wi = w.getI()
        except numpy.linalg.linalg.LinAlgError as e:
            #print "Singular matrix: ", e
            return False
        #print "wi", wi
        x = numpy.dot(wi, b)

        u, s, v = numpy.linalg.svd(x)

        self.raw_eigen_values = s[:]
        s /= sum(s)
        self.eigen_value_percentages = s[:]

        rotation_matrix = numpy.zeros(( self.nVariable, self.nVariable ))

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
            if variances[p] != 0: p_ += 1

        np_data = numpy.zeros(( self.nObservation, self.nVariable ))
        for p in range(self.nObservation):
            for q in range(self.nVariable):
                np_data[p, q] = float(actual_data[p][q])

        self.rotation_matrix = rotation_matrix
        self.rotated_matrix = numpy.dot(np_data, rotation_matrix)
        self.loading = rotation_matrix
        return True


def PerformCVA(dataset_ops, classifier_index):
    cva = MdCanonicalVariate()

    #property_index = group_by
    logger.info("Perform CVA group by classifier index %s",classifier_index)
    if classifier_index < 0:
        #QMessageBox.information(self, "Information", "Please select a property.")
        return
    datamatrix = []
    category_list = []
    #obj = dataset_ops.object_list[0]
    #print(obj, obj.property_list, property_index)
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
    if analysis_return == False:
        return None

    number_of_axes = min(cva.nObservation, cva.nVariable)
    cva_done = True

    return cva

def PerformPCA(dataset_ops):

    pca = MdPrincipalComponent()
    datamatrix = []
    for obj in dataset_ops.object_list:
        datum = []
        for lm in obj.landmark_list:
            datum.extend( lm )
        datamatrix.append(datum)

    pca.SetData(datamatrix)
    analysis_result = pca.Analyze()
    if analysis_result == False:
        return None

    number_of_axes = min(pca.nObservation, pca.nVariable)
    pca_done = True

    return pca


class MdManova:
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
        #print("column_list", column_list)
    
    def SetGroupby(self, group_by):
        self.group_by = group_by

    def Analyze(self):
        '''analyze'''
        formula = ""
        for i in range(self.nVariable):
            if i > 0:
                formula += "+"
            formula += self.column_list[i]
        formula += "~" + self.group_by
        #print(formula)
        df = pd.DataFrame(self.data, columns=self.column_list)
        df[self.group_by] = self.category_list
        #print(self.group_by)
        #print(df)
        #print(df.columns)
        #print(df[self.group_by])
        #print(df[self.column_list])
        # Define independent and dependent variables
        model = MANOVA.from_formula(formula, data=df)
        #print(model.mv_test())
        self.results = model.mv_test()
        return
    
def PerformManova(dataset_ops, new_coords, classifier_index):
    dimension = dataset_ops.dimension
    manova = MdManova()

    #property_index = group_by
    logger.info("Perform Manova group by property index %s",classifier_index)
    if classifier_index < 0:
        #QMessageBox.information(self, "Information", "Please select a property.")
        return
    datamatrix = new_coords
    column_list = []
    for pc_idx, pc_val in enumerate(new_coords[0]):
        column_list.append("PC"+str(pc_idx+1))

    category_list = []
    group_by_name = dataset_ops.variablename_list[classifier_index]
    #obj = dataset_ops.object_list[0]
    #print(obj, obj.property_list, property_index)
    #xyz = ["x", "y", "z"]
    for idx, obj in enumerate(dataset_ops.object_list):
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
        import numpy as np
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"PCA Analysis starting with {len(landmarks_data)} specimens")
        if landmarks_data:
            logger.info(f"First specimen has {len(landmarks_data[0])} landmarks")
            if landmarks_data[0]:
                logger.info(f"Each landmark has {len(landmarks_data[0][0])} dimensions")
        
        # Flatten landmark data
        flattened_data = []
        for landmarks in landmarks_data:
            flat_coords = []
            for landmark in landmarks:
                flat_coords.extend(landmark)  # Use all coordinates (X, Y, Z for 3D)
            flattened_data.append(flat_coords)
        
        # Convert to numpy array
        data_matrix = np.array(flattened_data)
        logger.info(f"Data matrix shape after flattening: {data_matrix.shape}")
        
        # Standardize data
        scaler = StandardScaler()
        data_scaled = scaler.fit_transform(data_matrix)
        
        # Perform PCA
        if n_components is None:
            n_components = min(data_matrix.shape[0] - 1, data_matrix.shape[1])
        
        pca = PCA(n_components=n_components)
        scores = pca.fit_transform(data_scaled)
        
        # Calculate cumulative variance
        cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
        
        # Calculate mean shape
        mean_coords = np.mean(data_matrix, axis=0)
        mean_shape = []
        # Determine dimension from first landmark
        dim = len(landmarks_data[0][0]) if landmarks_data and landmarks_data[0] else 2
        for i in range(0, len(mean_coords), dim):
            if dim == 2:
                mean_shape.append([mean_coords[i], mean_coords[i+1]])
            elif dim == 3:
                mean_shape.append([mean_coords[i], mean_coords[i+1], mean_coords[i+2]])
        
        # Create full rotation matrix (for compatibility with original code)
        # This is the transformation matrix from original space to PCA space
        rotation_matrix = pca.components_.T  # Transpose to get (n_features x n_components)
        # Pad with identity for unused dimensions if needed
        n_features = data_matrix.shape[1]
        full_rotation_matrix = np.eye(n_features)
        full_rotation_matrix[:, :rotation_matrix.shape[1]] = rotation_matrix
        
        logger.info(f"Full rotation matrix shape: {full_rotation_matrix.shape}")
        logger.info(f"PCA scores shape: {scores.shape}")
        
        return {
            'n_components': n_components,
            'eigenvalues': pca.explained_variance_.tolist(),
            'eigenvectors': pca.components_.tolist(),
            'rotation_matrix': full_rotation_matrix.tolist(),  # Add full rotation matrix
            'scores': scores.tolist(),
            'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
            'cumulative_variance_ratio': cumulative_variance.tolist(),
            'mean_shape': mean_shape,
            'scaler_mean': scaler.mean_.tolist(),
            'scaler_scale': scaler.scale_.tolist()
        }
        
    except Exception as e:
        raise ValueError(f"PCA analysis failed: {str(e)}")


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
        from sklearn.preprocessing import StandardScaler
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
        
        # Standardize data
        scaler = StandardScaler()
        data_scaled = scaler.fit_transform(data_matrix)
        
        # Perform LDA (equivalent to CVA)
        lda = LinearDiscriminantAnalysis()
        cv_scores = lda.fit_transform(data_scaled, group_array)
        
        # Predict classifications
        predictions = lda.predict(data_scaled)
        accuracy = accuracy_score(group_array, predictions) * 100
        
        # Calculate group centroids
        unique_groups = np.unique(group_array)
        centroids = []
        for group in unique_groups:
            group_mask = group_array == group
            group_centroid = np.mean(cv_scores[group_mask], axis=0)
            centroids.append(group_centroid.tolist())
        
        return {
            'canonical_variables': cv_scores.tolist(),
            'eigenvalues': lda.explained_variance_ratio_.tolist(),
            'group_centroids': centroids,
            'classification': predictions.tolist(),
            'accuracy': accuracy,
            'groups': unique_groups.tolist(),
            'n_components': cv_scores.shape[1]
        }
        
    except Exception as e:
        raise ValueError(f"CVA analysis failed: {str(e)}")


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
        for i, (group, size) in enumerate(zip(unique_groups, group_sizes)):
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
            df_error = n_obs - n_groups   # error degrees of freedom 
            
            # F-statistics and p-values for each test
            s = min(df_hypothesis, n_vars)
            m = abs(df_hypothesis - n_vars - 1) / 2
            n = (df_error - n_vars - 1) / 2
            
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
            'test_statistics': [
                {
                    'name': "Wilks' Lambda",
                    'value': wilks_lambda,
                    'f_statistic': wilks_f,
                    'p_value': wilks_p,
                    'df_num': df_num,
                    'df_den': df_den
                },
                {
                    'name': "Pillai's Trace", 
                    'value': pillais_trace,
                    'f_statistic': pillai_f,
                    'p_value': pillai_p,
                    'df_num': s,
                    'df_den': df_den - s + 1
                },
                {
                    'name': "Hotelling-Lawley Trace",
                    'value': hotellings_trace, 
                    'f_statistic': hotelling_f,
                    'p_value': hotelling_p,
                    'df_num': s,
                    'df_den': df_den - s + 1
                },
                {
                    'name': "Roy's Greatest Root",
                    'value': roys_greatest_root,
                    'f_statistic': roy_f, 
                    'p_value': roy_p,
                    'df_num': s,
                    'df_den': df_den
                }
            ],
            'group_means': group_means.tolist(),
            'overall_mean': overall_mean.tolist(),
            'n_groups': n_groups,
            'group_sizes': group_sizes
        }
        
    except Exception as e:
        raise ValueError(f"MANOVA analysis failed: {str(e)}")


def do_procrustes_analysis(landmarks_data, scaling=True, reflection=True):
    """Perform Procrustes analysis on landmark data.
    
    Args:
        landmarks_data: List of landmark arrays
        scaling: Allow scaling transformation
        reflection: Allow reflection transformation
        
    Returns:
        Dictionary with Procrustes results
    """
    try:
        import numpy as np
        from scipy.spatial.distance import procrustes
        
        if len(landmarks_data) < 2:
            raise ValueError("At least 2 specimens required for Procrustes analysis")
        
        # Convert to numpy arrays
        shapes = [np.array(landmarks) for landmarks in landmarks_data]
        
        # Use first shape as reference
        reference = shapes[0]
        aligned_shapes = [reference.copy()]
        
        # Align all other shapes to reference
        for i in range(1, len(shapes)):
            try:
                # Procrustes alignment
                aligned, ref_aligned, disparity = procrustes(reference, shapes[i])
                aligned_shapes.append(aligned)
                
            except Exception as e:
                # If procrustes fails, use original shape
                aligned_shapes.append(shapes[i])
        
        # Calculate mean shape (consensus configuration)
        mean_shape = np.mean(aligned_shapes, axis=0)
        
        # Calculate centroid sizes
        centroid_sizes = []
        for shape in shapes:
            centroid = np.mean(shape, axis=0)
            distances = np.sqrt(np.sum((shape - centroid)**2, axis=1))
            centroid_size = np.sqrt(np.sum(distances**2))
            centroid_sizes.append(centroid_size)
        
        return {
            'aligned_shapes': [shape.tolist() for shape in aligned_shapes],
            'mean_shape': mean_shape.tolist(),
            'centroid_sizes': centroid_sizes,
            'consensus_configuration': mean_shape.tolist(),
            'scaling_enabled': scaling,
            'reflection_enabled': reflection,
            'n_specimens': len(landmarks_data),
            'n_landmarks': len(landmarks_data[0]) if landmarks_data else 0
        }
        
    except Exception as e:
        raise ValueError(f"Procrustes analysis failed: {str(e)}")

