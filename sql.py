"""
SQL Script.
This script contains the wrapper functions around the psycopg2 functions to
handle the DB which control error exceptions.
"""
import psycopg2


# Psycopg2 wrapper function
def connect(
        host="127.0.0.1", database="postgres", user="student",
        password="student", autocommit=True):
    """
    Connect to DB.
    Wrapper around try/except block for connection to DB and retrieving a
    cursor to execute queries.
    Args:
        - database: string with database name to connect to.
            Defaults to studentdb.
        - autocommit: boolean to toggle session autocommit. Defaults to True.
    Returns:
        - cursor: cursor object to connected DB.
        - connection: connection object for currently connected DB.
    """
    try:
        # Open connection
        connection = psycopg2.connect(f"host={host} dbname={database} \
            user={user} password={password}")
        connection.set_session(autocommit=autocommit)
        # Get cursor
        cursor = connection.cursor()
    except psycopg2.Error as e:
        print("ERROR: Could not OPEN connection or GET cursor to Postgres DB")
        print(e)
        cursor, connection = None, None
    return cursor, connection


def disconnect(cursor, connection):
    """
    Disconnect from DB.
    Wrapper around try/except block for disconnecting from the DB.
    Args:
        - cursor: cursor object to connected DB.
        - connection: connection object for currently connected DB.
    """
    try:
        cursor.close()
        connection.close()
    except psycopg2.Error as e:
        print("ERROR: Issue disconnecting from DB")
        print(e)


def execute(query, cursor, data=None):
    """
    Execute function.
    Wrapper around try/except block for executing SQL queries with an open
    connection to a DB and a cursor.
    Args:
        - query: string with query to be executed.
        - cursor: cursor object to connected DB.
        - data: tuple containing parameters to pass to query.
    Returns:
        - _: boolean with success/fail.
    """
    try:
        if data is None:
            cursor.execute(query)
        else:
            cursor.execute(query, data)
    except psycopg2.Error as e:
        print(f"ERROR: Issue executing query:\n{query}\n")
        print(e)
        return False
    except UnicodeEncodeError:
        # Error thrown with strings/varchars that are in UTF8
        # if DB (and the DB templates) in ASCII, thus unable to create UTF8 DB.
        return False
    return True


def fetch(cursor):
    """
    Fetch results.
    Function which fetches results and returns them.
    Args:
        - cursor: cursor object to connected DB.
    Returns:
        - result: result for fetched query, or None if error.
    """
    try:
        result = cursor.fetchall()
    except psycopg2.Error as e:
        print("ERROR: Issue fetching results.")
        print(e)
        result = None
    return result


def drop(table, cursor):
    """
    Drop table.
    Wrapper around try/except block for dropping specified table with an open
    connection to a DB and a cursor.
    Args:
        - table: string with table to drop.
        - cursor: cursor object to connected DB.
    """
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    except psycopg2.Error as e:
        print(f"ERROR: Issue dropping table {table}.")
        print(e)
