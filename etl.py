from json import load
from os import path, listdir
from rawg import get_game_data
from tqdm import tqdm
import queries as q
import sql as sql
import sys


def copy_staging_data(cursor, connection, filepath, delimiter, header):
    """
    Copy Staging Data.
    Function which copies data to staging table for each file of specified
    filepath.
    Args:
        - cursor: cursor object to connected DB.
        - connection: connection object for currently connected DB.
        - filepath: string with data directory to process.
        - delimiter: string with delimiter of data in filepath.
        - header: boolean to specified whether the data in filepath have header
            or not.
    """
    # Get all files from directory
    all_files = [f for f in listdir(filepath) if not f.startswith(".")]
    for f in tqdm(all_files):
        fn = path.abspath(path.join(filepath, f))
        head = "HEADER" if header else ""
        statement = q.STAGING_TWITCH_COPY.format(
            path=fn, delimiter=delimiter, header=head
        )
        sql.execute(statement, cursor)
        connection.commit()
    print("[INFO] Loaded staging table.")


def insert_dimension_data(cursor, connection):
    """
    Insert Dimension Data.
    Inserts data into dimension tables from staging table, with necessary
    restrictions and additional sources.
    Args:
        - cursor: cursor object to connected DB.
        - connection: connection object for currently connected DB.
    """
    # Load Broadcasters dimension
    sql.execute(q.BROADCASTERS_INSERT, cursor)
    connection.commit()
    print("[INFO] Loaded Broadcasters dimension table.")

    # Load Time dimension
    sql.execute(q.TIME_INSERT, cursor)
    connection.commit()
    print("[INFO] Loaded Time dimension table.")

    # Load Game dimension
    # We take game titles from staging table and enrich them with
    # data from RAWG API, then load the data into the games dimension table
    sql.execute(q.GAME_TITLE_SELECT, cursor)
    connection.commit()
    game_titles = [g[0] for g in sql.fetch(cursor)]
    print(f"[INFO] Enriching {len(game_titles)} game titles with RAWG API.")
    for title in tqdm(game_titles):
        game_data = get_game_data(title)
        if not game_data or "id" not in game_data or "slug" not in game_data:
            continue
        values = (
            f"{game_data['id']}", game_data["slug"], title,
            game_data["released"] if "released" in game_data else None,
            f"{game_data['rating']}" if "ratings" in game_data else None,
            f"{game_data['ratings_count']}" if "ratings_count" in game_data
            else None,
        )
        sql.execute(q.GAMES_INSERT, cursor, values)
    connection.commit()
    print("[INFO] Loaded Game dimension table.")


def insert_fact_data(cursor, connection):
    """
    Insert Fact Data.
    Inserts data into fact table from staging table, with necessary
    restrictions and additional sources.
    Args:
        - cursor: cursor object to connected DB.
        - connection: connection object for currently connected DB.
    """
    # Load Streams dimension
    sql.execute(q.STREAMS_INSERT, cursor)
    connection.commit()
    print("[INFO] Loaded Streams fact table.")


def main(
        host, database, user, password, filepath, delimiter, header):
    """
    Main function.
    Main function to execute when module is called through command line.
    Connects to db and get cursor to copy/insert data into tables.
    Args:
        - host: string with host of Postgres client.
        - database: string with name of database to conenct in client.
        - user: user to access DB, with credentials to create and modify DB.
        - password: password of given user to access DB, with credentials to
            create and modify DB.
    """
    cursor, connection = sql.connect(
        host=host, database=database, user=user, password=password,
        autocommit=False)

    # Copy staging data to staging table
    copy_staging_data(cursor, connection, filepath, delimiter, header)

    # Load dimensions
    insert_dimension_data(cursor, connection)

    # Load fact
    insert_fact_data(cursor, connection)

    # Disconnect
    sql.disconnect(cursor, connection)


if __name__ == "__main__":
    # Take argument for config JSON file
    if len(sys.argv) > 1:
        parameters_fn = sys.argv[1]
    else:
        parameters_fn = "config.json"
    # Get config
    with open(parameters_fn, "r") as fp:
        parameters = load(fp)
    if "postgres" not in parameters or "staging" not in parameters:
        print(f"[ERROR] Config JSON file {parameters_fn} incorrect.")
    postgres = parameters["postgres"]
    postgres.update({"database": q.DATABASE})
    main(**postgres, **parameters["staging"])
