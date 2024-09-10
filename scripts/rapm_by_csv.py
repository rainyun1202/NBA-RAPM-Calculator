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

def calculate_rapm_from_csv(season: str, alphas: List[int],
                            min_appearances: int = None):
    '''
    Calculates RAPM (Regularized Adjusted Plus-Minus)
    for NBA players based on per-possession data from CSV files.
    
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
    Outputs the RAPM of all players for the specified seasons to a CSV file.    
    '''
    # Create a dictionary to count appearances per season for each player
    player_appearances = defaultdict(int)
    all_data = []

    df = pd.read_csv(f'base_poss_data_{season}.csv')
    all_data.extend(df.itertuples(index=False))
    
    all_players = {item[i]: 1 for item in all_data for i in range(2, 12)}
    player_to_col = {}; col_to_player = {}
    for player in all_players:
        if player not in player_to_col:
            column_number = len(player_to_col)
            player_to_col[player] = column_number
            col_to_player[column_number] = player

    for item in all_data:
        players = [getattr(item, f) for f in ['a1', 'a2', 'a3', 'a4', 'a5',
                                              'h1', 'h2', 'h3', 'h4', 'h5']]
        for player in players:
            player_appearances[player] += 1

    X = lil_matrix((len(all_data), len(col_to_player)))
    y = np.zeros(len(all_data))

    if min_appearances is not None:          
        cols_to_keep  = [idx for idx, player in col_to_player.items() if player_appearances[player] >= min_appearances]
        col_to_player = {i: col_to_player[idx] for i, idx in enumerate(cols_to_keep)}
        player_to_col = {}
        for i, player in col_to_player.items():
            player_to_col[player] = i
        X = lil_matrix((len(all_data), len(col_to_player)))

    for counter, item in tqdm(enumerate(all_data)):
        pts = item.pts
        players = [getattr(item, f) for f in ['a1', 'a2', 'a3', 'a4', 'a5',
                                              'h1', 'h2', 'h3', 'h4', 'h5']]
        off_players = players[5:] if item.home_poss else players[:5]
        def_players = players[:5] if item.home_poss else players[5:]
        # Players with appearances greater than min_appearances will be considered
        # It is possible to have fewer than 10 players in a single row, but the impact on the results is minimal
        for player in off_players:
            if player in col_to_player.values():
                X[counter, player_to_col[player]] = 1
        for player in def_players:
            if player in col_to_player.values():
                X[counter, player_to_col[player]] = -1
        
        y[counter] = pts

    X_filtered, y_filtered = remove_zero_rows(X, y)

    beta_ridge = run_ridge_model(X_filtered.tocsr(), y_filtered, alphas)

    with open(f'player_rapm_{season}.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Player', 'RAPM', 'Appearances'])
        for idx, player in col_to_player.items():
            appearances = player_appearances[player]
            rapm = beta_ridge[idx]*100
            writer.writerow([player, rapm, appearances])

seasons = [str(season) for season in range(2014, 2023)]
for season in seasons:
    calculate_rapm_from_csv(season, alphas=[3250], min_appearances=1200)
