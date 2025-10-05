import pandas as pd
from sklearn import datasets
from statsmodels.multivariate.manova import MANOVA

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
column_names = ['sepal_length_cm','sepal_width_cm','petal_length_cm','petal_width_cm']
# Fit the MANOVA model
print(df)
print(df.columns)
print(df['species'])
print(df[column_names])

model = MANOVA.from_formula(formula, data=df)

# View the MANOVA results
results = model.mv_test()
print(results)
print(results.results['species']['stat'])
stat_text = str(results.results['species']['stat'])
# Split the text into lines
lines = stat_text.strip().splitlines()

# Remove empty lines
lines = [line for line in lines if line.strip()]

# Create column names from the header line
column_names = ["Value", "Num DF", "Den DF", "F Value", "Pr > F"]

def is_numeric(value):
    """Checks if a value is numeric (float)."""
    try:
        float(value)
        return True
    except ValueError:
        return False


# Extract data from remaining lines and create the dictionary
stat_dict = {}
for line in lines[1:]:
    data = line.split()
    stat_name = ""  # Initialize stat_name as an empty string
    stat_values = []
    for entry in data:
        if is_numeric(entry):  # Check if entry is numeric
            stat_values.append(float(entry))
        else:
            stat_name += entry + " "  # Append entry with whitespace
    stat_name = stat_name.strip()  # Remove trailing whitespace from stat_name
    stat_dict[stat_name] = {}
    #print(column_names, stat_values)
    for idx, colname in enumerate(column_names):
        stat_dict[stat_name][colname] = stat_values[idx]

print(stat_dict)