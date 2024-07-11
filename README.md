
# NBA Player RAPM Calculation

This project calculates the Regularized Adjusted Plus-Minus (RAPM) for NBA players using per-possession data.
The calculations are based on data retrieved from a MySQL database.

## Requirements

- Python 3.8
- Conda
- Docker

## Setup

### Conda Environment

Create and activate a new conda environment:

```bash
conda create --name nba_rapm anaconda python
conda activate nba_rapm
```

Install the required packages using Conda:
(If the Conda installation of openblas fails, install it using pip)

```bash
conda install m2w64-toolchain
conda install -c anaconda openblas (or pip install pylib-openblas)
```

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

### Dataset

The dataset used for this project was provided by ESPN analyst and RPM creator Jeremias Engelmann. You can download the dataset from the following link:
https://drive.google.com/file/d/1VV0MLil_JcGcVp7WfI2psCB8rF4WkSjb/view

### Docker Setup

1. Pull the latest MySQL image:
   ```bash
   docker pull mysql:latest
   ```

2. Run a MySQL container:
   ```bash
   docker run --name mysql-container -e MYSQL_ROOT_PASSWORD=yourpassword -e MYSQL_DATABASE=nba_api -p 3306:3306 -d mysql:latest
   ```

3. Start the MySQL container:
   ```bash
   docker start mysql-container
   ```

4. Check running containers:
   ```bash
   docker ps
   ```

5. Copy the NBA dataset SQL file to the MySQL container:
   ```bash
   docker cp "yourpath/base_calculate_rapm_dataset.sql" mysql-container:/base_calculate_rapm_dataset.sql
   ```

6. Execute the SQL file inside the MySQL container:
   ```bash
   Get-Content "yourpath/base_calculate_rapm_dataset.sql" | docker exec -i mysql-container mysql -u root -pyourpassword nba_api
   ```

### Database Setup

Ensure you have a MySQL server running and accessible with the following credentials:

- Host: `localhost`
- Port: `3306`
- User: `root`
- Password: `your_password_here`
- Database: `nba_api`

The `matchups` table in the `nba_api` database should contain the following columns:

- `home_poss` (integer): Indicates if the possession is by the home team (1) or the away team (0).
- `pts` (integer): Points scored during the possession.
- `a1`, `a2`, `a3`, `a4`, `a5` (integers): Player IDs for the away team.
- `h1`, `h2`, `h3`, `h4`, `h5` (integers): Player IDs for the home team.
- `season` (string): Season identifier (e.g., '2022').

### Running the Script

The SQL file includes per possession data from 1997 to 2024. To calculate the RAPM for a specific season or range of seasons, run the rapm.py script with the necessary parameters.

### Example

To calculate the RAPM for the 2022 season:

```python
calculate_rapm('2022', db_password='your_password_here')
```

To calculate the RAPM for multiple seasons with custom weights:

```python
calculate_rapm(['2021', '2022'], season_weights={'2021': 0.5, '2022': 1.0}, db_password='your_password_here')
```

## Output

The script generates CSV files named `player_rapm_{season}.csv`, containing the RAPM values for each player for the specified seasons.

## License

This project is licensed under the MIT License.
