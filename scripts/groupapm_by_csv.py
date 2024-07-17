import csv
import numpy as np
import pandas as pd
from tqdm import tqdm
from scipy.sparse import lil_matrix
from typing import List
from collections import defaultdict
from run_ridge_model import run_ridge_model

def remove_zero_rows(X, y):
    nonzero_row_indices = np.unique(X.nonzero()[0])
    X_filtered = X[nonzero_row_indices]
    y_filtered = y[nonzero_row_indices]

    return X_filtered, y_filtered

def calculate_apm_from_csv(season: str, alphas: List[int],
                            min_appearances: int = None):
    '''
    Calculates APM (Adjusted Plus-Minus)
    for NBA player groups based on per-possession data.
    
    Parameters
    ----------
    season : str
        season to include in the calculation.
    alphas : List[int]
        The range of alpha values for cross-validation in the Ridge regression.
    min_appearances : int, optional
        Minimum number of appearances to include a player in the calculation.

    Returns
    -------
    Outputs the APM of all player groups for the specified seasons to a CSV file.    
    '''
    # Create a dictionary to count appearances per season for each player groups
    group_appearances = defaultdict(int)
    all_data = []

    df = pd.read_csv(f'base_poss_data_{season}.csv')
    all_data.extend(df.itertuples(index=False))
        
    all_groups = {tuple(sorted([item[i] for i in range(2, 7)])): 1 for item in all_data}
    all_groups.update({tuple(sorted([item[i] for i in range(7, 12)])): 1 for item in all_data})
    group_to_col = {}; col_to_group = {}
    for group in all_groups:
        if group not in group_to_col:
            column_number = len(group_to_col)
            group_to_col[group] = column_number
            col_to_group[column_number] = group

    for item in all_data:
        court_away_players = tuple(sorted([item[i] for i in range(2, 7)]))
        court_home_players = tuple(sorted([item[i] for i in range(7, 12)]))
        
        group_appearances[court_away_players] += 1
        group_appearances[court_home_players] += 1

    X = lil_matrix((len(all_data), len(col_to_group)))
    y = np.zeros(len(all_data))
          
    if min_appearances is not None:          
        cols_to_keep = [idx for idx, group in col_to_group.items() if group_appearances[group] >= min_appearances]
        col_to_group = {i: col_to_group[idx] for i, idx in enumerate(cols_to_keep)}
        group_to_col = {}
        for i, group in col_to_group.items():
            group_to_col[group] = i
        X = lil_matrix((len(all_data), len(col_to_group)))

    for counter, item in tqdm(enumerate(all_data)):
        pts = item.pts
        away_players = tuple(sorted([item[i] for i in range(2, 7)]))
        home_players = tuple(sorted([item[i] for i in range(7, 12)]))
        off_players = home_players if item.home_poss else away_players
        def_players = away_players if item.home_poss else home_players
        
        if min_appearances is not None:
            # Only consider player pairs with appearances greater than min_appearances in both lineups
            # if off_players in col_to_group.values() and def_players in col_to_group.values():
            #     X[counter, group_to_col[off_players]] = 1
            #     X[counter, group_to_col[def_players]] = -1
                
            # Groups with appearances greater than min_appearances will be considered
            if off_players in col_to_group.values():
                X[counter, group_to_col[off_players]] = 1
            if def_players in col_to_group.values():
                X[counter, group_to_col[def_players]] = -1
        
        else:
            X[counter, group_to_col[off_players]] = 1
            X[counter, group_to_col[def_players]] = -1
        
        y[counter] = pts

    X_filtered, y_filtered = remove_zero_rows(X, y)
    beta_ridge = run_ridge_model(X_filtered.tocsr(), y_filtered, alphas)

    with open(f'group_apm_{season}.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Group', 'APM', 'Appearances'])
        for idx, group in col_to_group.items():
            appearances = group_appearances[group]
            apm = beta_ridge[idx]*100
            writer.writerow([group, apm, appearances])

# Calculate APM directly before removing pairs with low appearances.
# This approach improves precision compared to removing low appearance pairs before calculating APM.
seasons = [str(season) for season in range(2014, 2023)]
for season in seasons:
    calculate_apm_from_csv(season, alphas=[0.0000001], min_appearances = None)

for season in seasons:
    df = pd.read_csv(f'group_apm_{season}.csv')
    df = df[df['Appearances'] >= 800]
    df.to_csv(f'group_apm_{season}.csv', index=False)
    