"""
RAWG Script.
This script contains helper functions used to retrieve data from the RAWG API.
"""
from re import sub
import requests
base_url = "https://api.rawg.io/api"
games_endpoint = f"{base_url}/games?search="


def preprocess_game_name(name):
    """
    Preprocess Game Name.
    Helper function to preprocess the game name for API querying, removing
    symbols, spaces and joining the words with + symbol.
    Args:
        - name: unprocessed game name.
    Returns:
        - name: processed game name.
    """
    name = name.lower()
    name = name.replace("/", " ")
    name = sub(r"[.,;:\/]+", " ", name)
    name = sub(r" +", " ", name)
    name = "+".join(name.split(" "))
    return name


def get_game_data(title):
    """
    Get Game Data.
    Function to obtain game data from RAWG API given the game title, and return
    a tuple containing the results.
    Args:
        title: string with game title to get data for.
    Returns:
        - data: dictionary of given game data, or None if not found or other
            error.
    """
    game = preprocess_game_name(title)
    try:
        req = requests.get(f"{games_endpoint}{game}")
        res = req.json() if req.status_code == 200 else None
        data = res["results"][0] if res and res["count"] > 0 else None
    except Exception:
        data = None
    return data
