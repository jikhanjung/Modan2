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
        return


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

        wi = w.getI()
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
        return


def PerformCVA(dataset_ops, group_by):
    cva = MdCanonicalVariate()

    property_index = group_by
    logger.info("Perform CVA group by property index %s",property_index)
    if property_index < 0:
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
        category_list.append(obj.property_list[property_index])

    cva.SetData(datamatrix)
    cva.SetCategory(category_list)
    cva.Analyze()

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
    pca.Analyze()

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
        print(formula)
        df = pd.DataFrame(self.data, columns=self.column_list)
        df[self.group_by] = self.category_list
        print(df)
        print(df.columns)
        print(df[self.group_by])
        print(df[self.column_list])
        # Define independent and dependent variables
        model = MANOVA.from_formula(formula, data=df)
        print(model.mv_test())
        return
    





def PerformManova(dataset_ops, group_by):
    dimension = dataset_ops.dimension
    manova = MdManova()

    property_index = group_by
    logger.info("Perform Manova group by property index %s",property_index)
    if property_index < 0:
        #QMessageBox.information(self, "Information", "Please select a property.")
        return
    datamatrix = []
    category_list = []
    group_by_name = dataset_ops.property_list[property_index]
    #obj = dataset_ops.object_list[0]
    #print(obj, obj.property_list, property_index)
    column_list = []
    xyz = ["x", "y", "z"]
    for idx, obj in enumerate(dataset_ops.object_list):
        if idx == 0:
            for lm in obj.landmark_list:
                for i in range(dimension):
                    column_list.append(xyz[i]+str(idx+1))

        datum = []
        for lm in obj.landmark_list:
            datum.extend(lm[:dimension])
        datamatrix.append(datum)
        category_list.append(obj.property_list[property_index])

    manova.SetData(datamatrix)
    manova.SetCategory(category_list)
    manova.SetColumnList(column_list)
    manova.SetGroupby(group_by_name)
    manova.Analyze()

    number_of_axes = min(manova.nObservation, manova.nVariable)
    cva_done = True

    return manova

