import pandas as pd
from statsmodels.multivariate.manova import MANOVA
from sklearn import datasets

# Load the Iris dataset
iris = datasets.load_iris()
#print(iris)
#exit()
df = pd.DataFrame(iris.data, columns=iris.feature_names)
df['species'] = iris.target

# Define independent and dependent variables
#formula = 'sepal_length + sepal_width + petal_length + petal_width ~ species' 
#formula = 'sepal length (cm) + sepal width (cm) + petal length (cm) + petal width (cm) ~ species' 
#formula = 'sepal length \(cm\) + sepal width \(cm\) + petal length \(cm\) + petal width \(cm\) ~ species' 


df.rename(columns = {'sepal length (cm)': 'sepal_length_cm', 
                     'sepal width (cm)': 'sepal_width_cm',
                     'petal length (cm)': 'petal_length_cm',
                     'petal width (cm)': 'petal_width_cm'}, inplace=True)

formula = 'sepal_length_cm + sepal_width_cm + petal_length_cm + petal_width_cm ~ species'

# Fit the MANOVA model
model = MANOVA.from_formula(formula, data=df)

# View the MANOVA results
print(model.mv_test())