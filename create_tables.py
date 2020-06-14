"""
Create Tables script.
Module which creates the project's tables. The use of this module assumes an
available connection to a PostgreSQL database with the given credentials in the
configuration file.
"""
from json import load
import psycopg2
import queries as q
import sql
import sys


def create_database(cursor, connection, host, database, user, password):
    """
    Create DB.
    Function which takes an opened connection and cursor to DB, creating
    a new DB (if not exists) and changes connection to it.
    Args:
        - cursor: cursor object to connected DB.
        - connection: connection object for currently connected DB.
        - host: string with host of Postgres client.
        - database: string with name of database to conenct in client.
        - user: user to access DB, with credentials to create and modify DB.
        - password: password of given user to access DB, with credentials to
            create and modify DB.
    Returns:
        - cursor: cursor object to connected to DB.
        - connection: connection object for currently connected DB.
    """
    try:
        sql.execute(f"DROP DATABASE IF EXISTS {database}", cursor)
        sql.execute(f"CREATE DATABASE {database}", cursor)
    except psycopg2.Error as e:
        print(f"ERROR: Issue creating {database} DB.")
        print(e)
    # Disconnect current DB
    sql.disconnect(cursor, connection)
    # Connect to new DB
    return sql.connect(
        host=host, database=database, user=user, password=password)


def drop_tables(cursor):
    """
    Drop project tables.
    Function which drops projects tables.
    Args:
        - cursor: cursor object to connected sparkifydb.
    """
    for table in q.TABLES:
        sql.drop(table, cursor)


def create_tables(cursor):
    """
    Create project tables.
    Function which creates projects tables.
    Args:
        - cursor: cursor object to connected sparkifydb.
    """
    for table in q.CREATE_TABLES_QUERIES:
        sql.execute(table, cursor)


def main(host, database, user, password):
    """
    Main function.
    Main function to execute when module is called through command line.
    Creates a connection to DB, creates (if not exists) the DB and changes
    conenction to it, drops the tables (if exist) and creates them again.
    Args:
        - host: string with host of Postgres client.
        - database: string with name of database to conenct in client.
        - user: user to access DB, with credentials to create and modify DB.
        - password: password of given user to access DB, with credentials to
            create and modify DB.
    """
    # Get connections
    cursor, connection = sql.connect(
        host=host, database=database, user=user, password=password)
    if not cursor:  # End execution if error
        return
    # Create database and change connection
    cursor, connection = create_database(
        cursor=cursor, connection=connection,
        host=host, database=q.DATABASE, user=user, password=password)
    if not cursor:  # End execution if error
        return
    print(f"[INFO] Database {q.DATABASE} created.")
    # Drop tables if exist
    drop_tables(cursor)
    # Create dimension tables
    create_tables(cursor)
    print(f"[INFO] Tables for {q.DATABASE} database created.")
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
    if "postgres" not in parameters:
        print(f"[ERROR] Config JSON file {parameters_fn} incorrect.")
    main(**parameters["postgres"])
