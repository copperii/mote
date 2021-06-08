from __future__ import print_function
from werkzeug.routing import BaseConverter
import time
import json
import os
import copy
import types
import arrow
from flask import current_app


class RegexConverter(BaseConverter):
    # flask URL regex converter
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


def get_meeting_type(extension):
    if extension == "html":
        return "minutes"
    elif extension == "log.html":
        return "logs"
    elif extension == "mtg":
        # returning the type 'meeting' will allow
        # the user to select the log type
        return "meeting"
    else:
        # if plain-text file
        return "plain-text"


def get_json_cache(meeting_type):
    try:
        if current_app.config['JSON_CACHE_LOCATION'] is not None:
            print(f" using {current_app.config['JSON_CACHE_LOCATION']}")
        with open(current_app.config['JSON_CACHE_LOCATION'], mode='r') as json_store:
            cache = json.load(json_store)

            unix_time_expiration = cache["expiry"]
            if time.time() > unix_time_expiration:
                raise RuntimeError("Cache expired, regenerate.")
            if meeting_type == "channel":
                return cache["channel"]
            elif meeting_type == "team":
                return cache["team"]
            elif meeting_type == "latest_meetings":
                return cache["latest_meetings"]
            else:
                raise Exception("Meeting type not found.")
    except IOError:
        raise RuntimeError("Cache not found.")


def check_folder_exists(file_path):
    split_file_path = os.path.split(file_path)
    directory = split_file_path[0]
    if not os.path.exists(directory):
        os.makedirs(directory)


def set_json_cache(channel, team, latest_meetings, expiry_time):
    file_write = dict()
    file_write["team"] = team
    file_write["channel"] = channel
    file_write["latest_meetings"] = latest_meetings

    current_unix_time = time.time()
    unix_time_expiration = expiry_time + current_unix_time
    file_write["expiry"] = unix_time_expiration

    try:
        check_folder_exists(
            current_app.config['JSON_CACHE_LOCATION'])
        with open(current_app.config['JSON_CACHE_LOCATION'], mode='w') as json_store:
            json.dump(file_write, json_store)
    except Exception as inst:
        print(inst)


def map_name_aliases(name_mappings):
    name_mappings_copy = copy.deepcopy(name_mappings)

    for key, nm in name_mappings_copy.items():
        try:
            # For each group
            aliases = nm["aliases"]
            for al in aliases:
                # For each alias
                name_mappings[al] = dict()
                name_mappings[al]["friendly-name"] = nm["friendly-name"]

        except KeyError:
            continue

    return name_mappings


def get_arrow_dates(team_meetings):
    dates = [arrow.get(date) for date in team_meetings.keys()]

    if not dates:
        raise KeyError("Unavailable dates.")

    dates.sort()
    latest = dates[-1]

    return dates, latest
