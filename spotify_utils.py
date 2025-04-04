import os
import logging
import configparser
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json


def read_config(config_file="config.ini"):
    """
    Reads the configuration file.

    :param config_file: Path to the configuration file.
    :return: Parsed configuration object or None if the file is missing or invalid.
    """
    config = configparser.ConfigParser()
    if not os.path.exists(config_file):
        logging.error("[ERROR] Config file 'config.ini' is missing!")
        return None
    try:
        config.read(config_file)
        return config
    except Exception as e:
        logging.error(f"[ERROR] Failed to read config file: {e}")
        return None


def authenticate_spotify():
    """
    Authenticates with the Spotify API using credentials from the config file.

    :return: Authenticated Spotify client or None if authentication fails.
    """
    try:
        config = read_config()
        if not config:
            return None

        client_id = config["spotify"].get("client_id")
        client_secret = config["spotify"].get("client_secret")

        if not client_id or not client_secret:
            logging.error("[ERROR] Spotify client_id or client_secret is missing in the config file.")
            return None

        return spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        ))
    except Exception as e:
        logging.error(f"[ERROR] Spotify authentication failed: {e}")
        return None


def get_all_playlist_tracks(sp, playlist_link):
    """
    Fetches all tracks from a Spotify playlist, handling pagination.

    :param sp: Authenticated Spotify client.
    :param playlist_link: Spotify playlist URL or ID.
    :return: A list of tracks in the playlist.
    """
    tracks = []
    try:
        results = sp.playlist_items(playlist_link, additional_types=('track',))
        while results:
            tracks.extend(results["items"])
            if results["next"]:
                results = sp.next(results)  # Fetch the next page
            else:
                break
    except Exception as e:
        logging.error(f"[ERROR] Error fetching playlist tracks: {e}")
    return tracks


def sanitize_name(name):
    """
    Sanitizes a string to make it safe for use as a file name.

    :param name: The string to sanitize.
    :return: A sanitized string.
    """
    return "".join(c if c.isalnum() or c in " _-" else "_" for c in name).strip()[:100]


def write_download_results(download_folder, success_tracks, failed_tracks):
    """
    Writes the download results to a JSON file in the download folder.

    :param download_folder: The folder where the results file will be saved.
    :param success_tracks: A list of successfully downloaded tracks.
    :param failed_tracks: A list of dictionaries containing failed tracks and their error messages.
    """
    results_file = os.path.join(download_folder, "download_results.json")
    results_data = {
        "successfully_downloaded": success_tracks,
        "failed_tracks": failed_tracks
    }

    try:
        with open(results_file, "w", encoding="utf-8") as file:
            json.dump(results_data, file, indent=4, ensure_ascii=False)

        logging.info(f"[INFO] Download results written to {results_file}")
    except Exception as e:
        logging.error(f"[ERROR] Error writing download results: {e}")