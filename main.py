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

algo_df = precovid_df[['datetime','temp_of_water_celsius','nitrate_mg_per_liter']]
algo_df.dropna(inplace=True)
algo_df.set_index('datetime', inplace=True)

### Multivariate: water against nitrate
# This follow concepts from the Introduction to Anomaly Detection tutorial in R
# Some of the concepts had a one to one correspondence in Python, and others didn't

# Let's build a KNN score for each point by taking the average distance from all its 20 neighbors

from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import scale

scaled_df = pd.DataFrame(scale(algo_df))

neigh = NearestNeighbors(n_neighbors=20)
neigh.fit(scaled_df)

kneighbors = neigh.kneighbors()
knn_distances = kneighbors[0]
knn_indices = kneighbors[1]

knn_distances = pd.DataFrame(knn_distances)
knn_distances['knn_score'] = knn_distances.mean(axis=1)
knn_distances = pd.DataFrame(knn_distances['knn_score'])

scaled_df = scaled_df.join(knn_distances)

# knn_top_anomalies2 = scaled_df.nlargest(20, 'knn_score')

algo_df.reset_index(drop=False,inplace=True)
scaled_df = scaled_df['knn_score']

final_algo_df_with_score = algo_df.join(scaled_df)

final_algo_df_with_score['knn_score_rank'] = final_algo_df_with_score['knn_score'].rank(pct=True) * 100
final_algo_df_with_score.drop(columns={'knn_score'},inplace=True)

### LOF
from pyod.pyod.models.lof import LOF

algo_scaled_df = pd.DataFrame(scale(algo_df))

# Fit
lof = LOF(n_neighbors=12, metric="manhattan")
lof.fit(algo_scaled_df)
probs = lof.predict_proba(algo_scaled_df)
probs = pd.DataFrame(probs)

lof2 = LOF(n_neighbors=8, metric="manhattan")
lof2.fit(algo_scaled_df)
probs2 = lof2.predict_proba(algo_scaled_df)
probs2 = pd.DataFrame(probs2)

lof_final = probs.join(probs2, rsuffix='_8neighbors')
# Returns a dataset, first column is probability the observation is normal,
# second column is probability observation is outlier
lof_final['outlier_12n'] = lof_final['1'].apply(lambda x: 1 if x > 0.001 else 0)
lof_final['outlier_8n'] = lof_final['1_8neighbors'].apply(lambda x: 1 if x > 0.001 else 0)

train_df = algo_df.reset_index(drop=False).copy()

lof_final = lof_final.join(train_df)
lof_final.set_index('datetime',inplace=True)

lof_final.rename(columns={'0':'norm_prob_12n',
                          '1':'outlier_prob_12n',
                          '0_8neighbors':'norm_prob_8n',
                          '1_8neighbors':'outlier_prob_8n'},
                 inplace=True)

lof_final = lof_final[['norm_prob_8n','outlier_prob_12n','outlier_8n','outlier_12n']]

final_algo_df_with_score.set_index('datetime',inplace=True)
final_algo_df_with_score = final_algo_df_with_score.join(lof_final)

final_algo_df_with_score.to_excel(r"C:\Users\chris\OneDrive\Documents\python_rivers 04-07-12 1006am.xlsx")


