import MySQLdb
import csv
from sklearn import linear_model
import numpy as np
from scipy.sparse import lil_matrix
from typing import Optional, Union, List, Dict

def run_ridge_model(X, y, alphas, sample_weights):
    """
    Fits a Ridge Regression model with cross-validation and returns the coefficients.
    
    Parameters
    ----------
    X : scipy.sparse matrix
        Feature matrix used to train the model.
    y : numpy array
        Target vector, representing the dependent variable.
    alphas : list of float
        List of alpha values to try. Alpha corresponds to the regularization strength.
    sample_weights : list of float
        Weights for each sample, used to weigh the importance of each sample differently.
    
    Returns
    -------
    numpy array
        Coefficients of the fitted Ridge Regression model.
    """
    clf = linear_model.RidgeCV(alphas=alphas, cv=5)
    clf.fit(X, y, sample_weight=sample_weights)
    print('lambda:', clf.alpha_)
    return clf.coef_

def calculate_rapm(seasons: Union[str, List[str]] = '2022',
                   season_weights: Optional[Dict[str, float]] = None,
                   db_password: str = '',
                   alphas: List[int] = [1500, 1750, 2000, 2250, 2500, 2750, 3000, 3250, 3500, 3750, 4000]):
    '''
    Calculates RAPM (Regularized Adjusted Plus-Minus)
    for NBA players based on per-possession data.

    Parameters
    ----------
    seasons : Union[str, List[str]], optional
        Seasons to include in the calculation. Default is '2022'.
    season_weights : Optional[Dict[str, float]], optional
        Add weights for previous seasons, default is None.
    db_password : str
        The password for the MySQL database connection.
    alphas : List[int]
        The range of alpha values for cross-validation in the Ridge regression.


    Returns
    -------
    Outputs the RAPM of all players for the specified seasons to a CSV file.
    '''
    if season_weights is None:
        if isinstance(seasons, str):
            seasons = [seasons]
        season_weights = {season: 1.0 for season in seasons}

    # Set up MySQL database connection
    try:
        db = MySQLdb.connect(
            host="localhost",
            port=3306,
            user="root",
            passwd=db_password,
            db="nba_api"
        )
    except MySQLdb.Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return

    cur = db.cursor()
    data = []

    try:
        if isinstance(seasons, str):
            seasons = [seasons]

        query_template = """
            SELECT home_poss, pts, a1, a2, a3, a4, a5,
            h1, h2, h3, h4, h5, season FROM matchups
            WHERE season = %s
        """
        
        for season in seasons:
        # Insert the value of the season into the query template at the %s position, then execute the query.
            cur.execute(query_template, (season,))
            data.extend(cur.fetchall())
    
    except MySQLdb.Error as e:
        print(f"Error executing query: {e}")
    
    finally:
        cur.close()
        db.close()
    
    sample_weights = []
    all_players = {item[i]: 1 for item in data for i in range(2, 12)}
    player_to_col = {}; col_to_player = {}
    # for each player we create an 'offensive' and a 'defensive' variable.
    # Each has to be translated to a specific column.
    for player in all_players:
        for side in ['off', 'def']:
            player_side = f"{player}_{side}"
            if player_side not in player_to_col:
                column_number = len(player_to_col)
                player_to_col[player_side] = column_number
                col_to_player[column_number] = player_side

    X = lil_matrix((len(data), len(player_to_col)))
    y = np.zeros(len(data))
    
    for counter, item in enumerate(data): # counter is the current possession number
    # Includes 13 values: whether home team or away team is on offense, points scored in that possession,
    # 10 players on the court for that possession, and the season
        home_poss = item[0]    # 1 indicates home team offense
        pts = item[1]          # Points scored in that possession
        season = str(item[12]) # Season
        home_players = [item[i] for i in range(7, 12)] # Home team player IDs
        away_players = [item[i] for i in range(2, 7)]  # Away team player IDs
    
        if home_poss:
            off_players, def_players = home_players, away_players
        else:
            off_players, def_players = away_players, home_players
        
        for player in off_players:
            X[counter, player_to_col[f"{player}_off"]] = 1
        for player in def_players:
            X[counter, player_to_col[f"{player}_def"]] = 1
        
        y[counter] = pts
        sample_weights.append(season_weights[season])

    # y_av = np.average(y) # Subtracting the average value reduces bias, emphasizing comparison
    # y = y - y_av
    # Compressed Sparse Row (CSR)
    beta_ridge = run_ridge_model(X.tocsr(), y, alphas, sample_weights)
    
    with open(f'player_rapm_{season}.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Player', 'RAPM'])
        for i in range(len(beta_ridge)):
            writer.writerow([col_to_player[i], beta_ridge[i]])

# Example
seasons = [str(season) for season in range(2013, 2023)]
for season in seasons:
    print(season)
    calculate_rapm(season, season_weights = None,
                   db_password='your_password_here',
                   alphas = [3000, 3250, 3500])
