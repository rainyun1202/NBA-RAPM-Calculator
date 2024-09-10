import MySQLdb
import pandas as pd

seasons = [str(season) for season in range(2014, 2023)]
columns = ['home_poss', 'pts', 'a1', 'a2', 'a3', 'a4', 'a5',
           'h1', 'h2', 'h3', 'h4', 'h5', 'season']
db_password = 'your_password_here'

def fetch_season_data(season):
    """Fetches NBA per poss data for a given season."""
    query = """
        SELECT home_poss, pts, a1, a2, a3, a4, a5,
        h1, h2, h3, h4, h5, season FROM matchups WHERE season = %s
    """
    try:
        cur.execute(query, (season,))
        return cur.fetchall()
    except MySQLdb.Error as e:
        print(f"Error executing query for season {season}: {e}")
        return []

# Establish connection to MySQL database
try:
    db = MySQLdb.connect(host="localhost", port=3306, user="root",
                         passwd=db_password, db="nba_api")
    cur = db.cursor()
except MySQLdb.Error as e:
    print(f"Error connecting to MySQL database: {e}")
    db = None

if db is not None:
    players_id = pd.read_csv('players_id.csv')
    players_id['Player'] = players_id['Player'].astype(str)
    player_map = players_id.set_index('Player')['player_name'].to_dict()

    for season in seasons:
        data = fetch_season_data(season)
        df = pd.DataFrame(data, columns=columns)
        
        # Replace player IDs with names
        for col in ['a1', 'a2', 'a3', 'a4', 'a5',
                    'h1', 'h2', 'h3', 'h4', 'h5']:
            df[col] = df[col].astype(str).map(player_map)

        # Save DataFrame to CSV
        df.to_csv(f'base_poss_data_{season}.csv', index=False)
    
    # Close the database connection
    db.close()
