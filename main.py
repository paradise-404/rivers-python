import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_excel(r"C:\Users\chris\Downloads\delaware_river_trenton_nj last_five_years clean 04-01-23 0614pm.xlsx")

df['turbidity'] = pd.to_numeric(df['turbidity'],errors='coerce')
df['chlorophyll_mg_per_liter'] = pd.to_numeric(df['chlorophyll_mg_per_liter'],errors='coerce')
df['nitrate_mg_per_liter'] = pd.to_numeric(df['nitrate_mg_per_liter'],errors='coerce')
df['dissolved_oxygen_mg_per_liter'] = pd.to_numeric(df['dissolved_oxygen_mg_per_liter'],errors='coerce')
df['dissolved_oxygen_percent'] = pd.to_numeric(df['dissolved_oxygen_percent'],errors='coerce')
df['specific_conductance'] = pd.to_numeric(df['specific_conductance'],errors='coerce')
df['ph'] = pd.to_numeric(df['ph'],errors='coerce')

df.drop(columns=['discharge_per_second'],inplace=True)

precovid_df = df[df['datetime']<'2021']

### KNNs

from pyod.pyod.models.knn import KNN # Strange import issue, so I had to go down two subdirectories
import sklearn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

import numpy as np

algo_df = precovid_df[['temp_of_water_celsius','nitrate_mg_per_liter']]

algo_df['datetime'] = pd.to_datetime(algo_df['datetime'])
algo_df['date_delta'] = (algo_df['datetime'] - algo_df['datetime'].min())  / np.timedelta64(1,'D')
algo_df.dropna(inplace=True)

algo_df_summer_2020 = algo_df[(algo_df['datetime']>'2020-06-01') & (algo_df['datetime']<'2020-09-01')]
algo_df_summer_2020_for_fit = algo_df_summer_2020.drop(columns=['datetime'])
algo_df_summer_2020_for_fit.dropna(inplace=True)

# Tune the number of neighbors and contamination
knn = KNN(n_neighbors=20, contamination=0.01, n_jobs=-1)
# Let's find outliers in summer of 2020
knn.fit(algo_df_summer_2020_for_fit)
probs = knn.predict_proba(algo_df_summer_2020_for_fit)
# Use 55% threshold for filtering
is_outlier = probs[:, 1] > 0.55
# Isolate the outliers
outliers = algo_df_summer_2020_for_fit[is_outlier]
len(outliers)

# Quantile transformer
from sklearn.preprocessing import QuantileTransformer

qt = QuantileTransformer(output_distribution='normal')
X = algo_df_summer_2020_for_fit.drop('nitrate_mg_per_liter', axis=1)
y = algo_df_summer_2020_for_fit['nitrate_mg_per_liter']

X.loc[:,:] = qt.fit_transform(X)


# Tune the number of neighbors and contamination
knn = KNN(n_neighbors=20, contamination=0.01, n_jobs=-1)
# Let's find outliers in summer of 2020
knn.fit(X)
probs = knn.predict_proba(X)
# Use 55% threshold for filtering
is_outlier = probs[:, 1] > 0.55
# Isolate the outliers
outliers = X[is_outlier]
len(outliers)

# Split the data into features (X) and target (y)
X = algo_df_summer_2020_for_fit.drop('nitrate_mg_per_liter', axis=1)
y = algo_df_summer_2020_for_fit['nitrate_mg_per_liter']

# Split the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Scale the features using StandardScaler
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)
from sklearn.neighbors import KNeighborsClassifier
knn = KNeighborsClassifier(n_neighbors=3)
knn.fit(X_train, y_train)






